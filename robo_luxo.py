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
    print("🌐 Minerando notícia, link e imagem de destaque...")
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
                link = item.find('link').text
                
                # Tenta capturar a imagem dentro das tags de mídia padrão do WordPress/RSS
                img_url = ""
                # 1ª Opção: Tag media:content do RSS
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    img_url = media_content.attrib['url']
                
                # 2ª Opção: Se não achar, procura na tag enclosure (comum em imagens)
                if not img_url:
                    enclosure = item.find('enclosure')
                    if enclosure is not None and 'url' in enclosure.attrib:
                        img_url = enclosure.attrib['url']
                
                return title, desc, link, img_url
        except Exception as e:
            print(f"⚠️ Alerta ao ler feed: {e}")
            continue
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, img_url):
    print("🧠 Gerando artigo adaptado editorialmente...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    # Prepara a tag de imagem se ela existir no RSS
    tag_imagem_html = f'<p style="text-align: center;"><img src="{img_url}" style="max-width: 100%; height: auto; border-radius: 8px;" /></p>' if img_url else ""
    
    prompt = f"""
    Você é o editor-chefe da revista de alto padrão 'Destinos de Charme'. 
    Sua tarefa é traduzir e transformar a notícia internacional abaixo em um artigo de luxo narrativo.

    Dados:
    - Título: {titulo}
    - Conteúdo: {conteudo}
    
    DIRETRIZES OBRIGATÓRIAS:
    1. Crie um título poético e refinado 100% em PORTUGUÊS.
    2. Texto envolvente sem usar clichês como "Destaque Internacional" ou "Análise sobre".
    3. Ao final da matéria em português, insira exatamente este bloco de atribuição de fonte:
       '<p><i>Fonte original: <a href="{link_original}">Clique aqui para ler a matéria completa no site oficial</a></i></p>'
    
    FORMATOS DE MARCAÇÃO PARA PARSER:
    [TITULO_DO_POST] O título em português gerado por você.
    [CORPO_DO_POST] Insira primeiro esta tag de imagem exatamente como ela está aqui: {tag_imagem_html}
    Logo após a imagem, insira o seu texto formatado em HTML (<p>, <strong>), seguido da fonte original, a linha divisória <hr> e por fim a 'ENGLISH VERSION' completa.
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def publicar_postagem(blogger_service, titulo, corpo_html):
    body = {"kind": "blogger#post", "title": titulo, "content": corpo_html}
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        request.execute()
        print("✨ SUCESSO ABSOLUTO: Post publicado com a imagem de destaque integrada!")
    except Exception as e:
        raise e

if __name__ == "__main__":
    blogger_client = inicializar_client_blogger()
    orig_titulo, orig_desc, orig_link, orig_img = buscar_noticia()
    
    if orig_titulo:
        resultado_ia = gerar_conteudo_ia(orig_titulo, orig_desc, orig_link, orig_img)
        try:
            t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
            c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
            publicar_postagem(blogger_client, t_final, c_final)
        except Exception:
            publicar_postagem(blogger_client, "Destino de Elite", resultado_ia)
