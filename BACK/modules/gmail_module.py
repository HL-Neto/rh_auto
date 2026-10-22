import os
import firebase_admin
import base64

from pypdf                              import PdfReader
from BACK.authentication.conect_gmail   import conectar_gmail
from dotenv                             import load_dotenv
from firebase_admin                     import credentials, firestore


load_dotenv()

gmail  = conectar_gmail()
 
" ----------- FIREBASE OPERATIONS ----------- "


def fb_get_curriculum():
    
    #inicia o fb
    
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    credential       = credentials.Certificate(credentials_path)

    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credential)

    
    #busca e pega os curriculos dentro do fb
    
    db        = firestore.client()
    doc_ref   = db.collection("curriculos")
    query     = doc_ref.limit(10)
    docs      = query.get()
    curriculo = []

    # retira os dados do curriculo 
    
    if docs:
        
        for doc in docs:
           
            curriculo.append({

                "id": doc.id,
                "conteudo": doc.to_dict()

            })


    return curriculo



def fb_send_curriculum(curriculo):


    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    credential       = credentials.Certificate(credentials_path)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credential)
    

    db = firestore.client()

    for candidato in curriculo:

        doc_id = candidato["id"]

        db.collection("curriculos").document(doc_id).set({
            "id": doc_id,
            "conteudo": {
                "remetente": candidato["remetente"],
                "curriculo": candidato["curriculo"]
            }
        })


def fb_get_curriculum(remetente):
    
    db      = firestore.client()
    col_ref = db.collection("curriculos")
    vendedores = []
    
    "retornar todos os vendedores no banco de dados"
    if remetente == "all":
        
        search = col_ref.stream()
    
    
    else:
        
        "retorna uma pessoa específica"
        search = col_ref.where("remetente", "==", remetente).stream()
    
    "procura por todos os resultados da pesquisa no banco e retorna os dados"   
    for doc in search:
        
        dados = doc.to_dict() 
        dados["id"] = doc.id 
        vendedores.append(dados)
    
    return vendedores
    



" ----------- GMAIL OPERATIONS ----------- "



def gmail_inbox(quant_curriculo):

        
    subject_curriculo = [

        
        "currículo",
        "curriculo",
        "cv",
        "c.v.",
        "resume",
        "resumé",
        "curriculum",
        "curriculum vitae",
        "envio de currículo",
        "envio do currículo",
        "enviando currículo",
        "envio de cv",
        "envio do cv",
        "currículo profissional",
        "curriculo profissional",
        "currículo atualizado",
        "curriculo atualizado",

        
        "candidatura",
        "candidatura à vaga",
        "candidatura a vaga",
        "candidatura para vaga",
        "candidatura espontânea",
        "vaga",
        "vaga de emprego",
        "vaga de trabalho",
        "oportunidade",
        "oportunidade de emprego",
        "oportunidade profissional",
        "processo seletivo",
        "processo de seleção",
        "candidato",
        "perfil profissional",
        "apresentação profissional",
        "interesse na vaga",
        "interesse profissional",


        "vendedor externo",
        "supervisor externo",
        "vendedor online",
        "auxiliar administrativo",
        "assistente de rh",
        "analista de ti",
        "jovem aprendiz",
        "operador de caixa",
        "montador",
        "auxiliar mecânico",
        "auxiliar serviços gerais",
        "auxiliar de serviços gerais",
        "assistente de administrativo",
        "assistente administrativo",
        "auxiliar administrativo credere",
        "assistente administrativo emplacamento",
        "assistente administrativo consorcio",
        "assistente administrativo consórcio",
        "vendedora",
        "vendedora show room",
        "vendedora showroom",
        "show room",
        "showroom",
        "assistente de faturamento",
        "jovem aprendiz faturamento",
        "jovem aprendiz pós vendas",
        "jovem aprendiz pós-vendas",
        "estagiário de arquivologia",
        "estagiária contábil",
        "estagiario de arquivologia",
        "estagiaria contabil",
        "estagiária de adm pessoal",
        "estagiario de adm pessoal",
        "estagiário de adm pessoal",
        "garantista",
        "gerente de pós vendas",
        "gerente de pós-vendas",
        "motorista"

    ]

    inbox = gmail.users().messages().list(

            userId     = "me",
            q          = "in:inbox",
            maxResults =  quant_curriculo

    ).execute()   # puxa as 20 primeiras menssagens do inbox

    

    inbox_msg     =  inbox.get("messages",[]) 
    gmail_content = []

    for msgs in inbox_msg:


        msg = gmail.users().messages().get(

            userId = "me",
            id     = msgs["id"],
            format = "full"

        ).execute()  # vai por menssagem em messagem retornando todo conteudo dela, no inbox ele so retorna o ID e o ID trhead, aqui ele usa esses ids para puxar o conteudo inteiro da menssagem

        snippet     = msg.get("snippet")
        headers_msg = msg["payload"].get("headers")   # puxa o cabeçalho do email, quem eviou , o email , name etcetcetc


        #estou criando aqui para caso o email n tenha algum dos dois ele n dê erro 
        assunto = ""
        header  = ""

        for header in headers_msg:

        # uma representação visual de como o header ta agr  
        #    headers = [    
        #       {"name": "From", "value": "joao@gmail.com"},
        #        {"name": "To", "value": "humberto@gmail.com"},
        #        {"name": "Subject", "value": "Meu currículo"},
        #        {"name": "Date", "value": "04 Sep 2026"}
        #    ]
        # ele faz várias voltas passando por cada parte do header até o fim   
            
            if header["name"].lower()   == "from":

                print( " PUXANDO O REMETENTE ")
                remetente = header["value"]

            elif header["name"].lower() == "subject":

                print( " PUXANDO O SUBJECT ")
                assunto = header["value"]


        #verifica se tem alguma palavra passa no subject do email , independente se for maiúscula ou minuscula 

        if any(pass_word.lower() in assunto.lower() for pass_word in subject_curriculo):


            gmail_content.append({
            
                            "id" : msg["id"],
                            "remetente" : remetente,
                            "assunto"   : assunto,
                            "conteudo"  : snippet
                    })
        
    
    return gmail_content




def  attachment(emails):


    #lista dos conteudos dos anexos em base 64 que a gente vai pegar
    attachments = []


    # aqui a gente ta buscando os email completos dos IDs selecionados 
    for email in emails:

        get_full_email = gmail.users().messages().get(              

            userId   = "me",
            id       =  email["id"],
            format   = "full"
        ).execute() 

      
        #retorna uma lista parecida com o heardes
        partes = get_full_email["payload"].get("parts",[])                 

        for part in partes:

            print("PROCURANDO ANEXO")
            # rodamos a lista até acharmos o id do anexo 
            attachment_id = part.get("body", {}).get("attachmentId")

            
            if attachment_id: 

                print("ANEXO ENCONTRADO")

                attachment = gmail.users().messages().attachments().get(

                    userId    = "me",
                    messageId = email["id"],
                    id        = attachment_id

                ).execute() # pegamos o conteudo do pdf em base 64

                print("ANEXO BAIXADO EM BASE 64")

                attachments.append({

                    "id"       : email["id"],
                    "remetente": email["remetente"],
                    "data"     : attachment["data"]

                    })

    
    return attachments




" ----------- PDF OPERATIONS ----------- "


def get_curriculum(anexos):

     
    curriculo = []

    # baixar o pdf
    
    for anexo in anexos:
        
        pdf = base64.urlsafe_b64decode(

            anexo["data"]

        )

        name_file = f' curriculo_{anexo["id"]}.pdf'

        with open(name_file, "wb") as file:

            file.write(pdf)

        print(" PDF BAIXADO ")

        # ler pdf 
        
        reader = PdfReader(name_file)

        #onde vai ficar armazenado o texto inteiro do curriculo
        full_text = ""

        #passamos página por página do pdf
        for page in reader.pages:

            text = page.extract_text()

            if text:

                full_text += text

        curriculo.append({

            "id"        : anexo["id"],
            "remetente" : anexo["remetente"],
            "curriculo" : full_text
        })

    
    return curriculo
