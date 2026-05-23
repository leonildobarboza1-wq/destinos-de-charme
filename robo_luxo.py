import json
import os
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============================================
# CONFIG
# ============================================

BLOG_ID = "2362582861639823192"

SCOPES = [
    "https://www.googleapis.com/auth/blogger"
]

# ============================================
# AUTH
# ============================================

def get_blogger_service():
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

    if not credentials_json:
        raise RuntimeError(
            "Segredo GOOGLE_CREDENTIALS_JSON não encontrado."
        )

    try:
        creds_info = json.loads(credentials_json)

        credentials = Credentials.from_authorized_user_info(
            creds_info,
            SCOPES
        )

        # Renovação automática oficial via refresh_token
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        service = build(
            "blogger",
            "v3",
            credentials=credentials,
            cache_discovery=False
        )

        return service

    except Exception as e:
        print("ERRO AO AUTENTICAR NO GOOGLE BLOGGER API")
        raise e


# ============================================
# POSTAGEM
# ============================================

def publicar_artigo(service, titulo, html_content):
    body = {
        "kind": "blogger#post",
        "title": titulo,
        "content": html_content
    }

    try:
        response = (
            service.posts()
            .insert(
                blogId=BLOG_ID,
                body=body,
                isDraft=False
            )
            .execute()
        )

        print("POST PUBLICADO COM SUCESSO")
        print(f"ID: {response.get('id')}")
        print(f"URL: {response.get('url')}")

        return response

    except HttpError as e:
        print("ERRO REAL DA BLOGGER API")
        print(e)

        # NÃO MASCARAR ERRO
        raise e

    except Exception as e:
        print("ERRO INESPERADO AO PUBLICAR")
        raise e


# ============================================
# EXEMPLO DE EXECUÇÃO
# ============================================

def gerar_html_exemplo():
    agora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
    <h2>Artigo Automático</h2>

    <p>Publicado automaticamente via GitHub Actions.</p>

    <p><strong>Timestamp UTC:</strong> {agora}</p>

    <p>Sistema oficial com OAuth2 Google.</p>
    """


def main():
    try:
        print("INICIANDO AUTENTICAÇÃO GOOGLE")

        service = get_blogger_service()

        print("AUTENTICAÇÃO OK")

        titulo = f"Post Automático - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"

        html_content = gerar_html_exemplo()

        publicar_artigo(
            service=service,
            titulo=titulo,
            html_content=html_content
        )

        print("PROCESSO FINALIZADO COM SUCESSO")

    except Exception as e:
        print("FALHA CRÍTICA NO PROCESSO")
        raise e


if __name__ == "__main__":
    main()
