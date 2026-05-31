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

def gerar_conteudo_ia(titulo, conteudo, link_original, imagem_url):
    """
    Usa o Gemini para transformar a notícia de turismo em um post de blog de luxo,
    já injetando as duas opções da Amazon no final.
    """
    client = genai.Client()
    
    prompt = f"""
    Você é o editor-chefe da revista digital de alto padrão 'Destinos de Charme'. 
    Sua tarefa é pegar os dados da notícia internacional abaixo e transformá-la em um artigo de luxo narrativo, envolvente e sofisticado em português.

    Dados da Notícia:
    - Título Original: {titulo}
    - Conteúdo original: {conteudo}
    
    DIRETRIZES OBRIGATÓRIAS DE FORMATAÇÃO:
    1. O retorno deve ter EXATAMENTE esta estrutura de tags para o parser funcionar:
       [TITULO_DO_POST]
       Coloque aqui um título poético, refinado e chamativo em português (Sem aspas e sem markdown).
       
       [CORPO_DO_POST]
       Escreva o artigo em português com parágrafos bem estruturados e elegantes. Use subtítulos em markdown (###) se achar necessário.
       
    2. No final do texto do [CORPO_DO_POST], pule uma linha e adicione as seguintes seções de monetização e créditos exatamente em HTML:
       
       <hr>
       <p><i>Fonte original em inglês: <a href="{link_original}" target="_blank" rel="noopener">Clique aqui</a></i></p>
       
       <br>
       <h3>🧳 Essenciais para a Sua Próxima Viagem de Elite</h3>
       
       <p><b>Tecnologia de Ponta:</b> Viaje conectado e registre cada momento com qualidade cinematográfica. <a href="https://www.amazon.com.br/Apple-iPhone-17-Pro-Max/dp/B0FQHGM3B1?pd_rd_w=cODwv&content-id=amzn1.sym.49c30b43-6327-4205-bff7-940d62245e41&pf_rd_p=49c30b43-6327-4205-bff7-940d62245e41&pf_rd_r=3KMK1GRVN60FNDRZ9HPR&pd_rd_wg=MswXb&pd_rd_r=0164f6b9-946a-456f-b5f2-baf11d396763&pd_rd_i=B0FQHGM3B1&th=1&linkCode=ll2&tag=destinosdecha-20&linkId=33320d053a0d9437ccec1d70552e1b05&ref_=as_li_ss_tl" target="_blank" rel="noopener"><b>Adquira o novo iPhone 17 Pro Max na Amazon com frete rápido</b></a>.</p>
       
       <p><b>Malas & Bagagem de Elite:</b> Viaje com máxima elegância, segurança e o conforto de acessórios premium. <a href="https://www.amazon.com.br/s?k=malas+de+viagem+samsonite&tag=destinosdecha-20" target="_blank" rel="noopener"><b>Confira as melhores malas de bordo e organizadores sofisticados na Amazon</b></a>.</p>
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        texto_gerado = response.text
        if imagem_url and "[CORPO_DO_POST]" in texto_gerado:
            tag_imagem = f'<img src="{imagem_url}" style="max-width:100%; height:auto; margin-bottom:20px; border-radius:8px;"><br>\n'
            texto_gerado = texto_gerado.replace("[CORPO_DO_POST]", f"[CORPO_DO_POST]\n{tag_imagem}")
            
        return texto_gerado
    except Exception as e:
        print(f"❌ Erro na API do Gemini: {e}")
        return f"[TITULO_DO_POST]\nDestino de Elite\n\n[CORPO_DO_POST]\nErro ao gerar conteúdo. Veja a fonte original: {link_original}"

def publicar_postagem(client, titulo, conteudo):
    """
    Publica o artigo final gerado pela IA diretamente no Blogger.
    """
    try:
        if not BLOG_ID:
            print("❌ Erro: BLOG_ID não configurado.")
            return

        post_body = {
            "kind": "blogger#post",
            "title": titulo,
            "content": conteudo
        }
        
        request = client.posts().insert(blogId=BLOG_ID, body=post_body)
        response = request.execute()
        print(f"🎉 Postagem publicada com sucesso! URL: {response.get('url')}")
    except Exception as e:
        print(f"❌ Erro ao publicar no Blogger: {e}")

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
        import sys
        sys.exit("Erro: O site passou 24 horas sem novas postagens automáticas.")
