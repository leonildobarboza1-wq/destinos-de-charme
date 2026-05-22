import os
import urllib.request
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES DE ACESSO (O GitHub vai preencher isso em segredo depois)
# ---------------------------------------------------------------------------
BLOG_ID = "2362582861639823192"
API_KEY = os.environ.get("GEMINI_API_KEY")
BLOGGER_TOKEN = os.environ.get("BLOGGER_ACCESS_TOKEN")

# Fontes de turismo de luxo (Feed RSS público da Relais & Châteaux)
FEED_URL = "https://www.relaischateaux.com/magazine/feed"

def buscar_ultima_noticia():
    print("Buscando novidades no mercado de luxo...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(FEED_URL, headers=headers)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        item = root.find('.//item') # Pega a matéria mais recente lançada
        
        if item is not None:
            titulo = item.find('title').text
            link = item.find('link').text
            descricao = item.find('description').text if item.find('description') is not None else ""
            return titulo, link, descricao
    except Exception as e:
        print(f"Erro ao buscar feed: {e}")
    return None, None, None

def usar_gemini_para_luxo(titulo_original, conteudo_original):
    print("Acionando a inteligência do Gemini para tradução e refinamento...")
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Você é um editor-chefe de uma revista digital de turismo de luxo e hotéis boutique chamada 'Destinos de Charme'.
    Sua missão é transformar a notícia abaixo em um artigo sofisticado, elegante e altamente aspiracional.

    Título Original: {titulo_original}
    Conteúdo Original: {conteúdo_original}

    Regras de Formatação:
    1. Crie um título maravilhoso em Português (estilo revista de elite).
    2. Escreva o corpo do texto em Português de forma envolvente, destacando o design, o conforto, a gastronomia e a exclusividade do lugar. Use parágrafos limpos.
    3. Adicione uma linha divisória elegante usando tags HTML.
    4. Logo abaixo da divisória, crie uma seção chamada 'ENGLISH VERSION' e coloque o mesmo artigo traduzido com extrema elegância para o Inglês.
    5. O resultado final DEVE estar formatado em tags HTML limpas (como <p>, <strong>, etc) para o Blogger aceitar direto. Não use markdown (```html).

    Retorne o texto estritamente no formato:
    [TITULO_DO_POST] Seu título sofisticado aqui
    [CORPO_DO_POST] Seu texto em HTML aqui juntando as duas versões (PT/EN).
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def publicar_no_blogger(titulo_final, corpo_html):
    print("Postando de forma automatizada no Blogger...")
    url = f"[https://www.googleapis.com/blogger/v3/blogs/](https://www.googleapis.com/blogger/v3/blogs/){BLOG_ID}/posts/"
    
    # Montando a estrutura que a API do Google exige
    import json
    dados_post = {
        "kind": "blogger#post",
        "blog": {"id": BLOG_ID},
        "title": titulo_final,
        "content": corpo_html
    }
    
    data = json.dumps(dados_post).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data,
        headers={
            'Authorization': f'Bearer {BLOGGER_TOKEN}',
            'Content-Type': 'application/json'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 200 or res.status == 201:
                print("✨ Sucesso! O Destinos de Charme tem um novo post exclusivo global!")
    except Exception as e:
        print(f"Erro ao publicar no Blogger: {e}")

# Execução principal do Robô
if __name__ == "__main__":
    if not API_KEY or not BLOGGER_TOKEN:
        print("⚠️ Chaves de acesso ausentes nas variáveis de ambiente.")
    else:
        orig_titulo, orig_link, orig_desc = buscar_ultima_noticia()
        if orig_titulo:
            resultado_ia = usar_gemini_para_luxo(orig_titulo, orig_desc)
            
            # Separando o título e o corpo gerados pelo Gemini
            try:
                titulo_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                corpo_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                
                # Publicando de verdade
                publicar_no_blogger(titulo_final, corpo_final)
            except Exception as e:
                print("Erro ao processar resposta da IA. Tentando publicar texto completo.")
                publicar_no_blogger("Refúgio de Charme Exclusivo", resultado_ia)
        else:
            print("Nenhuma novidade encontrada no momento.")
