import os
import json
import time
import feedparser
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
        print("ERRO AO AUTENTICAR NO BLOGGER")
        raise e


# =========================
# GEMINI API
# =========================

def get_gemini_client():
    try:
        api_key = os.environ["GEMINI_API_KEY"]

        client = genai.Client(
            api_key=api_key
        )

        return client

    except Exception as e:
        print("ERRO AO INICIALIZAR GEMINI")
        raise e


# =========================
# RSS
# =========================

def obter_noticia():
    for url in RSS_FEEDS:
        try:
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

        except Exception as e:
            print(f"ERRO RSS: {url}")
            print(e)

    raise Exception("Nenhuma notícia encontrada nos feeds RSS")


# =========================
# GERAR ARTIGO IA
# =========================

def gerar_artigo(cliente, noticia):

    prompt = f"""
Você é um redator especialista em:
- turismo de luxo
- hotéis premium
- destinos sofisticados
- lifestyle internacional

Crie um artigo PREMIUM em HTML para Blogger.

REGRAS:
- Texto elegante
- SEO avançado
- Linguagem refinada
- Estrutura profissional
- Use subtítulos H2
- Use HTML puro
- Use parágrafos HTML
- NÃO use markdown
- Mínimo 1200 palavras
- Finalize com conclusão elegante

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
            raise Exception("Resposta vazia da IA")

        titulo_final = noticia["titulo"]

        return titulo_final, html

    except Exception as e:

        print("ERRO AO GERAR ARTIGO")
        print(e)

        html_fallback = f"""
<h1>{noticia['titulo']}</h1>

<p>
O universo do luxo continua evoluindo com experiências exclusivas,
destinos sofisticados e tendências premium que redefinem o turismo
internacional.
</p>

<p>
A notícia original destaca:
<a href="{noticia['link']}" target="_blank">
{noticia['titulo']}
</a>
</p>

<h2>Experiência Premium</h2>

<p>
Hotéis exclusivos, experiências personalizadas e serviços de alto padrão
continuam atraindo viajantes exigentes ao redor do mundo.
</p>

<h2>Tendências do Mercado de Luxo</h2>

<p>
O mercado global de lifestyle premium segue crescendo, impulsionado por
novas experiências de hospitalidade e turismo sofisticado.
</p>

<h2>Conclusão</h2>

<p>
O segmento de luxo permanece como referência em inovação, exclusividade
e experiências memoráveis para viajantes internacionais.
</p>
"""

        return noticia["titulo"], html_fallback


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

        print("\nNOTÍCIA ENCONTRADA:")
        print(noticia["titulo"])

        time.sleep(3)

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
        print(e)

        raise e


if __name__ == "__main__":
    main()
