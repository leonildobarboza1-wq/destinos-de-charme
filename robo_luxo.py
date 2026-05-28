def gerar_conteudo_ia(titulo, conteudo, link_original, img_url):
    print("🧠 Gerando artigo com Área de Mensagens Protegida e Anônima...")
    client = genai.Client(api_key=GEMINI_KEY)
    
    # 🔐 PEGUE SEU TOKEN GRATUITO EM https://formsubmit.co/
    # Cole o código gerado entre as aspas abaixo (substituindo o exemplo)
    TOKEN_SEGURO = "7a8b9c2d3e4f5g6h7i8j9k0l1m2n3o4p" 
    
    tag_interatividade_html = f"""
    <br><hr><br>
    <div style="background-color: #fafafa; padding: 30px; border-radius: 4px; border: 1px solid #e5e5e5; font-family: 'Georgia', serif; max-width: 600px; margin: 0 auto;">
        <h3 style="text-align: center; color: #111; font-weight: normal; letter-spacing: 1px; margin-bottom: 5px;">Deixe sua Mensagem</h3>
        <p style="text-align: center; font-size: 13px; color: #666; font-style: italic; margin-bottom: 25px;">Compartilhe suas impressões ou sugestões com nossa redação.</p>
        
        <form action="https://formsubmit.co/{TOKEN_SEGURO}" method="POST" style="display: flex; flex-direction: column; gap: 15px;">
            <input type="hidden" name="_subject" value="Novo Feedback: {titulo.replace("'", "")}">
            <input type="hidden" name="_captcha" value="false">

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <label style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #333;">Seu Nome</label>
                <input type="text" name="name" required style="padding: 10px; border: 1px solid #ccc; background: #fff; font-size: 14px;">
            </div>

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <label style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #333;">Seu E-mail</label>
                <input type="email" name="email" required style="padding: 10px; border: 1px solid #ccc; background: #fff; font-size: 14px;">
            </div>

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <label style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #333;">Mensagem</label>
                <textarea name="mensagem" rows="5" required style="padding: 10px; border: 1px solid #ccc; background: #fff; font-size: 14px; resize: vertical;"></textarea>
            </div>

            <button type="submit" style="background-color: #111; color: #fff; border: none; padding: 12px; text-transform: uppercase; letter-spacing: 2px; font-size: 13px; cursor: pointer; margin-top: 10px;">
                Enviar Comentário
            </button>
        </form>
    </div>
    """
    
    tag_imagem_html = f"""
    <p style="text-align: center;">
        <img src="{img_url}" style="max-width: 100%; height: auto; border-radius: 8px;" /><br>
        <span style="font-size: 11px; color: #888888;">Imagem: Reprodução / Fonte Original</span>
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
    2. Ao final da matéria em português, insira a atribuição de fonte com target="_blank".
    
    FORMATOS DE MARCAÇÃO PARA PARSER:
    [TITULO_DO_POST] O título em português gerado por você.
    [CORPO_DO_POST] {tag_imagem_html}
    Insira o seu texto formatado em HTML (<p>, <strong>), seguido da fonte original com abertura em nova aba, a linha divisória <hr> e a 'ENGLISH VERSION' completa. No final absoluto de TUDO, anexe este bloco de código: {tag_interatividade_html}
    """
    
    for tentativa in range(1, 4):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text
        except Exception as e:
            if tentativa == 3: raise e
            time.sleep(10)
