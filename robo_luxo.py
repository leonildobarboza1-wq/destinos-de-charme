import os
import json
import random
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ==========================================
# CONFIGURAÇÕES DE AMBIENTE
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
BLOG_ID = "2362582861639823192"

# Substitua pelo seu número real com DDD e o código do país (ex: 55 para Brasil)
SEU_NUMERO_WHATSAPP = "5511999999999" 

FONTES_NEWS = [
    {"nome": "Robb Report - Travel", "url": "https://robbreport.com/travel/feed/"},
    {"nome": "Robb Report - Gear", "url": "https://robbreport.com/motors/aviation/feed/"},
    {"nome": "Robb Report - Style", "url": "https://robbreport.com/style/fashion/feed/"}
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

def listar_titulos_publicados_24h(blogger_service):
    titulos_recentes = set()
    try:
        time_threshold = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        request = blogger_service.posts().list(blogId=BLOG_ID, startDate=time_threshold, maxResults=10)
        response = request.execute()
        if 'items' in response:
            for post in response['items']:
                titulos_recentes.add(post['title'].strip().lower())
    except Exception as e:
        print(f"⚠️ Histórico do Blogger inacessível: {e}")
    return titulos_recentes

def buscar_noticia_aleatoria(titulos_bloqueados):
    print("🎲 Iniciando mineração randômica anti-duplicação...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    fontes_aleatorias = list(FONTES_NEWS)
    random.shuffle(fontes_aleatorias)
    
    for fonte in fontes_aleatorias:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())
            
            items = root.findall('.//item')
            if not items:
                continue
                
            random.shuffle(items)
            for item in items:
                title = item.find('title').text
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text
                
                if title.strip().lower() in titulos_bloqueados:
                    continue
                
                img_url = ""
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    img_url = media_content.attrib['url']
                if not img_url:
                    enclosure = item.find('enclosure')
                    if enclosure is not None and 'url' in enclosure.attrib:
                        img_url = enclosure.attrib['url']
                
                print(f"🎯 Selecionada: {title}")
                return title, desc, link, img_url
        except Exception:
            continue
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, img_url):
    print("🧠 Gerando artigo com Sistema de Discussão Pública (Utterances)...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    # Substitua 'SEU_USUARIO/NOME_DO_REPOSITORIO' pelo seu caminho real no GitHub
    # Exemplo: 'lucas/meu-blog-luxo'
    REPO_GITHUB = "SEU_USUARIO/NOME_DO_REPOSITORIO" 
    
    # Bloco de Código que cria a área de discussão pública
    tag_discussao_html = f"""
    <br><hr><br>
    <div style="background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #eee;">
        <h3 style="font-family: 'Georgia', serif; color: #111; text-align: center;">Área de Discussão</h3>
        <script src="https://utteranc.es/client.js"
                repo="{REPO_GITHUB}"
                issue-term="title"
                label="comentário"
                theme="github-light"
                crossorigin="anonymous"
                async>
        </script>
    </div>
    """
    
    tag_imagem_html = f"""
    <p style="text-align: center;">
        <img src="{img_url}" style="max-width: 100%; height: auto; border-radius: 8px;" /><br>
        <span style="font-size: 11px; color: #888888;">Imagem: Reprodução / Fonte Original</span>
    </p>
    """ if img_url else ""
    
    prompt = f"""
    Você é o editor-chefe da revista de alto padrão 'Destinos de Charme'. 
    Transforme a notícia abaixo em um artigo de luxo sofisticado.

    Dados:
    - Título: {titulo}
    - Conteúdo: {conteudo}
    
    FORMATOS DE MARCAÇÃO:
    [TITULO_DO_POST] O título em português.
    [CORPO_DO_POST] {tag_imagem_html}
    Texto HTML, fonte original com target="_blank", <hr>, 'ENGLISH VERSION' e, ao final de tudo, este código: {tag_discussao_html}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text
