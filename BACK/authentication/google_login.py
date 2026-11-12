"""
Login com Google por usuário (OAuth 2.0 para aplicação web).

Os tokens do usuário ficam no cookie de sessão do Flask (assinado com
FLASK_SECRET_KEY e marcado como HttpOnly). Assim o login funciona com
vários workers do gunicorn e sobrevive a reinícios do servidor no Render.
O client_secret nunca vai para o cookie: ele é lido do arquivo de
credenciais a cada uso.
"""

import json
import os
from datetime import datetime

from flask import session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


# Atrás do proxy do Render a conexão interna é HTTP; localmente também.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
# O Google pode devolver os escopos em outra ordem ou com "openid" extra.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def caminho_credenciais():
    """
    Ordem de busca do JSON do cliente OAuth:
    1. GOOGLE_CLIENT_SECRETS (caminho definido no ambiente)
    2. credentials.json na raiz do projeto
    3. /etc/secrets/credentials.json (Secret File do Render)
    """
    candidatos = [
        os.getenv("GOOGLE_CLIENT_SECRETS"),
        os.path.join(BASE_DIR, "credentials.json"),
        "/etc/secrets/credentials.json",
    ]

    for caminho in candidatos:
        if caminho and os.path.exists(caminho):
            return caminho

    raise FileNotFoundError(
        "Arquivo de credenciais do Google (credentials.json) não encontrado."
    )


def _cliente():
    with open(caminho_credenciais(), encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    return dados.get("web") or dados.get("installed") or {}


def criar_flow(redirect_uri, state=None):
    return Flow.from_client_secrets_file(
        caminho_credenciais(),
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
    )


def url_de_login(redirect_uri):
    """Gera a URL do Google e guarda na sessão o que o retorno vai precisar."""
    flow = criar_flow(redirect_uri)

    url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account",
    )

    session["google_state"] = state
    session["google_verifier"] = getattr(flow, "code_verifier", None)

    return url


def _guardar(creds):
    session["google_token"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token or session.get("google_token", {}).get("refresh_token"),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


def concluir_login(redirect_uri, authorization_response):
    """Troca o código devolvido pelo Google por credenciais e identifica o usuário."""
    flow = criar_flow(redirect_uri, state=session.pop("google_state", None))

    verifier = session.pop("google_verifier", None)
    if verifier:
        flow.code_verifier = verifier

    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials

    perfil = build("oauth2", "v2", credentials=creds, cache_discovery=False) \
        .userinfo().get().execute()

    _guardar(creds)
    session["google_email"] = perfil.get("email", "")
    session["google_nome"] = perfil.get("name", "")
    session["google_foto"] = perfil.get("picture", "")
    session.permanent = True

    return perfil


def obter_credenciais():
    dados = session.get("google_token")
    if not dados:
        return None

    cliente = _cliente()

    creds = Credentials(
        token=dados.get("token"),
        refresh_token=dados.get("refresh_token"),
        token_uri=cliente.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=cliente.get("client_id"),
        client_secret=cliente.get("client_secret"),
        scopes=SCOPES,
    )

    if dados.get("expiry"):
        # A biblioteca compara a validade com datetime sem fuso (UTC).
        creds.expiry = datetime.fromisoformat(dados["expiry"]).replace(tzinfo=None)

    if creds.valid:
        return creds

    if creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            sair()
            return None

        _guardar(creds)
        return creds

    return None


def usuario_logado():
    if not obter_credenciais():
        return None

    return {
        "email": session.get("google_email", ""),
        "nome": session.get("google_nome", ""),
        "foto": session.get("google_foto", ""),
    }


def servico_gmail():
    """Cliente da API do Gmail do usuário logado, ou None se não houver login."""
    creds = obter_credenciais()
    if not creds:
        return None

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def sair():
    for chave in ("google_token", "google_email", "google_nome", "google_foto",
                  "google_state", "google_verifier"):
        session.pop(chave, None)
