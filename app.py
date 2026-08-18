import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Configuração da página
st.set_page_config(page_title="Senhora Lavanderia", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

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

# FUSO HORÁRIO
fuso_brasilia = timezone(timedelta(hours=-3))

# 2. SESSÃO E LOGIN
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

def registrar_log(uid, nome, setor, acao):
    try: supabase.table("logs_acesso").insert({"usuario_id": uid, "usuario_nome": nome, "setor": setor, "acao": acao}).execute()
    except: pass

if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Login - Senhora Lavanderia</h2>", unsafe_allow_html=True)
    usuarios = supabase.table("usuarios").select("*").order("nome").execute().data
    mapa_usuarios = {f"{u['nome']} ({u['setor']})": u for u in usuarios}
    usuario_sel = st.selectbox("Selecione seu perfil:", list(mapa_usuarios.keys()))
    senha = st.text_input("Sua senha:", type="password")
    if st.button("Entrar"):
        dados = mapa_usuarios[usuario_sel]
        if senha == dados.get("senha", "123456"):
            st.session_state["autenticado"] = True
            st.session_state["usuario_logado"] = dados
            st.rerun()
    st.stop()

# APP LIBERADO
usuario_atual = st.session_state["usuario_logado"]

# CSS E SIDEBAR
st.markdown("""<style>[data-testid="stSidebarCollapseButton"]{display:none;}</style>""", unsafe_allow_html=True)
st.sidebar.title(f"👤 {usuario_atual['nome']}")
if st.sidebar.button("🚪 Sair"):
    st.session_state["autenticado"] = False
    st.rerun()

tipo_chat = st.sidebar.radio("Navegação:", ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)"])

# LÓGICA DE CANAIS/DMS
if tipo_chat == "🏢 Canais de Setor":
    canais = supabase.table("canais").select("*").execute().data
    mapa_canais = {f"{c['icone']} #{c['nome']}": c for c in canais}
    sel = st.sidebar.radio("Canal:", list(mapa_canais.keys()))
    canal_id = mapa_canais[sel]['id']
    titulo = f"#{mapa_canais[sel]['nome']}"
else:
    usuarios_todos = supabase.table("usuarios").select("*").neq("id", usuario_atual['id']).execute().data
    mapa_dms = {f"👤 {u['nome']}": u for u in usuarios_todos}
    sel = st.sidebar.selectbox("Falar com:", list(mapa_dms.keys()))
    destinatario = mapa_dms[sel]
    titulo = f"Conversa com {destinatario['nome']}"

# CHAT E TAREFAS
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo)
    @st.fragment(run_every=2)
    def renderizar():
        if tipo_chat == "🏢 Canais de Setor":
            msgs = supabase.table("mensagens").select("*").eq("canal_id", canal_id).order("criado_em").execute().data
        else:
            res1 = supabase.table("mensagens").select("*").eq("usuario_nome", usuario_atual['nome']).eq("destinatario_id", destinatario['id']).execute().data
            res2 = supabase.table("mensagens").select("*").eq("usuario_nome", destinatario['nome']).eq("destinatario_id", usuario_atual['id']).execute().data
            msgs = sorted(res1 + res2, key=lambda x: x['criado_em'])
        
        for msg in msgs:
            is_me = msg['usuario_nome'] == usuario_atual['nome']
            hora = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00")).astimezone(fuso_brasilia).strftime("%H:%M")
            with st.chat_message("user", avatar="🟢" if is_me else "👤"):
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{msg['usuario_nome']}**")
                c2.caption(hora)
                st.write(msg['texto'])
                if not is_me: st.caption("✔️ Visualizado")
    
    renderizar()
    
    # INPUT INTUITIVO (ENTER PARA ENVIAR)
    prompt = st.chat_input("Digite sua mensagem...")
    if prompt:
        supabase.table("mensagens").insert({
            "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" else None,
            "usuario_nome": usuario_atual['nome'],
            "texto": prompt,
            "destinatario_id": destinatario['id'] if tipo_chat != "🏢 Canais de Setor" else None
        }).execute()
        st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas")
    # Lógica de tarefas simplificada
    if st.expander("+ Nova Tarefa"):
        t_titulo = st.text_input("Tarefa:")
        if st.button("Salvar"):
            supabase.table("tarefas").insert({"canal_id": canal_id if tipo_chat=="🏢 Canais de Setor" else 1, "titulo": t_titulo, "status": "Pendente"}).execute()
            st.rerun()
    
    tarefas = supabase.table("tarefas").select("*").execute().data
    for t in tarefas:
        st.info(f"{t['titulo']} - {t['status']}")
