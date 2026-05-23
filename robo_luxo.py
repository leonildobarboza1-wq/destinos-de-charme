import os
import urllib.request
import json
import xml.etree.ElementTree as ET
from google import genai

# CONFIGURAÇÕES DIRETAS
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ACCESS_TOKEN = os.environ.get("BLOGGER_ACCESS_TOKEN")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")
BLOG_ID = "2362582861639823192"

FONTES_NEWS = [
    {"nome": "Robb Report", "url": "https://robbreport.com/travel/feed/"}
]

def renovar_token():
    print("🔄 Atualizando credenciais de acesso ao Blogger...")
    # Usamos o Client ID padrão do ecossistema para renovação direta
    url = "https://oauth2.googleapis.com/token"
    payload = f"refresh_token={REFRESH_TOKEN}&grant_type=refresh_token"
    req = urllib.request.Request(
        url, 
        data=payload.encode('utf-8'), 
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("access_token", ACCESS_TOKEN)
    except Exception:
        return ACCESS_TOKEN

def buscar_noticia():
    print("🌐 Minerando mercado de luxo internacional...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for fonte in FONTES_NEWS:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())
            item = root.find('.//item')
            if item is not None:
                return item.find('title').text, (item.find('description').text if item.find('description') is not None else "")
        except Exception:
            continue
    return None, None

def usar_gemini(titulo, conteudo):
    print("🧠 Gerando artigo de luxo via Gemini IA...")
    client = genai.Client(api_key=GEMINI_KEY)
    prompt = f"""
    Você é o editor-chefe da revista 'Destinos de Charme'. Transforme a matéria em um artigo de luxo altamente sofisticado.
    Título Original: {titulo}
    Conteúdo Original: {conteudo}
    Formatos obrigatórios:
    [TITULO_DO_POST] Seu título aqui
    [CORPO_DO_POST] Conteúdo em HTML limpo. Use <p>, <strong>. Inclua uma linha divisória elegante <hr> e coloque a versão traduzida para o inglês abaixo com o título 'ENGLISH VERSION'.
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def publicar_no_blogger(token, titulo, corpo_html):
    print("🚀 Injetando post diretamente no ecossistema Blogger...")
    url = f"https://blogger.googleapis.com/v3/blogs/{BLOG_ID}/posts"
    payload = {
        "kind": "blogger#post",
        "title": titulo,
        "content": corpo_html
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            if 'id' in res:
                print(f"✨ SUCESSO ABSOLUTO! Post publicado sob o ID: {res['id']}")
    except Exception as e:
        print(f"❌ Erro na publicação: {e}")

if __name__ == "__main__":
    if not GEMINI_KEY:
        print("⚠️ Chave do Gemini ausente.")
    else:
        orig_titulo, orig_desc = buscar_noticia()
        if orig_titulo:
            token_valido = renovar_token() if REFRESH_TOKEN else ACCESS_TOKEN
            try:
                resultado_ia = usar_gemini(orig_titulo, orig_desc)
                t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                publicar_no_blogger(token_valido, t_final, c_final)
            except Exception:
                publicar_no_blogger(token_valido, "Escape de Elite Internacional", resultado_ia)
