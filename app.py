import os
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Meu Chat Gemini Multiusuário", page_icon="🤖")
st.title("🤖 Meu Chat com Gemini")

# 1. Sistema de Chave Dinâmica (Traga sua própria API Key)
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"] != "":
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
else:
    st.sidebar.header("🔑 Configuração")
    chave_usuario = st.sidebar.text_input(
        "Insira sua Gemini API Key para conversar:", 
        type="password",
        placeholder="AIzaSy..."
    )
        # Link direto para a criação de chaves do Google AI Studio
    st.sidebar.markdown(
        "[Pegue uma chave gratuita aqui](https://aistudio.google.com/app/apikey)"
    )

    if chave_usuario:
        os.environ["GEMINI_API_KEY"] = chave_usuario

if not os.environ.get("GEMINI_API_KEY"):
    st.info("👋 Bem-vindo! Para começar a conversar, insira sua **Gemini API Key** na barra lateral esquerda.", icon="👈")
    st.stop()

# 2. Definição do Arquivo de Histórico Único por Usuário (Usa o final da chave como ID)
id_usuario = os.environ.get("GEMINI_API_KEY")[-12:]
ARQUIVO_HISTORICO = f"historico_{id_usuario}.txt"

# 3. Inicializa as variáveis na memória da página (session_state)
if "historico_visual" not in st.session_state:
    st.session_state.historico_visual = []

# 4. FUNÇÃO: Carrega o histórico exclusivo deste usuário ao iniciar
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
    if st.button("💾 Salvar Minha Conversa"):
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
            
    # BÔNUS: Botão para limpar o histórico se o usuário quiser recomeçar
    if st.button("🗑️ Limpar Conversa Atual"):
        st.session_state.historico_visual = []
        if os.path.exists(ARQUIVO_HISTORICO):
            os.remove(ARQUIVO_HISTORICO)
        st.rerun()

# 6. Exibe o histórico de mensagens exclusivo na tela
for message in st.session_state.historico_visual:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Entrada de novas mensagens e Processamento Direto
if user_input := st.chat_input("Digite sua mensagem..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.historico_visual.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                client = genai.Client()
                
                historico_completo = []
                for msg in st.session_state.historico_visual:
                    role_ia = "user" if msg["role"] == "user" else "model"
                    historico_completo.append(
                        types.Content(
                            role=role_ia,
                            parts=[types.Part.from_text(text=msg["content"])]
                        )
                    )
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=historico_completo
                )
                
                st.markdown(response.text)
                st.session_state.historico_visual.append({"role": "assistant", "content": response.text})
            except Exception as error:
                st.error(f"Erro de conexão: {error}")
