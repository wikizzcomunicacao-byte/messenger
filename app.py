import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components

# Configuração da página - Layout em largura total
st.set_page_config(
    page_title="Senhora Lavanderia - WhatsApp Chats", 
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
if "chat_ativo" not in st.session_state:
    st.session_state["chat_ativo"] = ("canal", 1)

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

# TEMA ESCURO PADRÃO WHATSAPP
p = {
    "bg_app": "#0b141a", 
    "bg_sidebar": "#111b21", 
    "bg_msg_out": "#005c4b", 
    "bg_msg_in": "#202c33", 
    "primary": "#00a884", 
    "text": "#e9edef",
    "subtext": "#8696a0"
}

# CSS PERSONALIZADO PARA ESTILIZAR OS BOTÕES DA LATERAL IGUAL WHATSAPP
st.markdown(f"""
    <style>
        .stApp {{ background-color: {p['bg_app']} !important; color: {p['text']} !important; }}
        [data-testid="stSidebar"] {{ background-color: {p['bg_sidebar']} !important; border-right: 1px solid rgba(255, 255, 255, 0.1); }}
        [data-testid="stSidebar"] * {{ color: {p['text']} !important; }}
        
        /* Deixar os botões da barra lateral com cara de lista de conversas do WhatsApp */
        [data-testid="stSidebar"] .stButton button {{
            background-color: transparent !important;
            border: none !important;
            text-align: left !important;
            padding: 8px 10px !important;
            border-radius: 8px !important;
            margin-bottom: 4px !important;
        }}
        [data-testid="stSidebar"] .stButton button:hover {{
            background-color: rgba(255, 255, 255, 0.05) !important;
        }}

        .msg-out {{
            background-color: {p['bg_msg_out']};
            color: {p['text']};
            padding: 10px 14px;
            border-radius: 8px 0px 8px 8px;
            margin: 5px 0;
            max-width: 65%;
            margin-left: auto;
            word-wrap: break-word;
            box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
        }}
        .msg-in {{
            background-color: {p['bg_msg_in']};
            color: {p['text']};
            padding: 10px 14px;
            border-radius: 0px 8px 8px 8px;
            margin: 5px 0;
            max-width: 65%;
            margin-right: auto;
            word-wrap: break-word;
            box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
        }}
        .msg-info {{
            font-size: 0.7em;
            color: {p['subtext']};
            text-align: right;
            margin-top: 4px;
        }}
        .chat-header {{
            background-color: {p['bg_sidebar']};
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BARRA LATERAL - ABA DE CONVERSAS RECENTES
# ---------------------------------------------------------
st.sidebar.markdown(f"### 💬 Conversas")
st.sidebar.caption(f"Logado como: {nome_limpo_usuario}")

if usuario_atual.get("eh_admin"):
    if st.sidebar.button("⚙️ Painel Admin", use_container_width=True, key="nav_admin"):
        st.session_state["chat_ativo"] = ("admin", 0)
        st.rerun()
    if st.sidebar.button("📊 Relatórios de Auditoria", use_container_width=True, key="nav_rel"):
        st.session_state["chat_ativo"] = ("relatorios", 0)
        st.rerun()

if st.sidebar.button("🚪 Sair da Conta", use_container_width=True, key="nav_sair"):
    registrar_log(usuario_atual['id'], nome_limpo_usuario, usuario_atual['setor'], "LOGOFF", "Encerrou a sessão")
    st.session_state["autenticado"] = False
    st.session_state["usuario_logado"] = None
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("📢 **Canais de Setor**")

try:
    canais = supabase.table("canais").select("*").order("id").execute().data or []
except:
    canais = []

for c in canais:
    try:
        msgs_c = supabase.table("mensagens").select("texto, criado_em, leituras_confirmadas, usuario_nome").eq("canal_id", c['id']).is_("destinatario_id", "null").order("criado_em", desc=True).execute().data or []
        ultima_txt = msgs_c[0].get("texto", "Nenhuma mensagem") if msgs_c else "Toque para iniciar"
        nao_lidas = sum(1 for m in msgs_c if not m.get("usuario_nome", "").startswith(nome_limpo_usuario) and usuario_atual['id'] not in (m.get("leituras_confirmadas") or []))
    except:
        ultima_txt = "Toque para iniciar"
        nao_lidas = 0
        
    badge = f" 🟢 {nao_lidas}" if nao_lidas > 0 else ""
    
    # Ao clicar, atualiza o estado e força o rerun imediato
    if st.sidebar.button(f"📢 **#{c['nome']}**{badge}\n💬 {ultima_txt[:26]}...", key=f"btn_canal_{c['id']}", use_container_width=True):
        st.session_state["chat_ativo"] = ("canal", c['id'])
        st.rerun()

st.sidebar.divider()
st.sidebar.markdown("👤 **Conversas Diretas (DMs)**")

outros_usuarios = [u for u in todos_usuarios if u['id'] != usuario_atual['id']]
for u in outros_usuarios:
    try:
        res1 = supabase.table("mensagens").select("texto, criado_em, leituras_confirmadas, usuario_nome").eq("destinatario_id", u['id']).order("criado_em", desc=True).execute().data or []
        res2 = supabase.table("mensagens").select("texto, criado_em, leituras_confirmadas, usuario_nome").eq("destinatario_id", usuario_atual['id']).order("criado_em", desc=True).execute().data or []
        
        todas_dm = sorted(res1 + res2, key=lambda x: x.get('criado_em', ''), reverse=True)
        ultima_txt_dm = todas_dm[0].get("texto", "Nenhuma conversa") if todas_dm else "Nenhuma conversa"
        
        nao_lidas_dm = sum(1 for m in res2 if (m.get("usuario_nome", "").startswith(u['nome']) or m.get("usuario_nome") == u['nome']) and usuario_atual['id'] not in (m.get("leituras_confirmadas") or []))
    except:
        ultima_txt_dm = "Nenhuma conversa"
        nao_lidas_dm = 0
        
    badge_dm = f" 🟢 {nao_lidas_dm}" if nao_lidas_dm > 0 else ""
    
    if st.sidebar.button(f"👤 **{u['nome']}**{badge_dm}\n💬 {ultima_txt_dm[:26]}...", key=f"btn_dm_{u['id']}", use_container_width=True):
        st.session_state["chat_ativo"] = ("dm", u)
        st.rerun()

# ---------------------------------------------------------
# TELA DE ADMINISTRAÇÃO E RELATÓRIOS
# ---------------------------------------------------------
tipo_chat, obj_chat = st.session_state["chat_ativo"]

if tipo_chat == "admin":
    st.title("⚙️ Gestão de Usuários e Sistema")
    col_cad, col_lista = st.columns(2)
    setores_existentes = ["licitacao", "compras", "financeiro", "farmaceutica", "estoque", "faturamento-pedidos", "cotacao", "loja-online", "geral"]

    with col_cad:
        st.subheader("➕ Cadastrar Colaborador")
        with st.form("form_novo_usuario"):
            novo_nome = st.text_input("Nome Completo:")
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
        st.subheader("👥 Usuários & Gerenciamento")
        for u in todos_usuarios:
            with st.container(border=True):
                st.markdown(f"**{u['nome']}** ({u['setor']})")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("✏️ Editar", key=f"edit_u_{u['id']}"):
                        st.session_state[f"edit_{u['id']}"] = not st.session_state.get(f"edit_{u['id']}", False)
                        st.rerun()
                with col_b2:
                    if u['id'] != usuario_atual['id']:
                        if st.button("❌ Remover", key=f"del_u_{u['id']}"):
                            try:
                                supabase.table("mensagens").delete().eq("destinatario_id", u['id']).execute()
                                supabase.table("usuarios").delete().eq("id", u['id']).execute()
                                st.success("Removido com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                
                if st.session_state.get(f"edit_{u['id']}", False):
                    with st.form(f"form_ed_{u['id']}"):
                        ed_n = st.text_input("Nome:", value=u['nome'])
                        ed_s = st.selectbox("Setor:", setores_existentes, index=setores_existentes.index(u['setor']) if u['setor'] in setores_existentes else 0)
                        ed_p = st.text_input("Senha:", value=u.get('senha', '123456'))
                        ed_adm = st.checkbox("Admin", value=u.get('eh_admin', False))
                        if st.form_submit_button("Salvar"):
                            supabase.table("usuarios").update({"nome": ed_n, "setor": ed_s, "senha": ed_p, "eh_admin": ed_adm}).eq("id", u['id']).execute()
                            st.session_state[f"edit_{u['id']}"] = False
                            st.rerun()
    st.stop()

if tipo_chat == "relatorios":
    st.title("📊 Relatórios e Logs de Auditoria")
    try:
        logs = supabase.table("logs_acesso").select("*").order("criado_em", desc=True).limit(50).execute().data or []
    except:
        logs = []
    st.dataframe(logs, hide_index=True, use_container_width=True)
    st.stop()

# ---------------------------------------------------------
# TELA DA JANELA DE CHAT ABERTA
# ---------------------------------------------------------
col_chat, col_tarefas = st.columns([2, 1])

with col_chat:
    if tipo_chat == "canal":
        canal_info = next((c for c in canais if c['id'] == obj_chat), {"nome": "geral", "icone": "💬"})
        titulo_janela = f"{canal_info['icone']} #{canal_info['nome']}"
    else:
        titulo_janela = f"👤 Conversa com {obj_chat['nome']} ({obj_chat['setor']})"

    st.markdown(f"<div class='chat-header'><h3>{titulo_janela}</h3></div>", unsafe_allow_html=True)

    with st.container(height=480):
        @st.fragment(run_every=3)
        def renderizar_janela_chat():
            mensagens = []
            try:
                if tipo_chat == "canal":
                    mensagens = supabase.table("mensagens").select("*").eq("canal_id", obj_chat).is_("destinatario_id", "null").order("criado_em", desc=False).execute().data or []
                else:
                    res1 = supabase.table("mensagens").select("*").eq("usuario_nome", nome_formatado_logado).eq("destinatario_id", obj_chat['id']).execute().data or []
                    res2 = supabase.table("mensagens").select("*").eq("usuario_nome", f"{obj_chat['nome']} ({obj_chat['setor']})").eq("destinatario_id", usuario_atual['id']).execute().data or []
                    res3 = supabase.table("mensagens").select("*").eq("usuario_nome", obj_chat['nome']).eq("destinatario_id", usuario_atual['id']).execute().data or []
                    
                    todas = {m['id']: m for m in (res1 + res2 + res3)}
                    mensagens = sorted(list(todas.values()), key=lambda x: x['criado_em'])
            except:
                mensagens = []

            for msg in mensagens:
                remetente = msg.get("usuario_nome", "")
                is_me = remetente.startswith(nome_limpo_usuario)
                
                leituras = msg.get("leituras_confirmadas") or []
                if not is_me and usuario_atual['id'] not in leituras:
                    leituras.append(usuario_atual['id'])
                    try:
                        supabase.table("mensagens").update({"leituras_confirmadas": leituras}).eq("id", msg['id']).execute()
                    except:
                        pass

                hora = ""
                if msg.get("criado_em"):
                    try:
                        dt = datetime.fromisoformat(msg["criado_em"].replace("Z", "+00:00")).astimezone(fuso_brasilia)
                        hora = dt.strftime("%H:%M")
                    except:
                        pass

                if is_me:
                    st.markdown(f"""
                        <div class='msg-out'>
                            <div style='font-size: 0.8em; font-weight: bold; color: #00a884; margin-bottom: 2px;'>Você</div>
                            <div>{msg.get('texto', '')}</div>
                            <div class='msg-info'>{hora} ✓✓</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class='msg-in'>
                            <div style='font-size: 0.8em; font-weight: bold; color: #53bdeb; margin-bottom: 2px;'>{remetente}</div>
                            <div>{msg.get('texto', '')}</div>
                            <div class='msg-info'>{hora}</div>
                        </div>
                    """, unsafe_allow_html=True)

        renderizar_janela_chat()
        
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
                }
                setTimeout(autoScroll, 50);
                setTimeout(autoScroll, 200);
            </script>
        """, height=0, width=0)

    texto_envio = st.chat_input("Digite uma mensagem...")
    if texto_envio:
        try:
            supabase.table("mensagens").insert({
                "canal_id": obj_chat if tipo_chat == "canal" else None,
                "usuario_nome": nome_formatado_logado,
                "texto": texto_envio,
                "destinatario_id": obj_chat['id'] if tipo_chat == "dm" else None,
                "leituras_confirmadas": [usuario_atual['id']]
            }).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao enviar: {e}")

# ---------------------------------------------------------
# COLUNA DE TAREFAS
# ---------------------------------------------------------
with col_tarefas:
    st.subheader("📋 Tarefas")
    
    @st.fragment(run_every=3)
    def renderizar_tarefas():
        c_id = obj_chat if tipo_chat == "canal" else 1
        try:
            tarefas = supabase.table("tarefas").select("*").eq("canal_id", c_id).order("id", desc=True).execute().data or []
        except:
            tarefas = []
        
        for t in tarefas:
            with st.container(border=True):
                status_cor = "🟢" if t['status'] == "Concluído" else "⏳"
                st.markdown(f"{status_cor} **{t['status']}**")
                st.write(t['titulo'])
                st.caption(f"Atribuído a: {t.get('atribuido_a', 'Geral')}")
                
                if t['status'] != "Concluído":
                    if st.button("Concluir", key=f"t_{t['id']}"):
                        supabase.table("tarefas").update({"status": "Concluído"}).eq("id", t['id']).execute()
                        st.rerun()

    renderizar_tarefas()

    with st.expander("+ Criar Nova Tarefa"):
        nova_t = st.text_input("Título da tarefa:")
        if st.button("Salvar Tarefa"):
            if nova_t:
                supabase.table("tarefas").insert({
                    "canal_id": obj_chat if tipo_chat == "canal" else 1,
                    "titulo": nova_t,
                    "atribuido_a": "Geral",
                    "status": "Pendente"
                }).execute()
                st.rerun()
