import os

from flask import Flask, request, render_template

from MODULLES.module import (
    add_user,
    delet_user,
    get_user,
    pdfRead,
    edit_user,
    calc
)

from LLM.llm import (
    llm_process,
    command_process
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "FRONT")
)


@app.route("/")
def index():

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores
    )

@app.route("/cadastro")
def cadastro():

    return render_template(
        "cadastro.html"
    )


@app.route("/cadastrar", methods=["POST"])
def add():

    nome = request.form.get("nome")
    tipo = request.form.get("tipo")

    meta = int(request.form.get("meta"))
    motos = int(request.form.get("motos"))
    pops = int(request.form.get("pops"))

    vendas_card = int(
        request.form.get("vendas_card")
    )

    vendas_other = int(
        request.form.get("vendas_other")
    )

    add_user(
        nome,
        tipo,
        meta,
        motos,
        pops,
        vendas_card,
        vendas_other
    )

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores
    )


# ============================================================
# DELETAR
# ============================================================

@app.route("/deletar", methods=["POST"])
def delete():

    nome = request.form.get("nome")

    delet_user(nome)

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores
    )


# ============================================================
# EDITAR
# ============================================================

@app.route("/editar", methods=["POST"])
def edit():

    nome = request.form.get("nome")

    meta = request.form.get("meta")
    motos = request.form.get("motos")
    pops = request.form.get("pops")

    vendas_card = request.form.get(
        "vendas_card"
    )

    vendas_other = request.form.get(
        "vendas_other"
    )

    edit_user(
        nome,
        meta,
        motos,
        pops,
        vendas_card,
        vendas_other
    )

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores
    )


# ============================================================
# BUSCAR
# ============================================================

@app.route("/buscar", methods=["POST"])
def get():

    nome = request.form.get("nome")

    vendedores = get_user(nome)

    return render_template(
        "index.html",
        vendedores=vendedores
    )


# ============================================================
# PROCESSAR PDFs
# ============================================================

@app.route("/processar-pdfs", methods=["POST"])
def processar_pdfs():

    print("\n==============================")
    print("PROCESSANDO PDFs")
    print("==============================")

    resultado = llm_process()

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores,
        resultado=resultado
    )


# ============================================================
# IA DE COMANDOS
# ============================================================

@app.route("/llm", methods=["POST"])
def ia():

    context = request.form.get(
        "comando",
        ""
    ).strip()

    print("\n==============================")
    print("COMANDO RECEBIDO PELA API")
    print("==============================")

    print(context)

    resultado = command_process(context)

    vendedores = get_user("all")

    return render_template(
        "index.html",
        vendedores=vendedores,
        resultado=resultado
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )