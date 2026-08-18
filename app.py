import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Configuração da página - Barra lateral fixa
st.set_page_config(
    page_title="Chat Corporativo", 
    page_icon="💬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if usuario_atual.get("eh_admin"):
    st.sidebar.success("👑 Administrador do Sistema")

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
        
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# TIPO DE CONVERSA
st.sidebar.divider()
tipo_chat = st.sidebar.radio("Modo de Conversa:", ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)"])

canal_id = None
destinatario = None
membros_canal = []

if tipo_chat == "🏢 Canais de Setor":
    def obter_canais():
        res = supabase.table("canais").select("*").order("id").execute()
        return res.data
    
    lista_canais = obter_canais()
    mapa_canais = {f"{c['icone']} #{c['nome']}": c for c in lista_canais}
    canal_nome_sel = st.sidebar.radio("Selecione o canal:", list(mapa_canais.keys()))
    obj_canal = mapa_canais[canal_nome_sel]
    canal_id = obj_canal['id']
    canal_nome_limpo = obj_canal['nome']
    
    if canal_nome_limpo == "geral":
        membros_canal = todos_usuarios
    else:
        membros_canal = [u for u in todos_usuarios if u['setor'].lower() in canal_nome_limpo.lower()]
    
    st.sidebar.caption(f"👥 **Integrantes do Canal ({len(membros_canal)}):**")
    for m in membros_canal[:5]:
        st.sidebar.text(f"• {m['nome']}")
    if len(membros_canal) > 5:
        st.sidebar.caption(f"...e mais {len(membros_canal)-5} pessoas")
        
    titulo_chat = f"Conversa em {canal_nome_sel}"

else:
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

    # Buscar mensagens do canal ou DMs
    if tipo_chat == "🏢 Canais de Setor":
        mensagens_res = supabase.table("mensagens").select("*").eq("canal_id", canal_id).is_("destinatario_id", "null").order("criado_em", desc=False).execute()
        mensagens = mensagens_res.data
    else:
        res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", destinatario['id']).execute().data
        res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{destinatario['nome']} ({destinatario['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data
        mensagens = sorted(res1 + res2, key=lambda x: x['criado_em'])

    # EXIBIÇÃO E EXPIRAÇÃO DE MENSAGENS
    agora = datetime.now(timezone.utc)
    for msg in mensagens:
        # Verificar se mensagem temporária expirou
        if msg.get("tempo_expiracao_minutos"):
            criado_em = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00"))
            expira_em = criado_em + timedelta(minutes=msg["tempo_expiracao_minutos"])
            if agora > expira_em:
                supabase.table("mensagens").delete().eq("id", msg["id"]).execute()
                st.rerun()

        is_me = msg['usuario_nome'] == nome_formatado_logado
        avatar = "📢" if msg.get("eh_comunicado") else ("🟢" if is_me else "👤")
        
        with st.chat_message("user", avatar=avatar):
            if msg.get("eh_comunicado"):
                st.warning("📌 **COMUNICADO OFICIAL**")
            
            st.markdown(f"**{msg['usuario_nome']}**")
            st.write(msg['texto'])

            # Lógica do Comunicado Oficial (Restrita aos membros do setor)
            if msg.get("eh_comunicado"):
                leituras = msg.get("leituras_confirmadas") or []
                total_alvo = len(membros_canal) if membros_canal else len(todos_usuarios)
                
                ids_membros_canal = [m['id'] for m in membros_canal] if membros_canal else [u['id'] for u in todos_usuarios]
                eh_membro_do_setor = usuario_atual['id'] in ids_membros_canal

                if usuario_atual['id'] not in leituras:
                    if eh_membro_do_setor:
                        if st.button("✅ Confirmar Leitura / Estar Ciente", key=f"read_{msg['id']}"):
                            leituras.append(usuario_atual['id'])
                            supabase.table("mensagens").update({"leituras_confirmadas": leituras}).eq("id", msg['id']).execute()
                            st.rerun()
                    else:
                        st.caption("🔒 *Apenas colaboradores pertencentes a este setor podem confirmar leitura.*")
                else:
                    st.caption("✔️ Você já confirmou leitura deste comunicado.")
                
                st.progress(len(leituras) / max(total_alvo, 1))
                st.caption(f"📊 **Confirmações:** {len(leituras)} de {total_alvo} colaboradores do setor leram.")

            if msg.get("tempo_expiracao_minutos"):
                st.caption(f"⏱️ *Mensagem temporária (Autodestruição em {msg['tempo_expiracao_minutos']} min)*")

            # 🗑️ PERMISSÃO DE EXCLUSÃO (EXCLUSIVA PARA ADMINISTRADORES)
            if usuario_atual.get("eh_admin"):
                if st.button("🗑️ Apagar Mensagem", key=f"del_{msg['id']}"):
                    supabase.table("mensagens").delete().eq("id", msg["id"]).execute()
                    st.rerun()

    # ENVIAR NOVA MENSAGEM
    with st.container():
        prompt = st.chat_input("Digite sua mensagem...")
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            eh_comunicado = st.checkbox("📌 Marcar como Comunicado Oficial")
        with col_opt2:
            expiracao_opcao = st.selectbox("⏱️ Autodestruição:", ["Desativada", "5 minutos", "60 minutos"])

        minutos_expira = None
        if expiracao_opcao == "5 minutos":
            minutos_expira = 5
        elif expiracao_opcao == "60 minutos":
            minutos_expira = 60

        if prompt:
            nova_msg = {
                "canal_id": canal_id if canal_id else 1,
                "usuario_nome": nome_formatado_logado,
                "texto": prompt,
                "destinatario_id": destinatario['id'] if destinatario else None,
                "eh_comunicado": eh_comunicado,
                "tempo_expiracao_minutos": minutos_expira,
                "leituras_confirmadas": []
            }
            supabase.table("mensagens").insert(nova_msg).execute()
            st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas do Grupo")
    
    c_id_tarefa = canal_id if canal_id else 1
    tarefas_res = supabase.table("tarefas").select("*").eq("canal_id", c_id_tarefa).order("id", desc=True).execute()
    tarefas = tarefas_res.data
    
    ids_membros_grupo = [m['id'] for m in membros_canal] if membros_canal else [u['id'] for u in todos_usuarios]
    
    for tarefa in tarefas:
        with st.container(border=True):
            status_cor = "🟢" if tarefa['status'] == "Concluído" else "⏳"
            st.markdown(f"{status_cor} **{tarefa['status']}**")
            st.write(tarefa['titulo'])
            st.caption(f"Atribuído a: {tarefa.get('atribuido_a', 'Geral')}")
            
            if tarefa['status'] != "Concluído":
                if st.button("Marcar Concluída", key=f"t_{tarefa['id']}"):
                    eh_membro = usuario_atual['id'] in ids_membros_grupo
                    eh_responsavel = usuario_atual['nome'] in tarefa.get('atribuido_a', '')
                    
                    if eh_membro or eh_responsavel or usuario_atual.get("eh_admin"):
                        supabase.table("tarefas").update({"status": "Concluído"}).eq("id", tarefa['id']).execute()
                        st.success("Tarefa concluída!")
                        st.rerun()
                    else:
                        st.error("🔒 Permissão negada: Somente membros deste grupo podem concluir a tarefa.")

    with st.expander("+ Criar Nova Tarefa"):
        nova_tarefa_titulo = st.text_input("Descrição da tarefa:")
        opcoes_membros = ["Todos do Setor"] + [u['nome'] for u in (membros_canal if membros_canal else todos_usuarios)]
        responsavel_sel = st.selectbox("Atribuir a integrante:", opcoes_membros)
        
        if st.button("Salvar Tarefa"):
            if nova_tarefa_titulo:
                supabase.table("tarefas").insert({
                    "canal_id": c_id_tarefa,
                    "titulo": nova_tarefa_titulo,
                    "atribuido_a": responsavel_sel,
                    "status": "Pendente"
                }).execute()
                st.rerun()
