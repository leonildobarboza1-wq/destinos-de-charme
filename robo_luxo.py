import os
import urllib.request
import json
import xml.etree.ElementTree as ET
import requests
from google import genai

# CONFIGURAÇÕES DA API
API_KEY = os.environ.get("GEMINI_API_KEY")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")
BLOG_ID = "2362582861639823192"

# Link atualizado com barra no final para evitar o erro 308
FEED_URL = "https://www.relaischateaux.com/magazine/feed/"

def renovar_access_token():
    print("Renovando passe de acesso do Blogger...")
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": "407408718192.apps.googleusercontent.com",
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Erro ao renovar token: {e}")
    return os.environ.get("BLOGGER_ACCESS_TOKEN")

def buscar_ultima_noticia():
    print("Buscando novidades no mercado de luxo...")
    try:
        # Criamos um rastreador inteligente que aceita e segue redirecionamentos automaticamente
        class RedirectionHandler(urllib.request.HTTPRedirectHandler):
            def http_error_308(self, req, fp, code, msg, headers):
                return self.http_error_301(req, fp, code, msg, headers)

        opener = urllib.request.build_opener(RedirectionHandler)
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        
        with opener.open(FEED_URL) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        item = root.find('.//item')
        
        if item is not None:
            titulo = item.find('title').text
            descricao = item.find('description').text if item.find('description') is not None else ""
            return titulo, descricao
    except Exception as e:
        print(f"Erro ao buscar feed: {e}")
    return None, None

def usar_gemini_para_luxo(titulo_original, conteudo_original):
    print("Acionando o Gemini para criação do artigo de luxo...")
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Você é um editor-chefe de uma revista digital de turismo de luxo e hotéis boutique chamada 'Destinos de Charme'.
    Sua missão é transformar a notícia abaixo em um artigo sofisticado, elegante e altamente aspiracional.

    Título Original: {titulo_original}
    Conteúdo Original: {conteúdo_original}

    Regras de Formatação:
    1. Crie um título maravilhoso em Português (estilo revista de elite).
    2. Escreva o corpo do texto em Português de forma envolvente, destacando o design, o conforto e a exclusividade. Use parágrafos limpos.
    3. Adicione uma linha divisória elegante usando tags HTML (<hr style='border: 0; height: 1px; background: #ccc; margin: 20px 0;'>).
    4. Logo abaixo da divisória, crie uma seção chamada 'ENGLISH VERSION' e coloque o mesmo artigo traduzido com extrema elegância para o Inglês.
    5. O resultado final DEVE estar formatado em tags HTML limpas (como <p>, <strong>, etc). Não use blocos de código markdown.

    Retorne o texto estritamente no formato:
    [TITULO_DO_POST] Seu título sofisticado aqui
    [CORPO_DO_POST] Seu texto em HTML aqui juntando as duas versões (PT/EN).
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def publicar_no_blogger_oficial(titulo, corpo_html, token_valido):
    print("--------------------------------------------------")
    print("Publicando de forma autenticada no seu Blogger...")
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
    
    payload = {
        "kind": "blogger#post",
        "blog": {"id": BLOG_ID},
        "title": titulo,
        "content": corpo_html
    }
    
    headers = {
        'Authorization': f'Bearer {token_valido}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(f"RESPOSTA DO BLOGGER (STATUS): {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"✨ SUCESSO REAL! Artigo publicado no ar: '{titulo}'")
        else:
            print(f"TEXTO DO ERRO: {response.text}")
        print("--------------------------------------------------")
    except Exception as e:
        print(f"Erro ao conectar com o Blogger: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️ Chave GEMINI_API_KEY ausente.")
    else:
        token_atualizado = renovar_access_token()
        orig_titulo, orig_desc = buscar_ultima_noticia()
        if orig_titulo:
            resultado_ia = usar_gemini_para_luxo(orig_titulo, orig_desc)
            try:
                titulo_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                corpo_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                publicar_no_blogger_oficial(titulo_final, corpo_final, token_atualizado)
            except Exception as e:
                publicar_no_blogger_oficial("Refúgio de Luxo Internacional", resultado_ia, token_atualizado)
