import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gerador de Ofertas Pro", page_icon="💰")

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

    url_input = st.text_input("🔗 Link Original do Produto:")
    loja_sel = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    detalhes = st.text_area("📝 Preço e detalhes:")
    img_manual = st.text_input("🖼️ URL da Imagem (Opcional):")

    if st.button("✨ GERAR PROMOÇÃO"):
        if not url_input:
            st.warning("Insira o link!")
        else:
            with st.spinner("Construindo oferta..."):
                # 1. LINK DE AFILIADO
                tag_amazon = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                link_limpo = url_input.split("&tag=")[0].split("?tag=")[0]
                separador = "&" if "?" in link_limpo else "?"
                
                if "Amazon" in loja_sel:
                    link_final = f"{link_limpo}{separador}tag={tag_amazon}"
                elif "Magalu" in loja_sel:
                    link_final = f"https://www.magazinevoce.com.br/magazinewiltimato/p/{link_limpo.split('/')[-1]}"
                else:
                    link_final = url_input

                # 2. CAPTURA DE IMAGEM
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    res = requests.get(url_input, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    img = soup.find("meta", property="og:image")
                    st.session_state.img_url = img["content"] if img else img_manual
                except:
                    st.session_state.img_url = img_manual

                # 3. IA (AJUSTE DE SEGURANÇA)
                try:
                    # Tenta pegar a chave do Secret
                    api_key = st.secrets["GEMINI_KEY"].strip().replace('"', '')
                    genai.configure(api_key=api_key)
                    
                    # Seleção do modelo mais recente e estável
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"Crie um post de oferta curto. Produto: {detalhes}. Use emojis e negrito. Link de compra: {link_final}. NÃO use o link original."
                    
                    response = model.generate_content(prompt)
                    
                    if response.text:
                        st.session_state.texto_gerado = response.text
                        st.success("✅ IA respondeu!")
                    else:
                        raise Exception("A IA retornou uma resposta vazia.")

                except Exception as e:
                    # Se a IA falhar, gera o texto manualmente para o seu link de afiliado funcionar
                    st.session_state.texto_gerado = f"🔥 *OFERTA IMPERDÍVEL!*\n\n{detalhes}\n\n🛒 COMPRE AQUI: {link_final}"
                    st.error(f"Erro na IA: {e}")

    # --- EXIBIÇÃO E ENVIO ---
    if st.session_state.texto_gerado:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
        
        post_final = st.text_area("Texto Final:", value=st.session_state.texto_gerado, height=250)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.img_url:
                        requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                     data={"chat_id": c, "photo": st.session_state.img_url, "caption": post_final, "parse_mode": "Markdown"})
                    else:
                        requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                     data={"chat_id": c, "text": post_final, "parse_mode": "Markdown"})
                    st.success("Postado!")
                except: st.error("Erro no envio.")
        
        with c2:
            st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(post_final)}")