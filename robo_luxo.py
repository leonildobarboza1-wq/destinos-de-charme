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
CATEGORIAS_BLOG = ["Destinos", "Hoteis", "Resorts"]

# ==========================================
# UNSPLASH
# ==========================================

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# ==========================================
# BLOGGER AUTH
# ==========================================

def get_blogger_service():
    credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    credentials = Credentials.from_authorized_user_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )
    credentials.refresh(Request())
    service = build("blogger", "v3", credentials=credentials)
    return service

# ==========================================
# GEMINI
# ==========================================

def get_gemini_client():
    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
    return client

# ==========================================
# LIMPAR HTML
# ==========================================

def limpar_html(texto):
    texto = re.sub(r"<.*?>", "", texto)
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
                noticia = random.choice(feed.entries[:7])
                titulo = noticia.title
                resumo = getattr(noticia, "summary", "")
                resumo = limpar_html(resumo)
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

    raise Exception("Nenhuma notícia encontrada")

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

def gerar_imagens(titulo_noticia):
    imagens = []

    if not UNSPLASH_ACCESS_KEY:
        print("\nUNSPLASH NÃO CONFIGURADO")
        return imagens_fallback()

    try:
        palavras_chave = [palavra for word in re.findall(r'\b[A-ZÀ-Úa-zà-ú]{4,}\b', titulo_noticia) 
                          if (palavra := word.lower()) not in ['para', 'com', 'uma', 'mais', 'sobre', 'luxo', 'exclusive']]
        
        termo_busca = " ".join(palavras_chave[:3]) if palavras_chave else random.choice(TEMAS_IMAGENS)

        for i in range(3):
            print(f"\nBUSCANDO IMAGEM ESPECÍFICA NO UNSPLASH: {termo_busca}")

            url = "https://api.unsplash.com/search/photos"
            headers = {"Accept-Version": "v1"}
            params = {
                "query": termo_busca,
                "orientation": "landscape",
                "per_page": 15,
                "client_id": UNSPLASH_ACCESS_KEY
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                resultados = data.get("results", [])
                if resultados:
                    imagem = random.choice(resultados)
                    imagens.append({
                        "url": imagem["urls"]["regular"],
                        "autor": imagem["user"]["name"]
                    })
            time.sleep(1)

        if len(imagens) < 2:
            imagens.extend(imagens_fallback())

        return imagens

    except Exception as e:
        print("\nERRO IMAGENS - Usando Fallback")
        print(e)
        return imagens_fallback()

# ==========================================
# BLOCO IMAGEM (Padrão do Blogger para feeds)
# ==========================================

def bloco_imagem(imagem):
    return f"""
<div class="separator" style="clear: both; text-align: center; margin: 30px 0;">
  <img src="{imagem['url']}" alt="Luxury Travel" style="width: 100%; height: auto; border-radius: 8px; max-width: 100%;"/>
  <br/>
  <span style="font-size: 12px; color: #999; letter-spacing: 1px;">Photo by {imagem['autor']} / Unsplash</span>
</div>
"""

# ==========================================
# SEO TÍTULO
# ==========================================

def gerar_titulo_seo(titulo):
    prefixos = [
        "Descubra", "Conheça", "Veja", "Luxo:", 
        "Exclusivo:", "Turismo Premium:", "Destino de Luxo:"
    ]
    prefixo = random.choice(prefixos)
    return f"{prefixo} {titulo}"

# ==========================================
# GERAR ARTIGO IA
# ==========================================

def gerar_artigo(cliente, noticia, imagens):
    titulo_seo = gerar_titulo_seo(noticia["titulo"])

    prompt = f"""
Você é um jornalista de turismo internacional de altíssimo padrão e redator-chefe de uma revista de estilo de vida de luxo.
Sua missão é ler o fato abaixo e criar uma reportagem de cobertura exclusiva, totalmente inédita e autoral.

CONTEXTO DA NOTÍCIA:
Título original: {noticia['titulo']}
Fatos/Resumo: {noticia['resumo']}

REGRAS CRUCIAIS DE ESCRITA:
1. Escreva um artigo completo e robusto utilizando tags HTML puras (<p>, <h2>, <h3>). 
2. NÃO use tags de estrutura global como <html>, <body>, <h1> ou <div> engessando estilos. Foque apenas nos parágrafos e cabeçalhos internos.
3. Não copie frases da fonte original. Reescreva com um tom sofisticado, glamouroso, focado no público de alto padrão (VIP/Ultra-wealthy).
4. Desenvolva o cenário, arquitetura, serviços e detalhes ricos para expandir o assunto de forma inteligente.
5. NUNCA use marcações Markdown (sem asteriscos **, sem blocos de ```html). Retorne apenas o texto cru com as tags HTML permitidas.

Gere o artigo completo em Português.
"""

    try:
        resposta = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        html = resposta.text
        if not html:
            raise Exception("Resposta vazia")

        # Limpeza de possíveis resíduos de markdown da IA
        html = re.sub(r"```html", "", html)
        html = re.sub(r"```", "", html)
        html = html.strip()

        # Montagem do corpo da postagem respeitando a arquitetura do Tema do Blogger
        # A primeira imagem DEVE ser a primeira coisa no código HTML para o feed capturar.
        html_final = bloco_imagem(imagens[0])
        
        partes = html.split("</h2>")
        if len(partes) > 1:
            contador_imagem = 1
            for parte in partes:
                html_final += parte + "</h2>" if not parte.endswith("</h2>") else parte
                if contador_imagem < len(imagens) and parte != partes[-1]:
                    html_final += bloco_imagem(imagens[contador_imagem])
                    contador_imagem += 1
        else:
            html_final += html
            if len(imagens) > 1:
                html_final += bloco_imagem(imagens[1])

        # Seção de créditos e link externo elegante
        html_final += f"""
<div style="margin-top: 50px; padding: 20px; border-top: 1px solid #e5e5e5;">
  <p style="font-size: 14px; color: #666; font-style: italic;">
    Com informações complementares da cobertura oficial da <a href="{noticia['link']}" target="_blank" style="color: #000; font-weight: 600; text-decoration: underline;">Fonte Original ({noticia['titulo']})</a>.
  </p>
</div>
"""
        return titulo_seo, html_final

    except Exception as e:
        print("\nERRO GEMINI - Usando Fallback")
        print(e)
        
        # Fallback limpo que herda o CSS do tema perfeitamente
        fallback = f"""
{bloco_imagem(imagens[0])}
<p>O turismo de luxo continua crescendo globalmente com experiências exclusivas, resorts premium e destinos paradisíacos que redefinem o mercado de alto padrão.</p>
{bloco_imagem(imagens[-1])}
<h2>Experiências Extraordinárias e Hospitalidade Premium</h2>
<p>Viajantes sofisticados buscam o mais alto nível de conforto, privacidade total e experiências sob medida criadas por hotéis e resorts de elite mundiais.</p>
<h2>Destinos Exclusivos Globais</h2>
<p>O mercado internacional de turismo premium segue ditando fortes tendências e expandindo o conceito clássico de hospitalidade de alto luxo.</p>
<p style="margin-top: 40px;"><a href="{noticia['link']}" target="_blank" style="font-weight: bold; text-decoration: underline;">Acesse a cobertura completa na fonte.</a></p>
"""
        return titulo_seo, fallback

# ==========================================
# PUBLICAR BLOGGER
# ==========================================

def publicar_post(service, titulo, html):
    categoria_escolhida = random.choice(CATEGORIAS_BLOG)
    
    body = {
        "title": titulo,
        "content": html,
        "labels": [categoria_escolhida]
    }

    post = service.posts().insert(
        blogId=BLOG_ID,
        body=body,
        isDraft=False
    ).execute()

    print("\n================================")
    print(f"POST PUBLICADO NA CATEGORIA: {categoria_escolhida}")
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

        gemini = get_get_gemini_client() if 'get_get_gemini_client' in globals() else get_gemini_client()
        print("GEMINI OK")

        noticia = obter_noticia()
        imagens = gerar_imagens(noticia["titulo"]) 
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

if __name__ == "__main__":
    main()
