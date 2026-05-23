import os
import urllib.request
import json
import xml.etree.ElementTree as ET
import time
from google import genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# CONFIGURAÇÕES DE INFRAESTRUTURA
API_KEY = os.environ.get("GEMINI_API_KEY")
SERVICE_ACCOUNT_INFO = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
BLOG_ID = "2362582861639823192"

FONTES_NEWS = [
    {"nome": "Robb Report (Viagens)", "url": "https://robbreport.com/travel/feed/"},
    {"nome": "Luxury Travel Advisor", "url": "https://www.luxurytraveladvisor.com/rss.xml"},
    {"nome": "Condé Nast Traveler (Luxo)", "url": "https://www.cntraveler.com/feed/luxury-travel/rss"},
    {"nome": "Elite Traveler", "url": "https://elitetraveler.com/feed"}
]

def conectar_blogger():
    print("🔑 Autenticando via Conta de Serviço de nível corporativo...")
    try:
        info = json.loads(SERVICE_ACCOUNT_INFO)
        credenciais = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/blogger']
        )
        service = build('blogger', 'v3', credentials=credenciais)
        return service
    except Exception as e:
        print(f"❌ Falha crítica na conexão com o gateway do Google: {e}")
        return None

def buscar_noticia_com_contingencia():
    print("🌐 Minerando mercado de luxo internacional...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for fonte in FONTES_NEWS:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            item = root.find('.//item')
            if item is not None:
                return item.find('title').text, (item.find('description').text if item.find('description') is not None else "")
        except Exception:
            continue
    return None, None

def usar_gemini_para_luxo(titulo_original, conteudo_original):
    print("🧠 Gerando artigo de luxo via Gemini IA...")
    client = genai.Client(api_key=API_KEY)
    prompt = f"""
    Você é o editor-chefe da revista 'Destinos de Charme'. Transforme a matéria em um artigo de luxo altamente sofisticado.
    Título Original: {titulo_original}
    Conteúdo Original: {conteudo_original}
    Formatos obrigatórios:
    [TITULO_DO_POST] Seu título aqui
    [CORPO_DO_POST] Conteúdo em HTML limpo. Use <p>, <strong>. Inclua uma linha divisória elegante <hr> e coloque a versão traduzida para o inglês abaixo com o título 'ENGLISH VERSION'.
    """
    for tentativa in range(1, 4):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text
        except Exception as e:
            if tentativa == 3: raise e
            time.sleep(5)

def publicar_no_blogger(service, titulo, corpo_html):
    print("🚀 Injetando post diretamente no ecossistema Blogger...")
    try:
        body = {
            "kind": "blogger#post",
            "title": titulo,
            "content": corpo_html
        }
        request = service.posts().insert(blogId=BLOG_ID, body=body)
        response = request.execute()
        if 'id' in response:
            print(f"✨ SUCESSO ABSOLUTO! Post publicado sob o ID: {response['id']}")
        else:
            print(f"❌ Resposta inesperada do Google: {response}")
    except Exception as e:
        print(f"❌ Erro na execução do insert da API do Blogger: {e}")

if __name__ == "__main__":
    if not API_KEY or not SERVICE_ACCOUNT_INFO:
        print("⚠️ Variáveis de ambiente críticas ausentes (GEMINI_API_KEY ou GOOGLE_SERVICE_ACCOUNT_KEY).")
    else:
        blogger_service = conectar_blogger()
        orig_titulo, orig_desc = buscar_noticia_com_contingencia()
        
        if orig_titulo and blogger_service:
            try:
                resultado_ia = usar_gemini_para_luxo(orig_titulo, orig_desc)
                titulo_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                corpo_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                publicar_no_blogger(blogger_service, titulo_final, corpo_final)
            except Exception:
                publicar_no_blogger(blogger_service, "Escape de Elite Internacional", resultado_ia)
        else:
            print("📭 Pipeline abortada: Erro de dados ou autenticação.")
