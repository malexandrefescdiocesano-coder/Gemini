import os
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Meu Chat Gemini", page_icon="🤖")
st.title("🤖 Meu Chat com Gemini")

# 1. Configuração Segura da API Key (Puxa dos Secrets do Streamlit Cloud)
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
else:
    # Caso você queira testar localmente antes de subir
    os.environ["GEMINI_API_KEY"] = st.sidebar.text_input("Insira sua Gemini API Key:", type="password")

if not os.environ.get("GEMINI_API_KEY"):
    st.info("Por favor, adicione sua API Key para começar.", icon="🔑")
    st.stop()

# Estabiliza o cliente de rede na memória de sessão do Streamlit
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client()

# 2. Definição do Arquivo de Histórico Local
ARQUIVO_HISTORICO = "historico_chat.txt"

# 3. Inicializa as variáveis na memória da página (session_state)
if "mensagens_ia" not in st.session_state:
    st.session_state.mensagens_ia = []
if "historico_visual" not in st.session_state:
    st.session_state.historico_visual = []

# 4. FUNÇÃO: Tenta carregar o histórico salvo do arquivo texto
if "historico_carregado" not in st.session_state:
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            for linha in linhas:
                if linha.startswith("Você: "):
                    txt = linha.replace("Você: ", "").strip()
                    st.session_state.historico_visual.append({"role": "user", "content": txt})
                    st.session_state.mensagens_ia.append(types.Content(role="user", parts=[types.Part.from_text(text=txt)]))
                elif linha.startswith("Gemini: "):
                    txt = linha.replace("Gemini: ", "").strip()
                    st.session_state.historico_visual.append({"role": "assistant", "content": txt})
                    st.session_state.mensagens_ia.append(types.Content(role="model", parts=[types.Part.from_text(text=txt)]))
        except Exception as e:
            st.sidebar.error(f"Erro ao ler histórico: {e}")
    st.session_state.historico_carregado = True

# 5. Cria o chat usando o cliente estabilizado na sessão
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.gemini_client.chats.create(
        model="gemini-2.5-flash",
        history=st.session_state.mensagens_ia if st.session_state.mensagens_ia else None
    )

# 6. Barra Lateral com Opções
with st.sidebar:
    st.header("⚙️ Opções")
    if st.button("💾 Salvar Conversa Atual"):
        try:
            texto_final = ""
            for msg in st.session_state.historico_visual:
                autor = "Você" if msg["role"] == "user" else "Gemini"
                texto_final += f"{autor}: {msg['content']}\n"
            with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
                f.write(texto_final)
            st.success("Histórico salvo no servidor do aplicativo!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# 7. Exibe o histórico de mensagens na tela com o visual de chat do Streamlit
for message in st.session_state.historico_visual:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. Entrada de novas mensagens
if user_input := st.chat_input("Digite sua mensagem..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.historico_visual.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.historico_visual.append({"role": "assistant", "content": response.text})
            except Exception as error:
                st.error(f"Erro de conexão: {error}")
