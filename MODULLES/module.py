import os
import firebase_admin

from io                         import BytesIO
from fpdf                       import FPDF
from firebase_admin             import credentials, firestore
from dotenv                     import load_dotenv
from pypdf                      import PdfReader
from pathlib                    import Path
from datetime                   import datetime
from docling.document_converter import DocumentConverter

load_dotenv()
    

''' 
    AQUI FICAM AS FUNÇÕES QUE ULTILIZAMOS NO SISTEMA INTEIRO  

'''

"credencias de autenticação do firebase , para operações com o bd"
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred)
    

BASE_DIR = Path(__file__).resolve().parent.parent


" ler os pdfs no arquivo PDF"
def pdfRead():
    
    "procura o arquivo PDF"
    
    PDF_DIR  = BASE_DIR / "PDF"
    
    converter = DocumentConverter()
    
    
    "procuras arquivos .pdf e transforma em uma lista"
    files = list(PDF_DIR.glob("*.pdf"))

    "texto extraido do pdf"
    dados = ""
    
    "procura arquivo por arquivo e ler todo o texto dele e armazena no data antes de ir pro próximo"
    for file in files:
        

        try:
            
            resultado = converter.convert(file)
            doc       = resultado.document
            text      = doc.export_to_markdown()
            
            
            dados += "\n\n"
            dados += "=" * 80
            dados += "\n"
            dados += f"ARQUIVO: {file.name}"
            dados += "\n"
            dados += "=" * 80
            dados += "\n\n"

            dados += text

            dados += "\n\n"

        except Exception as e:
            
            print (f" Erro ao ler {file}: {e}")
        
    return dados
            




"transforma em pdf"

def pdfTurn(vendedores: str):

    pdf = FPDF( orientation="L", unit="mm", format="A4")

    pdf.set_auto_page_break( auto=True, margin=15 )

    pdf.add_page()

    pdf.set_fill_color(20, 20, 20)

    pdf.rect( 0, 0, 297, 32, style="F")

    pdf.set_text_color(255, 255, 255)

    pdf.set_font( "Arial", "B", 22 )

    pdf.set_xy(15, 7)

    pdf.cell( 0, 10, "MOTOMAR" )

    pdf.set_font( "Arial", "", 10 )

    pdf.set_xy(15, 18)

    pdf.cell( 0, 6, "GESTAO DE VENDEDORES" )


    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf.set_font("Arial","",9)

    pdf.set_xy( 205, 12)

    pdf.cell( 75, 6, f"Emitido em: {data_atual}", align="R" )


    pdf.set_text_color( 30, 30, 30 )

    pdf.set_font( "Arial", "B", 18 )

    pdf.set_xy( 15, 43 )

    pdf.cell( 0, 10, "RELATORIO DE VENDEDORES" )



    total_vendedores = len(vendedores)

    total_motos = sum(int(v.get("motos", 0) or 0) for v in vendedores)

    total_bonus = sum(float(v.get("bonus", 0) or 0) for v in vendedores)


    pdf.set_font( "Arial" , "" , 10)

    pdf.set_text_color( 90, 90, 90 )

    pdf.set_xy( 15, 54 )

    pdf.cell( 80, 7, f"Vendedores: {total_vendedores}" )

    pdf.cell( 80, 7, f"Motos vendidas: {total_motos}" )

    pdf.cell( 80, 7, f"Bonus total: R$ {total_bonus:,.2f}" )



    y = 70

    colunas = [
        ("VENDEDOR", 65),
        ("TIPO", 28),
        ("META", 20),
        ("MOTOS", 22),
        ("POPS", 20),
        ("CARTAO", 25),
        ("OUTRAS", 25),
        ("BONUS", 35),
    ]


    pdf.set_fill_color( 220, 30, 30 )

    pdf.set_text_color( 255, 255, 255 )

    pdf.set_font( "Arial", "B", 9 )

    pdf.set_xy( 15, y )

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



    pdf.set_font( "Arial", "", 8 )


    for vendedor in vendedores:


        # Nova página caso necessário

        if y > 185:

            pdf.add_page()

            y = 20

            pdf.set_fill_color( 220, 30, 30 )

            pdf.set_text_color( 255, 255, 255 )

            pdf.set_font( "Arial", "B", 9 )

            pdf.set_xy( 15, y )

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

            pdf.set_font( "Arial", "", 8 )


        nome = str(
            vendedor.get("nome", "")
        )


        tipo = str(
            vendedor.get("tipo", "")
        )


        meta = int(
            vendedor.get("meta", 0) or 0
        )


        motos = int(
            vendedor.get("motos", 0) or 0
        )


        pops = int(
            vendedor.get("pops", 0) or 0
        )


        card = int(
            vendedor.get("vendas_card", 0) or 0
        )


        outras = int(
            vendedor.get("vendas_other", 0) or 0
        )


        bonus = float(
            vendedor.get("bonus", 0) or 0
        )


        # Cor alternada das linhas

        if (y // 7) % 2 == 0:

            pdf.set_fill_color( 248, 248, 248 )

        else:

            pdf.set_fill_color( 255, 255, 255 )


        pdf.set_text_color( 40, 40, 40 )

        pdf.set_xy( 15, y )


        pdf.cell(
            65,
            8,
            nome[:35],
            border=1,
            align="L",
            fill=True
        )


        pdf.cell(
            28,
            8,
            tipo.upper(),
            border=1,
            align="C",
            fill=True
        )


        pdf.cell(
            20,
            8,
            str(meta),
            border=1,
            align="C",
            fill=True
        )


        pdf.cell(
            22,
            8,
            str(motos),
            border=1,
            align="C",
            fill=True
        )


        pdf.cell(
            20,
            8,
            str(pops),
            border=1,
            align="C",
            fill=True
        )


        pdf.cell(
            25,
            8,
            str(card),
            border=1,
            align="C",
            fill=True
        )


        pdf.cell(
            25,
            8,
            str(outras),
            border=1,
            align="C",
            fill=True
        )


        pdf.set_font( "Arial", "B", 8 )

        pdf.cell(
            35,
            8,
            f"R$ {bonus:,.2f}",
            border=1,
            align="C",
            fill=True
        )

        pdf.set_font( "Arial", "", 8 )


        y += 8


    # Rodapé

    pdf.set_y( -15 )

    pdf.set_font( "Arial", "", 8 )

    pdf.set_text_color( 120, 120, 120 )

    pdf.cell(
        0,
        5,
        "Motomar - Relatorio de vendedores",
        align="C"
    )


    pdf_bytes = pdf.output()

    return BytesIO(
        pdf_bytes
    )


    
        

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



    
    
            
