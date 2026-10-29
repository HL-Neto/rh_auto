
import os
import logging

from flask import (
    Flask,
    request,
    render_template,
    send_file,
    jsonify
)

from BACK.modules.bonus_module import (
    add_user,
    pdfTurn,
    get_user,
    pdfRead,
    delet_pdfs
)

from BACK.modules.gmail_module import (
    gmail_inbox,
    attachment,
    get_curriculum,
    fb_send_curriculum,
    fb_get_curriculum
)

from BACK.llm.llm import (
    bonus_llm_process,
    command_process,
    curriculo_llm_process
)


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

FRONT_DIR = os.path.join(BASE_DIR, "FRONT")

app = Flask(
    __name__,
    template_folder=FRONT_DIR
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
    return render_template("curriculo.html")


# ============================================================
# BÔNUS — CADASTRO E BUSCA
# ============================================================

@app.route("/cadastrar", methods=["POST"])
def add():
    nome = request.form.get("nome")
    tipo = request.form.get("tipo")
    meta = int(request.form.get("meta"))
    motos = int(request.form.get("motos"))
    pops = int(request.form.get("pops"))
    vendas_card = int(request.form.get("vendas_card"))
    vendas_other = int(request.form.get("vendas_other"))

    add_user(
        nome,
        tipo,
        meta,
        motos,
        pops,
        vendas_card,
        vendas_other
    )

    vendedor = get_user(nome)

    return render_template(
        "index.html",
        vendedores=vendedor
    )


@app.route("/buscar", methods=["POST"])
def buscar_vendedor():
    nome = request.form.get("nome")
    vendedor = get_user(nome)

    return render_template(
        "index.html",
        vendedores=vendedor
    )


# ============================================================
# BÔNUS — EXPORTAÇÃO
# ============================================================

@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():
    vendedores = get_user("all")
    pdf = pdfTurn(vendedores)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="relatorio_vendedores.pdf"
    )


# ============================================================
# BÔNUS — PROCESSAMENTO DE PDFs
# ============================================================

@app.route("/processar-pdfs", methods=["POST"])
def processar_pdfs():
    pdf = pdfRead()

    bonus_llm_process(pdf)

    delet_pdfs()

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores
    )


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
    context = request.form.get("comando", "").strip()

    resultado = command_process(context)
    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores,
        resultado=resultado
    )


# ============================================================
# CURRÍCULOS — IMPORTAÇÃO DO GMAIL PARA FIREBASE
# ============================================================

@app.route("/push", methods=["POST"])
def processes_email_curriculum():
    try:
        quant_curriculo = request.args.get(
            "quant_curriculo",
            default=20,
            type=int
        )

        inbox = gmail_inbox(quant_curriculo)
        anexos = attachment(inbox)
        curriculos = get_curriculum(anexos)

        resultado = fb_send_curriculum(curriculos)

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
# CURRÍCULOS — ANÁLISE INDIVIDUAL
# ============================================================

@app.route("/analise", methods=["POST"])
def analise_curriculo():
    try:
        dados = request.get_json(silent=True) or {}
        curriculo_id = dados.get("curriculo_id")

        if not curriculo_id:
            return jsonify({
                "success": False,
                "message": "O ID do currículo não foi enviado."
            }), 400

        # Passa o ID recebido para a função de IA.
        resultado = curriculo_llm_process(
            curriculo_id=str(curriculo_id)
        )

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


# ============================================================
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=2000,
        debug=False
    )
