import streamlit as st
import google.generativeai as genai
import re

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
    "admin": "senha123",
    "amigo1": "festa456",
    "amigo2": "oferta789"
}

# --- FUNÇÕES DE LÓGICA ---

def criar_link_afiliado(url_original, loja):
    """
    Transforma o link comum em link de afiliado conforme a loja selecionada.
    """
    link = url_original.strip()
    if "Amazon" in loja:
        tag = "seu_id_amazon-20" # Substitua pelo seu ID
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
    Você é um copywriter especialista em vendas rápidas para grupos de WhatsApp e Telegram.
    Crie uma oferta curta e impactante para o produto abaixo.
    
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
        if st.button("✨ Gerar Promoção"):
            if not url_input:
                st.warning("Por favor, insira o link do produto.")
            else:
                with st.spinner("Processando informações..."):
                    link_final = criar_link_afiliado(url_input, loja_selecionada)
                    
                    if usar_ia:
                        resultado = gerar_texto_ia(url_input, loja_selecionada, info_adicional)
                        if resultado:
                            st.session_state.texto_final = resultado.replace("[LINK]", link_final)
                        else:
                            st.error("IA fora do ar ou limite atingido. Use o modo manual.")
                            st.session_state.texto_final = f"🔥 PROMOÇÃO!\n{info_adicional}\n\n🛒 Compre aqui: {link_final}"
                    else:
                        st.session_state.texto_final = f"🔥 PROMOÇÃO!\n{info_adicional}\n\n🛒 Compre aqui: {link_final}"

        # Área de Edição e Envio
        if "texto_final" in st.session_state:
            st.divider()
            st.subheader("📝 Resultado Final (Pode editar)")
            post_final = st.text_area("Texto formatado:", value=st.session_state.texto_final, height=300)
            
            col_post1, col_post2 = st.columns(2)
            with col_post1:
                if st.button("📤 Postar no Telegram"):
                    # Aqui você integraria com a API do bot de Telegram
                    # Ex: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": ID, "text": post_final})
                    st.success("Enviado para o Telegram!")
            
            with col_post2:
                if st.button("💬 Postar no WhatsApp"):
                    # Como o WhatsApp Web é bloqueado em servidores, 
                    # aqui geralmente usamos um link de API para abrir no celular de quem postou
                    st.info("Função de API do WhatsApp em integração...")

if __name__ == "__main__":
    main()