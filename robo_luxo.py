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

# ==========================================
# UNSPLASH
# ==========================================

UNSPLASH_ACCESS_KEY = os.environ.get(
    "UNSPLASH_ACCESS_KEY",
    ""
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
# LIMPAR HTML
# ==========================================

def limpar_html(texto):

    texto = re.sub(
        r"<.*?>",
        "",
        texto
    )

    texto = texto.replace("\n", " ")

    return texto.strip()


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

                resumo = limpar_html(
                    resumo
                )

                link = noticia.link

                print("\nNOTÍCIA ENCONTRADA")
                print(titulo)

                return {
                    "titulo": titulo,
                    "resumo": resumo,
                    "link": link
                }

        except Exception as e:

            print("\nERRO RSS")
            print(e)

    raise Exception(
        "Nenhuma notícia encontrada"
    )


# ==========================================
# FALLBACK IMAGEM
# ==========================================

def imagens_fallback():

    return [
        {
            "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
            "autor": "Unsplash"
        },
        {
            "url": "https://images.unsplash.com/photo-1493558103817-58b2924bce98",
            "autor": "Unsplash"
        },
        {
            "url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb",
            "autor": "Unsplash"
        }
    ]


# ==========================================
# BUSCAR IMAGENS
# ==========================================

def gerar_imagens():

    imagens = []

    if not UNSPLASH_ACCESS_KEY:

        print(
            "\nUNSPLASH NÃO CONFIGURADO"
        )

        return imagens_fallback()

    try:

        for i in range(5):

            tema = random.choice(
                TEMAS_IMAGENS
            )

            print(
                f"\nBUSCANDO IMAGEM: {tema}"
            )

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

                print(
                    f"ERRO UNSPLASH: {response.status_code}"
                )

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

        if imagens:

            print(
                f"\nTOTAL IMAGENS: {len(imagens)}"
            )

            return imagens

    except Exception as e:

        print("\nERRO IMAGENS")
        print(e)

    return imagens_fallback()


# ==========================================
# BLOCO IMAGEM
# ==========================================

def bloco_imagem(imagem):

    return f"""
<div style="
margin:50px 0;
text-align:center;
">

<img
src="{imagem['url']}"
alt="Luxury Travel"
style="
width:100%;
border-radius:20px;
box-shadow:0 10px 35px rgba(0,0,0,0.18);
"
>

<p style="
font-size:13px;
color:#888;
margin-top:10px;
">
Photo by {imagem['autor']} / Unsplash
</p>

</div>
"""


# ==========================================
# SEO TÍTULO
# ==========================================

def gerar_titulo_seo(titulo):

    prefixos = [
        "Descubra",
        "Conheça",
        "Veja",
        "Luxo:",
        "Exclusivo:",
        "Turismo Premium:",
        "Destino de Luxo:"
    ]

    prefixo = random.choice(
        prefixos
    )

    return f"{prefixo} {titulo}"


# ==========================================
# GERAR ARTIGO IA
# ==========================================

def gerar_artigo(
    cliente,
    noticia,
    imagens
):

    titulo_seo = gerar_titulo_seo(
        noticia["titulo"]
    )

    prompt = f"""
Você é um redator profissional especialista em:

- turismo de luxo
- hotéis premium
- lifestyle sofisticado
- destinos exclusivos
- experiências internacionais

Crie um artigo PREMIUM em HTML.

OBJETIVO:
Criar um conteúdo estilo revista internacional.

REGRAS:

- mínimo 1500 palavras
- SEO extremamente forte
- estrutura estilo magazine
- linguagem sofisticada
- texto altamente humanizado
- storytelling elegante
- usar H2 e H3
- HTML puro
- NÃO use markdown
- criar leitura agradável
- criar subtítulos fortes
- incluir tendências do turismo de luxo
- incluir dicas sofisticadas
- incluir experiências premium
- incluir sensação de exclusividade
- finalizar com conclusão elegante

TÍTULO:
{titulo_seo}

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

            raise Exception(
                "Resposta vazia"
            )

        partes = html.split("</h2>")

        html_final = f"""
<div style="
max-width:1050px;
margin:auto;
font-family:Arial,sans-serif;
line-height:1.95;
color:#222;
font-size:19px;
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

<div style="
margin-top:60px;
padding:30px;
background:#fafafa;
border-radius:18px;
">

<h3>
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

        return titulo_seo, html_final

    except Exception as e:

        print("\nERRO GEMINI")
        print(e)

        fallback = f"""
<div style="
max-width:1000px;
margin:auto;
font-family:Arial;
line-height:1.9;
font-size:19px;
">

{bloco_imagem(imagens[0])}

<h1>{titulo_seo}</h1>

<p>
O turismo de luxo continua crescendo
globalmente com experiências exclusivas,
resorts premium e destinos paradisíacos.
</p>

{bloco_imagem(imagens[-1])}

<h2>Experiências Premium</h2>

<p>
Viajantes sofisticados buscam conforto,
privacidade e experiências memoráveis
em hotéis e resorts de alto padrão.
</p>

<h2>Destinos Exclusivos</h2>

<p>
O mercado internacional de turismo premium
segue redefinindo o conceito de hospitalidade.
</p>

<h2>Conclusão</h2>

<p>
O universo das viagens sofisticadas continua
evoluindo com novas tendências de luxo.
</p>

<p>
<a href="{noticia['link']}" target="_blank">
Fonte Original
</a>
</p>

</div>
"""

        return titulo_seo, fallback


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
    print("POST PUBLICADO")
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
