import streamlit as st
import time

# Configuração da página para parecer um aplicativo
st.set_page_config(
    page_title="WhatsApp Clone - Python",
    page_icon="💬",
    layout="centered"
)

# Estilização CSS personalizada para dar um toque semelhante ao WhatsApp
st.markdown("""
    <style>
    .stChatInput {
        position: fixed;
        bottom: 0;
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 WhatsApp Web (Python Edition)")
st.write("Um protótipo rápido de chat usando Streamlit.")

# Inicializa o histórico de mensagens no estado da sessão do Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou seu assistente virtual. Como posso ajudar você hoje?"}
    ]

# Exibe o histórico de mensagens na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Caixa de texto para digitar a mensagem (fica fixada embaixo)
if prompt := st.chat_input("Digite uma mensagem..."):
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Exibe a mensagem do usuário imediatamente
    with st.chat_message("user"):
        st.markdown(prompt)

    # Simula a resposta do bot (ou de outro usuário)
    with st.chat_message("assistant"):
        with st.spinner("Digitando..."):
            time.sleep(1) # Simula o tempo de resposta
            
            # Resposta automática simples baseada no que o usuário digitou
            if "olá" in prompt.lower() or "tudo bem" in prompt.lower():
                response = "Olá! Tudo ótimo por aqui, e com você?"
            elif "python" in prompt.lower():
                response = "Python é incrível para criar desde scripts simples até aplicações web completas!"
            else:
                response = f"Entendi o que você disse sobre: '{prompt}'. Muito interessante!"
                
            st.markdown(response0 := response)
            
    # Adiciona a resposta do assistente ao histórico
    st.session_state.messages.append({"role": "assistant", "content": response})
