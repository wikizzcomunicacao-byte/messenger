import streamlit as st
from supabase import create_client, Client

# Configuração da página
st.set_page_config(page_title="Chat Corporativo", page_icon="💬", layout="wide")

# 1. CONEXÃO COM O SUPABASE
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Erro de conexão com o Supabase.")
    st.stop()

# 2. GERENCIAMENTO DE SESSÃO / LOGIN
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

def buscar_usuarios():
    res = supabase.table("usuarios").select("*").order("nome").execute()
    return res.data

# TELA DE LOGIN
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Login - Chat Corporativo</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuarios = buscar_usuarios()
            mapa_usuarios = {f"{u['nome']} ({u['setor']})": u for u in usuarios}
            
            usuario_selecionado = st.selectbox("Selecione seu perfil:", list(mapa_usuarios.keys()))
            senha_input = st.text_input("Sua senha:", type="password")
            
            btn_entrar = st.form_submit_button("Entrar no Chat", use_container_width=True)
            
            if btn_entrar:
                dados_usuario = mapa_usuarios[usuario_selecionado]
                if senha_input == dados_usuario.get("senha", "123456"):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = dados_usuario
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
    st.stop()

# ---------------------------------------------------------
# APLICATIVO LIBERADO APÓS LOGIN
# ---------------------------------------------------------
usuario_atual = st.session_state["usuario_logado"]

# PALETAS DE CORES
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

# BARRA LATERAL - PERFIL
st.sidebar.title("👤 Perfil Conectado")
st.sidebar.markdown(f"**{usuario_atual['nome']}**")
st.sidebar.caption(f"Setor: {usuario_atual['setor']}")

if st.sidebar.button("🚪 Sair / Logoff", use_container_width=True):
    st.session_state["autenticado"] = False
    st.session_state["usuario_logado"] = None
    st.rerun()

# TEMAS
st.sidebar.divider()
st.sidebar.title("🎨 Personalização")
tema_escolhido = st.sidebar.selectbox("Escolha o tema visual:", list(PALETAS.keys()))
p = PALETAS[tema_escolhido]

# CSS DINÂMICO
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

# TIPO DE CONVERSA (CANAL OU MENSAGEM DIRETA)
st.sidebar.divider()
tipo_chat = st.sidebar.radio("Modo de Conversa:", ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)"])

canal_id = None
destinatario = None

if tipo_chat == "🏢 Canais de Setor":
    def obter_canais():
        res = supabase.table("canais").select("*").order("id").execute()
        return res.data
    
    lista_canais = obter_canais()
    mapa_canais = {f"{c['icone']} #{c['nome']}": c['id'] for c in lista_canais}
    canal_selecionado = st.sidebar.radio("Selecione o canal:", list(mapa_canais.keys()))
    canal_id = mapa_canais[canal_selecionado]
    titulo_chat = f"Conversa em {canal_selecionado}"

else:
    todos_usuarios = buscar_usuarios()
    # Filtrar para não listar o próprio usuário logado
    outros_usuarios = [u for u in todos_usuarios if u['id'] != usuario_atual['id']]
    mapa_dms = {f"👤 {u['nome']} ({u['setor']})": u for u in outros_usuarios}
    
    usuario_dm_selecionado = st.sidebar.selectbox("Mandar mensagem para:", list(mapa_dms.keys()))
    destinatario = mapa_dms[usuario_dm_selecionado]
    titulo_chat = f"Conversa Privada com {destinatario['nome']}"

# INTERFACE PRINCIPAL
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo_chat)
    nome_formatado_logado = f"{usuario_atual['nome']} ({usuario_atual['setor']})"

    if tipo_chat == "🏢 Canais de Setor":
        # Buscar mensagens do canal
        mensagens_res = supabase.table("mensagens").select("*").eq("canal_id", canal_id).is_("destinatario_id", "null").order("criado_em", desc=False).execute()
        mensagens = mensagens_res.data
    else:
        # Buscar mensagens privadas trocadas entre os dois usuários
        # Mensagens de mim para ele OU dele para mim
        res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", destinatario['id']).execute().data
        res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{destinatario['nome']} ({destinatario['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data
        
        # Junta e ordena por data
        mensagens = sorted(res1 + res2, key=lambda x: x['criado_em'])

    # Exibir histórico de mensagens
    for msg in mensagens:
        is_me = msg['usuario_nome'] == nome_formatado_logado
        avatar = "🟢" if is_me else "👤"
        with st.chat_message("user", avatar=avatar):
            st.markdown(f"**{msg['usuario_nome']}**")
            st.write(msg['texto'])

    # Enviar mensagem
    if prompt := st.chat_input("Digite sua mensagem..."):
        if tipo_chat == "🏢 Canais de Setor":
            nova_msg = {
                "canal_id": canal_id,
                "usuario_nome": nome_formatado_logado,
                "texto": prompt,
                "destinatario_id": None
            }
        else:
            nova_msg = {
                "canal_id": 1, # Canal geral padrão para DMs
                "usuario_nome": nome_formatado_logado,
                "texto": prompt,
                "destinatario_id": destinatario['id']
            }
        supabase.table("mensagens").insert(nova_msg).execute()
        st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas")
    
    # Exibir tarefas do setor se estiver em canal, ou tarefas gerais se em DM
    c_id_tarefa = canal_id if canal_id else 1
    tarefas_res = supabase.table("tarefas").select("*").eq("canal_id", c_id_tarefa).order("id", desc=True).execute()
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

    with st.expander("+ Criar Nova Tarefa"):
        nova_tarefa_titulo = st.text_input("Descrição da tarefa:")
        responsavel = st.text_input("Atribuir a:", placeholder="Ex: Ana / Compras")
        if st.button("Salvar Tarefa"):
            if nova_tarefa_titulo:
                supabase.table("tarefas").insert({
                    "canal_id": c_id_tarefa,
                    "titulo": nova_tarefa_titulo,
                    "atribuido_a": responsavel,
                    "status": "Pendente"
                }).execute()
                st.rerun()
