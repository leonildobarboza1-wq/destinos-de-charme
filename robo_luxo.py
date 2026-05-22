import os
import urllib.request
import json
import xml.etree.ElementTree as ET
import requests
import time
from google import genai

# CONFIGURAÇÕES DA API DO GOOGLE (Projeto Portal Luxo Oficial)
API_KEY = os.environ.get("GEMINI_API_KEY")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")
CLIENT_ID = "249327057605-smqgro53c1cmrvf3gjdoqfp12s19l1o1.apps.googleusercontent.com"
BLOG_ID = "2362582861639823192"

# LISTA DE FONTES DE LUXO
FONTES_NEWS = [
    {"nome": "Robb Report (Viagens)", "url": "https://robbreport.com/travel/feed/"},
    {"nome": "Luxury Travel Advisor", "url": "https://www.luxurytraveladvisor.com/rss.xml"},
    {"nome": "Condé Nast Traveler (Luxo)", "url": "https://www.cntraveler.com/feed/luxury-travel/rss"},
    {"nome": "Elite Traveler", "url": "https://elitetraveler.com/feed"}
]

def renovar_access_token():
    print("🔄 Renovando passe de acesso usando o projeto Portal Luxo...")
    url = "https://oauth2.googleapis.com/token"
    # O Google aceita a renovação direta quando se usa o ecossistema do Playground
    payload = {
        "client_id": CLIENT_ID,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("🔑 Novo Access Token gerado com total autorização!")
            return response.json().get("access_token")
        else:
            print(f"⚠️ Alerta na autenticação própria. Status: {response.status_code}")
            print(f"Detalhes: {response.text}")
            return os.environ.get("BLOGGER_ACCESS_TOKEN")
    except Exception as e:
        print(f"❌ Erro ao renovar token: {e}")
    return os.environ.get("BLOGGER_ACCESS_TOKEN")

def buscar_noticia_com_contingencia():
    print("🌐 Iniciando busca de novidades no mercado de luxo mundial...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for fonte in FONTES_NEWS:
        print(f"📡 Tentando conectar com a fonte: {fonte['nome']}...")
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            item = root.find('.//item')
            
            if item is not None:
                titulo = item.find('title').text
                descricao = item.find('description').text if item.find('description') is not None else ""
                print(f"✅ Sucesso! Matéria capturada: '{titulo[:50]}...'")
                return titulo, descricao
        except Exception as e:
            print(f"⚠️ A fonte {fonte['nome']} falhou. Pulando...")
            continue
    return None, None

def usar_gemini_para_luxo(titulo_original, conteudo_original):
    print("🧠 Acionando a inteligência do Gemini para criação do artigo de luxo...")
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Você é um editor-chefe de uma revista digital de turismo de luxo e hotéis boutique chamada 'Destinos de Charme'.
    Sua missão é transformar a notícia abaixo em um artigo sofisticado, elegante e altamente aspiracional.

    Título Original: {titulo_original}
    Conteúdo Original: {conteudo_original}

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
    
    for tentativa in range(1, 4):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ Servidor do Gemini ocupado (Tentativa {tentativa}/3). Aguardando...")
            if tentativa < 3:
                time.sleep(6)
            else:
                raise e

def publicar_no_blogger_oficial(titulo, corpo_html, token_valido):
    print("--------------------------------------------------")
    print("🚀 Enviando artigo formatado para o seu Blogger...")
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
        print(f"📊 RESPOSTA DO BLOGGER (STATUS): {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"✨ SUCESSO REAL! Artigo publicado com sucesso: '{titulo}'")
        else:
            print(f"❌ TEXTO DO ERRO DO GOOGLE: {response.text}")
        print("--------------------------------------------------")
    except Exception as e:
        print(f"❌ Erro crítico ao conectar com o Blogger: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️ Chave GEMINI_API_KEY ausente.")
    else:
        token_atualizado = renovar_access_token()
        orig_titulo, orig_desc = buscar_noticia_com_contingencia()
        
        if orig_titulo:
            try:
                resultado_ia = usar_gemini_para_luxo(orig_titulo, orig_desc)
                titulo_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                corpo_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                publicar_no_blogger_oficial(titulo_final, corpo_final, token_atualizado)
            except Exception as e:
                print(f"Falha ao separar tags: {e}")
                if 'resultado_ia' in locals():
                    publicar_no_blogger_oficial("Escape de Elite Internacional", resultado_ia, token_atualizado)
        else:
            print("📭 Nenhuma notícia foi minerada.")
