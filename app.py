import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
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
st.sidebar.title(f"👤 {usuario_atual['nome']}")
st.sidebar.caption(f"Setor: {usuario_atual['setor']}")
st.sidebar.markdown(f"**Expediente:** {usuario_atual.get('hora_inicio_expediente', 7)}h às {usuario_atual.get('hora_fim_expediente', 19)}h")

if usuario_atual.get("eh_admin"):
    st.sidebar.success("👑 Administrador")

if st.sidebar.button("🚪 Sair", use_container_width=True):
    registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "LOGOFF", "Encerrou a sessão")
    st.session_state["autenticado"] = False
    st.session_state["usuario_logado"] = None
    st.rerun()

tema_escolhido = st.sidebar.selectbox("🎨 Tema:", list(PALETAS.keys()))
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
        
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# OPÇÕES DE NAVEGAÇÃO
st.sidebar.divider()
opcoes_modo = ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)"]
if usuario_atual.get("eh_admin"):
    opcoes_modo.append("⚙️ Admin")
    opcoes_modo.append("📊 Relatórios")

tipo_chat = st.sidebar.radio("Navegação:", opcoes_modo)

# ---------------------------------------------------------
# TELA: PAINEL DE GESTÃO (ADMIN)
# ---------------------------------------------------------
if tipo_chat == "⚙️ Admin":
    st.title("⚙️ Gestão de Usuários e Sistema")
    col_cad, col_lista = st.columns(2)
    
    with col_cad:
        st.subheader("➕ Cadastrar Colaborador")
        with st.form("form_novo_usuario"):
            novo_nome = st.text_input("Nome Completo:")
            setores_existentes = ["licitacao", "compras", "financeiro", "farmaceutica", "estoque", "faturamento-pedidos", "cotacao", "loja-online", "geral"]
            novo_setor = st.selectbox("Setor:", setores_existentes)
            nova_senha = st.text_input("Senha:", value="123456")
            h_inicio = st.number_input("Início Expediente:", value=7, min_value=0, max_value=23)
            h_fim = st.number_input("Fim Expediente:", value=19, min_value=0, max_value=23)
            e_admin = st.checkbox("Administrador")
            
            if st.form_submit_button("Cadastrar"):
                if novo_nome:
                    supabase.table("usuarios").insert({
                        "nome": novo_nome, "setor": novo_setor, "senha": nova_senha,
                        "hora_inicio_expediente": h_inicio, "hora_fim_expediente": h_fim, "eh_admin": e_admin
                    }).execute()
                    st.success("Cadastrado com sucesso!")
                    st.rerun()

    with col_lista:
        st.subheader("👥 Usuários")
        for u in todos_usuarios:
            with st.container(border=True):
                st.markdown(f"**{u['nome']}** ({u['setor']})")
                if u['id'] != usuario_atual['id']:
                    if st.button("❌ Remover", key=f"del_u_{u['id']}"):
                        supabase.table("usuarios").delete().eq("id", u['id']).execute()
                        st.rerun()
    st.stop()

# ---------------------------------------------------------
# TELA: RELATÓRIOS E LOGS (ADMIN)
# ---------------------------------------------------------
if tipo_chat == "📊 Relatórios":
    st.title("📊 Relatórios e Logs de Auditoria")
    logs = supabase.table("logs_acesso").select("*").order("criado_em", desc=True).limit(50).execute().data or []
    st.dataframe(logs, hide_index=True, use_container_width=True)
    st.stop()

# ---------------------------------------------------------
# NAVEGAÇÃO CHAT (CANAIS / DMs) COM CONTADORES DE NÃO LIDAS
# ---------------------------------------------------------
canal_id = None
destinatario = None
membros_canal = []

if tipo_chat == "🏢 Canais de Setor":
    st.sidebar.divider()
    st.sidebar.subheader("Canal:")
    canais = supabase.table("canais").select("*").order("id").execute().data or []
    
    # Mapeia canais adicionando contagem de mensagens indicadoras
    mapa_canais = {}
    for c in canais:
        # Busca contagem de mensagens do canal
        msgs_canal = supabase.table("mensagens").select("id", count="exact").eq("canal_id", c['id']).is_("destinatario_id", "null").execute().data or []
        qtd_msgs = len(msgs_canal)
        
        badge = f" 🔴 ({qtd_msgs})" if qtd_msgs > 0 else ""
        label = f"{c['icone']} #{c['nome']}{badge}"
        mapa_canais[label] = c

    canal_nome_sel = st.sidebar.radio("Selecione:", list(mapa_canais.keys()), label_visibility="collapsed")
    obj_canal = mapa_canais[canal_nome_sel]
    canal_id = obj_canal['id']
    canal_nome_limpo = obj_canal['nome']
    titulo_chat = f"#{canal_nome_limpo}"
    
    membros_canal = todos_usuarios if canal_nome_limpo == "geral" else [u for u in todos_usuarios if u['setor'].lower() in canal_nome_limpo.lower()]
else:
    st.sidebar.divider()
    outros = [u for u in todos_usuarios if u['id'] != usuario_atual['id']]
    
    mapa_dms = {}
    for u in outros:
        # Conta mensagens diretas não lidas recebidas deste usuário
        dm_nao_lidas = supabase.table("mensagens").select("id", count="exact").eq("usuario_nome", u['nome']).eq("destinatario_id", usuario_atual['id']).execute().data or []
        qtd_dm = len(dm_nao_lidas)
        badge_dm = f" 🔴 ({qtd_dm})" if qtd_dm > 0 else ""
        
        label_dm = f"👤 {u['nome']} ({u['setor']}){badge_dm}"
        mapa_dms[label_dm] = u

    usuario_dm_sel = st.sidebar.selectbox("Falar com:", list(mapa_dms.keys()))
    destinatario = mapa_dms[usuario_dm_sel]
    titulo_chat = f"Conversa com {destinatario['nome']}"

# INTERFACE PRINCIPAL DO CHAT E TAREFAS
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo_chat)
    nome_formatado_logado = f"{usuario_atual['nome']} ({usuario_atual['setor']})"

    # Container com altura controlada e scroll interno
    with st.container(height=480):
        @st.fragment(run_every=3)
        def renderizar_mensagens():
            if tipo_chat == "🏢 Canais de Setor":
                mensagens = supabase.table("mensagens").select("*").eq("canal_id", canal_id).is_("destinatario_id", "null").order("criado_em", desc=False).execute().data or []
            else:
                res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", destinatario['id']).execute().data or []
                res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{destinatario['nome']} ({destinatario['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data or []
                res3 = supabase.table("mensagens").select("*").eq("usuario_nome", destinatario['nome']).eq("destinatario_id", usuario_atual['id']).execute().data or []
                
                todas_mensagens = {m['id']: m for m in (res1 + res2 + res3)}
                mensagens = sorted(list(todas_mensagens.values()), key=lambda x: x['criado_em'])

            for msg in mensagens:
                is_me = msg['usuario_nome'] == nome_formatado_logado or msg['usuario_nome'].startswith(usuario_atual['nome'])
                avatar = "🟢" if is_me else "👤"
                
                hora_formatada = ""
                if msg.get("criado_em"):
                    try:
                        dt_local = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00")).astimezone(fuso_brasilia)
                        hora_formatada = dt_local.strftime("%H:%M")
                    except:
                        pass

                with st.chat_message("user", avatar=avatar):
                    col_nome, col_hora = st.columns([5, 1])
                    with col_nome:
                        st.markdown(f"**{msg['usuario_nome']}**")
                    with col_hora:
                        if hora_formatada:
                            st.markdown(f"<div style='text-align: right; color: gray; font-size: 0.85em;'>{hora_formatada}</div>", unsafe_allow_html=True)

                    if msg.get('texto'):
                        st.write(msg['texto'])

                    if msg.get("arquivo_url"):
                        url_arq = msg.get("arquivo_url")
                        nome_display = url_arq.split("/")[-1].split("_", 1)[-1] if "_" in url_arq else "documento"
                        st.markdown(f"<a href='{url_arq}' target='_blank'>📥 Baixar Arquivo ({nome_display})</a>", unsafe_allow_html=True)

                    if not is_me:
                        st.markdown("<div style='text-align: right; font-size: 0.75em; color: #0284c7;'>✔️ Visualizado</div>", unsafe_allow_html=True)

                    if usuario_atual.get("eh_admin"):
                        if st.button("🗑️ Apagar", key=f"del_{msg['id']}"):
                            supabase.table("mensagens").delete().eq("id", msg['id']).execute()
                            st.rerun()

        renderizar_mensagens()
        
        # SCRIPT JAVASCRIPT AUTOMÁTICO PARA ROLAGEM AUTOMÁTICA ATÉ O FINAL
        components.html("""
            <script>
                const doc = window.parent.document;
                function autoScroll() {
                    const scrollBoxes = doc.querySelectorAll('div[data-testid="stVerticalBlockBorderWrapper"]');
                    scrollBoxes.forEach(box => {
                        const inner = box.querySelector('div[style*="overflow"]');
                        if (inner) {
                            inner.scrollTop = inner.scrollHeight;
                        }
                    });
                    const containers = doc.querySelectorAll('div[data-testid="stVerticalBlock"]');
                    containers.forEach(el => {
                        if (el.scrollHeight > el.clientHeight && el.style.overflow !== 'hidden') {
                            el.scrollTop = el.scrollHeight;
                        }
                    });
                }
                setTimeout(autoScroll, 50);
                setTimeout(autoScroll, 200);
            </script>
        """, height=0, width=0)
    
    # Campo nativo de chat (Fixo no rodapé, envia com Enter, sem botões extras)
    prompt = st.chat_input("Digite sua mensagem e aperte Enter...", key="chat_input_chat_principal")
    
    if prompt:
        supabase.table("mensagens").insert({
            "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" else None,
            "usuario_nome": nome_formatado_logado,
            "texto": prompt,
            "destinatario_id": destinatario['id'] if tipo_chat == "👤 Mensagens Diretas (DM)" else None,
            "leituras_confirmadas": []
        }).execute()
        st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas")
    
    @st.fragment(run_every=3)
    def renderizar_tarefas():
        c_id_tarefa = canal_id if tipo_chat == "🏢 Canais de Setor" else 1
        tarefas = supabase.table("tarefas").select("*").eq("canal_id", c_id_tarefa).order("id", desc=True).execute().data or []
        
        for t in tarefas:
            with st.container(border=True):
                status_cor = "🟢" if t['status'] == "Concluído" else "⏳"
                st.markdown(f"{status_cor} **{t['status']}**")
                st.write(t['titulo'])
                st.caption(f"Atribuído a: {t.get('atribuido_a', 'Geral')}")
                
                if t['status'] != "Concluído":
                    if st.button("Marcar Concluída", key=f"t_{t['id']}"):
                        supabase.table("tarefas").update({"status": "Concluído"}).eq("id", t['id']).execute()
                        st.rerun()

    renderizar_tarefas()

    with st.expander("+ Criar Nova Tarefa"):
        nova_tarefa_titulo = st.text_input("Descrição da tarefa:")
        opcoes_membros = ["Todos do Setor"] + [u['nome'] for u in (membros_canal if tipo_chat == "🏢 Canais de Setor" else todos_usuarios)]
        responsavel_sel = st.selectbox("Atribuir a:", opcoes_membros)
        
        if st.button("Salvar Tarefa"):
            if nova_tarefa_titulo:
                supabase.table("tarefas").insert({
                    "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" else 1,
                    "titulo": nova_tarefa_titulo,
                    "atribuido_a": responsavel_sel,
                    "status": "Pendente"
                }).execute()
                st.rerun()
