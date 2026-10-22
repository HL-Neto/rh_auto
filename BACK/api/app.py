import os
import logging
import traceback

from flask                      import Flask, request, render_template, send_file , jsonify
from BACK.modules.bonus_module  import ( add_user, pdfTurn, get_user , pdfRead,delet_pdfs) 
from BACK.modules.gmail_module  import ( gmail_inbox, attachment , get_curriculum , fb_send_curriculum , fb_get_curriculum)
from BACK.llm.llm               import ( bonus_llm_process, command_process, curriculo_llm_process )


"procura uma pasta usando como referencia a pasta principal"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FRONT_DIR = os.path.join(BASE_DIR, "FRONT")

"procura a pasta do front"
app = Flask( __name__, template_folder=os.path.join(BASE_DIR, "FRONT"))
@app.before_request

def log_request():
    print(f"Requisição: {request.method} {request.path}")

logging.basicConfig(
    filename="erro_motomar.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@app.errorhandler(Exception)
def registrar_erro(e):
    traceback.print_exc()
    app.logger.exception("Erro interno na aplicação")
    return "Erro interno. Consulte erro_motomar.log", 500




"// ROTAS //"

"define a rota principal"
@app.route("/")
def index():

    return render_template("index.html",)

"rota do  formulário de cadastro"
@app.route("/cadastro")
def cadastro():

    return render_template("cadastro.html")

@app.route("/curriculo")
def curriculo():

    return render_template("curriculo.html")



"// API  BONUS//"





"CADASTRO"
@app.route("/cadastrar", methods=["POST"])
def add():
    
    
    "pegas os dados do formulário"
    nome  = request.form.get("nome")
    tipo  = request.form.get("tipo")
    meta  = int(request.form.get("meta"))
    motos = int(request.form.get("motos"))
    pops  = int(request.form.get("pops"))
    vendas_card  = int(request.form.get("vendas_card"))
    vendas_other = int(request.form.get("vendas_other"))

    "manda para a função no module"
    add_user(nome, tipo, meta,motos, pops, vendas_card, vendas_other)
    
    "busca o vendedor que a gente acabou de add"
    vendedor = get_user(nome)
                        
    "retorna pro template e mostra o vendedor na barra de pesquisa"
    return render_template("index.html", vendedores = vendedor )





"BUSCA"
@app.route("/buscar", methods=["POST"])
def get():

    "recebe o nome do formulário e manda para a função no modulo"
    nome       = request.form.get("nome")
    vendedor  = get_user(nome)

    return render_template("index.html", vendedores = vendedor)





"EXPORTAR"

@app.route("/exportar-pdf", methods=["GET"])
def exportar_pdf():

    # Busca todos os vendedores
    vendedores = get_user("all")

    # Gera o PDF
    pdf = pdfTurn(vendedores)

    # Envia diretamente para o navegador
    return send_file( pdf, mimetype="application/pdf", as_attachment=True, download_name="relatorio_vendedores.pdf" )





"PROCESSAR PDF"
@app.route("/processar-pdfs", methods=["POST"])
def processar_pdfs():
    
    "processa os pdf"
    pdf = pdfRead()
    
    "ativa a llm"
    bonus_llm_process(pdf)
    
    "deleta os pdfs"
    delet_pdfs()
    
    "mostra os cendedores adicionados"
    vendedores = get_user("all")

    return render_template("index.html", vendedores = vendedores)





"MANDAR OS PDFS PARA O ARQUIVO PDF"
@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():

    "acha a pasta pdf"
    PDF_DIR = os.path.join(BASE_DIR, "PDF")

    "verifica se existe , se n existir ele cria"
    os.makedirs(PDF_DIR, exist_ok=True)

    "recebe os arquivos do front"
    arquivos = request.files.getlist("arquivos")
    
    "para cada arquivo"
    for arquivo in arquivos:

    
        "verifica se ta vazio"
        if not arquivo or not arquivo.filename:
            continue
        "verifica se é um pdf"
        if not arquivo.filename.lower().endswith(".pdf"):
            continue
        
        "manda o arquivo para pasta PDF"
        caminho = os.path.join(PDF_DIR, arquivo.filename)
        arquivo.save(caminho)


    return render_template("index.html")



"LLM"
@app.route("/llm", methods=["POST"])
def ia():

    "menssagem do usuário"
    context = request.form.get("comando","").strip()

    "resposta da llms"
    resultado = command_process(context)

    "mostra todos os vendedores para confirmar as auterações feitas"
    vendedores = get_user("all")

    return render_template("index.html", vendedores=vendedores, resultado=resultado)






"// API  CURRICULO//"


"envia os curriculos para o firebase"
@app.route("/push", methods=["POST"])
def processes_email_curriculum():
    
    quant_curriculo = request.args.get("quant_curriculo",default=20,type=int)
    
    "puxa o conteudo dos emails"
    inbox      = gmail_inbox(quant_curriculo) 
    "verifica se tem algum anexo e baixa ele em base 64"
    anexo      = attachment(inbox)
    "baixa os curriculos em base 64 e armazena suas informações"
    curriculos = get_curriculum(anexo)
    "manda os curriculos para o fb"
    resultado =  fb_send_curriculum(curriculos)

    return jsonify({
        "success": True,
        "message": "Processamento dos currículos concluído",
        "quantidade": len(curriculos),
        "resultado": resultado
    }), 200



"envia para llm analisar"
@app.route("/analise", methods=["POST"])
def analise_curriculo():
 

    resultado = curriculo_llm_process()
   
        
    return jsonify({
        "success": True,
        "message": "Análise concluída",
        "resultado": resultado
    }), 200
    
    
@app.route("/buscar-curriculos", methods = ["GET"])
def list_curriculos():
    
    result = fb_get_curriculum("all")
    
    return jsonify(result), 200
