import os
import firebase_admin

from firebase_admin import credentials, firestore
from dotenv         import load_dotenv
from pypdf          import PdfReader
from pathlib        import Path

load_dotenv()
    

''' 
    AQUI FICAM AS FUNÇÕES QUE ULTILIZAMOS NO SISTEMA INTEIRO  

'''

"credencias de autenticação do firebase , para operações com o bd"
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred)
    



" ler os pdfs no arquivo PDF"
def pdfRead():
    
    "procura o arquivo PDF"
    BASE_DIR = Path(__file__).resolve().parent.parent
    PDF_DIR  = BASE_DIR / "PDF"
    
    "procuras arquivos .pdf e transforma em uma lista"
    files = list(PDF_DIR.glob("*.pdf"))

    "texto extraido do pdf"
    data = ""
    
    "procura arquivo por arquivo e ler todo o texto dele e armazena no data antes de ir pro próximo"
    for file in files:

        reader = PdfReader(file)

        for page in reader.pages:

            text = page.extract_text()

            if text:
                
                data += text


    return data

    
        

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



    
    
            
