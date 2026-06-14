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

# 2. Definição do Arquivo de Histórico Local no Servidor
ARQUIVO_HISTORICO = "historico_chat.txt"

# 3. Inicializa as variáveis na memória da página (session_state)
if "historico_visual" not in st.session_state:
    st.session_state.historico_visual = []

# 4. FUNÇÃO: Tenta carregar o histórico salvo do arquivo texto ao iniciar o app
if "historico_carregado" not in st.session_state:
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            for linha in linhas:
                if linha.startswith("Você: "):
                    txt = linha.replace("Você: ", "").strip()
                    st.session_state.historico_visual.append({"role": "user", "content": txt})
                elif linha.startswith("Gemini: "):
                    txt = linha.replace("Gemini: ", "").strip()
                    st.session_state.historico_visual.append({"role": "assistant", "content": txt})
        except Exception as e:
            st.sidebar.error(f"Erro ao ler histórico: {e}")
    st.session_state.historico_carregado = True

# 5. Barra Lateral com Opções
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
            st.success("Histórico salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# 6. Exibe o histórico de mensagens na tela com o visual de chat do Streamlit
for message in st.session_state.historico_visual:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Entrada de novas mensagens e Processamento Direto
if user_input := st.chat_input("Digite sua mensagem..."):
    # Mostra e guarda o texto do usuário
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.historico_visual.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # Cria um cliente limpo e novo a cada requisição
                client = genai.Client()
                
                # Monta a estrutura de histórico exigida pelo método generate_content
                historico_completo = []
                for msg in st.session_state.historico_visual:
                    role_ia = "user" if msg["role"] == "user" else "model"
                    historico_completo.append(
                        types.Content(
                            role=role_ia,
                            parts=[types.Part.from_text(text=msg["content"])]
                        )
                    )
                
                # Envia o bloco de histórico inteiro para a API responder contextualmente
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=historico_completo
                )
                
                st.markdown(response.text)
                st.session_state.historico_visual.append({"role": "assistant", "content": response.text})
            except Exception as error:
                st.error(f"Erro de conexão: {error}")
