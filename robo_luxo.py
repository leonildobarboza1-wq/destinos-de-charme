import os
import json
import time
import random
import requests
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
# VARIÁVEIS DE AMBIENTE
# ==========================================

UNSPLASH_ACCESS_KEY = os.getenv(
    "UNSPLASH_ACCESS_KEY"
)

if not UNSPLASH_ACCESS_KEY:
    raise Exception(
        "UNSPLASH_ACCESS_KEY não encontrada nos Secrets do GitHub"
    )

# ==========================================
# BLOGGER AUTH
# ==========================================

def get_blogger_service():

    credentials_info = json.loads(
        os.environ["GOOGLE_CREDENTIALS_JSON"]
    )

    credentials = Credentials.from_authorized_user_info(
        credentials_info,
        scopes=[
            "https://www.googleapis.com/auth/blogger"
        ]
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
# RSS NEWS
# ==========================================

def obter_noticia():

    random.shuffle(RSS_FEEDS)

    for url in RSS_FEEDS:

        try:

            print(f"\nLENDO RSS: {url}")

            feed = feedparser.parse(url)

            if feed.entries:

                noticia = random.choice(
                    feed.entries[:5]
                )

                titulo = noticia.title

                resumo = getattr(
                    noticia,
                    "summary",
                    ""
                )

                link = noticia.link

                return {
                    "titulo": titulo,
                    "resumo": resumo,
                    "link": link
                }

        except Exception as e:

            print(f"ERRO RSS: {url}")
            print(e)

    raise Exception(
        "Nenhuma notícia encontrada"
    )


# ==========================================
# UNSPLASH API
# ==========================================

def gerar_imagem_url():

    try:

        tema = random.choice(
            TEMAS_IMAGENS
        )

        print(f"\nBUSCANDO IMAGEM: {tema}")

        url = (
            "https://api.unsplash.com/search/photos"
        )

        headers = {
            "Accept-Version": "v1"
        }

        params = {
            "query": tema,
            "orientation": "landscape",
            "per_page": 30,
            "client_id": UNSPLASH_ACCESS_KEY
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code != 200:

            print(response.text)

            raise Exception(
                f"Erro Unsplash: {response.status_code}"
            )

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:

            raise Exception(
                "Nenhuma imagem encontrada"
            )

        imagem = random.choice(results)

        imagem_url = imagem["urls"]["regular"]

        autor = imagem["user"]["name"]

        print("\nIMAGEM ENCONTRADA")
        print(imagem_url)
        print(f"Autor: {autor}")

        return imagem_url

    except Exception as e:

        print("\nERRO UNSPLASH")
        print(e)

        return (
            "https://images.unsplash.com/"
            "photo-1507525428034-b723cf961d3e"
        )


# ==========================================
# GERAR ARTIGO
# ==========================================

def gerar_artigo(
    cliente,
    noticia,
    imagem_url
):

    prompt = f"""
Você é um redator profissional especialista em:

- turismo de luxo
- resorts premium
- hotéis sofisticados
- lifestyle internacional
- experiências exclusivas

Crie um artigo PREMIUM em HTML.

REGRAS IMPORTANTES:

- mínimo 1200 palavras
- SEO avançado
- tom sofisticado
- linguagem elegante
- texto humanizado
- estrutura profissional
- use H2 e H3
- HTML puro
- NÃO use markdown
- use storytelling
- destaque experiências premium
- destaque destinos sofisticados
- inclua dicas de viagem
- finalize com conclusão elegante

TÍTULO:
{noticia['titulo']}

RESUMO:
{noticia['resumo']}

LINK ORIGINAL:
{noticia['link']}
"""

    try:

        resposta = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        html = resposta.text

        if not html:

            raise Exception(
                "Resposta vazia da IA"
            )

        html_final = f"""
<div style="max-width:1000px;margin:auto;">

<img
src="{imagem_url}"
style="
width:100%;
border-radius:18px;
margin-bottom:30px;
box-shadow:0 8px 25px rgba(0,0,0,0.15);
"
>

<div style="
font-family:Arial;
font-size:18px;
line-height:1.9;
color:#222;
">

{html}

</div>

<hr style="margin-top:50px;">

<p style="
font-size:14px;
color:#777;
">

Fonte original:
<a href="{noticia['link']}" target="_blank">
{noticia['titulo']}
</a>

</p>

</div>
"""

        return noticia["titulo"], html_final

    except Exception as e:

        print("\nERRO GEMINI")
        print(e)

        fallback = f"""
<div style="max-width:1000px;margin:auto;">

<img
src="{imagem_url}"
style="
width:100%;
border-radius:18px;
margin-bottom:30px;
box-shadow:0 8px 25px rgba(0,0,0,0.15);
"
>

<h1>{noticia['titulo']}</h1>

<p>
O turismo de luxo continua evoluindo
globalmente com experiências exclusivas,
hotéis premium e destinos sofisticados.
</p>

<h2>Experiências Premium</h2>

<p>
Viajantes de alto padrão buscam cada vez mais
privacidade, conforto e serviços personalizados.
</p>

<h2>Destinos Exclusivos</h2>

<p>
Resorts paradisíacos e hotéis sofisticados
seguem redefinindo o mercado internacional
de hospitalidade de luxo.
</p>

<h2>Conclusão</h2>

<p>
O segmento premium permanece crescendo
globalmente, impulsionado por experiências
memoráveis e viagens exclusivas.
</p>

<p>
Fonte original:
<a href="{noticia['link']}" target="_blank">
{noticia['titulo']}
</a>
</p>

</div>
"""

        return noticia["titulo"], fallback


# ==========================================
# PUBLICAR NO BLOGGER
# ==========================================

def publicar_post(
    service,
    titulo,
    html
):

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

        print("\n================================")
        print("INICIANDO ROBÔ PREMIUM")
        print("================================")

        service = get_blogger_service()

        print("\nBLOGGER OK")

        gemini = get_gemini_client()

        print("GEMINI OK")

        noticia = obter_noticia()

        print("\nNOTÍCIA ENCONTRADA:")
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

        print("\n================================")
        print("PROCESSO FINALIZADO")
        print("================================")

    except Exception as e:

        print("\n================================")
        print("ERRO CRÍTICO")
        print("================================")

        print(e)

        raise e


if __name__ == "__main__":
    main()
