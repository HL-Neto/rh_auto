import os
import hashlib

from dotenv                         import load_dotenv
from BACK.modules.gmail_module     import fb_get_curriculum
from pinecone                       import Pinecone
from pinecone                       import ServerlessSpec
from langchain_pinecone             import PineconeVectorStore
from langchain_huggingface          import HuggingFaceEmbeddings
from langchain_text_splitters       import RecursiveCharacterTextSplitter

load_dotenv()
def splitter(curriculo_id=None):
    from firebase_admin import firestore

    db = firestore.client()
    colecao = db.collection("curriculos")

    if curriculo_id is not None:
        doc = colecao.document(str(curriculo_id)).get()

        if not doc.exists:
            return []

        registro = doc.to_dict()
        registro["id"] = doc.id
        curriculos = [registro]

    else:
        curriculos = []

        for doc in colecao.stream():
            registro = doc.to_dict()
            registro["id"] = doc.id
            curriculos.append(registro)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    split = []

    for curriculo in curriculos:
        data = curriculo.get("conteudo", curriculo)
        texto = data.get("curriculo", "")

        if not texto or not texto.strip():
            continue

        chunks = text_splitter.create_documents(
            [texto],
            metadatas=[{
                "id": str(curriculo["id"]),
                "remetente": data.get("remetente", "")
            }]
        )

        split.extend(chunks)

    return split




def embendding():

    #iniciando o modelo de embendding 

    embendding = HuggingFaceEmbeddings(

        model_name    = "sentence-transformers/all-mpnet-base-v2",
        encode_kwargs = {"normalize_embeddings": True}
    )

    return embendding


def pinecone(split):

    

    #instancias basicas do pinecone
    pcapikey    = os.getenv("PINECONE_API_KEY")
    pinecone    = Pinecone(api_key = pcapikey)
    index_name  = "rh-curriculo-analisador"    
    embenddings = embendding()
    
    
    #verifica se existe um banco vetorial com esse nome , se n tiver ele cria
    if not pinecone.has_index(index_name):

        pinecone.create_index(

            name      = index_name,
            dimension = 768,
            metric    = "cosine",
            spec      = ServerlessSpec( cloud = "aws", region = "us-east-1")
        )

    index = pinecone.Index(index_name)



    # colocanddo dentro do pinecone 
    vector_store = PineconeVectorStore( index = index, embedding = embenddings)
    
    ids = []

    for doc in split:

        # ID estável para cada chunk do currículo
        conteudo = (
            f'{doc.metadata["id"]}:'
            f'{doc.page_content}'
        )

        chunk_id = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()

        ids.append(chunk_id)

    if split:
        vector_store.add_documents( documents=split, ids=ids)

    
    return vector_store
