import os
import smtplib
import urllib.request
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google import genai

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES DE ENVIO POR E-MAIL
# ---------------------------------------------------------------------------
# Cole aqui o e-mail secreto que você gerou no painel do seu Blogger:
EMAIL_SECRETO_BLOGGER = "COLE_AQUI_O_SEU_EMAIL_SECRETO@blogger.com"

# Configurações da sua conta de e-mail que vai enviar (o e-mail secreto do robô)
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
SENHA_REMETENTE = os.environ.get("SENHA_REMETENTE") # Senha de App do Google

API_KEY = os.environ.get("GEMINI_API_KEY")
FEED_URL = "https://www.relaischateaux.com/magazine/feed"

def buscar_ultima_noticia():
    print("Buscando novidades no mercado de luxo...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(FEED_URL, headers=headers)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        item = root.find('.//item')
        
        if item is not None:
            titulo = item.find('title').text
            descricao = item.find('description').text if item.find('description') is not None else ""
            return titulo, descricao
    except Exception as e:
        print(f"Erro ao buscar feed: {e}")
    return None, None

def usar_gemini_para_luxo(titulo_original, conteudo_original):
    print("Acionando a inteligência do Gemini para criação do artigo...")
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Você é um editor-chefe de uma revista digital de turismo de luxo e hotéis boutique chamada 'Destinos de Charme'.
    Sua missão é transformar a notícia abaixo em um artigo sofisticado, elegante e altamente aspiracional.

    Título Original: {titulo_original}
    Conteúdo Original: {conteúdo_original}

    Regras de Formatação:
    1. Crie um título maravilhoso em Português (estilo revista de elite).
    2. Escreva o corpo do texto em Português de forma envolvente, destacando o design, o conforto, a gastronomia e a exclusividade do lugar. Use parágrafos limpos.
    3. Adicione uma linha divisória elegante usando tags HTML (<hr style='border: 0; height: 1px; background: #ccc; margin: 20px 0;'>).
    4. Logo abaixo da divisória, crie uma seção chamada 'ENGLISH VERSION' e coloque o mesmo artigo traduzido com extrema elegância para o Inglês.
    5. O resultado final DEVE estar formatado em tags HTML limpas (como <p>, <strong>, etc). Não use markdown (```html).

    Retorne o texto estritamente no formato:
    [TITULO_DO_POST] Seu título sofisticado aqui
    [CORPO_DO_POST] Seu texto em HTML aqui juntando as duas versões (PT/EN).
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def enviar_email_blogger(titulo_final, corpo_html):
    print("Enviando artigo por e-mail para o Blogger...")
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = titulo_final
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_SECRETO_BLOGGER
    
    parte_html = MIMEText(corpo_html, 'html', 'utf-8')
    msg.attach(parte_html)
    
    try:
        # Conectando ao servidor de e-mail do Google (SMTP)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.sendmail(EMAIL_REMETENTE, EMAIL_SECRETO_BLOGGER, msg.as_string())
        server.quit()
        print("✨ Sucesso! E-mail enviado. O Blogger publicará o post em instantes!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

if __name__ == "__main__":
    if not API_KEY or not EMAIL_REMETENTE or not SENHA_REMETENTE:
        print("⚠️ Chaves ou credenciais de e-mail ausentes no GitHub Secrets.")
    elif EMAIL_SECRETO_BLOGGER == "COLE_AQUI_O_SEU_EMAIL_SECRETO@blogger.com":
        print("⚠️ Você esqueceu de colar o seu e-mail secreto do Blogger na linha 13 do código!")
    else:
        orig_titulo, orig_desc = buscar_ultima_noticia()
        if orig_titulo:
            resultado_ia = usar_gemini_para_luxo(orig_titulo, orig_desc)
            try:
                titulo_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
                corpo_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
                enviar_email_blogger(titulo_final, corpo_final)
            except Exception as e:
                print("Erro ao processar resposta da IA. Enviando texto completo.")
                enviar_email_blogger("Refúgio de Luxo Exclusivo", resultado_ia)
        else:
            print("Nenhuma novidade encontrada no momento.")
