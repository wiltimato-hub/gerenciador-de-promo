import streamlit as st
import google.generativeai as genai
import re
import requests
import urllib.parse 

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Gerador de Ofertas IA", page_icon="💰")

# Configuração da IA (A chave deve ser colocada nos Secrets do Streamlit ou .env)
# Para testes locais, você pode substituir por st.secrets["GEMINI_KEY"]
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("Erro: Chave da API do Gemini não configurada.")

# --- BANCO DE DADOS DE USUÁRIOS ---
USUARIOS = {
    "WilliamP": "1",
    "WesleyB": "festa456",
    "PedroA": "oferta789"
}

# --- FUNÇÕES DE LÓGICA ---

def criar_link_afiliado(url_original, loja):
    """
    Transforma o link comum em link de afiliado conforme a loja selecionada.
    """
    link = url_original.strip()
    if "Amazon" in loja:
        tag = "wiltimato-20" # Substitua pelo seu ID
        return f"{link}&tag={tag}" if "?" in link else f"{link}?tag={tag}"
    
    elif "Magalu" in loja:
        # Exemplo de link de divulgador Magalu
        id_magalu = "seu_user_magalu"
        return f"https://www.magazinevoce.com.br/magazine{id_magalu}/p/{link.split('/')[-1]}"
    
    elif "Shopee" in loja:
        # Links da Shopee geralmente exigem a API para converter, 
        # aqui mantemos o original ou adicionamos um parâmetro simples
        return f"{link}?smtt=0.0.9"
        
    return link

def gerar_texto_ia(url, loja, texto_manual=""):
    """
    Solicita à IA a criação de uma copy de vendas.
    """
    prompt = f"""
    Crie um post de oferta elegate:
    1. Nome do produto em NEGRITO
    2. Uma linha com o beneficio principal
    3. Preço em destaque com emoji de dinheiro
    4. link de compra claro
    Evite parágrafos longos. Use listas (.)
    
    
    Produto/Link: {url}
    Loja: {loja}
    Informações Adicionais: {texto_manual}
    
    REQUISITOS:
    1. Use emojis para chamar atenção.
    2. Use gatilhos de urgência (ex: 'Menor preço do ano', 'Corre que acaba').
    3. Coloque o preço em destaque.
    4. Deixe o local [LINK] para eu inserir depois.
    5. Não seja formal demais.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return None

# --- INTERFACE DO SITE ---

def main():
    # Inicialização do estado de login
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        # TELA DE LOGIN
        st.title("🔐 Acesso Privado")
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if user in USUARIOS and USUARIOS[user] == senha:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    else:
        # TELA PRINCIPAL
        st.sidebar.title(f"Bem-vindo!")
        if st.sidebar.button("Sair"):
            st.session_state.logado = False
            st.rerun()

        st.title("💰 Gerador de Ofertas Automático")
        st.info("Preencha os dados abaixo para postar nos grupos.")

        # Inputs
        url_input = st.text_input("Cole o link do produto aqui:", placeholder="https://www.amazon.com.br/...")
        
        col1, col2 = st.columns(2)
        with col1:
            loja_selecionada = st.selectbox("Selecione a Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
        with col2:
            usar_ia = st.toggle("Usar Inteligência Artificial", value=True)

        info_adicional = st.text_area("Informações extras (Preço, Nome do produto ou detalhes):", 
                                     placeholder="Ex: Galaxy S23 por R$ 2.999")

        # Botão Processar
        # --- NOVO CAMPO PARA IMAGEM ---
        url_imagem = st.text_input("URL da Imagem do Produto (Clique com o botão direito na imagem da loja e 'Copiar endereço da imagem'):")

        # Área de Edição e Envio
        if "texto_final" in st.session_state:
            st.divider()
            st.subheader("📝 Resultado Final")
            post_final = st.text_area("Texto formatado:", value=st.session_state.texto_final, height=250)
            
            col_post1, col_post2 = st.columns(2)
            with col_post1:
                if st.button("📤 Postar no Telegram"):
                    try:
                        token = st.secrets["TELEGRAM_TOKEN"]
                        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
                        
                        if url_imagem:
                            # Envia Foto com Legenda (Aparência Profissional)
                            url_api = f"https://api.telegram.org/bot{token}/sendPhoto"
                            payload = {
                                "chat_id": chat_id, 
                                "photo": url_imagem,
                                "caption": post_final, # O texto vira a legenda da foto
                                "parse_mode": "HTML"    # Permite negrito e links
                            }
                        else:
                            # Envia apenas texto se não houver imagem
                            url_api = f"https://api.telegram.org/bot{token}/sendMessage"
                            payload = {"chat_id": chat_id, "text": post_final, "parse_mode": "HTML"}
                        
                        response = requests.post(url_api, data=payload)
                        if response.status_code == 200:
                            st.success("✅ Oferta com foto enviada!")
                        else:
                            st.error(f"Erro: {response.json().get('description')}")
                    except Exception as e:
                        st.error("Erro técnico nos Secrets ou na URL da imagem.")
            
            with col_post2:
                if st.button("💬 Abrir no WhatsApp"):
                    # No WhatsApp, a melhor forma via web é gerar um link "api.whatsapp"
                    # Isso abre o seu WhatsApp com o texto pronto para você escolher o grupo e enviar
                    texto_url = urllib.parse.quote(post_final)
                    link_wp = f"https://api.whatsapp.com/send?text={texto_url}"
                    st.link_button("Confirmar Envio no WhatsApp", link_wp)
if __name__ == "__main__":
    main()