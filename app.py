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
if "ultima_qtd_msgs" not in st.session_state:
    st.session_state["ultima_qtd_msgs"] = 0
if "notificacoes_fechadas" not in st.session_state:
    st.session_state["notificacoes_fechadas"] = set()

def buscar_usuarios():
    try:
        res = supabase.table("usuarios").select("*").order("nome").execute()
        return res.data or []
    except Exception:
        return []

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
            
            usuario_selecionado = st.selectbox("Selecione seu perfil:", list(mapa_usuarios.keys()) if mapa_usuarios else ["Nenhum usuário encontrado"])
            senha_input = st.text_input("Sua senha:", type="password")
            
            btn_entrar = st.form_submit_button("Entrar no Chat", use_container_width=True)
            
            if btn_entrar and usuarios:
                dados_usuario = mapa_usuarios[usuario_selecionado]
                eh_admin = dados_usuario.get("eh_admin", False)
                hora_inicio = dados_usuario.get("hora_inicio_expediente", 7)
                hora_fim = dados_usuario.get("hora_fim_expediente", 22)

                fora_do_expediente = (hora_atual < hora_inicio or hora_atual >= hora_fim or dia_semana >= 5)

                if fora_do_expediente and not eh_admin:
                    st.error(f"⏰ Acesso negado! Seu expediente é das {hora_inicio}h às {hora_fim}h.")
                elif senha_input == dados_usuario.get("senha", "123456"):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = dados_usuario
                    try:
                        tot_msgs = supabase.table("mensagens").select("id", count="exact").execute().data or []
                        st.session_state["ultima_qtd_msgs"] = len(tot_msgs)
                    except:
                        st.session_state["ultima_qtd_msgs"] = 0
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
nome_limpo_usuario = usuario_atual['nome'].replace("*", "").strip()
nome_formatado_logado = f"{nome_limpo_usuario} ({usuario_atual['setor']})"

# TEMA FIXO: ESCURO PADRÃO (WHATSAPP)
p = {
    "bg_app": "#0b141a", 
    "bg_sidebar": "#111b21", 
    "bg_msg": "#202c33", 
    "primary": "#00a884", 
    "text": "#e9edef"
}

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

# ---------------------------------------------------------
# CÁLCULO E CAPTURA DE MENSAGENS NÃO LIDAS
# ---------------------------------------------------------
mensagens_nao_lidas_detalhes = []
total_geral_nao_lidas = 0
try:
    todas_as_msgs = supabase.table("mensagens").select("id, texto, criado_em, leituras_confirmadas, usuario_nome, destinatario_id, canal_id").execute().data or []
    for m in todas_as_msgs:
        msg_id = m.get("id")
        if msg_id in st.session_state["notificacoes_fechadas"]:
            continue
        remetente = m.get("usuario_nome", "")
        if not remetente.startswith(nome_limpo_usuario):
            dest_id = m.get("destinatario_id")
            canal_ref = m.get("canal_id")
            if dest_id == usuario_atual['id'] or (canal_ref is not None and dest_id is None):
                leituras = m.get("leituras_confirmadas") or []
                if usuario_atual['id'] not in leituras:
                    total_geral_nao_lidas += 1
                    mensagens_nao_lidas_detalhes.append(m)
except:
    pass

# BARRA LATERAL - PERFIL E MINI-CHATS DE RESPOSTA RÁPIDA
if total_geral_nao_lidas > 0:
    st.sidebar.markdown(f"🔔 **{nome_limpo_usuario}** <span style='background-color: #25d366; color: black; padding: 2px 6px; border-radius: 10px; font-size: 0.7em;'>{total_geral_nao_lidas} novas</span>", unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("💬 **Mini-Chats Pendentes:**")
    
    for mn in mensagens_nao_lidas_detalhes:
        m_id = mn.get("id")
        rem = mn.get("usuario_nome", "Alguém")
        txt = mn.get("texto", "")
        
        with st.sidebar.container(border=True):
            col_info, col_x = st.columns([5, 1])
            with col_info:
                st.markdown(f"**{rem}**")
                st.caption(txt)
            with col_x:
                if st.button("✕", key=f"fechar_notif_{m_id}"):
                    st.session_state["notificacoes_fechadas"].add(m_id)
                    st.rerun()
            
            # Caixa de resposta rápida direto no mini-chat
            resposta_mini = st.text_input("Responder:", key=f"resp_mini_{m_id}", placeholder="Digite e aperte Enter")
            if resposta_mini:
                try:
                    dest_id_env = mn.get("destinatario_id")
                    canal_id_env = mn.get("canal_id")
                    
                    supabase.table("mensagens").insert({
                        "canal_id": canal_id_env if canal_id_env else None,
                        "usuario_nome": nome_formatado_logado,
                        "texto": resposta_mini,
                        "destinatario_id": dest_id_env if dest_id_env else None,
                        "leituras_confirmadas": [usuario_atual['id']]
                    }).execute()
                    
                    # Marca como lida e fecha o mini-chat
                    leituras = mn.get("leituras_confirmadas") or []
                    if usuario_atual['id'] not in leituras:
                        leituras.append(usuario_atual['id'])
                        supabase.table("mensagens").update({"leituras_confirmadas": leituras}).eq("id", m_id).execute()
                    
                    st.session_state["notificacoes_fechadas"].add(m_id)
                    st.success("Enviado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
else:
    st.sidebar.title(f"👤 {nome_limpo_usuario}")

st.sidebar.caption(f"Setor: {usuario_atual['setor']}")
st.sidebar.markdown(f"**Expediente:** {usuario_atual.get('hora_inicio_expediente', 7)}h às {usuario_atual.get('hora_fim_expediente', 22)}h")

if usuario_atual.get("eh_admin"):
    st.sidebar.success("👑 Administrador")

if st.sidebar.button("🚪 Sair", use_container_width=True):
    registrar_log(usuario_atual['id'], nome_limpo_usuario, usuario_atual['setor'], "LOGOFF", "Encerrou a sessão")
    st.session_state["autenticado"] = False
    st.session_state["usuario_logado"] = None
    st.rerun()

st.sidebar.divider()

# OPÇÕES DE NAVEGAÇÃO PRINCIPAL
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
            h_fim = st.number_input("Fim Expediente:", value=22, min_value=0, max_value=23)
            e_admin = st.checkbox("Administrador")
            
            if st.form_submit_button("Cadastrar"):
                if novo_nome:
                    try:
                        supabase.table("usuarios").insert({
                            "nome": novo_nome, "setor": novo_setor, "senha": nova_senha,
                            "hora_inicio_expediente": h_inicio, "hora_fim_expediente": h_fim, "eh_admin": e_admin
                        }).execute()
                        st.success("Cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")

    with col_lista:
        st.subheader("👥 Usuários")
        for u in todos_usuarios:
            with st.container(border=True):
                st.markdown(f"**{u['nome']}** ({u['setor']})")
                if u['id'] != usuario_atual['id']:
                    if st.button("❌ Remover", key=f"del_u_{u['id']}"):
                        try:
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            st.rerun()
                        except:
                            pass
    st.stop()

# ---------------------------------------------------------
# TELA: RELATÓRIOS E LOGS (ADMIN)
# ---------------------------------------------------------
if tipo_chat == "📊 Relatórios":
    st.title("📊 Relatórios e Logs de Auditoria")
    try:
        logs = supabase.table("logs_acesso").select("*").order("criado_em", desc=True).limit(50).execute().data or []
    except:
        logs = []
    st.dataframe(logs, hide_index=True, use_container_width=True)
    st.stop()

# ---------------------------------------------------------
# NAVEGAÇÃO CHAT (CANAIS / DMs)
# ---------------------------------------------------------
canal_id = None
destinatario = None
membros_canal = []

if tipo_chat == "🏢 Canais de Setor":
    st.sidebar.divider()
    st.sidebar.subheader("Canal:")
    try:
        canais = supabase.table("canais").select("*").order("id").execute().data or []
    except:
        canais = []
    
    mapa_canais = {}
    for c in canais:
        try:
            msgs_canal = supabase.table("mensagens").select("id, leituras_confirmadas, usuario_nome").eq("canal_id", c['id']).is_("destinatario_id", "null").execute().data or []
        except:
            msgs_canal = []
            
        nao_lidas = 0
        for m in msgs_canal:
            remetente = m.get("usuario_nome", "")
            if not remetente.startswith(nome_limpo_usuario):
                leituras = m.get("leituras_confirmadas") or []
                if usuario_atual['id'] not in leituras:
                    nao_lidas += 1
        badge = f" 🟢 ({nao_lidas})" if nao_lidas > 0 else ""
        label = f"{c['icone']} #{c['nome']}{badge}"
        mapa_canais[label] = c

    if mapa_canais:
        canal_nome_sel = st.sidebar.radio("Selecione:", list(mapa_canais.keys()), label_visibility="collapsed")
        obj_canal = mapa_canais[canal_nome_sel]
        canal_id = obj_canal['id']
        canal_nome_limpo = obj_canal['nome']
        titulo_chat = f"#{canal_nome_limpo}"
        membros_canal = todos_usuarios if canal_nome_limpo == "geral" else [u for u in todos_usuarios if u['setor'].lower() in canal_nome_limpo.lower()]
    else:
        titulo_chat = "#geral"
else:
    st.sidebar.divider()
    outros = [u for u in todos_usuarios if u['id'] != usuario_atual['id']]
    
    mapa_dms = {}
    for u in outros:
        try:
            dm_nao_lidas = supabase.table("mensagens").select("id, leituras_confirmadas, usuario_nome, destinatario_id").eq("destinatario_id", usuario_atual['id']).execute().data or []
        except:
            dm_nao_lidas = []
            
        qtd_dm = 0
        for m in dm_nao_lidas:
            remetente = m.get("usuario_nome", "")
            if remetente.startswith(u['nome']) or remetente == u['nome']:
                leituras = m.get("leituras_confirmadas") or []
                if usuario_atual['id'] not in leituras:
                    qtd_dm += 1
        badge_dm = f" 🟢 ({qtd_dm})" if qtd_dm > 0 else ""
        label_dm = f"👤 {u['nome']} ({u['setor']}){badge_dm}"
        mapa_dms[label_dm] = u

    if mapa_dms:
        usuario_dm_sel = st.sidebar.selectbox("Falar com:", list(mapa_dms.keys()))
        destinatario = mapa_dms[usuario_dm_sel]
        titulo_chat = f"Conversa com {destinatario['nome']}"
    else:
        titulo_chat = "Conversa Direta"

# INTERFACE PRINCIPAL DO CHAT E TAREFAS
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    if total_geral_nao_lidas > 0:
        st.markdown(f"### 🔔 {titulo_chat} <span style='font-size: 0.6em; background-color: #25d366; color: black; padding: 2px 8px; border-radius: 10px;'>{total_geral_nao_lidas} novas mensagens</span>", unsafe_allow_html=True)
    else:
        st.subheader(titulo_chat)

    with st.container(height=480):
        @st.fragment(run_every=3)
        def renderizar_mensagens():
            try:
                todas_atuais = supabase.table("mensagens").select("id, usuario_nome, texto").execute().data or []
            except:
                todas_atuais = []
            qtd_atual = len(todas_atuais)
            
            if qtd_atual > st.session_state["ultima_qtd_msgs"]:
                st.session_state["ultima_qtd_msgs"] = qtd_atual

            mensagens = []
            try:
                if tipo_chat == "🏢 Canais de Setor" and canal_id:
                    mensagens = supabase.table("mensagens").select("*").eq("canal_id", canal_id).is_("destinatario_id", "null").order("criado_em", desc=False).execute().data or []
                elif destinatario:
                    res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", destinatario['id']).execute().data or []
                    res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{destinatario['nome']} ({destinatario['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data or []
                    res3 = supabase.table("mensagens").select("*").eq("usuario_nome", destinatario['nome']).eq("destinatario_id", usuario_atual['id']).execute().data or []
                    
                    todas_mensagens = {m['id']: m for m in (res1 + res2 + res3)}
                    mensagens = sorted(list(todas_mensagens.values()), key=lambda x: x['criado_em'])
            except:
                mensagens = []

            for msg in mensagens:
                remetente_msg = msg.get("usuario_nome", "")
                is_me = remetente_msg.startswith(nome_limpo_usuario)
                avatar = "🟢" if is_me else "👤"
                
                leituras = msg.get("leituras_confirmadas") or []
                if not is_me and usuario_atual['id'] not in leituras:
                    leituras.append(usuario_atual['id'])
                    try:
                        supabase.table("mensagens").update({"leituras_confirmadas": leituras}).eq("id", msg['id']).execute()
                    except:
                        pass

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
                        st.markdown(f"**{remetente_msg}**")
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
                            try:
                                supabase.table("mensagens").delete().eq("id", msg['id']).execute()
                                st.rerun()
                            except:
                                pass

        renderizar_mensagens()
        
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
    
    prompt = st.chat_input("Digite sua mensagem e aperte Enter...", key="chat_input_chat_principal")
    
    if prompt:
        try:
            supabase.table("mensagens").insert({
                "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" else None,
                "usuario_nome": nome_formatado_logado,
                "texto": prompt,
                "destinatario_id": destinatario['id'] if tipo_chat == "👤 Mensagens Diretas (DM)" and destinatario else None,
                "leituras_confirmadas": [usuario_atual['id']]
            }).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao enviar mensagem: {e}")

with col_tarefas:
    st.subheader("📋 Tarefas")
    
    @st.fragment(run_every=3)
    def renderizar_tarefas():
        c_id_tarefa = canal_id if tipo_chat == "🏢 Canais de Setor" and canal_id else 1
        try:
            tarefas = supabase.table("tarefas").select("*").eq("canal_id", c_id_tarefa).order("id", desc=True).execute().data or []
        except:
            tarefas = []
        
        for t in tarefas:
            with st.container(border=True):
                status_cor = "🟢" if t['status'] == "Concluído" else "⏳"
                st.markdown(f"{status_cor} **{t['status']}**")
                st.write(t['titulo'])
                st.caption(f"Atribuído a: {t.get('atribuido_a', 'Geral')}")
                
                if t['status'] != "Concluído":
                    if st.button("Marcar Concluída", key=f"t_{t['id']}"):
                        try:
                            supabase.table("tarefas").update({"status": "Concluído"}).eq("id", t['id']).execute()
                            st.rerun()
                        except:
                            pass

    renderizar_tarefas()

    with st.expander("+ Criar Nova Tarefa"):
        nova_tarefa_titulo = st.text_input("Descrição da tarefa:")
        opcoes_membros = ["Todos do Setor"] + [u['nome'] for u in (membros_canal if tipo_chat == "🏢 Canais de Setor" else todos_usuarios)]
        responsavel_sel = st.selectbox("Atribuir a:", opcoes_membros)
        
        if st.button("Salvar Tarefa"):
            if nova_tarefa_titulo:
                try:
                    supabase.table("tarefas").insert({
                        "canal_id": canal_id if tipo_chat == "🏢 Canais de Setor" and canal_id else 1,
                        "titulo": nova_tarefa_titulo,
                        "atribuido_a": responsavel_sel,
                        "status": "Pendente"
                    }).execute()
                    st.rerun()
                except:
                    pass
