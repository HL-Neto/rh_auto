import os
from flask  import Flask, request, render_template
from MODULLES.module import add_user , delet_user , get_user , pdfRead , edit_user
from LLM.llm  import llm


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
__name__,
template_folder=os.path.join(BASE_DIR, "templates")
)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cadastrar" , methods = ["POST"])
def add():

    
    nome  = request.form.get("nome")
    meta  = (request.form.get("meta"))
    motos = (request.form.get("motos"))
    pops  = (request.form.get("pops"))
    vendas_card  = (request.form.get("vendas_card"))
    vendas_other = (request.form.get("vendas_other"))

    add_user(nome, meta , motos , pops, vendas_card, vendas_other)
    
    return "usuário adicionado"

@app.route("/deletar" , methods = ["POST"])
def delete():
    
    nome = request.form.get("nome")
    delet_user(nome)
    
    vendedores = get_user("all")
    
    return render_template(
        "index.html",
        vendedores = vendedores
    )

@app.route("/editar", methods=["POST"]) 
def edit():
    
    nome  = request.form.get("nome")
    meta  = (request.form.get("meta"))
    motos = (request.form.get("motos"))
    pops  = (request.form.get("pops"))
    vendas_card  = (request.form.get("vendas_card"))
    vendas_other = (request.form.get("vendas_other"))
    
    edit_user(nome, meta , motos , pops, vendas_card, vendas_other)
    vendedores = get_user("all")
    
    return render_template(
        "index.html",
        vendedores = vendedores
    )

@app.route("/buscar", methods=["POST"]) 
def get(): 
    
    nome       = request.form.get("nome") 
    vendedores = get_user(nome) 
    
    return render_template( "index.html", vendedores=vendedores )


@app.route("/processar-pdfs", methods=["POST"])
def processar_pdfs():

    context = pdfRead()
    llm(context)
    
    vendedores = get_user("all")

    return render_template(
       
        "index.html",
        vendedores  = vendedores,
    )
    


if __name__ == "__main__":
    app.run(debug=True)