import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gerador WilliamP", page_icon="💰")

if "logado" not in st.session_state: st.session_state.logado = False
if "texto_final" not in st.session_state: st.session_state.texto_final = ""
if "img_url" not in st.session_state: st.session_state.img_url = ""

# --- FUNÇÃO ENCURTADORA (TinyURL) ---
def encurtar_link(url_longa):
    try:
        api_url = f"http://tinyurl.com/api-create.php?url={url_longa}"
        res = requests.get(api_url, timeout=5)
        return res.text if res.status_code == 200 else url_longa
    except:
        return url_longa

# --- LOGIN ---
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

else:
    st.title("🚀 Gerador de Ofertas Profissional")

    link_prod = st.text_input("🔗 Link Original do Produto:")
    
    col_loja, col_img = st.columns(2)
    with col_loja:
        loja = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    with col_img:
        img_manual = st.text_input("🖼️ Link da Imagem (Manual):", placeholder="Opcional")
        
    detalhes = st.text_area("📝 Preço e Detalhes:")

    if st.button("✨ GERAR OFERTA ENCURTADA"):
        with st.spinner("Encurtando link e gerando copy..."):
            # 1. Gerar Link de Afiliado
            link_final = link_prod
            if "Amazon" in loja:
                tag = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                link_limpo = link_prod.split("?")[0].split("&")[0]
                link_final = f"{link_limpo}?tag={tag}"
            elif "Magalu" in loja:
                # Extraímos o final do link original (ex: produto.html)
                link_limpo = link_prod.split("?")[0].split("&")[0]
                slug_produto = link_limpo.split("/")[-1]
                # Montamos o link usando sua loja 'Locatech'
                link_final = f"https://www.magazinevoce.com.br/magazinelocatech/p/{slug_produto}"
                
            # 2. Encurtar o link gerado
            link_curto = encurtar_link(link_final)

            # 3. Captura de Imagem
            if img_manual:
                st.session_state.img_url = img_manual
            else:
                try:
                    res = requests.get(link_prod, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    meta = soup.find("meta", property="og:image")
                    st.session_state.img_url = meta["content"] if meta else ""
                except:
                    st.session_state.img_url = ""

            # 4. Chamada da IA com o Link Curto
            try:
                api_key = st.secrets["GEMINI_KEY"].strip().replace('"', '')
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"Crie uma oferta curta. Detalhes: {detalhes}. Link de compra: {link_curto}. Use emojis."
                response = model.generate_content(prompt)
                st.session_state.texto_final = response.text
            except:
                st.session_state.texto_final = f"🔥 *OFERTA EXCLUSIVA*\n\n{detalhes}\n\n🛒 Compre aqui: {link_curto}"

    # --- EXIBIÇÃO E ENVIO ---
    if st.session_state.texto_final:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
        
        res_editado = st.text_area("Texto com Link Curto:", value=st.session_state.texto_final, height=200)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Enviar Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.img_url:
                        requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                     data={"chat_id": c, "photo": st.session_state.img_url, "caption": res_editado, "parse_mode": "Markdown"})
                    else:
                        requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                     data={"chat_id": c, "text": res_editado, "parse_mode": "Markdown"})
                    st.success("Enviado!")
                except: st.error("Erro no Telegram.")
        
        with c2:
            zap_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(res_editado)}"
            st.link_button("💬 WhatsApp", zap_url)