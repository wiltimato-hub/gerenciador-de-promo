import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
st.set_page_config(page_title="Gerador de Ofertas IA", page_icon="💰")

# Inicialização do Estado da Sessão (Para os dados não sumirem)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "texto_gerado" not in st.session_state:
    st.session_state.texto_gerado = ""
if "img_url" not in st.session_state:
    st.session_state.img_url = ""

# --- 2. FUNÇÕES DE SUPORTE ---

def extrair_imagem(url):
    """ Tenta capturar a imagem do produto automaticamente """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Busca em meta tags (padrão para redes sociais)
        meta_img = soup.find("meta", property="og:image") or soup.find("meta", {"name": "twitter:image"})
        if meta_img:
            return meta_img["content"]
    except Exception as e:
        return None
    return None

def preparar_link(url, loja):
    """ Aplica a tag de afiliado """
    link = url.strip()
    if "Amazon" in loja:
        tag = "wiltimato-20"
        return f"{link}&tag={tag}" if "?" in link else f"{link}?tag={tag}"
    elif "Magalu" in loja:
        return f"https://www.magazinevoce.com.br/magazinewiltimato/p/{link.split('/')[-1]}"
    return link

# --- 3. SISTEMA DE LOGIN ---

USUARIOS = {
    "WilliamP": "William08112006!",
    "WesleyB": "festa456",
    "PedroA": "oferta789"
}

if not st.session_state.logado:
    st.title("🔐 Login de Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# --- 4. ÁREA DO GERADOR (SÓ APARECE SE LOGADO) ---
else:
    st.title("💰 Gerador de Promoções")
    
    with st.container(border=True):
        url_input = st.text_input("Cole o link do produto aqui:")
        loja_sel = st.selectbox("Selecione a Loja:", ["Amazon", "Magalu", "Shopee", "Outra"])
        detalhes = st.text_area("Informações extras (Preço, Nome, etc):")
        
        btn_gerar = st.button("✨ GERAR PROMOÇÃO")

    # Lógica ao clicar em Gerar
    if btn_gerar:
        if not url_input:
            st.warning("Insira o link do produto primeiro!")
        else:
            with st.spinner("Processando..."):
                # 1. Busca Imagem
                st.session_state.img_url = extrair_imagem(url_input)
                
                # 2. Prepara Link
                link_final = preparar_link(url_input, loja_sel)
                
                # 3. Chama IA
                try:
                    genai.configure(api_key=st.secrets["GEMINI_KEY"])
                    model = genai.GenerativeModel('gemini-pro')
                    prompt = f"Crie um post para WhatsApp/Telegram. Produto: {url_input}. Loja: {loja_sel}. Detalhes: {detalhes}. Link de compra: {link_final}. Use emojis e negrito."
                    response = model.generate_content(prompt)
                    st.session_state.texto_gerado = response.text
                except Exception as e:
                    st.session_state.texto_gerado = f"🔥 PROMOÇÃO!\n{detalhes}\n\n🛒 Compre aqui: {link_final}"
                    st.error(f"Erro na IA (Modo Manual Ativado): {e}")

    # --- 5. RESULTADO E ENVIO (SÓ APARECE SE TIVER TEXTO) ---
    if st.session_state.texto_gerado:
        st.subheader("📝 Resultado da Promoção")
        
        # Mostra imagem se foi encontrada
        if st.session_state.img_url:
            st.image(st.session_state.img_url, width=250)
        else:
            st.info("Não conseguimos capturar a imagem automaticamente. O post irá apenas com texto ou você pode colar o link da imagem manualmente.")

        # Texto editável
        post_final = st.text_area("Texto final (você pode editar):", value=st.session_state.texto_gerado, height=250)

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Postar no Telegram"):
                try:
                    token = st.secrets["TELEGRAM_TOKEN"]
                    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
                    
                    if st.session_state.img_url:
                        # Envia FOTO com legenda
                        res = requests.post(
                            f"https://api.telegram.org/bot{token}/sendPhoto",
                            data={"chat_id": chat_id, "photo": st.session_state.img_url, "caption": post_final, "parse_mode": "Markdown"}
                        )
                    else:
                        # Envia só TEXTO
                        res = requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            data={"chat_id": chat_id, "text": post_final, "parse_mode": "Markdown"}
                        )
                    
                    if res.status_code == 200:
                        st.success("✅ Postado no Telegram!")
                    else:
                        st.error(f"Erro Telegram: {res.json().get('description')}")
                except Exception as e:
                    st.error(f"Erro de configuração: {e}")

        with col2:
            texto_encoded = urllib.parse.quote(post_final)
            whatsapp_url = f"https://api.whatsapp.com/send?text={texto_encoded}"
            st.link_button("💬 Enviar para WhatsApp", whatsapp_url)