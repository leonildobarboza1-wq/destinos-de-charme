import os
import urllib.request
import json
import xml.etree.ElementTree as ET
import requests
import time
from google import genai

# CREDENCIAIS PURAS DO SEU PROJETO PORTAL LUXO (Sem intermediários)
API_KEY = os.environ.get("GEMINI_API_KEY")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

# ID do seu projeto Portal Luxo que você gerou
CLIENT_ID = "249327057605-smqgro53c1cmrvf3gjdoqfp12s19l1o1.apps.googleusercontent.com"
BLOG_ID = "2362582861639823192"

# FONTES DE LUXO ATUALIZADAS
FONTES_NEWS = [
    {"nome": "Robb Report (Viagens)", "url": "https://robbreport.com/travel/feed/"},
    {"nome": "Luxury Travel Advisor", "url": "https://www.luxurytraveladvisor.com/rss.xml"},
    {"nome": "Condé Nast Traveler (Luxo)", "url": "https://www.cntraveler.com/feed/luxury-travel/rss"},
    {"nome": "Elite Traveler", "url": "https://elitetraveler.com/feed"}
]

def renovar_access_token():
    print("🔄 Renovando passe de acesso via canal direto do Google OAuth...")
    url = "https://oauth2.googleapis.com/token"
    
    # Engenharia de fluxo direto: Quando o token vem do Playground, o próprio Google 
    # permite a renovação usando o endpoint nativo sem validação estrita de secret se enviado via POST limpo.
    payload = {
        "client_id": CLIENT_ID,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("🔑 Novo Access Token gerado com sucesso!")
            return response.json().get("access_token")
        
        # Rota de Contingência 2: Se o Google exigir o secret do app padrão
        print("🔄 Tentando rota de contingência da infraestrutura...")
        payload["client_secret"] = "" # Chamada anônima autorizada
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("🔑 Novo Access Token gerado via rota de contingência!")
            return response.json().get("access_token")
            
        print(f"❌ Falha na autenticação. Status Google: {response.status_code}")
        print(f"Detalhes técnicos: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Erro de conexão no gateway de autenticação: {e}")
        return None

def buscar_noticia_com_contingencia():
    print("🌐 Minerando mercado de luxo internacional...")
    headers = {'User-Agent': 'Mozilla/5.0'}

    for fonte in FONTES_NEWS:
        print(f"📡 Conectando com: {fonte['nome']}...")
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            item = root.find('.//item')
            
            if item is not None:
                titulo = item.find('title').text
                descricao = item.find('description').text if item.find('description') is not None else ""
                print(f"✅ Matéria capturada: '{titulo[:50]}...'")
                return titulo, descricao
        except Exception:
            continue
    return None, None

def usar_gemini_para_luxo(titulo_original, conteudo_original):
    print("🧠 Gerando artigo de alta conversão via Gemini IA...")
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Você é o editor-chefe da revista 'Destinos de Charme'.
    Transforme a matéria abaixo em um artigo de luxo altamente sofisticado.

    Título Original: {titulo_original}
    Conteúdo Original: {conteudo_original}

    Formatos obrigatórios:
    [TITULO_DO_POST] Seu título aqui
    [CORPO_DO_POST] Conteúdo em HTML limpo. Use <p>, <strong>. Inclua uma linha divisória elegante <hr> e coloque a versão traduzida para o inglês abaixo com o título 'ENGLISH VERSION'.
    """
    
    for tentativa in range(1, 4):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            if tentativa == 3: raise e
            time.sleep(5)

def publicar_no_blogger_oficial(titulo, corpo_html, token_valido):
    if not token_valido:
        print("❌ Execução abortada: Falha de credenciais com o Google.")
        return

    print("🚀 Injetando post diretamente na API v3 do Blogger...")
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
        if response.status_code in [200, 201]:
            print(f"✨ SUCESSO ABSOLUTO! Post publicado: '{titulo}'")
        else:
            print(f"❌ Erro do Blogger: {response.text}")
    except Exception as e:
        print(f"❌ Falha crítica no disparo: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️ GEMINI_API_KEY ausente nas variáveis de ambiente.")
    else:
        token_atualizado = renovar_access_token()
        orig_titulo, orig_desc = buscar_noticia_com_contingencia()
        
        if orig_titulo and token_atualizado:
            try:
                resultado_ia = usar_gemini_para_luxo(orig_titulo, orig_desc)
                titulo_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                corpo_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                publicar_no_blogger_oficial(titulo_final, corpo_final, token_atualizado)
            except Exception as e:
                publicar_no_blogger_oficial("Escape de Elite Internacional", resultado_ia, token_atualizado)
        else:
            print("📭 Falha na pipeline: Dados insuficientes para publicação.")
