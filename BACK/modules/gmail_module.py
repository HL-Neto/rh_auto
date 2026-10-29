
import os
import base64

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from pypdf import PdfReader

from BACK.authentication.conect_gmail import conectar_gmail


load_dotenv()

gmail = conectar_gmail()


# ============================================================
# FIREBASE
# ============================================================

def conectar_firebase():
    """Inicializa o Firebase apenas uma vez."""
    if not firebase_admin._apps:
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if not credentials_path:
            raise ValueError(
                "A variável FIREBASE_CREDENTIALS_PATH não foi configurada."
            )

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado: {credentials_path}"
            )

        credential = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(credential)

    return firestore.client()


def fb_get_curriculum(curriculo_id="all"):
    """
    Busca todos os currículos ou um currículo específico pelo ID
    real do documento no Firestore.

    Retorno individual:
        {
            "id": "ID_DO_DOCUMENTO",
            "conteudo": {
                "remetente": "...",
                "curriculo": "..."
            }
        }
    """
    db = conectar_firebase()
    colecao = db.collection("curriculos")

    if str(curriculo_id) != "all":
        documento = colecao.document(str(curriculo_id)).get()

        if not documento.exists:
            return None

        dados = documento.to_dict() or {}
        dados["id"] = documento.id

        return dados

    documentos = colecao.limit(10).stream()
    curriculos = []

    for documento in documentos:
        dados = documento.to_dict() or {}
        dados["id"] = documento.id
        curriculos.append(dados)

    return curriculos


def fb_send_curriculum(curriculos):
    """Salva os currículos extraídos dos e-mails no Firestore."""
    db = conectar_firebase()
    colecao = db.collection("curriculos")
    quantidade = 0

    for candidato in curriculos:
        doc_id = candidato.get("id")

        if not doc_id:
            continue

        colecao.document(str(doc_id)).set({
            "id": str(doc_id),
            "conteudo": {
                "remetente": candidato.get("remetente", "Não informado"),
                "curriculo": candidato.get("curriculo", "")
            }
        })

        quantidade += 1

    return {
        "salvos": quantidade
    }


# ============================================================
# GMAIL
# ============================================================

def gmail_inbox(quant_curriculo=20):
    subject_curriculo = [
        "currículo", "curriculo", "cv", "c.v.",
        "resume", "resumé", "curriculum", "curriculum vitae",
        "envio de currículo", "envio do currículo",
        "enviando currículo", "envio de cv", "envio do cv",
        "currículo profissional", "curriculo profissional",
        "currículo atualizado", "curriculo atualizado",
        "candidatura", "candidatura à vaga", "candidatura a vaga",
        "candidatura para vaga", "candidatura espontânea",
        "vaga", "vaga de emprego", "vaga de trabalho",
        "oportunidade", "oportunidade de emprego",
        "oportunidade profissional", "processo seletivo",
        "processo de seleção", "candidato", "perfil profissional",
        "apresentação profissional", "interesse na vaga",
        "interesse profissional", "vendedor externo",
        "supervisor externo", "vendedor online",
        "auxiliar administrativo", "assistente de rh",
        "analista de ti", "jovem aprendiz", "operador de caixa",
        "montador", "auxiliar mecânico", "auxiliar serviços gerais",
        "auxiliar de serviços gerais", "assistente de administrativo",
        "assistente administrativo", "auxiliar administrativo credere",
        "assistente administrativo emplacamento",
        "assistente administrativo consorcio",
        "assistente administrativo consórcio", "vendedora",
        "vendedora show room", "vendedora showroom", "show room",
        "showroom", "assistente de faturamento",
        "jovem aprendiz faturamento", "jovem aprendiz pós vendas",
        "jovem aprendiz pós-vendas", "estagiário de arquivologia",
        "estagiária contábil", "estagiario de arquivologia",
        "estagiaria contabil", "estagiária de adm pessoal",
        "estagiario de adm pessoal", "estagiário de adm pessoal",
        "garantista", "gerente de pós vendas", "gerente de pós-vendas",
        "motorista"
    ]

    inbox = gmail.users().messages().list(
        userId="me",
        q="in:inbox",
        maxResults=quant_curriculo
    ).execute()

    mensagens = inbox.get("messages", [])
    gmail_content = []

    for mensagem in mensagens:
        msg = gmail.users().messages().get(
            userId="me",
            id=mensagem["id"],
            format="full"
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])

        remetente = "Não informado"
        assunto = ""

        for header in headers:
            nome_header = header.get("name", "").lower()
            valor_header = header.get("value", "")

            if nome_header == "from":
                remetente = valor_header

            elif nome_header == "subject":
                assunto = valor_header

        if any(
            palavra.lower() in assunto.lower()
            for palavra in subject_curriculo
        ):
            gmail_content.append({
                "id": msg["id"],
                "remetente": remetente,
                "assunto": assunto,
                "conteudo": msg.get("snippet", "")
            })

    return gmail_content


def attachment(emails):
    """Baixa anexos de e-mail em Base64."""
    attachments = []

    def percorrer_partes(partes, email):
        for parte in partes:
            attachment_id = parte.get("body", {}).get("attachmentId")

            if attachment_id:
                anexo = gmail.users().messages().attachments().get(
                    userId="me",
                    messageId=email["id"],
                    id=attachment_id
                ).execute()

                attachments.append({
                    "id": email["id"],
                    "remetente": email.get("remetente", "Não informado"),
                    "data": anexo.get("data", "")
                })

            subpartes = parte.get("parts", [])

            if subpartes:
                percorrer_partes(subpartes, email)

    for email in emails:
        mensagem = gmail.users().messages().get(
            userId="me",
            id=email["id"],
            format="full"
        ).execute()

        payload = mensagem.get("payload", {})
        partes = payload.get("parts", [])

        if partes:
            percorrer_partes(partes, email)

        elif payload.get("body", {}).get("attachmentId"):
            percorrer_partes([payload], email)

    return attachments


# ============================================================
# PDF
# ============================================================

def get_curriculum(anexos):
    """Decodifica os PDFs e extrai o texto."""
    curriculos = []

    for anexo in anexos:
        dados_base64 = anexo.get("data")

        if not dados_base64:
            continue

        pdf_bytes = base64.urlsafe_b64decode(dados_base64)

        nome_arquivo = f"curriculo_{anexo['id']}.pdf"

        with open(nome_arquivo, "wb") as arquivo:
            arquivo.write(pdf_bytes)

        try:
            leitor = PdfReader(nome_arquivo)
            texto_completo = ""

            for pagina in leitor.pages:
                texto = pagina.extract_text()

                if texto:
                    texto_completo += texto + "\n"

            curriculos.append({
                "id": anexo["id"],
                "remetente": anexo.get("remetente", "Não informado"),
                "curriculo": texto_completo.strip()
            })

        finally:
            if os.path.exists(nome_arquivo):
                os.remove(nome_arquivo)

    return curriculos
