"""O chat de texto em Streamlit, usando o mesmo src/ do assistente em Gradio (Encontro 3, bloco 3.3).

Como rodar, a partir da pasta raiz do projeto:
    streamlit run app/chat_streamlit.py

Leia de cima para baixo lembrando que o Streamlit reexecuta o script inteiro a cada mensagem:
a memória precisa ficar no st.session_state, e a conversa é redesenhada a cada execução.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from src.cliente import chamar_modelo_stream  # noqa: E402
from src.contexto import Memoria  # noqa: E402

st.set_page_config(page_title="Assistente", page_icon="💬")
st.title("Assistente (Streamlit)")

with st.sidebar:
    estrategia = st.selectbox("Estratégia de memória", ["janela", "completa", "resumo", "nenhuma"])
    if st.button("Nova conversa"):
        st.session_state.pop("memoria", None)

# Cria a memória só na primeira execução da sessão (ou depois de "Nova conversa" / troca de estratégia)
if "memoria" not in st.session_state or st.session_state.memoria.estrategia != estrategia:
    st.session_state.memoria = Memoria(estrategia)
mem = st.session_state.memoria

for t in mem.turnos:                                   # redesenha a conversa toda
    st.chat_message(t.papel).write(t.texto)

if pergunta := st.chat_input("Pergunte algo"):          # devolve o texto só na execução em que foi enviado
    st.chat_message("user").write(pergunta)
    try:
        resposta = st.chat_message("assistant").write_stream(   # consome o gerador e devolve o texto completo
            chamar_modelo_stream(pergunta, historico=mem.historico(), etiqueta="chat-streamlit"))
    except RuntimeError as erro:                             # sem chave, cota esgotada, provedor fora do ar
        st.error(f"Não foi possível falar com o modelo agora. {erro}")
        st.stop()
    mem.registrar(pergunta, resposta)
