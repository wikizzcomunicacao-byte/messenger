from datetime import datetime
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Mural da Empresa", page_icon="💬", layout="wide"
)

# Constantes e Cores
ADMIN_PASSWORD = "admin123"
DEPT_COLORS = {
    "Vendas": "#E8A33D",
    "Suporte": "#2F8F82",
    "Financeiro": "#8B6FB3",
    "RH": "#D9645F",
    "TI": "#3F7CAC",
    "Operações": "#B08B3F",
    "Diretoria": "#16232E",
}

# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if "view" not in st.session_state:
  st.session_state.view = "landing"  # landing, adminLogin, admin, employeeLogin, chat
if "employees" not in st.session_state:
  st.session_state.employees = []
if "groups" not in st.session_state:
  st.session_state.groups = []
if "messages" not in st.session_state:
  st.session_state.messages = []
if "current_user" not in st.session_state:
  st.session_state.current_user = None
if "active_conv" not in st.session_state:
  st.session_state.active_conv = None  # ('ind', id_outro) ou ('grp', id_grupo)
if "error_msg" not in st.session_state:
  st.session_state.error_msg = ""


# Funções Utilitárias
def get_initials(name):
  words = (name or "").strip().split()
  return (
      "".join([w[0].upper() for w in words[:2]]) if words else "?"
  )


def format_time(ts):
  return datetime.fromtimestamp(ts / 1000).strftime("%H:%M")


# ==========================================
# 1. TELA: LANDING PAGE
# ==========================================
def render_landing():
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.markdown(
        "<h1 style='text-align: center;'>💬 Mural da Empresa</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: gray;'>Protótipo de"
        " comunicação interna corporativa.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    if st.button("👤 Sou funcionário", use_container_width=True):
      st.session_state.error_msg = ""
      st.session_state.view = "employeeLogin"
      st.rerun()

    if st.button("🛠️ Sou administrador", use_container_width=True):
      st.session_state.error_msg = ""
      st.session_state.view = "adminLogin"
      st.rerun()

    st.info(
        "💡 **Aviso:** Este é um protótipo de demonstração. Dados salvos"
        " reiniciam se o servidor for reciclado."
    )


# ==========================================
# 2. TELA: LOGIN ADMIN
# ==========================================
def render_admin_login():
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.subheader("Painel do Administrador")
    st.caption(f"Senha padrão de demonstração: `{ADMIN_PASSWORD}`")

    pwd = st.text_input("Senha do administrador", type="password")

    if st.button("Entrar", use_container_width=True):
      if pwd == ADMIN_PASSWORD:
        st.session_state.view = "admin"
        st.rerun()
      else:
        st.error("Senha incorreta.")

    if st.button("Voltar", use_container_width=True):
      st.session_state.view = "landing"
      st.rerun()


# ==========================================
# 3. TELA: PAINEL DO ADMINISTRADOR
# ==========================================
def render_admin_dashboard():
  st.title("🛠️ Painel do Administrador")

  if st.button("Sair para o Início"):
    st.session_state.view = "landing"
    st.rerun()

  st.divider()

  tab1, tab2 = st.tabs(["👥 Funcionários", "📁 Grupos"])

  with tab1:
    st.subheader("Gerenciar Funcionários")

    with st.form("form_add_emp", clear_on_submit=True):
      col_a, col_b = st.columns(2)
      with col_a:
        name = st.text_input("Nome completo")
        username = st.text_input("Usuário (login)")
      with col_b:
        password = st.text_input("Senha", type="password")
        dept = st.selectbox("Departamento", list(DEPT_COLORS.keys()))

      submit_emp = st.form_submit_button("Cadastrar Funcionário")
      if submit_emp:
        if not name or not username or not password:
          st.error("Preencha todos os campos!")
        elif any(e["username"] == username for e in st.session_state.employees):
          st.error("Já existe um funcionário com esse usuário.")
        else:
          new_emp = {
              "id": "e_" + str(int(datetime.now().timestamp() * 1000)),
              "name": name,
              "username": username,
              "password": password,
              "department": dept,
          }
          st.session_state.employees.append(new_emp)
          st.success(f"Funcionário {name} cadastrado com sucesso!")
          st.rerun()

    st.divider()
    st.markdown("### Funcionários Cadastrados")
    if not st.session_state.employees:
      st.caption("Nenhum funcionário cadastrado ainda.")
    else:
      for emp in st.session_state.employees:
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
          st.write(f"**{emp['name']}** (`@{emp['username']}`)")
        with c2:
          st.caption(f"Depto: {emp['department']}")
        with c3:
          if st.button("Remover", key=f"del_emp_{emp['id']}"):
            st.session_state.employees = [
                e for e in st.session_state.employees if e["id"] != emp["id"]
            ]
            st.rerun()

  with tab2:
    st.subheader("Gerenciar Grupos")

    with st.form("form_add_grp", clear_on_submit=True):
      grp_name = st.text_input("Nome do Grupo (ex: Time de Vendas)")
      member_options = {e["name"]: e["id"] for e in st.session_state.employees}
      selected_member_names = st.multiselect(
          "Selecione os membros", options=list(member_options.keys())
      )

      submit_grp = st.form_submit_button("Criar Grupo")
      if submit_grp:
        if not grp_name or not selected_member_names:
          st.error("Informe o nome do grupo e selecione ao menos um membro.")
        else:
          member_ids = [member_options[name] for name in selected_member_names]
          new_grp = {
              "id": "g_" + str(int(datetime.now().timestamp() * 1000)),
              "name": grp_name,
              "members": member_ids,
          }
          st.session_state.groups.append(new_grp)
          st.success(f"Grupo '{grp_name}' criado com sucesso!")
          st.rerun()

    st.divider()
    st.markdown("### Grupos Criados")
    if not st.session_state.groups:
      st.caption("Nenhum grupo criado ainda.")
    else:
      for grp in st.session_state.groups:
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
          st.write(f"**{grp['name']}**")
        with c2:
          st.caption(f"{len(grp['members'])} membro(s)")
        with c3:
          if st.button("Remover", key=f"del_grp_{grp['id']}"):
            st.session_state.groups = [
                g for g in st.session_state.groups if g["id"] != grp["id"]
            ]
            st.rerun()


# ==========================================
# 4. TELA: LOGIN DE FUNCIONÁRIO
# ==========================================
def render_employee_login():
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.subheader("Entrar no Chat")
    st.caption("Use o usuário e a senha cadastrados pelo administrador.")

    username = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.session_state.error_msg:
      st.error(st.session_state.error_msg)

    if st.button("Entrar", use_container_width=True):
      emp = next(
          (
              e
              for e in st.session_state.employees
              if e["username"] == username.strip() and e["password"] == pwd
          ),
          None,
      )
      if emp:
        st.session_state.current_user = emp
        st.session_state.error_msg = ""
        st.session_state.view = "chat"
        st.rerun()
      else:
        st.session_state.error_msg = "Usuário ou senha inválidos."
        st.rerun()

    if st.button("Voltar", use_container_width=True):
      st.session_state.view = "landing"
      st.rerun()


# ==========================================
# 5. TELA: APLICAÇÃO DE CHAT PRINCIPAL
# ==========================================
def render_chat_app():
  me = st.session_state.current_user

  # Barra Lateral (Sidebar) para conversas
  with st.sidebar:
    st.write(f"👤 **{me['name']}**")
    st.caption(f"Depto: {me['department']}")
    if st.button("Sair / Logout"):
      st.session_state.current_user = None
      st.session_state.active_conv = None
      st.session_state.view = "landing"
      st.rerun()

    st.divider()
    st.markdown("### Conversas")

    # Listar conversas individuais (outros funcionários)
    others = [e for e in st.session_state.employees if e["id"] != me["id"]]
    my_groups = [g for g in st.session_state.groups if me["id"] in g["members"]]

    st.caption("Mensagens Diretas")
    for other in others:
      # Cria um ID único consistente para o chat DM entre dois usuários
      dm_key = "dm:" + "_".join(sorted([me["id"], other["id"]]))
      label = f"💬 {other['name']} ({other['department']})"
      if st.button(label, key=f"btn_dm_{other['id']}", use_container_width=True):
        st.session_state.active_conv = ("ind", dm_key, other["name"])
        st.rerun()

    if my_groups:
      st.caption("Grupos")
      for grp in my_groups:
        grp_key = "grp:" + grp["id"]
        label = f"👥 {grp['name']}"
        if st.button(
            label, key=f"btn_grp_{grp['id']}", use_container_width=True
        ):
          st.session_state.active_conv = ("grp", grp_key, grp["name"])
          st.rerun()

  # Área principal do Chat
  if not st.session_state.active_conv:
    st.info("👈 Selecione uma conversa na barra lateral para começar a conversar.")
  else:
    conv_type, conv_id, conv_name = st.session_state.active_conv
    st.subheader(f"Conversa: {conv_name}")
    st.divider()

    # Container de mensagens com rolagem simulada
    chat_container = st.container(height=400)

    # Filtrar mensagens da conversa atual
    conv_messages = [
        m for m in st.session_state.messages if m["convId"] == conv_id
    ]

    with chat_container:
      if not conv_messages:
        st.caption("Nenhuma mensagem ainda. Envie a primeira!")
      else:
        for m in conv_messages:
          sender = next(
              (
                  e
                  for e in st.session_state.employees
                  if e["id"] == m["senderId"]
              ),
              None,
          )
          sender_name = sender["name"] if sender else "Desconhecido"
          is_me = m["senderId"] == me["id"]

          if is_me:
            st.markdown(
                f"<div style='text-align: right; margin-bottom: 8px;'><b"
                f" style='color: #E8A33D;'>Você</b> <span"
                f" style='font-size: 11px; color: gray;'>({format_time(m['ts'])})</span><br><div"
                f" style='display: inline-block; background: #E8A33D33;"
                f" padding: 8px 12px; border-radius: 10px; text-align:"
                f" left;'>{m['text']}</div></div>",
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                f"<div style='text-align: left; margin-bottom: 8px;'><b"
                f" style='color: #2F8F82;'>{sender_name}</b> <span"
                f" style='font-size: 11px; color: gray;'>({format_time(m['ts'])})</span><br><div"
                f" style='display: inline-block; background: #f0f2f6; padding:"
                f" 8px 12px; border-radius: 10px;'>{m['text']}</div></div>",
                unsafe_allow_html=True,
            )

    # Caixa de envio de mensagem
    with st.form(
        key=f"form_msg_{conv_id}", clear_on_submit=True
    ):  # Chave dinâmica para limpar o input após envio
      col_input, col_btn = st.columns([5, 1])
      with col_input:
        msg_text = st.text_input(
            "Mensagem", label_visibility="collapsed", placeholder="Digite sua mensagem..."
        )
      with col_btn:
        send_pressed = st.form_submit_button("Enviar ➔", use_container_width=True)

      if send_pressed and msg_text.strip():
        new_msg = {
            "id": str(int(datetime.now().timestamp() * 1000)),
            "convId": conv_id,
            "senderId": me["id"],
            "text": msg_text.strip(),
            "ts": int(datetime.now().timestamp() * 1000),
        }
        st.session_state.messages.append(new_msg)
        st.rerun()


# ==========================================
# ROTEADOR DE TELAS
# ==========================================
if st.session_state.view == "landing":
  render_landing()
elif st.session_state.view == "adminLogin":
  render_admin_login()
elif st.session_state.view == "admin":
  render_admin_dashboard()
elif st.session_state.view == "employeeLogin":
  render_employee_login()
elif st.session_state.view == "chat":
  render_chat_app()
