import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Gerador de Ofertas IA", page_icon="💰", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #ff4b4b; color: white; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADO ---
if "logado" not in st.session_state: st.session_state.logado = False
if "texto_pronto" not in st.session_state: st.session_state.texto_pronto = ""
if "imagem_url" not in st.session_state: st.session_state.imagem_url = ""

# --- BANCO DE USUÁRIOS ---
USUARIOS = {"WilliamP": "William08112006!", "WesleyB": "festa456", "PedroA": "oferta789"}

# --- FUNÇÕES CORE ---

def limpar_e_gerar_link(url, loja):
    """ Remove lixo do link e aplica sua tag de afiliado """
    url = url.strip().split("?")[0].split("&")[0] # Limpa tags de terceiros
    
    if "Amazon" in loja:
        tag = st.secrets.get("AMAZON_TAG", "wiltimato-20")
        return f"{url}?tag={tag}"
    elif "Magalu" in loja:
        user_magalu = "seu_user_aqui" # Ajuste depois
        return f"https://www.magazinevoce.com.br/magazine{user_magalu}/p/{url.split('/')[-1]}"
    elif "Shopee" in loja:
        return f"{url}?smtt=0.0.9" # Ajuste para sua URL de afiliado Shopee
    elif "Mercado Livre" in loja:
        return url # Mercado Livre geralmente exige link encurtado manual
    return url

def pegar_imagem(url):
    """ Tenta capturar a imagem principal do produto """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        img = soup.find("meta", property="og:image") or soup.find("meta", {"name": "twitter:image"})
        return img["content"] if img else None
    except: return None

# --- FLUXO DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    with st.form("login"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state.logado = True
                st.rerun()
            else: st.error("Credenciais incorretas.")

# --- PAINEL PRINCIPAL ---
else:
    st.title("🚀 Gerador de Ofertas IA")
    st.caption("Crie posts profissionais com link de afiliado e imagem automática.")

    with st.sidebar:
        st.header("Configurações")
        if st.button("Sair"):
            st.session_state.logado = False
            st.rerun()

    # Form de Entrada
    with st.container():
        link_orig = st.text_input("🔗 Link Original do Produto:")
        col1, col2 = st.columns(2)
        with col1:
            loja = st.selectbox("🏪 Loja:", ["Amazon", "Magalu", "Shopee", "Mercado Livre", "Outra"])
        with col2:
            img_fix = st.text_input("🖼️ URL da Imagem (Manual):", placeholder="Opcional")

        detalhes = st.text_area("📝 Preço e Detalhes da Oferta:", placeholder="Ex: De R$ 299 por R$ 149 em 10x")

    if st.button("✨ GERAR PROMOÇÃO"):
        if not link_orig:
            st.warning("Insira o link do produto!")
        else:
            with st.spinner("Construindo oferta mágica..."):
                # 1. Gerar Link de Afiliado
                link_promo = limpar_e_gerar_link(link_orig, loja)
                
                # 2. Buscar Imagem
                st.session_state.imagem_url = img_fix if img_fix else pegar_imagem(link_orig)

                # 3. Chamar IA (Correção do Erro 404)
                try:
                    key = st.secrets["GEMINI_KEY"].strip().replace('"', '')
                    genai.configure(api_key=key)
                    
                    # Usando a chamada de modelo mais robusta disponível
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    Atue como copywriter de vendas. Crie um post para Telegram.
                    Produto: {detalhes}
                    Link: {link_promo}
                    REGRAS:
                    - Use emojis e negritos.
                    - Link deve estar no final com 'COMPRE AQUI'.
                    - Não invente informações.
                    """
                    response = model.generate_content(prompt)
                    st.session_state.texto_pronto = response.text
                except Exception as e:
                    st.error(f"Nota: IA em manutenção. Gerando texto padrão. Erro: {e}")
                    st.session_state.texto_pronto = f"🔥 **OFERTA IMPERDÍVEL**\n\n{detalhes}\n\n🛒 **COMPRE AQUI:** {link_promo}"

    # --- RESULTADO E ENVIO ---
    if st.session_state.texto_pronto:
        st.divider()
        if st.session_state.imagem_url:
            st.image(st.session_state.imagem_url, width=300)
        
        post_final = st.text_area("Edite seu post:", value=st.session_state.texto_pronto, height=250)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Postar no Telegram"):
                try:
                    t = st.secrets["TELEGRAM_TOKEN"]
                    c = st.secrets["TELEGRAM_CHAT_ID"]
                    if st.session_state.imagem_url:
                        res = requests.post(f"https://api.telegram.org/bot{t}/sendPhoto", 
                                           data={"chat_id": c, "photo": st.session_state.imagem_url, "caption": post_final, "parse_mode": "Markdown"})
                    else:
                        res = requests.post(f"https://api.telegram.org/bot{t}/sendMessage", 
                                           data={"chat_id": c, "text": post_final, "parse_mode": "Markdown"})
                    if res.status_code == 200: st.success("✅ Postado!")
                    else: st.error("Erro no envio.")
                except: st.error("Verifique os Tokens do Telegram.")
        
        with c2:
            enc = urllib.parse.quote(post_final)
            st.link_button("💬 Enviar no WhatsApp", f"https://api.whatsapp.com/send?text={enc}")