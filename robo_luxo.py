import os
import json
import time
import random
import requests
import feedparser
import re

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
    "private island luxury",
    "luxury beach resort",
    "luxury suite",
    "luxury vacation",
    "luxury destination",
    "luxury travel lifestyle",
    "five star hotel",
    "exclusive resort",
    "luxury yacht",
]

UNSPLASH_ACCESS_KEY = os.environ.get(
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
                    feed.entries[:7]
                )

                titulo = noticia.title

                resumo = getattr(
                    noticia,
                    "summary",
                    ""
                )

                resumo = limpar_html(resumo)

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
# LIMPAR HTML
# ==========================================

def limpar_html(texto):

    texto = re.sub(
        r"<.*?>",
        "",
        texto
    )

    return texto.strip()


# ==========================================
# BUSCAR MÚLTIPLAS IMAGENS
# ==========================================

def gerar_imagens():

    imagens = []

    try:

        for i in range(5):

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

                continue

            data = response.json()

            resultados = data.get(
                "results",
                []
            )

            if not resultados:
                continue

            imagem = random.choice(
                resultados
            )

            imagens.append({
                "url": imagem["urls"]["regular"],
                "autor": imagem["user"]["name"]
            })

            time.sleep(1)

        if not imagens:

            raise Exception(
                "Nenhuma imagem encontrada"
            )

        print(
            f"\nTOTAL DE IMAGENS: {len(imagens)}"
        )

        return imagens

    except Exception as e:

        print("\nERRO IMAGENS")
        print(e)

        return [
            {
                "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
                "autor": "Unsplash"
            }
        ]


# ==========================================
# HTML IMAGENS
# ==========================================

def bloco_imagem(imagem):

    return f"""
<div style="
margin:45px 0;
text-align:center;
">

<img
src="{imagem['url']}"
alt="Luxury Travel"
style="
width:100%;
border-radius:18px;
box-shadow:0 10px 30px rgba(0,0,0,0.15);
"
>

<p style="
font-size:13px;
color:#888;
margin-top:8px;
">
Photo: {imagem['autor']} / Unsplash
</p>

</div>
"""


# ==========================================
# GERAR ARTIGO IA
# ==========================================

def gerar_artigo(
    cliente,
    noticia,
    imagens
):

    prompt = f"""
Você é um redator profissional especialista em:

- turismo de luxo
- resorts premium
- hotéis sofisticados
- lifestyle internacional
- viagens exclusivas

Crie um artigo PREMIUM em HTML.

OBJETIVO:
Criar um conteúdo digno de revista internacional de luxo.

REGRAS IMPORTANTES:

- mínimo 1500 palavras
- SEO avançado
- tom sofisticado
- texto extremamente humanizado
- estrutura estilo MAGAZINE
- linguagem elegante
- storytelling profissional
- usar H2 e H3
- HTML puro
- NÃO use markdown
- incluir emoção e exclusividade
- criar subtítulos fortes
- incluir experiências premium
- incluir tendências de turismo de luxo
- incluir dicas sofisticadas
- criar leitura agradável
- finalizar com conclusão elegante
- não repetir frases
- criar aparência profissional

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

        partes = html.split("</h2>")

        html_final = f"""
<div style="
max-width:1000px;
margin:auto;
font-family:Arial,sans-serif;
line-height:1.9;
color:#222;
">

{bloco_imagem(imagens[0])}
"""

        contador_imagem = 1

        for parte in partes:

            html_final += parte

            if contador_imagem < len(imagens):

                html_final += bloco_imagem(
                    imagens[contador_imagem]
                )

                contador_imagem += 1

        html_final += f"""

<hr style="margin-top:60px;">

<div style="
background:#fafafa;
padding:25px;
border-radius:14px;
margin-top:40px;
">

<h3 style="margin-top:0;">
Fonte Original
</h3>

<p>
<a href="{noticia['link']}" target="_blank">
{noticia['titulo']}
</a>
</p>

</div>

</div>
"""

        return noticia["titulo"], html_final

    except Exception as e:

        print("\nERRO GEMINI")
        print(e)

        fallback = f"""
<div style="
max-width:1000px;
margin:auto;
font-family:Arial;
line-height:1.9;
">

{bloco_imagem(imagens[0])}

<h1>{noticia['titulo']}</h1>

<p>
O universo do turismo de luxo continua
evoluindo com experiências sofisticadas,
hotéis premium e destinos exclusivos.
</p>

{bloco_imagem(imagens[-1])}

<h2>Experiências Exclusivas</h2>

<p>
Viajantes modernos buscam privacidade,
serviços personalizados e experiências
memoráveis em destinos paradisíacos.
</p>

<h2>Mercado Premium</h2>

<p>
O segmento de luxo segue crescendo
globalmente impulsionado por resorts
sofisticados e hospitalidade cinco estrelas.
</p>

<h2>Conclusão</h2>

<p>
As viagens premium redefinem constantemente
o conceito de exclusividade e sofisticação.
</p>

</div>
"""

        return noticia["titulo"], fallback


# ==========================================
# PUBLICAR BLOGGER
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

    print("\n================================")
    print("POST PUBLICADO COM SUCESSO")
    print("================================")
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

        imagens = gerar_imagens()

        print("\nIMAGENS OK")

        time.sleep(2)

        titulo, html = gerar_artigo(
            gemini,
            noticia,
            imagens
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


# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    main()
