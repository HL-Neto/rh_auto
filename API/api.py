import os

from flask           import Flask, request, render_template, redirect, url_for , send_file
from MODULLES.module import ( add_user, pdfTurn, get_user , pdfRead) 
from LLM.llm         import ( llm_process, command_process )


"procura uma pasta usando como referencia a pasta principal"
BASE_DIR = os.path.dirname( os.path.dirname( os.path.abspath(__file__)))

"procura a pasta do front"
app = Flask( __name__, template_folder=os.path.join(BASE_DIR, "FRONT")
)





"// ROTAS //"

"define a rota principal"
@app.route("/")
def index():

    return render_template("index.html",)

"rota do  formulário de cadastro"
@app.route("/cadastro")
def cadastro():

    return render_template("cadastro.html")



"// API //"





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
    llm_process(pdf)
    "mostra os cendedores adicionados"
    vendedores = get_user("all")

    return render_template("index.html", vendedores=vendedores)





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





if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )