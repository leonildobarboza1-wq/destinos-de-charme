import os
import json
import time
import random
import requests
import feedparser
import re
from bs4 import BeautifulSoup

from google import genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ==========================================
# CONFIGURAÇÕES
# ==========================================

BLOG_ID = "2362582861639823192"

RSS_FEEDS = [
    "https://www.cntraveler.com/feed/wellness/rss",          # Condé Nast: Retiros e Bem-estar de Luxo
    "https://www.cntraveler.com/feed/interests/adventure-travel/rss", # Condé Nast: Aventura e Trilhas Premium
    "https://robbreport.com/luxury-travel/feed",            # Robb Report: Viagens e Destinos de Elite
    "https://www.luxuo.com/properties/hotel-resort/feed",   # Luxuo: Hotéis e Resorts Monumentais
    "https://www.forbes.com/travel/feed",                  # Forbes: Turismo de Luxo Global
]

TEMAS_IMAGENS = [
    "luxury mountain lodge dolomites", 
    "luxury wellness retreat bali", 
    "meditation sanctuary luxury", 
    "luxury yoga resort", 
    "swiss alps luxury hotel view",
    "luxury spa nature view"
]]

CATEGORIAS_BLOG = ["Destinos", "Hoteis", "Resorts"]

# ==========================================
# UNSPLASH
# ==========================================

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# ==========================================
# ACESSO E CONEXÕES
# ==========================================

def get_blogger_service():
    credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    credentials = Credentials.from_authorized_user_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )
    credentials.refresh(Request())
    return build("blogger", "v3", credentials=credentials)

def get_gemini_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def limpar_html(texto):
    texto = re.sub(r"<.*?>", "", texto)
    return texto.replace("\n", " ").strip()

# ==========================================
# RASPAGEM DA MATÉRIA COMPLETA (NOVIDADE)
# ==========================================

def raspar_materia_completa(url):
    """Acessa o site original e extrai todo o texto da matéria"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        print(f"[SCRAPER] Acessando a página original para leitura completa: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Busca parágrafos dentro de tags comuns de artigos jornalísticos
            paragrafos = soup.find_all("p")
            texto_completo = []
            
            for p in paragrafos:
                texto_p = p.get_text().strip()
                # Ignora textos curtos de rodapé ou menus
                if len(texto_p) > 60 and not any(w in texto_p.lower() for w in ["cookie", "subscribe", "privacy policy", "all rights reserved"]):
                    texto_completo.append(texto_p)
            
            conteúdo = " ".join(texto_completo[:15]) # Limita o tamanho para não estourar a cota da IA
            if len(conteúdo) > 200:
                print(f"[SCRAPER] Conteúdo extraído com sucesso ({len(conteúdo)} caracteres).")
                return conteúdo
                
    except Exception as e:
        print(f"[SCRAPER ERRO] Não foi possível ler o site diretamente: {e}")
    
    return None

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
                resumo_rss = getattr(noticia, "summary", "")
                resumo_rss = limpar_html(resumo_rss)
                link = noticia.link

                print(f"\nNOTÍCIA ENCONTRADA: {titulo}")
                
                # Tenta ler o conteúdo direto na página web original
                conteudo_profundo = raspar_materia_completa(link)
                resumo_final = conteudo_profundo if conteudo_profundo else resumo_rss

                return {
                    "titulo": titulo,
                    "resumo": resumo_final,
                    "link": link
                }
        except Exception as e:
            print(f"\nERRO RSS: {e}")

    raise Exception("Nenhuma notícia encontrada")

# ==========================================
# BUSCAR IMAGENS
# ==========================================

def imagens_fallback():
    return [
        {"url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e", "autor": "Unsplash"},
        {"url": "https://images.unsplash.com/photo-1493558103817-58b2924bce98", "autor": "Unsplash"}
    ]

def gerar_imagens(titulo_noticia):
    imagens = []
    if not UNSPLASH_ACCESS_KEY:
        return imagens_fallback()

    try:
        titulo_limpo = titulo_noticia.replace("'s", "").replace("’s", "")
        palavras = re.findall(r'\b[A-Za-z]{4,}\b', titulo_limpo)
        stop_words = ['inside', 'this', 'that', 'from', 'with', 'your', 'about', 'report', 'forbes', 'review']
        palavras_chave = [p.lower() for p in palavras if p.lower() not in stop_words]
        
        termo_busca = " ".join(palavras_chave[:2]) if palavras_chave else random.choice(TEMAS_IMAGENS)
        print(f"[UNSPLASH] Termo de busca de imagem: '{termo_busca}'")

        url = "https://api.unsplash.com/search/photos"
        params = {"query": termo_busca, "orientation": "landscape", "per_page": 8, "client_id": UNSPLASH_ACCESS_KEY}
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            resultados = response.json().get("results", [])
            if resultados:
                amostra = random.sample(resultados, min(len(resultados), 2))
                for img in amostra:
                    imagens.append({"url": img["urls"]["regular"], "autor": img["user"]["name"]})
        
        if len(imagens) < 2:
            imagens.extend(imagens_fallback())
        return imagens
    except Exception as e:
        print(f"[ERRO IMAGENS]: {e}")
        return imagens_fallback()

def bloco_imagem(imagem):
    return f"""
<div class="separator" style="clear: both; text-align: center; margin: 30px 0;">
  <img src="{imagem['url']}" alt="Luxury Concept" style="width: 100%; height: auto; border-radius: 8px; max-width: 100%;"/>
  <br/>
  <span style="font-size: 12px; color: #999;">Photo by {imagem['autor']} / Unsplash</span>
</div>
"""

# ==========================================
# GERAR ARTIGO IA
# ==========================================

def gerar_artigo(cliente, noticia, imagens):
    # Prompt agressivo exigindo tradução e reescrita total baseada no conteúdo coletado
    prompt = f"""
Você é o redator-chefe de uma revista de alto padrão. Leia a matéria internacional abaixo (em inglês) e faça uma reescrita jornalística completa e aprofundada em PORTUGUÊS DO BRASIL.

CONTEÚDO ORIGINAL DA MATÉRIA:
Título: {noticia['titulo']}
Texto de Origem: {noticia['resumo']}

REGRAS OBRIGATÓRIAS:
1. TÍTULO: Crie um título inédito, chamativo e luxuoso totalmente em português. Ele deve abrir a resposta na primeira linha.
2. CONTEÚDO: Não faça um resumo curto. Desenvolva um texto longo (mínimo de 600 palavras), fluido, reescrevendo os fatos com sinônimos e termos sofisticados.
3. FORMATO: Retorne apenas tags HTML puras (<p>, <h2>). Nunca use marcações Markdown (como asteriscos ** ou blocos de ```html).
4. IDIOMA: Proibido manter frases ou títulos em inglês. Tudo deve ser localizado para o português.
"""

    try:
        # Usando o 1.5-flash para economizar tokens e evitar o erro 429
        resposta = cliente.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        html = resposta.text
        if not html:
            raise Exception("Resposta da IA vazia.")

        html = re.sub(r"```html|```|\*\*", "", html).strip()

        # Separa a primeira linha como o título em português
        linhas = html.split("\n")
        titulo_final = linhas[0].replace("<p>", "").replace("</p>", "").replace("<h1>", "").replace("</h1>", "").strip()
        corpo_artigo = "\n".join(linhas[1:])

        # Garante que a primeira imagem abra a postagem na página interna
        html_final = bloco_imagem(imagens[0])
        
        partes = corpo_artigo.split("</h2>")
        if len(partes) > 1:
            contador = 1
            for parte in partes:
                html_final += parte + "</h2>" if not parte.endswith("</h2>") else parte
                if contador < len(imagens) and parte != partes[-1]:
                    html_final += bloco_imagem(imagens[contador])
                    contador += 1
        else:
            html_final += corpo_artigo
            if len(imagens) > 1:
                html_final += bloco_imagem(imagens[1])

        # Rodapé com link de créditos
        html_final += f"""
<div style="margin-top: 50px; padding: 20px; border-top: 1px solid #e5e5e5;">
  <p style="font-size: 14px; color: #666; font-style: italic;">
    Com informações e cobertura exclusiva adaptada da <a href="{noticia['link']}" target="_blank" style="color: #000; font-weight: 600; text-decoration: underline;">Matéria Original no veículo internacional</a>.
  </p>
</div>
"""
        return titulo_final, html_final

    except Exception as e:
        print(f"\n[ALERTA IA] Erro: {e}. Executando Fallback Traduzido...")
        # Fallback dinâmico em português caso a cota estoure de novo
        titulo_fallback = f"Destaque Internacional: Análise sobre {noticia['titulo']}"
        fallback = f"""
{bloco_imagem(imagens[0])}
<p>Novos desdobramentos movimentam o cenário global de alto padrão esta semana. O mercado internacional de estilo de vida premium acompanha atentamente as novas tendências de consumo, experiências customizadas e o comportamento do público de elite.</p>
{bloco_imagem(imagens[-1])}
<h2>Perspectivas e Impacto no Setor Premium</h2>
<p>Especialistas apontam que a busca por exclusividade total e serviços customizados continua redefinindo os investimentos de marcas e destinos sofisticados ao redor do mundo, criando novos nichos de mercado.</p>
<p style="margin-top: 40px;"><a href="{noticia['link']}" target="_blank" style="font-weight: bold; color: #000;">Clique aqui para ler os detalhes completos diretamente na cobertura oficial da fonte.</a></p>
"""
        return titulo_fallback, fallback

# ==========================================
# PUBLICAR BLOGGER
# ==========================================

def publicar_post(service, titulo, html):
    categoria = random.choice(CATEGORIAS_BLOG)
    body = {
        "title": titulo,
        "content": html,
        "labels": [categoria]
    }
    post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
    print(f"\n[SUCESSO] Post publicado em '{categoria}': {post['url']}")

# ==========================================
# MAIN
# ==========================================

def main():
    try:
        print("\n================================")
        print("INICIANDO SCRIPT DE COBERTURA INTEGRAL")
        print("================================")

        service = get_blogger_service()
        gemini = get_gemini_client()
        
        noticia = obter_noticia()
        imagens = gerar_imagens(noticia["titulo"]) 
        
        time.sleep(2)
        titulo, html = gerar_artigo(gemini, noticia, imagens)
        
        publicar_post(service, titulo, html)
        print("\n================================")
        print("PROCESSO CONCLUÍDO")
        print("================================")

    except Exception as e:
        print(f"\n[ERRO CRÍTICO]: {e}")
        raise e

if __name__ == "__main__":
    main()
