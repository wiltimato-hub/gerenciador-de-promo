import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Gerador de Ofertas IA", page_icon="💰")

# Configuração da IA
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("Erro: Verifique a GEMINI_KEY nos Secrets.")

USUARIOS = {
    "WilliamP": "1",
    "WesleyB": "festa456",
    "PedroA": "oferta789"
}

# --- FUNÇÃO PARA PEGAR IMAGEM AUTOMATICAMENTE ---
def extrair_dados_produto(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Tenta pegar a imagem das meta tags (padrão da maioria das lojas)
        img_tag = soup.find("meta", property="og:image") or soup.find("meta", {"name": "twitter:image"})
        if img_tag:
            return img_tag["content"]
        
        # Fallback para Amazon (procura a imagem principal)
        img_amazon = soup.find("img", {"id": "landingImage"}) or soup.find("img", {"id": "imgBlkFront"})
        if img_amazon:
            return img_amazon["src"]
            
        return None
    except:
        return None

def criar_link_afiliado(url, loja):
    link = url.strip()
    if "Amazon" in loja:
        tag = "wiltimato-20"
        return f"{link}&tag={tag}" if "?" in link else f"{link}?tag={tag}"
    elif "Magalu" in loja:
        return f"https://www.magazinevoce.com.br/magazinewiltimato/p/{link.split('/')[-1]}"
    return link

def gerar_texto_ia(url, loja, info):
    prompt = f"Crie um post de oferta para o produto no link {url}. Loja: {loja}. Info extra: {info}. Use negrito no título, emojis e uma lista de benefícios. Use o marcador [LINK] no final."
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return None

# --- INTERFACE ---
if "logado" not in st.session_state: st.session_state.logado = False
if "texto_final" not in st.session_state: st.session_state.texto_final = ""
if "img_url" not in st.session_state: st.session_state.img_url = ""

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
else:
    st.title("💰 Postador Inteligente")
    
    url_input = st.text_input("Link do Produto:")
    loja = st.selectbox("Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    info = st.text_area("Preço e Detalhes:")

    if st.button("✨ GERAR OFERTA COMPLETA"):
        if url_input:
            with st.spinner("Buscando imagem e criando texto..."):
                # Busca Imagem
                st.session_state.img_url = extrair_dados_produto(url_input)
                # Gera Link e Texto
                link_afiliado = criar_link_afiliado(url_input, loja)
                texto = gerar_texto_ia(url_input, loja, info)
                if texto:
                    st.session_state.texto_final = texto.replace("[LINK]", link_afiliado)
        else:
            st.warning("Insira o link!")

    # Exibição do Resultado (Só aparece se houver texto gerado)
    if st.session_state.texto_final:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300, caption="Imagem capturada automaticamente")
        
        post_editavel = st.text_area("Edite seu post:", value=st.session_state.texto_final, height=250)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Enviar para Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.img_url:
                        # Envia FOTO + LEGENDA
                        req = requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                          data={"chat_id": c, "photo": st.session_state.img_url, "caption": post_editavel, "parse_mode": "Markdown"})
                    else:
                        # Envia só TEXTO
                        req = requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                          data={"chat_id": c, "text": post_editavel, "parse_mode": "Markdown"})
                    
                    if req.status_code == 200: st.success("Postado!")
                    else: st.error(f"Erro: {req.json().get('description')}")
                except:
                    st.error("Erro nos Secrets do Telegram.")

        with c2:
            texto_zap = urllib.parse.quote(post_editavel)
            st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={texto_zap}")