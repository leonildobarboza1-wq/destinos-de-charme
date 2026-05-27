import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ==========================================
# CONFIGURAÇÕES DE AMBIENTE & DIRETIVAS
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
BLOG_ID = "2362582861639823192"

FONTES_NEWS = [
    {"nome": "Robb Report", "url": "https://robbreport.com/travel/feed/"}
]

def inicializar_client_blogger():
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("ERRO CRÍTICO: A variável GOOGLE_CREDENTIALS_JSON não foi populada no ambiente.")
    try:
        creds_data = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = Credentials.from_authorized_user_info(
            creds_data, 
            scopes=['https://www.googleapis.com/auth/blogger']
        )
        return build('blogger', 'v3', credentials=creds)
    except Exception as e:
        print("❌ Falha crítica ao processar estruturas de credenciais JSON do Google.")
        raise e

def buscar_noticia():
    print("🌐 Minerando mercado de luxo internacional via RSS...")
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
                return title, desc
        except Exception as e:
            print(f"⚠️ Falha temporária ao ler a fonte {fonte['nome']}: {e}")
            continue
    return None, None

def gerar_conteudo_ia(titulo, conteudo):
    print("🧠 Invocando Gemini 2.5 Flash para refatoração editorial sofisticada...")
    if not GEMINI_KEY:
        raise ValueError("ERRO CRÍTICO: A variável GEMINI_API_KEY está ausente.")
        
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    Você é o editor-chefe da revista de alto padrão 'Destinos de Charme'. 
    Sua tarefa é traduzir e transformar a notícia internacional abaixo em um artigo de luxo narrativo, envolvente e extremamente sofisticado.

    Dados da Notícia (Traduza e reescreva totalmente):
    - Título da Fonte: {titulo}
    - Conteúdo de Apoio: {conteudo}
    
    DIRETRIZES OBRIGATÓRIAS DE REDAÇÃO:
    1. O título PRINCIPAL deve ser 100% em PORTUGUÊS. Crie um título inteiramente novo, refinado, poético e que evoque o mercado de luxo.
    2. NUNCA use o título original em inglês no topo e NUNCA comece com jargões como "Destaque Internacional" ou "Análise sobre".
    3. O texto deve começar direto na atmosfera do destino em português.
    
    FORMATOS OBRIGATÓRIOS DE MARCAÇÃO PARA PARSER:
    [TITULO_DO_POST] Escreva aqui o título criado por você, 100% em português e sem prefixos.
    [CORPO_DO_POST] Conteúdo estruturado estritamente em HTML limpo (<p>, <strong>). Inclua uma linha divisória elegante <hr> e, logo abaixo dela, insira a versão em inglês com o título 'ENGLISH VERSION'.
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def publicar_postagem(blogger_service, titulo, corpo_html):
    print("🚀 Protocolando requisição POST no gateway da API do Blogger...")
    body = {
        "kind": "blogger#post",
        "title": titulo,
        "content": corpo_html
    }
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        response = request.execute()
        if 'id' in response:
            print(f"✨ SUCESSO DE PRODUÇÃO: Artigo publicado com o ID {response['id']}")
        else:
            raise RuntimeError(f"API respondeu com payload anômalo: {response}")
    except Exception as e:
        print("❌ Erro fatal retornado pelo barramento do Google Blogger.")
        raise e

if __name__ == "__main__":
    blogger_client = inicializar_client_blogger()
    orig_titulo, orig_desc = buscar_noticia()
    
    if not orig_titulo:
        raise RuntimeError("Não foi possível coletar dados de nenhuma das fontes RSS especificadas.")
        
    resultado_ia = gerar_conteudo_ia(orig_titulo, orig_desc)
    
    # Processamento e extração cirúrgica das tags da IA
    try:
        t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
        c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
    except IndexError:
        print("⚠️ Formatação da IA divergiu. Aplicando limpeza inteligente para garantir título em português...")
        # Fallback inteligente: se o parser falhar, limpa as tags textuais e deixa a IA definir o conteúdo
        linhas = [lin.strip() for lin in resultado_ia.split('\n') if lin.strip()]
        t_final = linhas[0].replace("[TITULO_DO_POST]", "").replace("[CORPO_DO_POST]", "").strip()
        c_final = resultado_ia.replace("[TITULO_DO_POST]", "").replace("[CORPO_DO_POST]", "")

    # Publicação final controlada
    publicar_postagem(blogger_client, t_final, c_final)
