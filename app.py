import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Postador de Ofertas Pro", page_icon="💰", layout="centered")

# Inicialização de variáveis de memória (Session State)
if "logado" not in st.session_state: st.session_state.logado = False
if "texto_gerado" not in st.session_state: st.session_state.texto_gerado = ""
if "img_url" not in st.session_state: st.session_state.img_url = ""

# --- BANCO DE DADOS DE USUÁRIOS ---
USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456", "PedroA": "oferta789"}

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# --- ÁREA DO GERADOR (SÓ APARECE LOGADO) ---
else:
    st.title("💰 Gerador de Promoções")
    
    with st.container():
        url_input = st.text_input("🔗 Link do Produto:", placeholder="Cole o link da Amazon, Magalu, etc.")
        
        col_loja, col_img = st.columns(2)
        with col_loja:
            loja_sel = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Mercado Livre", "Outra"])
        with col_img:
            img_manual = st.text_input("🖼️ URL da Imagem (Opcional):", placeholder="Caso a automação falhe")
        
        detalhes = st.text_area("📝 Informações Extras:", placeholder="Ex: De R$ 500 por R$ 299 em 10x sem juros")
        
        btn_gerar = st.button("✨ GERAR PROMOÇÃO AGORA")

    # --- LÓGICA DE GERAÇÃO ---
    if btn_gerar:
        if not url_input:
            st.warning("Por favor, insira o link do produto.")
        else:
            with st.spinner("Processando..."):
                # 1. Tentar capturar imagem automaticamente
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    res = requests.get(url_input, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    img_tag = soup.find("meta", property="og:image") or soup.find("meta", {"name": "twitter:image"})
                    st.session_state.img_url = img_tag["content"] if img_tag else img_manual
                except:
                    st.session_state.img_url = img_manual

                # 2. Gerar Texto com IA
                try:
                    genai.configure(api_key=st.secrets["GEMINI_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    link_afiliado = url_input
                    if "Amazon" in loja_sel:
                        link_afiliado = f"{url_input}?tag=wiltimato-20"
                    
                    prompt = f"Crie um post de oferta curto para WhatsApp/Telegram. Produto: {url_input}. Detalhes: {detalhes}. Use emojis, negrito e termine com: 🛒 Compre aqui: {link_afiliado}"
                    
                    response = model.generate_content(prompt)
                    st.session_state.texto_gerado = response.text
                    st.success("✅ Texto gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.session_state.texto_gerado = f"🔥 *PROMOÇÃO EXCLUSIVA*\n\n{detalhes}\n\n🛒 Compre aqui: {url_input}"

    # --- RESULTADO E ENVIO ---
    if st.session_state.texto_gerado:
        st.divider()
        st.subheader("📝 Resultado Final")
        
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
            st.caption("Prévia da imagem capturada")
        
        post_final = st.text_area("Edite o texto se necessário:", value=st.session_state.texto_gerado, height=250)

        col_tel, col_zap = st.columns(2)
        
        with col_tel:
            if st.button("📤 Postar no Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    
                    if st.session_state.img_url:
                        # Envia FOTO com legenda (HTML ativado para negritos)
                        api_url = f"https://api.telegram.org/bot{t}/sendPhoto"
                        payload = {"chat_id": c, "photo": st.session_state.img_url, "caption": post_final, "parse_mode": "Markdown"}
                    else:
                        # Envia só TEXTO
                        api_url = f"https://api.telegram.org/bot{t}/sendMessage"
                        payload = {"chat_id": c, "text": post_final, "parse_mode": "Markdown"}
                    
                    res = requests.post(api_url, data=payload)
                    if res.status_code == 200: st.success("✅ Enviado!")
                    else: st.error(f"Erro: {res.json().get('description')}")
                except:
                    st.error("Verifique os Tokens do Telegram nos Secrets.")

        with col_zap:
            texto_enc = urllib.parse.quote(post_final)
            st.link_button("💬 Enviar para WhatsApp", f"https://api.whatsapp.com/send?text={texto_enc}")