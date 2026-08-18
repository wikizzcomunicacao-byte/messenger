import streamlit as st

# Configuração da página
st.set_page_config(page_title="Chat Corporativo", page_icon="💬", layout="wide")

# 1. DICIONÁRIO DE PALETAS DE CORES (5 Opções)
PALETAS = {
    "🟢 Escuro Padrão (WhatsApp)": {
        "bg_app": "#0b141a",
        "bg_sidebar": "#111b21",
        "bg_msg": "#202c33",
        "primary": "#00a884",
        "text": "#e9edef"
    },
    "🔵 Azul Corporativo (Slack)": {
        "bg_app": "#0f172a",
        "bg_sidebar": "#1e293b",
        "bg_msg": "#334155",
        "primary": "#3b82f6",
        "text": "#f8fafc"
    },
    "🟣 Roxo Noturno (Discord)": {
        "bg_app": "#18181b",
        "bg_sidebar": "#27272a",
        "bg_msg": "#3f3f46",
        "primary": "#a855f7",
        "text": "#fafafa"
    },
    "🟠 Grafite & Laranja": {
        "bg_app": "#121212",
        "bg_sidebar": "#1e1e1e",
        "bg_msg": "#2d2d2d",
        "primary": "#f97316",
        "text": "#f3f4f6"
    },
    "⚪ Claro Corporativo": {
        "bg_app": "#f8fafc",
        "bg_sidebar": "#f1f5f9",
        "bg_msg": "#ffffff",
        "primary": "#0284c7",
        "text": "#0f172a"
    }
}

# 2. SELETOR DE TEMAS NA BARRA LATERAL
st.sidebar.title("🎨 Visual")
tema_escolhido = st.sidebar.selectbox("Selecione a paleta de cores:", list(PALETAS.keys()))
p = PALETAS[tema_escolhido]

# 3. CSS DINÂMICO APLICADO
st.markdown(f"""
    <style>
        /* Fundo principal e texto */
        .stApp {{
            background-color: {p['bg_app']} !important;
            color: {p['text']} !important;
        }}

        /* Barra Lateral */
        [data-testid="stSidebar"] {{
            background-color: {p['bg_sidebar']} !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        [data-testid="stSidebar"] * {{
            color: {p['text']} !important;
        }}

        /* Mensagens do Chat */
        [data-testid="stChatMessage"] {{
            background-color: {p['bg_msg']} !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: {p['text']} !important;
        }}
        [data-testid="stChatMessage"] * {{
            color: {p['text']} !important;
        }}

        /* Botões com a cor primária */
        .stButton button {{
            background-color: {p['primary']} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px;
        }}

        /* Destaque nos títulos */
        h1, h2, h3, p, span {{
            color: {p['text']} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. CONTEÚDO DO APLICATIVO
st.sidebar.divider()
st.sidebar.title("🏢 Canais da Empresa")

canais = [
    "📢 #geral",
    "💊 #farmaceutica (1)",
    "🛒 #compras (2)",
    "📦 #faturamento-pedidos (4)",
    "📋 #licitacao (5)",
    "💰 #financeiro (2)",
    "🏭 #estoque (3)",
    "🏷️ #cotacao (2)",
    "🌐 #loja-online (2)"
]

canal_atual = st.sidebar.radio("Selecione o setor:", canais)
st.sidebar.divider()
st.sidebar.caption("👤 Logado como: **Administrador**")

# Área Principal
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(f"Conversa em {canal_atual}")
    st.caption("Mensagens internas criptografadas")
    
    with st.chat_message("user", avatar="👤"):
        st.markdown("**Carlos (Licitação)**")
        st.write("Alguém do estoque pode verificar a quantidade do item X?")

    if prompt := st.chat_input(f"Enviar mensagem em {canal_atual}..."):
        with st.chat_message("user", avatar="🟢"):
            st.markdown("**Você**")
            st.write(prompt)

with col_tarefas:
    st.subheader("📋 Tarefas Pendentes")
    
    with st.container(border=True):
        st.markdown("⏳ **Pendente**")
        st.write("Verificar edital nº 04/2026")
        st.caption("Atribuído a: Equipe de Licitação")
        st.button("Marcar como Concluída", key="t1")
        
    if st.button("+ Criar Nova Tarefa", use_container_width=True):
        st.info("Formulário de criação de tarefa")
