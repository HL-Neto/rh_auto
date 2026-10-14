import os
import json
import firebase_admin
import pdfplumber

from io                         import BytesIO
from fpdf                       import FPDF
from firebase_admin             import credentials, firestore
from dotenv                     import load_dotenv
from pathlib                    import Path
from datetime                   import datetime


load_dotenv()
    

''' 
    AQUI FICAM AS FUNÇÕES QUE ULTILIZAMOS NO SISTEMA INTEIRO  

'''

"credencias de autenticação do firebase , para operações com o bd"
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred)
    

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "PDF"





" deleta os pdfs na pasta"

def delet_pdfs():
    
    
    # Localiza a pasta PDF na raiz do projeto
    if not PDF_DIR.exists():
        return False

    # Exclui todos os arquivos PDF
    for arquivo in PDF_DIR.iterdir():
        if arquivo.is_file() and arquivo.suffix.lower() == ".pdf":
            arquivo.unlink()

    return True



" ler os pdfs no arquivo PDF"

def pdfRead():
    dados = {
        "metas": {
            "arquivo": None,
            "tabelas": [],
            "texto": "",
        },
        "vendas": {
            "arquivo": None,
            "tabelas": [],
            "texto": "",
        },
        "outros_documentos": [],
    }

    if not PDF_DIR.exists():
        return json.dumps(dados, ensure_ascii=False, indent=2)

    arquivos = sorted(
        PDF_DIR.glob("*.pdf"),
        key=lambda arquivo: arquivo.name.casefold()
    )

    for arquivo in arquivos:
        try:
            tabelas = []
            textos = []

            with pdfplumber.open(arquivo) as pdf:
                for pagina_num, pagina in enumerate(pdf.pages, start=1):
                    texto = pagina.extract_text(
                        x_tolerance=2,
                        y_tolerance=3
                    ) or ""

                    textos.append(
                        f"PÁGINA {pagina_num}\n{texto}"
                    )

                    for tabela in pagina.extract_tables() or []:
                        if not tabela:
                            continue

                        linhas = [
                            [
                                str(celula).strip()
                                if celula is not None else ""
                                for celula in linha
                            ]
                            for linha in tabela
                            if linha and any(
                                celula is not None
                                and str(celula).strip()
                                for celula in linha
                            )
                        ]

                        if not linhas:
                            continue

                        colunas = [
                            valor or f"coluna_{i + 1}"
                            for i, valor in enumerate(linhas[0])
                        ]

                        # Impede que cabeçalhos duplicados sobrescrevam dados.
                        contagem = {}
                        colunas_unicas = []

                        for coluna in colunas:
                            contagem[coluna] = contagem.get(coluna, 0) + 1

                            if contagem[coluna] > 1:
                                coluna = (
                                    f"{coluna}_{contagem[coluna]}"
                                )

                            colunas_unicas.append(coluna)

                        registros = []

                        for linha in linhas[1:]:
                            linha = (
                                linha + [""] * len(colunas_unicas)
                            )[:len(colunas_unicas)]

                            registros.append({
                                colunas_unicas[i]: valor
                                for i, valor in enumerate(linha)
                            })

                        tabelas.append({
                            "pagina": pagina_num,
                            "tabela": len(tabelas) + 1,
                            "colunas": colunas_unicas,
                            "linhas": registros,
                        })

            texto_completo = "\n\n".join(textos)

            documento = {
                "arquivo": arquivo.name,
                "tabelas": tabelas,
                "texto_markdown": texto_completo,
            }

            nome = arquivo.name.casefold()

            if "vendas de motos por equipes" in nome:
                dados["metas"] = {
                    "arquivo": arquivo.name,
                    "tabelas": tabelas,
                    "texto": texto_completo,
                }

            elif "comissoes" in nome and "pagamento" in nome:
                dados["vendas"] = {
                    "arquivo": arquivo.name,
                    "tabelas": tabelas,
                    "texto": texto_completo,
                }

            else:
                dados["outros_documentos"].append(documento)

            print(
                f"PDF lido: {arquivo.name} | "
                f"Tabelas: {len(tabelas)}"
            )

        except Exception as erro:
            print(f"Erro ao ler {arquivo.name}: {erro}")

    return json.dumps(
        dados,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


"transforma em pdf"

def pdfTurn(vendedores: str):

    vendedores = [
        v for v in vendedores
        if float(v.get("bonus", 0) or 0) != 0
    ]
    
    vendedores = sorted( vendedores, key=lambda v: str(v.get("nome", "")).casefold() )

    pdf = FPDF(orientation="L", unit="mm", format="A4")

    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()

    pdf.set_fill_color(20, 20, 20)

    pdf.rect(0, 0, 297, 32, style="F")

    pdf.set_text_color(255, 255, 255)

    pdf.set_font("Arial", "B", 22)

    pdf.set_xy(15, 7)

    pdf.cell(0, 10, "MOTOMAR")

    pdf.set_font("Arial", "", 10)

    pdf.set_xy(15, 18)

    pdf.cell(0, 6, "GESTAO DE VENDEDORES")

    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf.set_font("Arial", "", 9)

    pdf.set_xy(205, 12)

    pdf.cell(75, 6, f"Emitido em: {data_atual}", align="R")

    pdf.set_text_color(30, 30, 30)

    pdf.set_font("Arial", "B", 18)

    pdf.set_xy(15, 43)

    pdf.cell(0, 10, "RELATORIO DE VENDEDORES")

    total_vendedores = len(vendedores)

    total_motos = sum(int(v.get("motos", 0) or 0) for v in vendedores)

    total_bonus = sum(float(v.get("bonus", 0) or 0) for v in vendedores)

    pdf.set_font("Arial", "", 10)

    pdf.set_text_color(90, 90, 90)

    pdf.set_xy(15, 54)

    pdf.cell(80, 7, f"Vendedores: {total_vendedores}")

    pdf.cell(80, 7, f"Motos vendidas: {total_motos}")

    pdf.cell(80, 7, f"Bonus total: R$ {total_bonus:,.2f}")

    y = 70

    colunas = [
        ("VENDEDOR", 75),
        ("TIPO", 35),
        ("META", 25),
        ("MOTOS", 30),
        ("CARTAO", 30),
        ("OUTRAS", 30),
        ("BONUS", 35),
    ]

    pdf.set_fill_color(220, 30, 30)

    pdf.set_text_color(255, 255, 255)

    pdf.set_font("Arial", "B", 9)

    pdf.set_xy(15, y)

    for titulo, largura in colunas:

        pdf.cell(
            largura,
            10,
            titulo,
            border=0,
            align="C",
            fill=True
        )

    y += 10

    pdf.set_font("Arial", "", 8)

    for vendedor in vendedores:

        # Nova página caso necessário

        if y > 185:

            pdf.add_page()

            y = 20

            pdf.set_fill_color(220, 30, 30)

            pdf.set_text_color(255, 255, 255)

            pdf.set_font("Arial", "B", 9)

            pdf.set_xy(15, y)

            for titulo, largura in colunas:

                pdf.cell(
                    largura,
                    10,
                    titulo,
                    border=0,
                    align="C",
                    fill=True
                )

            y += 10

            pdf.set_font("Arial", "", 8)

        nome = str(vendedor.get("nome", ""))

        tipo = str(vendedor.get("tipo", ""))

        meta = int(vendedor.get("meta", 0) or 0)

        motos = int(vendedor.get("motos", 0) or 0)

        card = int(vendedor.get("vendas_card", 0) or 0)

        outras = int(vendedor.get("vendas_other", 0) or 0)

        bonus = float(vendedor.get("bonus", 0) or 0)

        # Cor alternada das linhas

        if (y // 8) % 2 == 0:

            pdf.set_fill_color(248, 248, 248)

        else:

            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(40, 40, 40)

        pdf.set_xy(15, y)

        pdf.cell(
            75,
            8,
            nome[:40],
            border=1,
            align="L",
            fill=True
        )

        pdf.cell(
            35,
            8,
            tipo.upper(),
            border=1,
            align="C",
            fill=True
        )

        pdf.cell(
            25,
            8,
            str(meta),
            border=1,
            align="C",
            fill=True
        )

        pdf.cell(
            30,
            8,
            str(motos),
            border=1,
            align="C",
            fill=True
        )

        pdf.cell(
            30,
            8,
            str(card),
            border=1,
            align="C",
            fill=True
        )

        pdf.cell(
            30,
            8,
            str(outras),
            border=1,
            align="C",
            fill=True
        )

        pdf.set_font("Arial", "B", 8)

        pdf.cell(
            35,
            8,
            f"R$ {bonus:,.2f}",
            border=1,
            align="C",
            fill=True
        )

        pdf.set_font("Arial", "", 8)

        y += 8

    # Rodapé

    pdf.set_y(-15)

    pdf.set_font("Arial", "", 8)

    pdf.set_text_color(120, 120, 120)

    pdf.cell(
        0,
        5,
        "Motomar - Relatorio de vendedores",
        align="C"
    )

    pdf_bytes = pdf.output()

    return BytesIO(pdf_bytes)


    
        

"adiciona um usuário no banco de dados"
def add_user(nome:str , tipo:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    
    "ativa o firebase"
    db = firestore.client()
    
    "chamamos a função do bonus com os dados que a gente recebeu"
    bonus = calc( meta , motos , pops , vendas_card, vendas_other)
    
    " dados novos "
    data ={
        
        "nome":nome,
        "tipo":tipo,
        "meta":meta,
        "motos":motos,
        "pops":pops,
        "vendas_card": vendas_card,
        "vendas_other":vendas_other, 
        "bonus": bonus
    }
    
    "manda os dados para o firebase"
    db.collection ("vendedores").add(data)

    return




def edit_user(nome:str , tipo:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    
    "ativa o firebase e procura o nome da pessoa que vamos editar"
    db      = firestore.client()
    col_ref = db.collection("vendedores")
    search  = col_ref.where("nome", "==", nome).stream()
    
    data ={}
    
    "basicamente se tive alguma alteração ela vai ser armazenada no data "
    if nome not in (None, ""):
        data["nome"] = str(nome)
    if tipo not in (None, ""):
        data["tipo"] = str(tipo)
    if meta not in (None, ""):
        data["meta"] = int(meta)
    if motos not in (None, ""):
        data["motos"] = int(motos)
    if pops not in (None, ""):
        data["pops"] = int(pops)
    if vendas_card not in (None, ""):
        data["vendas_card"] = int(vendas_card)
    if vendas_other not in (None, ""):
        data["vendas_other"] = int(vendas_other)

    bonus = calc(
        data.get("meta", 0),
        data.get("motos", 0),
        data.get("pops", 0),
        data.get("vendas_card", 0),
        data.get("vendas_other", 0)
    )

    data["bonus"] = bonus

    
    if not data:
        return 0
    
    updated = 0

    "passa campo por campo da pessoa e atualiza "
    for doc in search:
        
        doc.reference.update(data)
        updated += 1
    

    return updated




"deleta o usuário"
def delet_user(nome:str):
    
    "ativa o fb e procura pelo nome da pessoa"
    db      = firestore.client()
    col_ref = db.collection("vendedores")
    query   = col_ref.where("nome", "==", nome)

    search = query.stream()
    
    deleted = 0 
    
    "procura as pessoas com esse nome e deleta"
    for doc in search:
        
        doc.reference.delete()
        deleted += 1
        
    return print(f"Sucesso! {deleted} documentos foram deletados.")
    
    
    
    
"busca o vendedor" 
def get_user(nome:str):
    
    db      = firestore.client()
    col_ref = db.collection("vendedores")
    vendedores = []
    
    "retornar todos os vendedores no banco de dados"
    if nome == "all":
        
        search = col_ref.stream()
    
    
    else:
        
        "retorna uma pessoa específica"
        search = col_ref.where("nome", "==", nome).stream()
    
    "procura por todos os resultados da pesquisa no banco e retorna os dados"   
    for doc in search:
        
        dados = doc.to_dict() 
        dados["id"] = doc.id 
        vendedores.append(dados)
    
    return vendedores


def calc(meta: int, motos: int, pops: int, vendas_card: int, vendas_other: int) -> int:
    
    """Calcula o bônus do vendedor quando a quantidade de vendas ultrapassa a meta."""
    
    "calcula o bonus se a venda for maior que a meta"
    if motos >= meta :
        
        vendas_card_bonus = vendas_card * 15
        vendas_other_bonus = vendas_other * 30
        
        total = vendas_other_bonus + vendas_card_bonus 
        
        
        return total
    
    return 0



    
    
            
