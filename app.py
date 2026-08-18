from datetime import datetime
import pytz

# Configuração de fuso horário local (Horário de Brasília)
fuso_brasilia = pytz.timezone("America_Sao_Paulo")

# TELA DE LOGIN COM RESTRIÇÃO DE HORÁRIO
if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Login - Chat Corporativo</h2>", unsafe_allow_html=True)
    
    agora_local = datetime.now(fuso_brasilia)
    hora_atual = agora_local.hour
    dia_semana = agora_local.weekday()  # 0 a 4 = Segunda a Sexta, 5 e 6 = Sábado e Domingo
    
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

                # Define o expediente (Ex: Segunda a Sexta, das 07:00 às 19:00)
                fora_do_expediente = (hora_atual < 7 or hora_atual >= 19 or dia_semana >= 5)

                if fora_do_expediente and not eh_admin:
                    st.error("⏰ Acesso bloqueado fora do horário de expediente corporativo (07:00 às 19:00, Seg-Sex).")
                elif senha_input == dados_usuario.get("senha", "123456"):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = dados_usuario
                    registrar_log(dados_usuario['id'], dados_usuario['nome'], dados_usuario['setor'], "LOGIN", f"Login realizado às {agora_local.strftime('%H:%M')}")
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
    st.stop()
