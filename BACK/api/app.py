
import io
import os
import hashlib
import secrets
import logging
from datetime import timedelta

from werkzeug.middleware.proxy_fix import ProxyFix

from flask                     import (Flask,request,render_template,send_file,jsonify,redirect,url_for,session)
from BACK.modules.bonus_module import (add_user,pdfTurn,get_user,pdfRead,delet_pdfs)
from BACK.modules.gmail_module import (gmail_inbox,attachment,get_curriculum,fb_send_curriculum,fb_get_curriculum,baixar_pdf_curriculo)
from BACK.authentication       import google_login
from BACK.llm.llm              import (bonus_llm_process,command_process,curriculo_llm_process)
from BACK.modules.desligamento_module import get_desligamentos, get_contratacoes

BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONT_DIR = os.path.join(BASE_DIR, "FRONT")

app = Flask( __name__,template_folder=FRONT_DIR,
    static_folder=os.path.join(FRONT_DIR, "static"),
    static_url_path="/static"
)

# O Render termina o HTTPS no proxy e repassa a requisição em HTTP.
# Sem isso o Flask acharia que o site é http:// e o login quebraria.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def _chave_secreta():
    """
    FLASK_SECRET_KEY deve ser definida no Render. Na falta dela, deriva
    uma chave estável do client_secret do Google, para que todos os
    workers do gunicorn (e os reinícios) aceitem os mesmos cookies.
    """
    chave = os.getenv("FLASK_SECRET_KEY")
    if chave:
        return chave

    try:
        with open(google_login.caminho_credenciais(), "rb") as arquivo:
            return hashlib.sha256(b"motomar-session:" + arquivo.read()).hexdigest()
    except FileNotFoundError:
        return secrets.token_hex(32)


app.secret_key = _chave_secreta()

# Endereço público do sistema. No Render, RENDER_EXTERNAL_URL já vem
# preenchida (ex.: https://rh-motomar.onrender.com).
APP_BASE_URL = (
    os.getenv("APP_BASE_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
    or "http://127.0.0.1:2000"
).rstrip("/")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=APP_BASE_URL.startswith("https://"),
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

logging.basicConfig(
    filename=os.path.join(BASE_DIR, "erro_motomar.log"),
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


@app.before_request
def log_request():
    print(f"Requisição: {request.method} {request.path}")


@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    # Não registra favicon ausente como erro interno.
    if request.path == "/favicon.ico":
        return "", 404

    return jsonify({
        "success": False,
        "message": "Rota não encontrada."
    }), 404


@app.errorhandler(Exception)
def registrar_erro(erro):
    app.logger.exception("Erro interno na aplicação")

    return jsonify({
        "success": False,
        "message": str(erro)
    }), 500


# ============================================================
# PÁGINAS
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/curriculo")
def curriculo():
    usuario = google_login.usuario_logado()

    if not usuario:
        return redirect(url_for("login_google", next="/curriculo"))

    return render_template("curriculo.html", usuario=usuario)


# ============================================================
# LOGIN COM GOOGLE
# ============================================================

# O endereço de retorno do Google é APP_BASE_URL + /oauth2callback e
# precisa estar cadastrado exatamente assim no cliente OAuth (tipo Web).
HOSTS_LOCAIS = ("127.0.0.1", "localhost", "[::1]")


def _redirect_uri():
    return f"{APP_BASE_URL}/oauth2callback"


def _host_atual():
    return request.host.rsplit(":", 1)[0] if not request.host.startswith("[") \
        else request.host.split("]")[0] + "]"


@app.route("/login-google")
def login_google():
    destino = request.args.get("next", "/curriculo")
    destino = destino if destino.startswith("/") else "/curriculo"

    base_atual = request.host_url.rstrip("/")

    if base_atual != APP_BASE_URL:

        # Mesmo computador, outro nome (ex.: localhost x 127.0.0.1):
        # troca para o endereço oficial antes de começar, senão o
        # cookie da sessão não volta junto com a resposta do Google.
        if _host_atual() in HOSTS_LOCAIS:
            return redirect(f"{APP_BASE_URL}/login-google?next={destino}")

        # Endereço não cadastrado no Google: ele recusaria o retorno
        # com o erro redirect_uri_mismatch.
        return render_template(
            "login_erro.html",
            mensagem=(
                f"O login com o Google não funciona pelo endereço {base_atual}. "
                f"Acesse o sistema por {APP_BASE_URL}."
            )
        ), 400

    session["google_next"] = destino

    return redirect(google_login.url_de_login(_redirect_uri()))


@app.route("/oauth2callback")
def oauth2callback():
    if request.args.get("error"):
        return render_template(
            "login_erro.html",
            mensagem="O login com o Google foi cancelado ou negado."
        ), 401

    try:
        google_login.concluir_login(_redirect_uri(), request.url)
    except Exception:
        app.logger.exception("Erro ao concluir login com o Google")
        return render_template(
            "login_erro.html",
            mensagem="Não foi possível concluir o login com o Google."
        ), 500

    return redirect(session.pop("google_next", "/curriculo"))


@app.route("/logout-google")
def logout_google():
    google_login.sair()
    return redirect(url_for("index"))


def _gmail_ou_401():
    gmail = google_login.servico_gmail()

    if gmail is None:
        return None, (jsonify({
            "success": False,
            "login_required": True,
            "message": "Sua sessão do Google expirou. Entre novamente."
        }), 401)

    return gmail, None



@app.route("/desligamento")
def desligamento():
    return render_template("desligamento.html")


# ============================================================
# BÔNUS — CADASTRO E BUSCA
# ============================================================

@app.route("/cadastrar", methods=["POST"])
def add():
    nome  = request.form.get("nome")
    tipo  = request.form.get("tipo")
    meta  = int(request.form.get("meta"))
    motos = int(request.form.get("motos"))
    pops  = int(request.form.get("pops"))
    vendas_card  = int(request.form.get("vendas_card"))
    vendas_other = int(request.form.get("vendas_other"))

    add_user(nome,tipo,meta,motos,pops,vendas_card,vendas_other)

    vendedor = get_user(nome)

    return render_template(
        "index.html",
        vendedores=vendedor
    )


@app.route("/buscar", methods=["POST"])
def buscar_vendedor():
    
    nome     = request.form.get("nome")
    vendedor = get_user(nome)

    return render_template("index.html",vendedores=vendedor)


# ============================================================
# BÔNUS — EXPORTAÇÃO
# ============================================================

@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():
    
    vendedores = get_user("all")
    pdf        = pdfTurn(vendedores)

    return send_file(pdf,mimetype="application/pdf",as_attachment=True,download_name="relatorio_vendedores.pdf")


# ============================================================
# BÔNUS — PROCESSAMENTO DE PDFs
# ============================================================

@app.route("/processar-pdfs", methods=["POST"])
def processar_pdfs():
   
    pdf = pdfRead()

    bonus_llm_process(pdf)

    delet_pdfs()

    vendedores = get_user("all")

    return render_template("index.html",vendedores=vendedores)


@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
   
    pdf_dir = os.path.join(BASE_DIR, "PDF")
    os.makedirs(pdf_dir, exist_ok=True)

    arquivos = request.files.getlist("arquivos")

    for arquivo in arquivos:
        if not arquivo or not arquivo.filename:
            continue

        if not arquivo.filename.lower().endswith(".pdf"):
            continue

        caminho = os.path.join(pdf_dir, os.path.basename(arquivo.filename))
        arquivo.save(caminho)

    return render_template("index.html")


# ============================================================
# BÔNUS — COMANDOS POR IA
# ============================================================

@app.route("/llm", methods=["POST"])
def ia():
    
    context    = request.form.get("comando", "").strip()
    resultado  = command_process(context)
    vendedores = get_user("all")

    return render_template("index.html",vendedores=vendedores,resultado=resultado)


# ============================================================
# CURRÍCULOS — IMPORTAÇÃO DO GMAIL PARA FIREBASE
# ============================================================

@app.route("/push", methods=["POST"])
def processes_email_curriculum():
    
    gmail, erro = _gmail_ou_401()
    if erro:
        return erro

    try:
        quant_curriculo = request.args.get(
            "quant_curriculo",
            default=20,
            type=int
        )

        inbox      = gmail_inbox(gmail, quant_curriculo)
        anexos     = attachment(gmail, inbox)
        curriculos = get_curriculum(anexos)
        resultado  = fb_send_curriculum(curriculos, session.get("google_email", ""))

        return jsonify({
            "success": True,
            "message": "Processamento dos currículos concluído.",
            "quantidade": len(curriculos),
            "resultado": resultado
        }), 200

    except Exception as erro:
        app.logger.exception("Erro ao importar currículos")

        return jsonify({
            "success": False,
            "message": str(erro)
        }), 500


# ============================================================
# CURRÍCULOS — LISTAGEM
# ============================================================

@app.route("/buscar-curriculos", methods=["GET"])
def list_curriculos():
    
    try:
        
        curriculos = fb_get_curriculum("all")

        return jsonify(curriculos or []), 200

    
    except Exception as erro:
        
        app.logger.exception("Erro ao buscar currículos")

        return jsonify({
            "success": False,
            "message": str(erro)
        }), 500


# ============================================================
# CURRÍCULOS — DOWNLOAD DO PDF DO CANDIDATO
# ============================================================

@app.route("/curriculo/<curriculo_id>/pdf", methods=["GET"])
def baixar_curriculo_pdf(curriculo_id):

    gmail, erro = _gmail_ou_401()
    if erro:
        return erro

    try:
        resultado = baixar_pdf_curriculo(gmail, curriculo_id)

    except Exception as erro_gmail:
        status = getattr(getattr(erro_gmail, "resp", None), "status", None)

        if status == 404:
            documento = fb_get_curriculum(curriculo_id) or {}
            dono = documento.get("importado_por")

            return jsonify({
                "success": False,
                "message": (
                    f"Este e-mail não está na sua caixa de entrada. "
                    f"Ele foi importado por {dono}." if dono else
                    "Este e-mail não foi encontrado na sua caixa de entrada do Gmail."
                )
            }), 404

        app.logger.exception("Erro ao baixar PDF do currículo")
        return jsonify({"success": False, "message": "Erro ao buscar o PDF no Gmail."}), 500

    if not resultado:
        return jsonify({
            "success": False,
            "message": "Nenhum PDF foi encontrado neste e-mail."
        }), 404

    conteudo, nome = resultado

    return send_file(
        io.BytesIO(conteudo),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome
    )


# ============================================================
# CURRÍCULOS — ANÁLISE INDIVIDUAL
# ============================================================

@app.route("/analise", methods=["POST"])
def analise_curriculo():
    
    try:
        
        dados        = request.get_json(silent=True) or {}
        curriculo_id = dados.get("curriculo_id")

        if not curriculo_id:
            
            return jsonify({
                "success": False,
                "message": "O ID do currículo não foi enviado."
            }), 400

      
        # Passa o ID recebido para a função de IA.
        resultado = curriculo_llm_process(curriculo_id=str(curriculo_id))

        if not isinstance(resultado, dict):
            return jsonify({
                "success": False,
                "message": "A IA retornou um resultado inválido."
            }), 500

        if resultado.get("erro"):
            return jsonify({
                "success": False,
                "message": resultado["erro"]
            }), 422

        return jsonify({
            "success": True,
            "message": "Análise concluída.",
            "resultado": resultado
        }), 200

    except Exception as erro:
        app.logger.exception("Erro na rota /analise")

        return jsonify({
            "success": False,
            "message": str(erro)
        }), 500





@app.route("/api/desligamentos", methods=["GET"])
def api_desligamentos():
    try:
        desligamentos = get_desligamentos()

        return jsonify({
            "success": True,
            "quantidade": len(desligamentos),
            "desligamentos": desligamentos
        }), 200

    except Exception:
        app.logger.exception("Erro ao buscar desligamentos no Firebase")

        return jsonify({
            "success": False,
            "message": "Erro ao buscar os desligamentos."
        }), 500
        
        
@app.route("/api/contratacoes", methods=["GET"])
def api_contratacoes():
    try:
        contratacoes = get_contratacoes()

        return jsonify({
            "success": True,
            "quantidade": len(contratacoes),
            "contratacoes": contratacoes
        }), 200

    except Exception:
        app.logger.exception(
            "Erro ao buscar contratações no Firebase"
        )

        return jsonify({
            "success": False,
            "message": "Erro ao buscar as contratações."
        }), 500
# ============================================================
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=2000,
        debug=False
    )
