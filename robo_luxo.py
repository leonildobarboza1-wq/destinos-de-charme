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
# GERAR ARTIGO IA (CORRIGIDO)
# ==========================================

def gerar_artigo(cliente, noticia, imagens):
    titulo_seo = gerar_titulo_seo(noticia["titulo"])

    prompt = f"""
Você é um jornalista de turismo internacional de altíssimo padrão e redator-chefe de uma revista de estilo de vida de luxo.
Sua missão é ler o fato abaixo e criar uma reportagem de cobertura exclusiva, detalhada, totalmente inédita e autoral.

CONTEXTO DA NOTÍCIA:
Título original: {noticia['titulo']}
Fatos/Resumo: {noticia['resumo']}

REGRAS CRUCIAIS DE ESCRITA:
1. Escreva um artigo LONGO, completo e robusto (mínimo de 800 a 1000 palavras). Quero parágrafos densos e profundos.
2. Utilize apenas tags HTML puras (<p>, <h2>, <h3>). 
3. NÃO use tags globais como <html>, <body>, <h1> ou <div> com estilos engessados.
4. Não copie frases da fonte original. Reescreva tudo com um tom sofisticado, glamouroso, focado no público Ultra-wealthy.
5. Desenvolva extensamente o cenário, a arquitetura dos locais mencionados, o nível do serviço VIP e detalhes que expandam o assunto de forma inteligente.
6. NUNCA use marcações Markdown (sem asteriscos **, sem blocos de ```html). Retorne APENAS o texto cru com as tags HTML misturadas.

Gere o artigo completo em Português.
"""

    try:
        # Chamada oficial e correta para a biblioteca google-genai
        resposta = cliente.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        html = resposta.text
        if not html:
            raise Exception("A resposta da IA veio completamente vazia.")

        # Limpeza agressiva contra qualquer Markdown que a IA teime em colocar
        html = re.sub(r"```html", "", html)
        html = re.sub(r"```", "", html)
        html = html.replace("**", "") # Remove asteriscos perdidos
        html = html.strip()

        # Montagem do corpo da postagem (A primeira imagem ABRE o post para o feed capturar)
        html_final = bloco_imagem(imagens[0])
        
        # Distribui as outras imagens ao longo dos subtítulos (<h2>) gerados pela IA
        partes = html.split("</h2>")
        if len(partes) > 1:
            contador_imagem = 1
            for parte in partes:
                # Reconstrói a tag <h2> após o split
                html_final += parte + "</h2>" if not parte.endswith("</h2>") else parte
                if contador_imagem < len(imagens) and parte != partes[-1]:
                    html_final += bloco_imagem(imagens[contador_imagem])
                    contador_imagem += 1
        else:
            html_final += html
            if len(imagens) > 1:
                html_final += bloco_imagem(imagens[1])

        # Rodapé elegante com link para a fonte
        html_final += f"""
<div style="margin-top: 50px; padding: 20px; border-top: 1px solid #e5e5e5;">
  <p style="font-size: 14px; color: #666; font-style: italic;">
    Com informações da cobertura jornalística de estilo de vida da <a href="{noticia['link']}" target="_blank" style="color: #000; font-weight: 600; text-decoration: underline;">Fonte Original ({noticia['titulo']})</a>.
  </p>
</div>
"""
        return titulo_seo, html_final

    except Exception as e:
        # Se cair aqui, vamos printar o erro real no terminal para você ver o que quebrou!
        print(f"\n[ALERTA] A IA FALHOU! Erro retornado: {e}")
        print("Usando o Fallback de segurança para não interromper o robô...")
        
        fallback = f"""
{bloco_imagem(imagens[0])}
<p>O segmento do turismo de alto padrão e lifestyle premium segue em constante expansão global, apresentando novas propriedades, roteiros customizados e experiências ultra-exclusivas voltadas para um público altamente exigente.</p>
{bloco_imagem(imagens[-1])}
<h2>Design Extraordinário e Hospitalidade de Elite</h2>
<p>Mais do que hotelaria tradicional, o mercado de luxo atual foca em privacidade absoluta, curadoria de experiências e arquitetura monumental. Destinos isolados e atendimento milimetricamente personalizado são os novos pilares desse mercado.</p>
<h2>Tendências Globais para o Consumidor Premium</h2>
<p>Seja através de iatismo charter, destinos sazonais sofisticados ou refúgios ecológicos cinco estrelas, as principais capitais e resorts do mundo continuam redefinindo o significado de exclusividade.</p>
<p style="margin-top: 40px; font-size: 15px;">Acompanhe os detalhes e desdobramentos completos acessando diretamente a <a href="{noticia['link']}" target="_blank" style="font-weight: bold; color: #000; text-decoration: underline;">matéria de cobertura na fonte</a>.</p>
"""
        return titulo_seo, fallback


# ==========================================
# MAIN (REVISADA)
# ==========================================

def main():
    try:
        print("\n================================")
        print("INICIANDO ROBÔ PREMIUM")
        print("================================")

        service = get_blogger_service()
        print("\nBLOGGER OK")

        # Correção na inicialização do cliente Gemini
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
        print("\nARTIGO GERADO COM SUCESSO")

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
        print("ERRO CRÍTICO NO PROCESSO")
        print("================================")
        print(e)
        raise e

if __name__ == "__main__":
    main()
