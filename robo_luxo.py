import os
import json
import feedparser
from datetime import datetime
from google import genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# =========================
# CONFIGURAÇÕES
# =========================

BLOG_ID = "2362582861639823192"

RSS_FEEDS = [
    "https://www.luxuo.com/feed",
    "https://robbreport.com/feed",
    "https://www.forbes.com/lifestyle/feed",
]

# =========================
# AUTENTICAÇÃO BLOGGER
# =========================

def get_blogger_service():
    try:
        credentials_info = json.loads(
            os.environ["GOOGLE_CREDENTIALS_JSON"]
        )

        credentials = Credentials.from_authorized_user_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/blogger"]
        )

        credentials.refresh(Request())

        service = build(
            "blogger",
            "v3",
            credentials=credentials
        )

        return service

    except Exception as e:
        print("ERRO AO AUTENTICAR NO GOOGLE BLOGGER API")
        raise e


# =========================
# GEMINI API
# =========================

def get_gemini_client():
    api_key = os.environ["GEMINI_API_KEY"]

    client = genai.Client(api_key=api_key)

    return client


# =========================
# RSS
# =========================

def obter_noticia():
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        if feed.entries:
            noticia = feed.entries[0]

            titulo = noticia.title
            resumo = getattr(noticia, "summary", "")
            link = noticia.link

            return {
                "titulo": titulo,
                "resumo": resumo,
                "link": link
            }

    raise Exception("Nenhuma notícia encontrada nos feeds RSS")


# =========================
# GERAR ARTIGO IA
# =========================

def gerar_artigo(cliente, noticia):
    prompt = f"""
    Você é um redator especialista em turismo de luxo,
    hotéis premium, destinos sofisticados e lifestyle internacional.

    Crie um artigo PREMIUM em HTML para Blogger.

    REGRAS:
    - Texto elegante
    - SEO avançado
    - Linguagem refinada
    - Estrutura profissional
    - Use subtítulos H2
    - Use parágrafos HTML
    - NÃO use markdown
    - Finalize com conclusão elegante

    TÍTULO:
    {noticia['titulo']}

    RESUMO:
    {noticia['resumo']}

    LINK ORIGINAL:
    {noticia['link']}
    """

    resposta = cliente.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt
    )

    html = resposta.text

    titulo_final = noticia["titulo"]

    return titulo_final, html


# =========================
# PUBLICAR BLOGGER
# =========================

def publicar_post(service, titulo, html):
    try:
        body = {
            "title": titulo,
            "content": html
        }

        post = service.posts().insert(
            blogId=BLOG_ID,
            body=body,
            isDraft=False
        ).execute()

        print("\nPOST PUBLICADO COM SUCESSO")
        print(post["url"])

    except Exception as e:
        print("ERRO AO PUBLICAR NO BLOGGER")
        raise e


# =========================
# MAIN
# =========================

def main():
    try:
        print("\nINICIANDO PIPELINE")

        service = get_blogger_service()

        print("BLOGGER OK")

        gemini = get_gemini_client()

        print("GEMINI OK")

        noticia = obter_noticia()

        print(f"\nNOTÍCIA ENCONTRADA:")
        print(noticia["titulo"])

        titulo, html = gerar_artigo(
            gemini,
            noticia
        )

        print("\nARTIGO GERADO")

        publicar_post(
            service,
            titulo,
            html
        )

        print("\nPROCESSO FINALIZADO")

    except Exception as e:
        print("\nFALHA CRÍTICA NO PROCESSO")
        raise e


if __name__ == "__main__":
    main()
