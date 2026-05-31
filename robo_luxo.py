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

# =========================================
# CONFIGURAÇÕES DE AMBIENTE
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
BLOG_ID = "2362582861639823192"

# Correção aplicada: Lista unificada, sem duplicações e separada por vírgulas corretamente
FONTES_NEWS = [
    # Robb Report (Motores e Estilo)
    {"nome": "Robb Report - Gear", "url": "https://robbreport.com/motors/aviation/feed/"},
    {"nome": "Robb Report - Style", "url": "https://robbreport.com/style/fashion/feed/"},
    {"nome": "Robb Report - Travel", "url": "https://robbreport.com/travel/feed/"},

    # Condé Nast Traveler (Viagens e Destinos Incríveis)
    {"nome": "Condé Nast Traveler - Destinos", "url": "https://www.cntraveler.com/feed/travel-tips-and-trends/rss"},
    {"nome": "Condé Nast Traveler - Hotéis", "url": "https://www.cntraveler.com/feed/hotels/rss"},
    
    # Architectural Digest (Mansões, Decoração e Arquitetura)
    {"nome": "Architectural Digest - Casas", "url": "https://www.architecturaldigest.com/feed/celebrity-style/rss"},
    
    # Elite Traveler (O Luxo Puro: Iates, Jatos e Relógios)
    {"nome": "Elite Traveler - Lifestyle", "url": "https://elitetraveler.com/feed"}
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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    fontes_aleatorias = list(FONTES_NEWS)
    random.shuffle(fontes_aleatorias)
    
    sucesso_leitura = False
    
    for fonte in fontes_aleatorias:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                sucesso_leitura = True
            
            items = root.findall('.//item')
            if not items:
                continue
                
            random.shuffle(items)
            for item in items:
                title = item.find('title').text
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text
                
                if not title:
                    continue
                    
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
            print(f"❌ ERRO CRÍTICO na leitura da fonte '{fonte['nome']}': {e}")
            continue
            
    if not sucesso_leitura:
        print("🚨 ALERTA: O script não conseguiu ler NENHUM dos feeds configurados.")
        
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, img_url):
    print("🧠 Gerando artigo com Sistema de Comentários Universal (Disqus)...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    post_id_limpo = urllib.parse.quote_plus(titulo[:30])
    
    tag_discussao_html = f"""
    <br><hr><br>
    <div style="background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #eee; max-width: 700px; margin: 0 auto;">
        <h3 style="font-family: 'Georgia', serif; color: #111; text-align: center; font-weight: normal; margin-bottom: 20px;">Comentários e Discussão</h3>
        
        <div id="disqus_thread"></div>
        <script>
            var disqus_config = function () {{
                this.page.url = window.location.href;
                this.page.identifier = '{post_id_limpo}';
            }};
            (function() {{
                var d = document, s = d.createElement('script');
                s.src = 'https://destinos-de-charme.disqus.com/embed.js';
                s.setAttribute('data-timestamp', +new Date());
                (d.head || d.body).appendChild(s);
            }})();
        </script>
        <noscript>Por favor, ative o JavaScript para visualizar os comentários.</noscript>
    </div>
    """
    
    tag_imagem_html = f"""
    <p style="text-align: center;">
        <a href="{link_original}" target="_blank" rel="noopener noreferrer" style="display: inline-block; text-decoration: none;">
            <img src="{img_url}" style="max-width: 100%; height: auto; border-radius: 8px; transition: transform 0.3s ease;" onmouseover="this.style.transform='scale(1.01)'" onmouseout="this.style.transform='scale(1)'" /><br>
            <span style="font-size: 11px; color: #888888; display: block; margin-top: 5px;">Imagem: Reprodução / Clique para ver a fonte original</span>
        </a>
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
    2. Ao final da matéria em português, insira a attribution de fonte com target="_blank".
    
    FORMATOS DE MARCAÇÃO PARA PARSER:
    [TITULO_DO_POST] O título em português gerado por você.
    [CORPO_DO_POST] {tag_imagem_html}
    Insira o seu text formatado em HTML (<p>, <strong>), seguido da fonte original com abertura em nova aba, a linha divisória <hr> e a 'ENGLISH VERSION' completa. No final absoluto de TUDO, anexe este bloco de código exato: {tag_discussao_html}
    """
    
    for tentativa in range(1, 4):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text
        except Exception as e:
            if tentativa == 3: raise e
            time.sleep(10)

def publicar_postagem(blogger_service, titulo, corpo_html):
    body = {"kind": "blogger#post", "title": titulo, "content": corpo_html}
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        request.execute()
        print("✨ SUCESSO: Post publicado com o Disqus ativo!")
    except Exception as e:
        print(f"❌ Erro ao inserir post no Blogger: {e}")
        raise e

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
        print("🛑 ATENÇÃO: Varredura completa. Nenhuma notícia inédita encontrada em NENHUMA das fontes nas últimas 24h.")
        # Isso força o erro no GitHub Actions se varrer todos os sites e não postar nada
        import sys
        sys.exit("Erro: O site passou 24 horas sem novas postagens automáticas.")
