import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ==========================================
# CONFIGURAÇÕES DE AMBIENTE
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
BLOG_ID = "2362582861639823192"

FONTES_NEWS = [
    {"nome": "Robb Report", "url": "https://robbreport.com/travel/feed/"}
]

def inicializar_client_blogger():
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("ERRO CRÍTICO: GOOGLE_CREDENTIALS_JSON ausente.")
    try:
        creds_data = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = Credentials.from_authorized_user_info(creds_data, scopes=['https://www.googleapis.com/auth/blogger'])
        return build('blogger', 'v3', credentials=creds)
    except Exception as e:
        raise e

def buscar_noticia():
    print("🌐 Minerando notícia e capturando link original...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for fonte in FONTES_NEWS:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())
            item = root.find('.//item')
            if item is not None:
                title = item.find('title').text
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text # Captura o link real da matéria
                return title, desc, link
        except Exception:
            continue
    return None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original):
    print("🧠 Gerando artigo com atribuição de fonte...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    Você é o editor-chefe da revista 'Destinos de Charme'. 
    Traduza e transforme a notícia abaixo em um artigo de luxo sofisticado.

    Dados:
    - Título: {titulo}
    - Conteúdo: {conteudo}
    
    DIRETRIZES:
    1. Título poético 100% em PORTUGUÊS.
    2. Texto envolvente sem jargões como "Destaque Internacional".
    3. Ao final da versão em português, insira OBRIGATORIAMENTE uma linha com: 
       '<p><i>Fonte original: <a href="{link_original}">Clique aqui para ler a matéria completa no site oficial</a></i></p>'
    
    FORMATOS:
    [TITULO_DO_POST] Título em português aqui.
    [CORPO_DO_POST] Conteúdo HTML. Inclua a <hr> e a ENGLISH VERSION após a fonte original.
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def publicar_postagem(blogger_service, titulo, corpo_html):
    body = {"kind": "blogger#post", "title": titulo, "content": corpo_html}
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        request.execute()
        print("✨ Postagem publicada com sucesso e link da fonte incluído!")
    except Exception as e:
        raise e

if __name__ == "__main__":
    blogger_client = inicializar_client_blogger()
    orig_titulo, orig_desc, orig_link = buscar_noticia()
    
    if orig_titulo:
        resultado_ia = gerar_conteudo_ia(orig_titulo, orig_desc, orig_link)
        try:
            t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
            c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
            publicar_postagem(blogger_client, t_final, c_final)
        except Exception:
            publicar_postagem(blogger_client, "Destino de Elite", resultado_ia)
