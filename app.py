import streamlit as st
from supabase import create_client, Client

# Configuração da página em modo amplo
st.set_page_config(page_title="Chat Corporativo", page_icon="💬", layout="wide")

# 1. CONEXÃO COM O SUPABASE (com suporte ao novo formato de chave sb_publishable_)
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    # Passa a chave nos cabeçalhos padrão do Supabase
    headers = {
        "apiKey": key,
        "Authorization": f"Bearer {key}"
    }
    return create_client(url, key, options={"headers": headers})

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"⚠️ Erro na inicialização: {e}")
    st.stop()

# 2. PALETAS DE CORES (5 OPÇÕES)
PALETAS = {
    "🟢 Escuro Padrão (WhatsApp)": {
        "bg_app": "#0b141a", "bg_sidebar": "#111b21", "bg_msg": "#202c33", "primary": "#00a884", "text": "#e9edef"
    },
    "🔵 Azul Corporativo (Slack)": {
        "bg_app": "#0f172a", "bg_sidebar": "#1e293b", "bg_msg": "#334155", "primary": "#3b82f6", "text": "#f8fafc"
    },
    "🟣 Roxo Noturno (Discord)": {
        "bg_app": "#18181b", "bg_sidebar": "#27272a", "bg_msg": "#3f3f46", "primary": "#a855f7", "text": "#fafafa"
    },
    "🟠 Grafite & Laranja": {
        "bg_app": "#121212", "bg_sidebar": "#1e1e1e", "bg_msg": "#2d2d2d", "primary": "#f97316", "text": "#f3f4f6"
    },
    "⚪ Claro Corporativo": {
        "bg_app": "#f8fafc", "bg_sidebar": "#f1f5f9", "bg_msg": "#ffffff", "primary": "#0284c7", "text": "#0f172a"
    }
}

# 3. SELETOR DE TEMAS
st.sidebar.title("🎨 Personalização")
tema_escolhido = st.sidebar.selectbox("Escolha o tema visual:", list(PALETAS.keys()))
p = PALETAS[tema_escolhido]

# 4. APLICAÇÃO DE CSS DINÂMICO
st.markdown(f"""
    <style>
        .stApp {{ background-color: {p['bg_app']} !important; color: {p['text']} !important; }}
        [data-testid="stSidebar"] {{ background-color: {p['bg_sidebar']} !important; border-right: 1px solid rgba(255, 255, 255, 0.1); }}
        [data-testid="stSidebar"] * {{ color: {p['text']} !important; }}
        [data-testid="stChatMessage"] {{ background-color: {p['bg_msg']} !important; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; color: {p['text']} !important; }}
        [data-testid="stChatMessage"] * {{ color: {p['text']} !important; }}
        .stButton button {{ background-color: {p['primary']} !important; color: #ffffff !important; border: none !important; border-radius: 6px; }}
        h1, h2, h3, p, span {{ color: {p['text']} !important; }}
        .stChatInputContainer textarea {{ background-color: {p['bg_msg']} !important; color: {p['text']} !important; }}
    </style>
""", unsafe_allow_html=True)

# 5. GERENCIAMENTO DE IDENTIDADE DO USUÁRIO
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""

st.sidebar.divider()
st.sidebar.title("👤 Identificação")
nome_input = st.sidebar.text_input("Seu nome e setor:", value=st.session_state["usuario_nome"], placeholder="Ex: Carlos (Licitação)")

if nome_input:
    st.session_state["usuario_nome"] = nome_input
else:
    st.sidebar.warning("Digite seu nome acima para poder enviar mensagens.")

# 6. CARREGAMENTO DOS CANAIS DO SUPABASE
st.sidebar.divider()
st.sidebar.title("🏢 Canais por Setor")

def obter_canais():
    res = supabase.table("canais").select("*").order("id").execute()
    return res.data

try:
    lista_canais = obter_canais()
    if not lista_canais:
        st.sidebar.warning("Nenhum canal encontrado na tabela 'canais'.")
        st.stop()
        
    mapa_canais = {f"{c['icone']} #{c['nome']}": c['id'] for c in lista_canais}
    canal_selecionado = st.sidebar.radio("Selecione a sala:", list(mapa_canais.keys()))
    canal_id = mapa_canais[canal_selecionado]
except Exception as e:
    st.sidebar.error(f"Erro ao conectar com o Supabase: {e}")
    st.stop()

# 7. INTERFACE PRINCIPAL (CHAT E TAREFAS)
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(f"Conversa em {canal_selecionado}")
    
    # Buscar histórico de mensagens no Supabase
    mensagens_res = supabase.table("mensagens").select("*").eq("canal_id", canal_id).order("criado_em", desc=False).execute()
    mensagens = mensagens_res.data

    # Exibir histórico
    for msg in mensagens:
        is_me = msg['usuario_nome'] == st.session_state["usuario_nome"]
        avatar = "🟢" if is_me else "👤"
        with st.chat_message("user", avatar=avatar):
            st.markdown(f"**{msg['usuario_nome']}**")
            st.write(msg['texto'])

    # Envio de nova mensagem
    if prompt := st.chat_input(f"Enviar mensagem em {canal_selecionado}..."):
        if not st.session_state["usuario_nome"]:
            st.warning("Por favor, preencha seu nome na barra lateral antes de enviar uma mensagem.")
        else:
            nova_msg = {
                "canal_id": canal_id,
                "usuario_nome": st.session_state["usuario_nome"],
                "texto": prompt
            }
            supabase.table("mensagens").insert(nova_msg).execute()
            st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas do Setor")
    
    # Buscar tarefas pendentes do setor
    tarefas_res = supabase.table("tarefas").select("*").eq("canal_id", canal_id).order("id", desc=True).execute()
    tarefas = tarefas_res.data
    
    for tarefa in tarefas:
        with st.container(border=True):
            status_cor = "🟢" if tarefa['status'] == "Concluído" else "⏳"
            st.markdown(f"{status_cor} **{tarefa['status']}**")
            st.write(tarefa['titulo'])
            st.caption(f"Atribuído a: {tarefa.get('atribuido_a', 'Geral')}")
            
            if tarefa['status'] != "Concluído":
                if st.button("Marcar Concluída", key=f"t_{tarefa['id']}"):
                    supabase.table("tarefas").update({"status": "Concluído"}).eq("id", tarefa['id']).execute()
                    st.rerun()

    # Adicionar nova tarefa
    with st.expander("+ Criar Nova Tarefa"):
        nova_tarefa_titulo = st.text_input("Descrição da tarefa:")
        responsavel = st.text_input("Atribuir a:", placeholder="Ex: Ana / Compras")
        if st.button("Salvar Tarefa"):
            if nova_tarefa_titulo:
                supabase.table("tarefas").insert({
                    "canal_id": canal_id,
                    "titulo": nova_tarefa_titulo,
                    "atribuido_a": responsavel,
                    "status": "Pendente"
                }).execute()
                st.rerun()
