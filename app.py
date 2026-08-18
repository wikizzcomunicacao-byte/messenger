import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import pytz

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
    st.markdown("<h2 style='text-align: center;'>🔒 Login - Chat Corporativo</h2>", unsafe_allow_html=True)
    
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

# CONFIGURAÇÃO DE SILENCIAMENTO E NOTIFICAÇÃO NATIVA
st.sidebar.divider()
st.sidebar.title("⏰ Notificações")
modo_silencioso = st.sidebar.checkbox("🔕 Modo Não Perturbe", value=usuario_atual.get("modo_silencioso", False))

# Script JavaScript para solicitar permissão de Notificação Push do Navegador
st.sidebar.markdown("""
    <script>
        if (window.Notification && Notification.permission !== "granted") {
            Notification.requestPermission();
        }
    </script>
""", unsafe_allow_html=True)

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

# OPÇÕES DE MODO NAVEGAÇÃO
st.sidebar.divider()
opcoes_modo = ["🏢 Canais de Setor", "👤 Mensagens Diretas (DM)"]
if usuario_atual.get("eh_admin"):
    opcoes_modo.append("⚙️ Painel de Gestão (Admin)")
    opcoes_modo.append("📊 Relatórios e Logs (Admin)")

tipo_chat = st.sidebar.radio("Modo de Navegação:", opcoes_modo)

# ---------------------------------------------------------
# TELA 1: PAINEL DE GESTÃO (ADMIN)
# ---------------------------------------------------------
if tipo_chat == "⚙️ Painel de Gestão (Admin)":
    st.title("⚙️ Gestão de Usuários e Sistema")
    st.caption("Cadastre novos colaboradores ou realize limpezas no sistema.")
    
    col_cad, col_lista = st.columns([1, 1])
    
    with col_cad:
        st.subheader("➕ Cadastrar Novo Colaborador")
        with st.form("form_novo_usuario"):
            novo_nome = st.text_input("Nome Completo:")
            setores_existentes = ["licitacao", "compras", "financeiro", "farmaceutica", "estoque", "faturamento-pedidos", "cotacao", "loja-online", "geral"]
            novo_setor = st.selectbox("Setor:", setores_existentes)
            nova_senha = st.text_input("Senha de Acesso:", value="123456")
            h_inicio = st.number_input("Início do Expediente (Hora):", value=7, min_value=0, max_value=23)
            h_fim = st.number_input("Fim do Expediente (Hora):", value=19, min_value=0, max_value=23)
            e_admin = st.checkbox("Dar permissões de Administrador")
            
            btn_salvar_user = st.form_submit_button("Cadastrar Usuário")
            if btn_salvar_user:
                if novo_nome:
                    supabase.table("usuarios").insert({
                        "nome": novo_nome,
                        "setor": novo_setor,
                        "senha": nova_senha,
                        "hora_inicio_expediente": h_inicio,
                        "hora_fim_expediente": h_fim,
                        "eh_admin": e_admin
                    }).execute()
                    registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "CRIAR_USUARIO", f"Cadastrou o usuário {novo_nome}")
                    st.success(f"Usuário '{novo_nome}' cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Informe o nome do usuário.")

    with col_lista:
        st.subheader("👥 Usuários Cadastrados")
        for u in todos_usuarios:
            with st.container(border=True):
                col_info, col_del = st.columns([3, 1])
                with col_info:
                    admin_tag = " 👑" if u.get("eh_admin") else ""
                    st.markdown(f"**{u['nome']}**{admin_tag}")
                    st.caption(f"Setor: {u['setor']} | Expediente: {u.get('hora_inicio_expediente', 7)}h às {u.get('hora_fim_expediente', 19)}h")
                with col_del:
                    if u['id'] != usuario_atual['id']:
                        if st.button("❌", key=f"del_u_{u['id']}"):
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "DELETAR_USUARIO", f"Removeu o usuário ID {u['id']}")
                            st.success("Removido!")
                            st.rerun()

    st.divider()

    st.subheader("⚠️ Limpeza do Histórico de Conversas")
    st.caption("Esta ação é irreversível e excluirá todas as mensagens enviadas em canais e DMs.")
    
    with st.expander("🗑️ Clique para expandir as opções de exclusão em massa"):
        st.error("Atenção: Todas as mensagens e comunicados serão apagados permanentemente!")
        confirmar_check = st.checkbox("Estou ciente e desejo apagar todas as conversas do sistema.")
        
        if st.button("🔥 Apagar Todas as Mensagens do Chat", type="primary"):
            if confirmar_check:
                try:
                    supabase.table("mensagens").delete().gte("id", 0).execute()
                    registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "LIMPAR_CONVERSAS", "Apagou todo o histórico do chat")
                    st.success("✅ Todo o histórico de mensagens foi excluído com sucesso!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erro ao limpar mensagens: {ex}")
            else:
                st.warning("Marque a caixa de seleção para confirmar a exclusão.")

    st.stop()

# ---------------------------------------------------------
# TELA 2: RELATÓRIOS E LOGS (ADMIN)
# ---------------------------------------------------------
if tipo_chat == "📊 Relatórios e Logs (Admin)":
    st.title("📊 Relatórios de Uso e Controle de Logs")
    st.caption("Painel restrito para auditoria e monitoramento de atividades dos colaboradores.")

    total_users = len(todos_usuarios)
    msgs_totais = len(supabase.table("mensagens").select("id", count="exact").execute().data or [])
    tarefas_totais = len(supabase.table("tarefas").select("id", count="exact").execute().data or [])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total de Colaboradores", total_users)
    c2.metric("💬 Total de Mensagens", msgs_totais)
    c3.metric("📋 Total de Tarefas Registradas", tarefas_totais)

    st.divider()

    st.subheader("📋 Histórico de Logs de Auditoria")
    logs_res = supabase.table("logs_acesso").select("*").order("criado_em", desc=True).limit(100).execute()
    logs_data = logs_res.data if logs_res.data else []

    busca_log = st.text_input("🔍 Filtrar logs por nome, setor ou ação:")
    
    if logs_data:
        logs_filtrados = [
            l for l in logs_data 
            if busca_log.lower() in str(l.get('usuario_nome', '')).lower() 
            or busca_log.lower() in str(l.get('acao', '')).lower()
            or busca_log.lower() in str(l.get('setor', '')).lower()
        ]

        st.dataframe(
            logs_filtrados,
            column_config={
                "criado_em": "Data/Hora",
                "usuario_nome": "Colaborador",
                "setor": "Setor",
                "acao": "Ação Realizada",
                "detalhes": "Detalhes"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Nenhum registro de log encontrado até o momento.")

    st.stop()

# ---------------------------------------------------------
# TELA 3: CHAT E TAREFAS (COM ATUALIZAÇÃO AUTOMÁTICA E NOTIFICAÇÕES)
# ---------------------------------------------------------
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

# INTERFACE PRINCIPAL DO CHAT
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    st.subheader(titulo_chat)
    nome_formatado_logado = f"{usuario_atual['nome']} ({usuario_atual['setor']})"

    @st.fragment(run_every=3)
    def renderizar_mensagens():
        if tipo_chat == "🏢 Canais de Setor":
            mensagens_res = supabase.table("mensagens").select("*").eq("canal_id", canal_id).is_("destinatario_id", "null").order("criado_em", desc=False).execute()
            mensagens = mensagens_res.data
        else:
            res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", destinatario['id']).execute().data
            res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{destinatario['nome']} ({destinatario['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data
            mensagens = sorted(res1 + res2, key=lambda x: x['criado_em'])

        # Sistema de Notificação Push via JavaScript seguro sem conflito de chaves
        if mensagens and not modo_silencioso:
            ultima_msg = mensagens[-1]
            if ultima_msg['usuario_nome'] != nome_formatado_logado:
                texto_notif = (ultima_msg.get('texto') or 'Enviou um anexo.').replace('"', '\\"')
                autor_notif = ultima_msg['usuario_nome'].replace('"', '\\"')
                js_code = f"""
                    <script>
                        if (window.Notification && Notification.permission === "granted") {{
                            if (document.hidden) {{
                                new Notification("{autor_notif}", {{
                                    body: "{texto_notif}",
                                    icon: "💬"
                                }});
                            }}
                        }}
                    </script>
                """
                st.markdown(js_code, unsafe_allow_html=True)

        for msg in mensagens:
            is_me = msg['usuario_nome'] == nome_formatado_logado
            avatar = "📢" if msg.get("eh_comunicado") else ("🟢" if is_me else "👤")
            
            with st.chat_message("user", avatar=avatar):
                if msg.get("eh_comunicado"):
                    st.warning("📌 **COMUNICADO OFICIAL**")
                
                st.markdown(f"**{msg['usuario_nome']}**")
                if msg.get('texto'):
                    st.write(msg['texto'])

                # EXIBIÇÃO DE ANEXOS (COM BOTÃO DE DOWNLOAD DIRETO)
                if msg.get("arquivo_url"):
                    tipo_arq = msg.get("arquivo_tipo", "") or ""
                    url_arq = msg.get("arquivo_url")
                    
                    if "image" in tipo_arq:
                        st.image(url_arq, use_container_width=True)
                    elif "audio" in tipo_arq:
                        st.audio(url_arq)
                    else:
                        nome_display = url_arq.split("/")[-1].split("_", 1)[-1] if "_" in url_arq else "documento.pdf"
                        st.markdown(
                            f"""
                            <a href="{url_arq}" download="{nome_display}" target="_blank" style="
                                display: inline-block;
                                padding: 8px 16px;
                                background-color: {p['primary']};
                                color: white;
                                text-decoration: none;
                                border-radius: 6px;
                                font-weight: bold;
                                margin-top: 5px;
                            ">
                                📥 Baixar Arquivo ({nome_display})
                            </a>
                            """,
                            unsafe_allow_html=True
                        )

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
                                registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "CONFIRMAR_LEITURA", f"Confirmou leitura da mensagem ID {msg['id']}")
                                st.rerun()
                        else:
                            st.caption("🔒 *Apenas colaboradores pertencentes a este setor podem confirmar leitura.*")
                    else:
                        st.caption("✔️ Você já confirmou leitura deste comunicado.")
                    
                    st.progress(len(leituras) / max(total_alvo, 1))
                    st.caption(f"📊 **Confirmações:** {len(leituras)} de {total_alvo} colaboradores do setor leram.")

                if usuario_atual.get("eh_admin"):
                    if st.button("🗑️ Apagar Mensagem", key=f"del_{msg['id']}"):
                        supabase.table("mensagens").delete().eq("id", msg["id"]).execute()
                        registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "DELETAR_MENSAGEM", f"Apagou a mensagem ID {msg['id']}")
                        st.rerun()

    renderizar_mensagens()

    # --- PAINEL DE ENVIO COMPACTO ---
    st.divider()
    
    col_input, col_com, col_clip, col_btn = st.columns([5.4, 0.6, 0.6, 0.8])

    with col_input:
        prompt = st.text_input("Mensagem", placeholder="Digite sua mensagem...", key="input_texto_msg", label_visibility="collapsed")

    with col_com:
        with st.popover("📢", help="Marcar como Comunicado Oficial"):
            eh_comunicado = st.checkbox("Tornar Comunicado Oficial", key="chk_comunicado_popover")

    with col_clip:
        with st.popover("📎", help="Anexar arquivo"):
            arquivo_enviado = st.file_uploader(
                "Selecione o arquivo:", 
                type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx", "mp3", "wav"],
                key=f"uploader_{st.session_state['uploader_key']}",
                label_visibility="collapsed"
            )

    with col_btn:
        btn_enviar = st.button("🚀", help="Enviar Mensagem")

    if 'chk_comunicado_popover' not in st.session_state:
        st.session_state['chk_comunicado_popover'] = False

    if btn_enviar and (prompt or 'arquivo_enviado' in locals() and arquivo_enviado is not None):
        url_publica = None
        tipo_arquivo = None

        if 'arquivo_enviado' in locals() and arquivo_enviado is not None:
            try:
                timestamp_atual = int(datetime.now().timestamp())
                nome_arquivo = f"{timestamp_atual}_{arquivo_enviado.name}"
                bytes_data = arquivo_enviado.getvalue()
                content_type = arquivo_enviado.type or "application/pdf"

                supabase.storage.from_("anexos").upload(
                    path=nome_arquivo, 
                    file=bytes_data, 
                    file_options={"content-type": content_type, "upsert": "true"}
                )
                url_publica = supabase.storage.from_("anexos").get_public_url(nome_arquivo)
                tipo_arquivo = content_type
            except Exception as ex:
                st.error(f"Erro ao subir arquivo: {ex}")

        nova_msg = {
            "canal_id": canal_id if canal_id else 1,
            "usuario_nome": nome_formatado_logado,
            "texto": prompt if prompt else "",
            "destinatario_id": destinatario['id'] if destinatario else None,
            "eh_comunicado": st.session_state.get('chk_comunicado_popover', False),
            "tempo_expiracao_minutos": None,
            "leituras_confirmadas": [],
            "arquivo_url": url_publica,
            "arquivo_tipo": tipo_arquivo
        }
        supabase.table("mensagens").insert(nova_msg).execute()
        registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "ENVIAR_MENSAGEM", f"Enviou mensagem no canal ID {canal_id}")
        
        st.session_state["uploader_key"] += 1
        st.rerun()

with col_tarefas:
    st.subheader("📋 Tarefas do Grupo")
    
    @st.fragment(run_every=3)
    def renderizar_tarefas():
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
                            registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "CONCLUIR_TAREFA", f"Concluiu a tarefa ID {tarefa['id']}")
                            st.success("Tarefa concluída!")
                            st.rerun()
                        else:
                            st.error("🔒 Permissão negada: Somente membros deste grupo podem concluir a tarefa.")

    renderizar_tarefas()

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
                registrar_log(usuario_atual['id'], usuario_atual['nome'], usuario_atual['setor'], "CRIAR_TAREFA", f"Criou tarefa '{nova_tarefa_titulo}'")
                st.rerun()
