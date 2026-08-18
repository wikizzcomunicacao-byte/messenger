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

# 2. FUNÇÃO DE REGISTRO DE LOGS DE AUDITORIA
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

# 3. GERENCIAMENTO DE SESSÃO / LOGIN
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

def buscar_usuarios():
    res = supabase.table("usuarios").select("*").order("nome").execute()
    return res.data

# FUSO HORÁRIO DE BRASÍLIA (UTC-3 Fixo)
fuso_brasilia = timezone(timedelta(hours=-3))

# TELA DE LOGIN COM RESTRIÇÃO DE HORÁRIO DE EXPEDIENTE
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Login - Senhora Lavanderia</h2>", unsafe_allow_html=True)
    
    agora_local = datetime.now(fuso_brasilia)
    hora_atual = agora_local.hour
    dia_semana = agora_local.weekday()
    
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
                eh_admin = dados_usuario.get("eh_admin", False)
                hora_inicio = dados_usuario.get("hora_inicio_expediente", 7)
                hora_fim = dados_usuario.get("hora_fim_expediente", 19)

                fora_do_expediente = (hora_atual < hora_inicio or hora_atual >= hora_fim or dia_semana >= 5)

                if fora_do_expediente and not eh_admin:
                    st.error(f"⏰ Acesso negado! Seu expediente é das {hora_inicio}h às {hora_fim}h.")
                elif senha_input == dados_usuario.get("senha", "123456"):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = dados_usuario
                    registrar_log(dados_usuario['id'], dados_usuario['nome'], dados_usuario['setor'], "LOGIN", f"Login às {agora_local.strftime('%H:%M')}")
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
    st.stop()

# ---------------------------------------------------------
# APLICATIVO LIBERADO APÓS LOGIN
# ---------------------------------------------------------
usuario_atual = st.session_state["usuario_logado"]
todos_usuarios = buscar_usuarios()

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
st.sidebar.markdown("**📅 Seu Expediente:**")
st.sidebar.caption(f"Das {usuario_atual.get('hora_inicio_expediente', 7)}h às {usuario_atual.get('hora_fim_expediente', 19)}h")

if usuario_atual.get("eh_admin"):
    st.sidebar.success("👑 Administrador do Sistema")

if st.sidebar.button("🚪 Sair / Logoff", use_container_width=True):
    registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "LOGOFF", "Encerrou a sessão")
    st.session_state["autenticado"] = False
    st.session_state["usuario_logado"] = None
    st.rerun()

# CONFIGURAÇÃO DE SILENCIAMENTO
st.sidebar.divider()
st.sidebar.title("⏰ Status")
modo_silencioso = st.sidebar.checkbox("🔕 Modo Não Perturbe", value=usuario_atual.get("modo_silencioso", False))

# TEMAS
st.sidebar.divider()
st.sidebar.title("🎨 Personalização")
tema_escolhido = st.sidebar.selectbox("Escolha o tema visual:", list(PALETAS.keys()))
p = PALETAS[tema_escolhido]

# CSS
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
        
        div[data-testid="stForm"] div[data-testid="horizontal-block"] {{
            display: flex;
            align-items: center;
            flex-wrap: nowrap;
        }}
        
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# NAVEGAÇÃO
opcoes_modo = ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)"]
if usuario_atual.get("eh_admin"):
    opcoes_modo.append("⚙️ Painel de Gestão (Admin)")
    opcoes_modo.append("📊 Relatórios e Logs (Admin)")

tipo_chat = st.sidebar.radio("Modo de Navegação:", opcoes_modo)

# INTERFACE DE CHAT (LÓGICA SEM COMUNICADOS)
if tipo_chat == "🏢 Canais de Setor":
    # ... (lógica de canais mantida igual)
    def obter_canais():
        res = supabase.table("canais").select("*").order("id").execute()
        return res.data
    
    lista_canais = obter_canais()
    mapa_canais = {f"{c['icone']} #{c['nome']}": c for c in lista_canais}
    canal_nome_sel = st.sidebar.radio("Selecione o canal:", list(mapa_canais.keys()))
    obj_canal = mapa_canais[canal_nome_sel]
    canal_id = obj_canal['id']
    titulo_chat = f"Conversa em #{obj_canal['nome']}"
else:
    # ... (lógica de DMs mantida igual)
    outros_usuarios = [u for u in todos_usuarios if u['id'] != usuario_atual['id']]
    mapa_dms = {f"👤 {u['nome']} ({u['setor']})": u for u in outros_usuarios}
    usuario_dm_selecionado = st.sidebar.selectbox("Mandar mensagem para:", list(mapa_dms.keys()))
    destinatario = mapa_dms[usuario_dm_selecionado]
    titulo_chat = f"Conversa Privada com {destinatario['nome']}"

# COLUNAS CHAT / TAREFAS
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo_chat)
    nome_formatado_logado = f"{usuario_atual['nome']} ({usuario_atual['setor']})"

    @st.fragment(run_every=3)
    def renderizar_mensagens():
        # Busca mensagens
        if tipo_chat == "🏢 Canais de Setor":
            msgs = supabase.table("mensagens").select("*").eq("canal_id", canal_id).order("criado_em", desc=False).execute().data
        else:
            res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", destinatario['id']).execute().data
            res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{destinatario['nome']} ({destinatario['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data
            msgs = sorted(res1 + res2, key=lambda x: x['criado_em'])

        for msg in msgs:
            is_me = msg['usuario_nome'] == nome_formatado_logado
            
            hora_formatada = ""
            if msg.get("criado_em"):
                dt_local = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00")).astimezone(fuso_brasilia)
                hora_formatada = dt_local.strftime("%H:%M")

            with st.chat_message("user", avatar="🟢" if is_me else "👤"):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{msg['usuario_nome']}**")
                with col2:
                    st.markdown(f"<div style='text-align: right; color: gray; font-size: 0.85em;'>{hora_formatada}</div>", unsafe_allow_html=True)
                
                st.write(msg['texto'])
                
                # Indicador automático de "Lido" para todas as mensagens que não são suas
                if not is_me:
                    st.markdown("<div style='text-align: right; font-size: 0.7em; color: #0284c7;'>✔️ Visualizado</div>", unsafe_allow_html=True)

                if usuario_atual.get("eh_admin"):
                    if st.button("🗑️", key=f"del_{msg['id']}"):
                        supabase.table("mensagens").delete().eq("id", msg["id"]).execute()
                        st.rerun()

    renderizar_mensagens()

    # Form de Envio Limpo
    st.divider()
    with st.form(key="form_envio_msg", clear_on_submit=True):
        col_i, col_c, col_b = st.columns([6, 1, 1])
        with col_i:
            prompt = st.text_input("Mensagem", placeholder="Digite sua mensagem...", key="input_texto_msg", label_visibility="collapsed")
        with col_c:
            arquivo = st.file_uploader("📎", type=["png", "jpg", "pdf"], key="up_f", label_visibility="collapsed")
        with col_b:
            btn = st.form_submit_button("🚀", use_container_width=True)

    if btn and (prompt or arquivo):
        # Lógica de inserção no Supabase (omitida por brevidade, idêntica à anterior)
        supabase.table("mensagens").insert({
            "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" else None,
            "usuario_nome": nome_formatado_logado,
            "texto": prompt,
            "destinatario_id": destinatario['id'] if tipo_chat != "🏢 Canais de Setor" else None
        }).execute()
        st.rerun()
