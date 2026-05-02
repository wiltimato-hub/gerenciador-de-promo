import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Diagnóstico de Ofertas", page_icon="🔍")

# Inicialização do Estado
if "logado" not in st.session_state: st.session_state.logado = False
if "texto_gerado" not in st.session_state: st.session_state.texto_gerado = ""
if "img_url" not in st.session_state: st.session_state.img_url = ""

USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456", "PedroA": "oferta789"}

# --- FUNÇÃO DE CAPTURA DE IMAGEM MELHORADA ---
def extrair_imagem(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return f"Erro: Site bloqueou acesso (Status {res.status_code})"
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # Tenta várias fontes de imagem comuns
        img = soup.find("meta", property="og:image") or \
              soup.find("meta", {"name": "twitter:image"}) or \
              soup.find("link", rel="image_src")
        
        if img:
            return img.get("content") or img.get("href")
        return "Imagem não encontrada no código do site."
    except Exception as e:
        return f"Erro na conexão: {str(e)}"

# --- INTERFACE ---
if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    st.title("💰 Gerador de Ofertas (Modo Diagnóstico)")
    
    with st.expander("🛠️ Verificar Configurações (Secrets)", expanded=False):
        # Verifica se as chaves existem nos Secrets sem mostrar o valor todo
        for key in ["GEMINI_KEY", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]:
            if key in st.secrets:
                st.write(f"✅ {key} configurada.")
            else:
                st.error(f"❌ {key} NÃO encontrada nos Secrets.")

    url_input = st.text_input("Link do Produto:")
    loja_sel = st.selectbox("Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
    detalhes = st.text_area("Detalhes (Preço/Nome):")

    if st.button("✨ GERAR PROMOÇÃO"):
        if not url_input:
            st.warning("Insira o link!")
        else:
            with st.spinner("1. Tentando capturar imagem..."):
                resultado_img = extrair_imagem(url_input)
                if resultado_img and resultado_img.startswith("http"):
                    st.session_state.img_url = resultado_img
                    st.success("✅ Imagem capturada!")
                else:
                    st.error(f"❌ Erro na imagem: {resultado_img}")
                    st.session_state.img_url = ""

            with st.spinner("2. Tentando falar com a IA..."):
                try:
                    if "GEMINI_KEY" not in st.secrets:
                        raise Exception("Falta a chave GEMINI_KEY nos Secrets.")
                    
                    genai.configure(api_key=st.secrets["GEMINI_KEY"])
                    model = genai.GenerativeModel('gemini-pro')
                    
                    link_final = url_input # Simplificado para teste
                    prompt = f"Gere uma oferta curta para: {url_input}. Detalhes: {detalhes}. Use emojis."
                    
                    response = model.generate_content(prompt)
                    st.session_state.texto_gerado = response.text
                    st.success("✅ IA respondeu com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro na IA: {str(e)}")
                    # Fallback manual para o botão não sumir
                    st.session_state.texto_gerado = f"🔥 OFERTA!\n{detalhes}\n🛒 Link: {url_input}"

    # --- EXIBIÇÃO DOS BOTÕES DE ENVIO ---
    if st.session_state.texto_gerado:
        st.divider()
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=300)
        
        post_final = st.text_area("Texto gerado:", value=st.session_state.texto_gerado, height=200)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Telegram"):
                st.info("Testando envio...")
                # Lógica de envio aqui...
        with c2:
            texto_encoded = urllib.parse.quote(post_final)
            st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={texto_encoded}")