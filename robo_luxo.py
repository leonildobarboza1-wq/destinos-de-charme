import os
import json
import time
import random
import feedparser

from google import genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ==========================================
# CONFIGURAÇÕES
# ==========================================

BLOG_ID = "2362582861639823192"

RSS_FEEDS = [
    "https://www.luxuo.com/feed",
    "https://robbreport.com/feed",
    "https://www.forbes.com/lifestyle/feed",
]

UNSPLASH_ACCESS_KEY = os.environ["UNSPLASH_ACCESS_KEY"]

TEMAS_IMAGENS = [
    "luxury hotel",
    "luxury resort",
    "maldives resort",
    "private island",
    "luxury travel",
    "luxury beach",
    "luxury suite",
    "luxury vacation",
    "luxury destination",
]

# ==========================================
# BLOGGER AUTH
# ==========================================

def get_blogger_service():

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


# ==========================================
# GEMINI
# ==========================================

def get_gemini_client():

    api_key = os.environ["GEMINI_API_KEY"]

    client = genai.Client(
        api_key=api_key
    )

    return client


# ==========================================
# RSS
# ==========================================

def obter_noticia():

    random.shuffle(RSS_FEEDS)

    for url in RSS_FEEDS:

        try:

            feed = feedparser.parse(url)

            if feed.entries:

                noticia = random.choice(feed.entries[:5])

                titulo = noticia.title
                resumo = getattr(noticia, "summary", "")
                link = noticia.link

                return {
                    "titulo": titulo,
                    "resumo": resumo,
                    "link": link
                }

        except Exception as e:

            print(f"ERRO RSS: {url}")
            print(e)

    raise Exception("Nenhuma notícia encontrada")


# ==========================================
# IMAGEM UNSPLASH
# ==========================================

def gerar_imagem_url():

    tema = random.choice(TEMAS_IMAGENS)

    image_url = (
        f"https://source.unsplash.com/1600x900/?{tema}"
    )

    return image_url


# ==========================================
# GERAR ARTIGO
# ==========================================

def gerar_artigo(cliente, noticia, imagem_url):

    prompt = f"""
Você é um redator profissional especialista em:

- turismo de luxo
- hotéis premium
- resorts exclusivos
- lifestyle sofisticado
- viagens internacionais

Crie um artigo PREMIUM em HTML para Blogger.

REGRAS:

- mínimo 1200 palavras
- SEO avançado
- tom sofisticado
- estrutura elegante
- use H2 e H3
- HTML puro
- NÃO use markdown
- texto humanizado
- conteúdo altamente profissional
- inclua dicas de viagem
- finalize com conclusão elegante

TÍTULO:
{noticia['titulo']}

RESUMO:
{noticia['resumo']}

LINK:
{noticia['link']}
"""

    try:

        resposta = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        html = resposta.text

        if not html:
            raise Exception("Resposta vazia")

        html_final = f"""
<div style="text-align:center;">
<img src="{imagem_url}" style="width:100%; border-radius:12px;">
</div>

{html}
"""

        return noticia["titulo"], html_final

    except Exception as e:

        print("ERRO GEMINI")
        print(e)

        fallback = f"""
<div style="text-align:center;">
<img src="{imagem_url}" style="width:100%; border-radius:12px;">
</div>

<h1>{noticia['titulo']}</h1>

<p>
O universo do turismo de luxo continua crescendo globalmente,
com experiências exclusivas e destinos sofisticados atraindo
viajantes exigentes.
</p>

<h2>Experiências Premium</h2>

<p>
Resorts exclusivos, hotéis cinco estrelas e viagens personalizadas
seguem dominando o mercado internacional de luxo.
</p>

<h2>Destinos Sofisticados</h2>

<p>
Os viajantes modernos buscam conforto, privacidade e experiências
memoráveis em destinos paradisíacos ao redor do mundo.
</p>

<p>
Fonte original:
<a href="{noticia['link']}" target="_blank">
{noticia['titulo']}
</a>
</p>

<h2>Conclusão</h2>

<p>
O setor premium continua redefinindo o conceito de viagens exclusivas,
elevando o padrão da hospitalidade internacional.
</p>
"""

        return noticia["titulo"], fallback


# ==========================================
# PUBLICAR
# ==========================================

def publicar_post(service, titulo, html):

    body = {
        "title": titulo,
        "content": html
    }

    post = service.posts().insert(
        blogId=BLOG_ID,
        body=body,
        isDraft=False
    ).execute()

    print("\nPOST PUBLICADO:")
    print(post["url"])


# ==========================================
# MAIN
# ==========================================

def main():

    try:

        print("\nINICIANDO ROBÔ")

        service = get_blogger_service()

        print("BLOGGER OK")

        gemini = get_gemini_client()

        print("GEMINI OK")

        noticia = obter_noticia()

        print("\nNOTÍCIA:")
        print(noticia["titulo"])

        imagem_url = gerar_imagem_url()

        print("\nIMAGEM OK")

        time.sleep(2)

        titulo, html = gerar_artigo(
            gemini,
            noticia,
            imagem_url
        )

        print("\nARTIGO GERADO")

        publicar_post(
            service,
            titulo,
            html
        )

        print("\nPROCESSO FINALIZADO")

    except Exception as e:

        print("\nERRO CRÍTICO")
        print(e)

        raise e


if __name__ == "__main__":
    main()
