import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÃO ---
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
    st.title("💰 Gerador de Ofertas Profissional")

    # --- INPUTS ---
    url_input = st.text_input("🔗 Link do Produto (Original):")
    loja_sel = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    detalhes = st.text_area("📝 Detalhes da Oferta (Preço/Nome):")
    img_manual = st.text_input("🖼️ URL da Imagem (Opcional):")

    if st.button("✨ GERAR PROMOÇÃO"):
        if not url_input:
            st.warning("Insira o link!")
        else:
            with st.spinner("Processando..."):
                # 1. TENTAR CAPTURAR IMAGEM
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    res = requests.get(url_input, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    img = soup.find("meta", property="og:image")
                    st.session_state.img_url = img["content"] if img else img_manual
                except:
                    st.session_state.img_url = img_manual

                # 2. CONFIGURAR LINK DE AFILIADO (Correção do Link)
                tag_amazon = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                if "Amazon" in loja_sel:
                    # Se o link já tem ?, usa &, senão usa ?
                    separador = "&" if "?" in url_input else "?"
                    link_final = f"{url_input}{separador}tag={tag_amazon}"
                else:
                    link_final = url_input

                # 3. CHAMAR IA (Modelo Flash - Mais estável)
                try:
                    genai.configure(api_key=st.secrets["GEMINI_KEY"])
                    # Mudança para o modelo estável mais recente
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Prompt focado em colocar o link no topo (melhor para o preview do WhatsApp)
                    prompt = f"""
                    Crie um post de oferta impactante. 
                    Produto: {url_input}
                    Detalhes: {detalhes}
                    REQUISITOS:
                    - Comece com emojis chamativos.
                    - Coloque o link de compra logo no início ou meio: {link_final}
                    - Use negrito para o preço.
                    - Seja breve.
                    """
                    response = model.generate_content(prompt)
                    st.session_state.texto_gerado = response.text
                    st.success("✅ IA e Link gerados!")
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.session_state.texto_gerado = f"🔥 *OFERTA CONFIRMADA!*\n\n{detalhes}\n\n🛒 COMPRE AQUI: {link_final}"

    # --- ÁREA DE ENVIO ---
    if st.session_state.texto_gerado:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
        
        post_final = st.text_area("Texto para copiar/enviar:", value=st.session_state.texto_gerado, height=250)

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
                    st.success("Enviado para o Telegram!")
                except: st.error("Erro no Telegram.")
        
        with c2:
            # WhatsApp: O link vai no texto. Ao enviar, o WhatsApp lê o link e puxa a imagem.
            texto_whatsapp = urllib.parse.quote(post_final)
            st.link_button("💬 Abrir WhatsApp", f"https://api.whatsapp.com/send?text={texto_whatsapp}")