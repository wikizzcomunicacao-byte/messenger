import streamlit as st

# Configuração da página em modo estendido
st.set_page_config(page_title="Chat Corporativo", page_icon="💬", layout="wide")

# CSS Otimizado para Tema Escuro de Alto Contraste
st.markdown("""
    <style>
        /* Fundo do aplicativo */
        .stApp {
            background-color: #0b141a;
            color: #e9edef;
        }

        /* Estilização dos textos do menu lateral */
        [data-testid="stSidebar"] {
            background-color: #111b21 !important;
            border-right: 1px solid #222d34;
        }
        [data-testid="stSidebar"] * {
            color: #e9edef !important;
        }

        /* Balões das mensagens */
        [data-testid="stChatMessage"] {
            background-color: #202c33 !important;
            border: 1px solid #2a3942;
            border-radius: 8px;
            color: #e9edef !important;
        }
        [data-testid="stChatMessage"] * {
            color: #e9edef !important;
        }

        /* Caixa de digitação */
        .stChatInputContainer textarea {
            background-color: #2a3942 !important;
            color: #ffffff !important;
        }

        /* Cartões de Tarefas */
        div[data-testid="stContainer"] {
            background-color: #1f2c33 !important;
            border: 1px solid #2a3942 !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# 1. LATERAL: Seleção de Canais
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

# 2. ÁREA PRINCIPAL
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
