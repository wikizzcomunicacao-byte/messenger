import streamlit as st
import time
import os
import json

# Configuração da página
st.set_page_config(
    page_title="WhatsApp Clone - Python",
    page_icon="💬",
    layout="centered"
)

# Estilização CSS personalizada para melhorar a barra de input e a aparência geral
st.markdown("""
    <style>
    /* Ajusta a barra de chat inferior */
    .stChatInput {
        position: fixed;
        bottom: 0;
        background-color: transparent;
        padding-bottom: 20px;
    }
    /* Estilo de balões para parecer mais com o WhatsApp */
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 WhatsApp Web (Python Edition)")

# Arquivo JSON simples para simular um banco de dados de chat compartilhado
DB_FILE = "chat_messages.json"

def carregar_mensagens():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return [
        {"user": "Sistema", "avatar": "🤖", "content": "Bem-vindo ao chat em tempo real!"}
    ]

def salvar_mensagens(msgs):
    with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(msgs, f, ensure_ascii=False, indent=4)

# --- SISTEMA DE LOGIN / PERFIL ---
with st.sidebar:
    st.header("⚙️ Configurações do Chat")
    username = st.text_input("Seu Nome de Usuário:", value="Visitante")
    avatar_choice = st.selectbox("Escolha seu ícone/avatar:", ["👤", "😎", "🚀", "🐱", "🦊", "💻", "⭐"])
    
    st.markdown("---")
    st.info(fLogan := f"Logado como: **{avatar_choice} {username}**")
    
    if st.button("🗑️ Limpar Conversa (Global)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.rerun()

# --- HISTÓRICO DE MENSAGENS ---
mensagens = carregar_mensagens()

# Atualizador automático a cada 3 segundos para ver mensagens de outros usuários
st.markdown("""
    <meta http-equiv="refresh" content="3">
""", unsafe_allow_html=True)

# Exibe todas as mensagens salvas
for msg in mensagens:
    # Define o papel visual com base em quem enviou
    role = "user" if msg.get("user") == username else "assistant"
    with st.chat_message(role, avatar=msg.get("avatar", "👤")):
        st.markdown(f"**{msg.get('user', 'Desconhecido')}**: {msg.get('content', '')}")

# --- CAIXA DE ENTRADA DE MENSAGEM ---
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    if not username.strip():
        st.warning("Por favor, digite um nome de usuário na barra lateral antes de enviar mensagens.")
    else:
        # Cria a nova mensagem
        nova_msg = {
            "user": username,
            "avatar": avatar_choice,
            "content": prompt
        }
        
        # Adiciona ao histórico e salva
        mensagens.append(nova_msg)
        salvar_mensagens(mensagens)
        
        # Recarrega a página para exibir instantaneamente
        st.rerun()
