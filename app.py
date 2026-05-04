import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador de Ofertas IA", page_icon="💰", layout="centered")

# CSS para melhorar a estética
st.markdown("""
    <style>
    .stButton>button { background-color: #25D366; color: white; border-radius: 20px; border: none; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 10px; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Estado da Sessão
if "logado" not in st.session_state: st.session_state.logado = False
if "texto_final" not in st.session_state: st.session_state.texto_final = ""
if "imagem_preview" not in st.session_state: st.session_state.imagem_preview = ""

# --- LOGIN ---
USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456"}

if not st.session_state.logado:
    st.title("🔐 Login de Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Acesso Negado")
else:
    st.title("🚀 Gerador de Ofertas Pro")

    # --- INPUTS ---
    with st.container():
        link_prod = st.text_input("🔗 Cole o Link do Produto:")
        
        c_loja, c_img = st.columns(2)
        with c_loja:
            loja = st.selectbox("🏪 Selecione a Loja:", ["Amazon", "Magalu", "Shopee", "Mercado Livre"])
        with c_img:
            img_manual = st.text_input("🖼️ Link da Imagem (Opcional):")
            
        detalhes = st.text_area("📝 Preço e Detalhes da Oferta:", placeholder="Ex: De R$ 100 por R$ 49,90")

    # --- PROCESSAMENTO ---
    if st.button("✨ GERAR PROMOÇÃO"):
        if not link_prod:
            st.warning("Insira o link primeiro!")
        else:
            with st.spinner("Processando..."):
                # 1. GERAÇÃO DO LINK DE AFILIADO
                link_afiliado = link_prod # Padrão
                if "Amazon" in loja:
                    tag = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                    link_limpo = link_prod.split("?")[0].split("&")[0]
                    link_afiliado = f"{link_limpo}?tag={tag}"
                elif "Magalu" in loja:
                    link_afiliado = f"https://www.magazinevoce.com.br/magazinewiltimato/p/{link_prod.split('/')[-1]}"
                
                # 2. BUSCA DE IMAGEM
                if img_manual:
                    st.session_state.imagem_preview = img_manual
                else:
                    try:
                        res = requests.get(link_prod, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        soup = BeautifulSoup(res.text, 'html.parser')
                        meta = soup.find("meta", property="og:image")
                        st.session_state.imagem_preview = meta["content"] if meta else ""
                    except: st.session_state.imagem_preview = ""

                # 3. CHAMADA DA IA (SISTEMA SEGURO)
                try:
                    key = st.secrets["GEMINI_KEY"].strip().replace('"', '')
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"Crie um post curto e atraente. Produto: {detalhes}. Use emojis. Link: {link_afiliado}"
                    response = model.generate_content(prompt)
                    st.session_state.texto_final = response.text
                except:
                    # Se a IA der qualquer erro, gera o texto padrão para não travar
                    st.session_state.texto_final = f"🔥 *OFERTA IMPERDÍVEL!*\n\n{detalhes}\n\n🛒 COMPRE AQUI: {link_afiliado}"

    # --- EXIBIÇÃO ---
    if st.session_state.texto_final:
        st.divider()
        if st.session_state.imagem_preview:
            st.image(st.session_state.imagem_preview, width=300)
        
        editado = st.text_area("Texto Final:", value=st.session_state.texto_final, height=200)

        col_t, col_w = st.columns(2)
        with col_t:
            if st.button("📤 Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.imagem_preview:
                        requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                     data={"chat_id": c, "photo": st.session_state.imagem_preview, "caption": editado, "parse_mode": "Markdown"})
                    else:
                        requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                     data={"chat_id": c, "text": editado, "parse_mode": "Markdown"})
                    st.success("Enviado!")
                except: st.error("Erro no Telegram.")
        
        with col_w:
            zap_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(editado)}"
            st.link_button("💬 WhatsApp", zap_link)