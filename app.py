import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Postador Pro", page_icon="💰")

if "logado" not in st.session_state: st.session_state.logado = False
if "texto_gerado" not in st.session_state: st.session_state.texto_gerado = ""
if "img_url" not in st.session_state: st.session_state.img_url = ""

# --- LOGIN ---
USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456", "PedroA": "oferta789"}

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreto")
else:
    st.title("💰 Gerador de Ofertas")

    # --- INPUTS ---
    url_input = st.text_input("Link do Produto:")
    loja_sel = st.selectbox("Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    detalhes = st.text_area("Informações Adicionais (Preço/Nome):")
    
    # Campo para caso a automação falhe
    img_manual = st.text_input("URL da Imagem (Opcional - Caso a automação falhe):")

    if st.button("✨ GERAR PROMOÇÃO"):
        if not url_input:
            st.warning("Insira o link!")
        else:
            with st.spinner("Buscando dados..."):
                # 1. Tentar capturar imagem automaticamente
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    res = requests.get(url_input, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    img = soup.find("meta", property="og:image")
                    st.session_state.img_url = img["content"] if img else img_manual
                except:
                    st.session_state.img_url = img_manual

                # 2. IA com modelo atualizado
                try:
                    genai.configure(api_key=st.secrets["GEMINI_KEY"])
                    # MODELO ATUALIZADO AQUI:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"Crie um post de promoção curto e atraente. Produto: {url_input}. Detalhes: {detalhes}. Use emojis e negrito. Link: [LINK]"
                    response = model.generate_content(prompt)
                    
                    # Gerar link de afiliado simples
                    link_final = url_input
                    if "Amazon" in loja_sel:
                        link_final = f"{url_input}?tag=wiltimato-20"
                    
                    st.session_state.texto_gerado = response.text.replace("[LINK]", link_final)
                    st.success("✅ Tudo pronto!")
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.session_state.texto_gerado = f"🔥 *PROMOÇÃO EXCLUSIVA*\n\n{detalhes}\n\n🛒 Compre aqui: {url_input}"

    # --- ÁREA DE ENVIO ---
    if st.session_state.texto_gerado:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
        
        post_final = st.text_area("Edite o texto:", value=st.session_state.texto_gerado, height=200)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Postar no Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.img_url:
                        requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                     data={"chat_id": c, "photo": st.session_state.img_url, "caption": post_final, "parse_mode": "Markdown"})
                    else:
                        requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                     data={"chat_id": c, "text": post_final, "parse_mode": "Markdown"})
                    st.success("Enviado!")
                except: st.error("Erro no envio.")
        with c2:
            texto_zap = urllib.parse.quote(post_final)
            st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={texto_zap}")