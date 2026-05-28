import os
import json
import time
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
                    print(f"⏭️ Pulando repetida: {title}")
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
        except Exception as e:
            print(f"⚠️ Erro na leitura do feed: {e}")
            continue
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, img_url):
    print("🧠 Gerando artigo com Área de Mensagens nativa e exclusiva...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    # 🔴 COLOQUE O SEU E-MAIL REAL AQUI PARA RECEBER OS COMENTÁRIOS
    EMAIL_ADMINISTRADOR = "leonildobarboza2@gmail.com" 
    
    # O SEU CÓDIGO DO FORMULÁRIO ENVELOPADO EM DESIGN LUXO FICA AQUI:
    tag_interatividade_html = f"""
    <br><hr><br>
    <div style="background-color: #fafafa; padding: 30px; border-radius: 4px; border: 1px solid #e5e5e5; font-family: 'Georgia', serif; max-width: 600px; margin: 0 auto;">
        <h3 style="text-align: center; color: #111; font-weight: normal; letter-spacing: 1px; margin-bottom: 5px;">Deixe sua Mensagem</h3>
        <p style="text-align: center; font-size: 13px; color: #666; font-style: italic; margin-bottom: 25px;">Compartilhe suas impressões ou sugestões com nossa redação.</p>
        
        <form action="https://formsubmit.co/{EMAIL_ADMINISTRADOR}" method="POST" style="display: flex; flex-direction: column; gap: 15px;">
            <input type="hidden" name="_subject" value="Novo Feedback: {titulo.replace("'", "")}">
            <input type="hidden" name="_captcha" value="false">

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <label style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #333;">Seu Nome</label>
                <input type="text" name="name" required style="padding: 10px; border: 1px solid #ccc; background: #fff; font-size: 14px;">
            </div>

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <label style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #333;">Seu E-mail</label>
                <input type="email" name="email" required style="padding: 10px; border: 1px solid #ccc; background: #fff; font-size: 14px;">
            </div>

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <label style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #333;">Mensagem</label>
                <textarea name="mensagem" rows="5" required style="padding: 10px; border: 1px solid #ccc; background: #fff; font-size: 14px; resize: vertical;"></textarea>
            </div>

            <button type="submit" style="background-color: #111; color: #fff; border: none; padding: 12px; text-transform: uppercase; letter-spacing: 2px; font-size: 13px; cursor: pointer; margin-top: 10px;">
                Enviar Comentário
            </button>
        </form>
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
    Sua tarefa é traduzir e transformar a notícia internacional abaixo em um artigo de luxo narrativo.

    Dados:
    - Título: {titulo}
    - Conteúdo: {conteudo}
    
    DIRETRIZES OBRIGATÓRIAS:
    1. Crie um título poético e refinado 100% em PORTUGUÊS.
    2. Ao final da matéria em português, insira a atribuição de fonte com target="_blank".
    
    FORMATOS DE MARCAÇÃO PARA PARSER:
    [TITULO_DO_POST] O título em português gerado por você.
    [CORPO_DO_POST] {tag_imagem_html}
    Insira o seu texto formatado em HTML (<p>, <strong>), seguido da fonte original com abertura em nova aba, a linha divisória <hr> e a 'ENGLISH VERSION' completa. No final absoluto de TUDO, anexe este bloco de código: {tag_interatividade_html}
    """
    
    for tentativa in range(1, 4):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text
        except Exception as e:
            if tentativa == 3: raise e
            time.sleep(10)

if __name__ == "__main__":
    blogger_client = inicializar_client_blogger()
    titulos_bloqueados = listar_titulos_publicados_24h(blogger_client)
    orig_titulo, orig_desc, orig_link, orig_img = buscar_noticia_aleatoria(titulos_bloqueados)
    
    if orig_titulo:
        resultado_ia = gerar_conteudo_ia(orig_titulo, orig_desc, orig_link, orig_img)
        try:
            t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
            c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
            publicar_postagem(blogger_client, t_final, c_final)
        except Exception as e:
            print(f"⚠️ Falha no parser, postando bruto: {e}")
            publicar_postagem(blogger_client, "Destino de Elite", resultado_ia)
    else:
        print("🛑 Nenhuma notícia inédita encontrada nos feeds nas últimas 24 horas.")
