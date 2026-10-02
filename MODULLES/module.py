import os
from pypdf import PdfReader
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()
    
    
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred)
    

def pdfRead():
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    file1 = os.path.join( BASE_DIR, "PDF" , "COMISSOES_-_A_PAGAR_-_VEICULO_-_PAGAMENTO.pdf")
    file2 = os.path.join( BASE_DIR, "PDF" , "COMISSOES_-_A_PAGAR_-_VEICULO.pdf")

    files = [file1, file2]
    
    data = ""   

    for file in files:

        reader = PdfReader(file)

        for page in reader.pages:

            text = page.extract_text()

            if text:
                
                data += text

   
    
    return data


def txtRead():

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    txt = os.path.join( BASE_DIR, "DICIONARIO" , "vendedores_metas.txt")
    
    with open (txt,'r', encoding = 'utf-8') as arquivo:
        
        conteudo = arquivo.read()
      
        return conteudo
        


def add_user(nome:str , tipo:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    
    db = firestore.client()
    
    bonus = calc( meta , motos , pops , vendas_card, vendas_other)
    
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
    
    db.collection ("vendedores").add(data)

    return

def edit_user(nome:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    
    db      = firestore.client()
    col_ref = db.collection("vendedores")
    search  = col_ref.where("nome", "==", nome).stream()
    
    data ={}
    
    
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

    if not data:
        return 0
    
    updated = 0

    for doc in search:
        
        doc.reference.update(data)
        updated += 1
    

    return updated


def delet_user(nome:str):
    
    db      = firestore.client()
    col_ref = db.collection("vendedores")
    query   = col_ref.where("nome", "==", nome)

    search = query.stream()
    
    deleted = 0 
    
    for doc in search:
        
        doc.reference.delete()
        deleted += 1
        
    return print(f"Sucesso! {deleted} documentos foram deletados.")
    
    
def get_user(nome:str):
    
    db      = firestore.client()
    col_ref = db.collection("vendedores")
    vendedores = []
    
    if nome == "all":
        
        search = col_ref.stream()
        
    else:
        
        search = col_ref.where("nome", "==", nome).stream()
        
    for doc in search:
        
        dados = doc.to_dict() 
        dados["id"] = doc.id 
        vendedores.append(dados)
    
    return vendedores


def calc(meta: int, motos: int, pops: int, vendas_card: int, vendas_other: int) -> int:
    
    """Calcula o bônus do vendedor quando a quantidade de vendas ultrapassa a meta."""
    
    
    if motos >= meta :
        
        vendas_card_bonus = vendas_card * 15
        vendas_other_bonus = vendas_other * 30
        
        total = vendas_other_bonus + vendas_card_bonus 
        
        
        return total
    
    return 0



    
    
            
