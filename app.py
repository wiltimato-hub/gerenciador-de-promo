import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- 1. CONFIGURAÇÃO DE SEGURANÇA ---
st.set_page_config(page_title="Gerador WilliamP", page_icon="💰")

# Inicializa variáveis para evitar erro de "variável não definida"
if "logado" not in st.session_state: st.session_state.logado = False
if "texto_final" not in st.session_state: st.session_state.texto_final = ""

# --- 2. LOGIN ---
USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456"}

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreto")

# --- 3. APP PRINCIPAL ---
else:
    st.title("🚀 Gerador de Ofertas")

    link_prod = st.text_input("🔗 Link do Produto:")
    loja = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    detalhes = st.text_area("📝 Detalhes (Preço/Nome):")

    if st.button("✨ GERAR"):
        with st.spinner("Processando..."):
            # Lógica de Afiliado
            link_final = link_prod
            if "Amazon" in loja:
                tag = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                link_limpo = link_prod.split("?")[0].split("&")[0]
                link_final = f"{link_limpo}?tag={tag}"
            elif "Magalu" in loja:
                link_final = f"https://www.magazinevoce.com.br/magazinewiltimato/p/{link_prod.split('/')[-1]}"

            # Tentativa de IA
            try:
                # O strip() remove espaços acidentais da chave
                api_key = st.secrets["GEMINI_KEY"].strip().replace('"', '')
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                response = model.generate_content(f"Crie uma oferta curta para: {detalhes}. Link: {link_final}")
                st.session_state.texto_final = response.text
            except Exception as e:
                # Se a IA der erro, o app NÃO PARA. Ele gera o texto padrão.
                st.session_state.texto_final = f"🔥 *OFERTA EXCLUSIVA*\n\n{detalhes}\n\n🛒 Compre aqui: {link_final}"
                st.info(f"Aviso: IA offline (usando modo manual).")

    # Exibição do Resultado
    if st.session_state.texto_final:
        st.divider()
        res = st.text_area("Texto Gerado:", value=st.session_state.texto_final, height=200)
        
        # WhatsApp Link
        zap = f"https://api.whatsapp.com/send?text={urllib.parse.quote(res)}"
        st.link_button("💬 Enviar para WhatsApp", zap)
        
        # Telegram Bot (Opcional - só se os segredos existirem)
        if st.button("📤 Enviar para Telegram"):
            try:
                t = st.secrets["TELEGRAM_TOKEN"]
                c = st.secrets["TELEGRAM_CHAT_ID"]
                requests.post(f"https://api.telegram.org/bot{t}/sendMessage", data={"chat_id": c, "text": res, "parse_mode": "Markdown"})
                st.success("Enviado!")
            except:
                st.error("Erro no Telegram. Verifique os Secrets.")