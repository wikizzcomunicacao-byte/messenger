import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Configuração da página
st.set_page_config(page_title="Senhora Lavanderia", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# 1. CONEXÃO COM SUPABASE
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

# 2. FUNÇÕES AUXILIARES
def registrar_log(uid, nome, setor, acao, detalhes=""):
    try: supabase.table("logs_acesso").insert({"usuario_id": uid, "usuario_nome": nome, "setor": setor, "acao": acao, "detalhes": detalhes}).execute()
    except: pass

def buscar_usuarios():
    return supabase.table("usuarios").select("*").order("nome").execute().data

# 3. SESSÃO E LOGIN
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

fuso_brasilia = timezone(timedelta(hours=-3))

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

# 4. APP LIBERADO
usuario_atual = st.session_state["usuario_logado"]
p_escolhida = {"primary": "#00a884"} # Pode integrar o seletor de temas aqui

st.sidebar.title(f"👤 {usuario_atual['nome']}")
if st.sidebar.button("🚪 Sair"):
    st.session_state["autenticado"] = False
    st.rerun()

tipo_chat = st.sidebar.radio("Navegação:", ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)", "⚙️ Admin"])

# 5. LÓGICA DE CANAIS/DMS
if tipo_chat == "🏢 Canais de Setor":
    canais = supabase.table("canais").select("*").execute().data
    mapa_canais = {f"{c['icone']} #{c['nome']}": c for c in canais}
    sel = st.sidebar.radio("Canal:", list(mapa_canais.keys()))
    canal_id = mapa_canais[sel]['id']
    titulo = f"#{mapa_canais[sel]['nome']}"
else:
    # Lógica de DM e Admin omitida para brevidade, mantenha a sua anterior
    pass

# 6. INTERFACE DE CHAT COM ST.CHAT_INPUT
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo)
    @st.fragment(run_every=3)
    def renderizar_mensagens():
        # Lógica de busca de mensagens (Canais ou DMs)
        msgs = supabase.table("mensagens").select("*").eq("canal_id", canal_id).order("criado_em").execute().data
        for msg in msgs:
            is_me = msg['usuario_nome'] == usuario_atual['nome']
            hora = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00")).astimezone(fuso_brasilia).strftime("%H:%M")
            
            with st.chat_message("user", avatar="🟢" if is_me else "👤"):
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{msg['usuario_nome']}**")
                c2.caption(hora)
                st.write(msg['texto'])
                if not is_me: st.caption("✔️ Visualizado")
                
                if usuario_atual.get("eh_admin"):
                    if st.button("🗑️", key=f"del_{msg['id']}"):
                        supabase.table("mensagens").delete().eq("id", msg['id']).execute()
                        st.rerun()

    renderizar_mensagens()
    
    # ENTRADA DE TEXTO INTUITIVA
    prompt = st.chat_input("Digite sua mensagem e aperte Enter...")
    if prompt:
        supabase.table("mensagens").insert({
            "canal_id": canal_id,
            "usuario_nome": usuario_atual['nome'],
            "texto": prompt
        }).execute()
        st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas")
    # Lógica de tarefas (Expanders, checkbox, etc)
    tarefas = supabase.table("tarefas").select("*").eq("canal_id", canal_id).execute().data
    for t in tarefas:
        st.info(f"{t['titulo']} - {t['status']}")
