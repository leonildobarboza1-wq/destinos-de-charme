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
        palavras_chave = [palavra for palavra in re.findall(r'\b[A-ZÀ-Úa-zà-ú]{4,}\b', titulo_noticia) 
                          if palavra.lower() not in ['para', 'com', 'uma', 'mais', 'sobre', 'luxo', 'exclusive']]
        
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
# BLOCO IMAGEM
# ==========================================

def bloco_imagem(imagem):
    return f"""
<div style="margin:50px 0; text-align:center;">
<img src="{imagem['url']}" alt="Luxury Travel" style="width:100%; border-radius:20px; box-shadow:0 10px 35px rgba(0,0,0,0.18);">
<p style="font-size:13px; color:#888; margin-top:10px;">
Photo by {imagem['autor']} / Unsplash
</p>
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
Você é um journalist de turismo internacional de altíssimo padrão e redator-chefe de uma revista de estilo de vida de luxo.
Sua missão é ler o fato abaixo e criar uma grande reportagem de cobertura exclusiva, totalmente inédita e autoral.

CONTEXTO DA NOTÍCIA:
Título original: {noticia['titulo']}
Fatos/Resumo: {noticia['resumo']}

REGRAS CRUCIAIS DE ESCRITA (PARA EVITAR PLÁGIO E ARTIFICIALIDADE):
1. Escreva um artigo completo e robusto em HTML puro (mínimo de 50 a 60 linhas de parágrafos de conteúdo denso, aproximadamente 1000 palavras).
2. Não copie frases da fonte original. Reescreva a história com um tom sofisticado, glamouroso, focado no público ultra-wealthy.
3. Desenvolva o cenário: Descreva como deve ser a experiência no local, a arquitetura, o serviço impecável e os detalhes que encantam viajantes de alto padrão. Expandir o assunto de forma inteligente.
4. Organize o texto utilizando cabeçalhos <h2> e <h3> elegantes ao longo da leitura.
5. NUNCA use marcações Markdown (sem asteriscos **, sem blocos de ```html). Escreva apenas o texto envolto nas tags HTML diretamente.

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

        html = re.sub(r"```html", "", html)
        html = re.sub(r"```", "", html)
        html = html.strip()

        html_final = f"""
<div style="max-width:1050px; margin:auto; font-family:Arial,sans-serif; line-height:2.0; color:#1a1a1a; font-size:19px; text-align: justify;">
{bloco_imagem(imagens[0])}
<h1 style="font-size:36px; margin-bottom:30px; color:#111; line-height:1.3;">{titulo_seo}</h1>
"""
        
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

        html_final += f"""
<div style="margin-top:60px; padding:30px; background:#fcfcfc; border-top:1px solid #eee; border-radius:18px;">
<h4 style="color:#777; text-transform:uppercase; letter-spacing:1px; font-size:13px; margin-bottom:10px;">Leitura Recomendada</h4>
<p style="font-size:16px;">Confira também os detalhes da cobertura oficial na <a href="{noticia['link']}" target="_blank" style="color:#111; font-weight:bold; text-decoration:underline;">Fonte Original ({noticia['titulo']})</a>.</p>
</div>
</div>
"""
        return titulo_seo, html_final

    except Exception as e:
        print("\nERRO GEMINI - Usando Fallback")
        print(e)
        
        fallback = f"""
<div style="max-width:1000px; margin:auto; font-family:Arial; line-height:1.9; font-size:19px;">
{bloco_imagem(imagens[0])}
<h1 style="font-size:36px; margin-bottom:30px; color:#111; line-height:1.3;">{titulo_seo}</h1>
<p>O turismo de luxo continua crescendo globalmente com experiências exclusivas, resorts premium e destinos paradisíacos.</p>
{bloco_imagem(imagens[-1])}
<h2>Experiências Premium</h2>
<p>Viajantes sofisticados buscam conforto, privacidade e experiências memoráveis em hotéis e resorts de alto padrão.</p>
<h2>Destinos Exclusivos</h2>
<p>O mercado internacional de turismo premium segue redefinindo o conceito de hospitalidade.</p>
<h2>Conclusão</h2>
<p>O universo das viagens sofisticadas continua evoluindo com novas tendências de luxo.</p>
<p><a href="{noticia['link']}" target="_blank">Fonte Original</a></p>
</div>
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

        gemini = get_gemini_client()
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
