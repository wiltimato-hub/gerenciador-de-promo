import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

# --- SETUP DA PÁGINA ---
st.set_page_config(page_title="Gerador de Ofertas", page_icon="💰", layout="centered")

# Estética CSS
st.markdown("""
    <style>
    .stButton>button { background-color: #00c853; color: white; font-weight: bold; border-radius: 10px; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Estado da Sessão
if "logado" not in st.session_state: st.session_state.logado = False
if "resultado" not in st.session_state: st.session_state.resultado = ""
if "thumb" not in st.session_state: st.session_state.thumb = ""

# --- LOGIN ---
USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456"}

if not st.session_state.logado:
    st.title("🔐 Login")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user in USUARIOS and USUARIOS[user] == senha:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Acesso negado.")

else:
    st.title("💰 Criador de Posts Pro")
    
    # --- FORMULÁRIO ---
    with st.container():
        link_orig = st.text_input("🔗 Link do Produto (Amazon, Magalu, Shopee...):")
        
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            loja = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Mercado Livre", "AliExpress"])
        with col_op2:
            img_manual = st.text_input("🖼️ Link da Imagem (Opcional):")
            
        detalhes = st.text_area("📝 Descrição/Preço:", placeholder="Ex: De R$ 200 por R$ 99")

    # --- LÓGICA DE GERAÇÃO ---
    if st.button("✨ GERAR OFERTA"):
        if not link_orig:
            st.warning("Insira o link primeiro!")
        else:
            with st.spinner("IA processando..."):
                # 1. GERAÇÃO DO LINK DE AFILIADO
                # Amazon
                if "Amazon" in loja:
                    tag = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                    link_final = f"{link_orig}&tag={tag}" if "?" in link_orig else f"{link_orig}?tag={tag}"
                # Magalu
                elif "Magalu" in loja:
                    link_final = f"https://www.magazinevoce.com.br/magazinewiltimato/p/{link_orig.split('/')[-1]}"
                # Outras (ajustar conforme necessidade)
                else:
                    link_final = link_orig

                # 2. CAPTURA DA IMAGEM
                if img_manual:
                    st.session_state.thumb = img_manual
                else:
                    try:
                        h = {"User-Agent": "Mozilla/5.0"}
                        r = requests.get(link_orig, headers=h, timeout=5)
                        s = BeautifulSoup(r.text, 'html.parser')
                        meta = s.find("meta", property="og:image")
                        st.session_state.thumb = meta["content"] if meta else ""
                    except: st.session_state.thumb = ""

                # 3. CHAMADA DA IA (TENTATIVA TRIPLA)
                try:
                    chave = st.secrets["GEMINI_KEY"].strip().replace('"', '')
                    genai.configure(api_key=chave)
                    
                    # Tentativa 1: Flash 1.5 (Mais novo)
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(f"Crie um post para {loja}. Produto: {detalhes}. Link: {link_final}. Use emojis.")
                        st.session_state.resultado = res.text
                    except:
                        # Tentativa 2: Pro (Mais estável)
                        model = genai.GenerativeModel('gemini-pro')
                        res = model.generate_content(f"Crie um post de oferta para: {detalhes}. Link: {link_final}")
                        st.session_state.resultado = res.text
                        
                    st.success("IA respondeu com sucesso!")
                except Exception as e:
                    # Fallback Manual (Se a IA falhar de vez, o post é criado mesmo assim)
                    st.session_state.resultado = f"🔥 **OFERTA {loja.upper()}**\n\n{detalhes}\n\n🛒 **COMPRE AQUI:** {link_final}"
                    st.error(f"Erro na IA: {e}. Geramos um texto padrão.")

    # --- RESULTADO FINAL ---
    if st.session_state.resultado:
        st.divider()
        if st.session_state.thumb:
            st.image(st.session_state.thumb, width=280)
        
        texto_editavel = st.text_area("Post Gerado:", value=st.session_state.resultado, height=250)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.thumb:
                        requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                     data={"chat_id": c, "photo": st.session_state.thumb, "caption": texto_editavel, "parse_mode": "Markdown"})
                    else:
                        requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                     data={"chat_id": c, "text": texto_editavel, "parse_mode": "Markdown"})
                    st.success("Enviado!")
                except: st.error("Erro no Telegram.")
        
        with c2:
            # WhatsApp (O próprio link de afiliado gera o card visual)
            zap_enc = urllib.parse.quote(texto_editavel)
            st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={zap_enc}")