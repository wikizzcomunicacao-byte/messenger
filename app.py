import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import pytz

# Configuração da página - Barra lateral fixa
st.set_page_config(
    page_title="Senhora Lavanderia", 
    page_icon="💬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. CONEXÃO COM O SUPABASE
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets.get("SUPABASE_SERVICE_KEY", st.secrets["SUPABASE_KEY"])
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Erro de conexão com o Supabase.")
    st.stop()

# 2. FUNÇÃO DE REGISTRO DE LOGS
def registrar_log(usuario_id, usuario_nome, setor, acao, detalhes=""):
    try:
        supabase.table("logs_acesso").insert({
            "usuario_id": usuario_id,
            "usuario_nome": usuario_nome,
            "setor": setor,
            "acao": acao,
            "detalhes": detalhes
        }).execute()
    except Exception:
        pass

# 3. GERENCIAMENTO DE SESSÃO
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None
if "uploader_key" not in st.session_state: st.session_state["uploader_key"] = 0

def buscar_usuarios():
    return supabase.table("usuarios").select("*").order("nome").execute().data

fuso_brasilia = timezone(timedelta(hours=-3))

# TELA DE LOGIN
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Login - Senhora Lavanderia</h2>", unsafe_allow_html=True)
    usuarios = buscar_usuarios()
    mapa_usuarios = {f"{u['nome']} ({u['setor']})": u for u in usuarios}
    u_sel = st.selectbox("Selecione seu perfil:", list(mapa_usuarios.keys()))
    senha = st.text_input("Sua senha:", type="password")
    if st.button("Entrar"):
        dados = mapa_usuarios[u_sel]
        if senha == dados.get("senha", "123456"):
            st.session_state["autenticado"] = True
            st.session_state["usuario_logado"] = dados
            st.rerun()
    st.stop()

# APP LIBERADO
usuario_atual = st.session_state["usuario_logado"]
todos_usuarios = buscar_usuarios()

# SIDEBAR E TEMAS
st.sidebar.title(f"👤 {usuario_atual['nome']}")
if st.sidebar.button("🚪 Sair"):
    st.session_state["autenticado"] = False
    st.rerun()

tipo_chat = st.sidebar.radio("Navegação:", ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)", "⚙️ Admin", "📊 Relatórios"])

# CSS PARA LAYOUT
st.markdown("""<style>
    [data-testid="stSidebarCollapseButton"]{display:none;}
    .stChatMessage { border-radius: 8px; }
</style>""", unsafe_allow_html=True)

# LÓGICA DE CANAIS OU DMs
if tipo_chat == "🏢 Canais de Setor":
    canais = supabase.table("canais").select("*").execute().data
    mapa_canais = {f"{c['icone']} #{c['nome']}": c for c in canais}
    sel = st.sidebar.radio("Canal:", list(mapa_canais.keys()))
    canal_id = mapa_canais[sel]['id']
    titulo = f"#{mapa_canais[sel]['nome']}"
elif tipo_chat == "👤 Mensagens Diretas (DM)":
    outros = [u for u in todos_usuarios if u['id'] != usuario_atual['id']]
    mapa_dms = {f"👤 {u['nome']}": u for u in outros}
    sel_dm = st.sidebar.selectbox("Falar com:", list(mapa_dms.keys()))
    destinatario = mapa_dms[sel_dm]
    titulo = f"Conversa com {destinatario['nome']}"
    canal_id = None
else:
    # Lógica de Admin/Relatórios permanece aqui conforme anterior
    titulo = tipo_chat

# INTERFACE DE CHAT
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo)
    @st.fragment(run_every=2)
    def renderizar_mensagens():
        # Lógica de busca de mensagens (Canais ou DMs)
        if tipo_chat == "🏢 Canais de Setor":
            msgs = supabase.table("mensagens").select("*").eq("canal_id", canal_id).order("criado_em").execute().data
        elif tipo_chat == "👤 Mensagens Diretas (DM)":
            res1 = supabase.table("mensagens").select("*").eq("usuario_nome", usuario_atual['nome']).eq("destinatario_id", destinatario['id']).execute().data
            res2 = supabase.table("mensagens").select("*").eq("usuario_nome", destinatario['nome']).eq("destinatario_id", usuario_atual['id']).execute().data
            msgs = sorted(res1 + res2, key=lambda x: x['criado_em'])
        else:
            msgs = []
        
        for msg in msgs:
            is_me = msg['usuario_nome'] == usuario_atual['nome']
            hora = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00")).astimezone(fuso_brasilia).strftime("%H:%M")
            with st.chat_message("user", avatar="🟢" if is_me else "👤"):
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{msg['usuario_nome']}**")
                c2.caption(hora)
                st.write(msg['texto'])
                if msg.get("arquivo_url"):
                    st.link_button("📥 Baixar Arquivo", msg['arquivo_url'])
                if not is_me: st.caption("✔️ Visualizado")
                
                if usuario_atual.get("eh_admin"):
                    if st.button("🗑️ Apagar", key=f"del_{msg['id']}"):
                        supabase.table("mensagens").delete().eq("id", msg['id']).execute()
                        st.rerun()

    renderizar_mensagens()
    
    # CHAT INPUT INTUITIVO
    prompt = st.chat_input("Digite sua mensagem e aperte Enter...")
    if prompt:
        supabase.table("mensagens").insert({
            "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" else None,
            "usuario_nome": usuario_atual['nome'],
            "texto": prompt,
            "destinatario_id": destinatario['id'] if tipo_chat == "👤 Mensagens Diretas (DM)" else None
        }).execute()
        st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas")
    # Lógica de tarefas conforme anterior
    tarefas = supabase.table("tarefas").select("*").execute().data
    for t in tarefas:
        with st.container(border=True):
            st.write(f"**{t['titulo']}**")
            st.caption(f"Status: {t['status']}")
