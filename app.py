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
    st.title("💰 Gerador de Ofertas Profissional")

    with st.container():
        url_input = st.text_input("🔗 Link Original do Produto (Amazon/Magalu):")
        loja_sel = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
        detalhes = st.text_area("📝 Preço e detalhes (Ex: R$ 199 em 10x):")
        img_manual = st.text_input("🖼️ URL da Imagem (Opcional):", placeholder="Cole aqui se a automática falhar")

    if st.button("✨ GERAR PROMOÇÃO"):
        if not url_input:
            st.warning("Insira o link!")
        else:
            with st.spinner("Construindo oferta..."):
                # 1. PROCESSAR LINK DE AFILIADO PRIMEIRO
                tag_amazon = st.secrets.get("AMAZON_TAG", "wiltimato-20")
                if "Amazon" in loja_sel:
                    # Garante que a tag vá no seu link
                    separador = "&" if "?" in url_input else "?"
                    # Remove tags de terceiros se existirem no link colado
                    link_limpo = url_input.split("&tag=")[0].split("?tag=")[0]
                    link_final = f"{link_limpo}{separador}tag={tag_amazon}"
                elif "Magalu" in loja_sel:
                    # Exemplo para Magalu (ajuste conforme seu padrão)
                    link_final = f"https://www.magazinevoce.com.br/magazinewiltimato/p/{url_input.split('/')[-1]}"
                else:
                    link_final = url_input

                # 2. CAPTURAR IMAGEM (Usando o original apenas para busca)
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    res = requests.get(url_input, headers=headers, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    img = soup.find("meta", property="og:image")
                    st.session_state.img_url = img["content"] if img else img_manual
                except:
                    st.session_state.img_url = img_manual

                # 3. GERAR TEXTO COM IA (Passando apenas o link de AFILIADO)
                try:
                    genai.configure(api_key=st.secrets["GEMINI_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Forçamos a IA a usar APENAS o link_final
                    prompt = f"""
                    Você é um especialista em vendas. Crie um post para Telegram/WhatsApp.
                    DETALHES DO PRODUTO: {detalhes}
                    LINK DE COMPRA: {link_final}
                    
                    REGRAS:
                    - Use emojis e negrito no preço.
                    - Use APENAS o LINK DE COMPRA fornecido acima. Nunca use o link original.
                    - O link deve estar bem visível.
                    """
                    response = model.generate_content(prompt)
                    st.session_state.texto_gerado = response.text
                    st.success("✅ Oferta Gerada com seu Link de Afiliado!")
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
                    st.session_state.texto_gerado = f"🔥 *OFERTA IMPERDÍVEL!*\n\n{detalhes}\n\n🛒 COMPRE AQUI: {link_final}"

    # --- ÁREA DE ENVIO ---
    if st.session_state.texto_gerado:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
        
        # Área para edição final
        post_final = st.text_area("Texto Final (Confira seu link abaixo):", value=st.session_state.texto_gerado, height=250)

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
                    st.success("Enviado com sucesso!")
                except: st.error("Erro ao enviar. Verifique se o Bot é ADM do Canal.")
        
        with c2:
            texto_whatsapp = urllib.parse.quote(post_final)
            st.link_button("💬 Abrir no WhatsApp", f"https://api.whatsapp.com/send?text={texto_whatsapp}")