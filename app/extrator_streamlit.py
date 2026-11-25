"""Prática 5B · O mesmo extrator de notas fiscais, agora em Streamlit (Encontro 3, bloco 3.3).

Compare com app/extrator.py (Gradio): a lógica em src/ é exatamente a mesma; só muda a camada da tela.

A diferença central do Streamlit: o script INTEIRO roda de novo, de cima para baixo, a cada interação
(clicar, enviar arquivo, mudar um controle). Por isso:
  - o que precisa sobreviver entre uma execução e outra vai para st.session_state;
  - funções caras podem ser guardadas com @st.cache_data / @st.cache_resource.

Como rodar, a partir da pasta raiz do projeto, com o ambiente ativado:
    streamlit run app/extrator_streamlit.py
O navegador abre sozinho (normalmente http://localhost:8501). Ao salvar o arquivo, a página oferece "Rerun".
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402
from PIL import Image  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from src.cliente import chamar_modelo  # noqa: E402
from src.contexto import eh_imagem, eh_pdf  # noqa: E402
from src.documentos import preparar_pdf  # noqa: E402
from src.esquemas import NotaFiscal  # noqa: E402
from src.midia import mensagem  # noqa: E402
from src.prompts import carregar  # noqa: E402
from src.uso import custo  # noqa: E402
from src.validacao import conferir  # noqa: E402

SISTEMA, USUARIO = carregar("extracao_v1")

# ---------------------------------------------------------------------------
# 1. Configuração da página: precisa ser o primeiro comando do Streamlit
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Extrator de notas fiscais", page_icon="🧾", layout="wide")
st.title("Extrator de notas fiscais")
st.caption("Envie a foto de um cupom ou um PDF de nota. **Não envie documentos com dados pessoais:** "
           "as imagens vão para uma API de plano gratuito.")

# Estado da sessão: sobrevive às reexecuções. Aqui guardamos o histórico de extrações desta aba.
if "historico" not in st.session_state:
    st.session_state.historico = []

# ---------------------------------------------------------------------------
# 2. Barra lateral: controles
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configurações")
    lado_max = st.radio("Lado maior da imagem enviada (px)", [512, 768, 1024], index=2,
                        help="Menos pixels, menos tokens. Até onde dá para reduzir sem perder a leitura?")
    if st.button("Limpar histórico"):
        st.session_state.historico = []
        st.rerun()                                   # força uma nova execução já com o estado limpo

# ---------------------------------------------------------------------------
# 3. Entrada e saída em duas colunas
# ---------------------------------------------------------------------------
esquerda, direita = st.columns(2)
with esquerda:
    enviado = st.file_uploader("Cupom (imagem ou PDF)", type=["png", "jpg", "jpeg", "webp", "pdf"])
    clicou = st.button("Extrair dados", type="primary", disabled=enviado is None)

# st.button devolve True SÓ na execução em que foi clicado; nas próximas, volta a False.
if clicou and enviado is not None:
    # O file_uploader entrega os bytes em memória; o src/ do projeto trabalha com caminhos de arquivo.
    sufixo = Path(enviado.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(enviado.getvalue())
        caminho = tmp.name

    pedido, imagens = USUARIO, []
    if eh_pdf(caminho):
        texto_pdf, imagens = preparar_pdf(caminho, max_paginas=2)
        pedido += f"\n\nConteúdo do documento:\n{texto_pdf}"
    elif eh_imagem(caminho):
        imagens = [caminho]

    with direita:
        try:
            with st.spinner("Lendo a nota..."):                       # indicador enquanto o modelo trabalha
                r = chamar_modelo(mensagem(pedido, imagens, lado_max=lado_max), esquema=NotaFiscal,
                                  sistema=SISTEMA, etiqueta="p5b-streamlit")
        except ValidationError:
            st.error("O modelo respondeu fora do formato esperado. Tente de novo ou use outra imagem.")
            st.stop()                                                 # interrompe esta execução do script
        except RuntimeError as erro:
            st.error(f"Não foi possível falar com o modelo agora. {erro}")
            st.stop()

        nota = r.conteudo
        if imagens:
            vista = Image.open(imagens[0]).convert("RGB")
            vista.thumbnail((lado_max, lado_max))
            st.image(vista, width=260, caption=f"O que o modelo recebeu: {vista.width} x {vista.height} px")

        problemas = conferir(nota)
        if problemas:
            st.warning("**Revisão humana**\n\n" + "\n".join(f"- {p}" for p in problemas))
        else:
            st.success("Segue automaticamente: nenhum problema nas regras de negócio.")

        with st.expander("Resposta bruta do modelo (para depurar)"):
            st.code(r.bruto or "", language="json")      # o texto exatamente como veio, antes do Pydantic
        st.json(nota.model_dump(), expanded=1)                        # a nota validada pelo Pydantic (clique para abrir os itens)
        st.caption(f"{r.provedor} · {r.modelo} · {r.tok_entrada} tokens de entrada · {r.tok_saida} de saída · "
                   f"{r.latencia:.1f} s · US$ {custo(r.provedor, r.tok_entrada, r.tok_saida):.5f}"
                   + (" · resposta do cache" if r.do_cache else ""))

    st.session_state.historico.append({"arquivo": enviado.name, "emitente": nota.emitente,
                                       "total": nota.valor_total, "revisão": "sim" if problemas else "não"})

# ---------------------------------------------------------------------------
# 4. Histórico da sessão: só existe porque está no session_state
# ---------------------------------------------------------------------------
# A métrica fica no fim do script de propósito: assim ela já conta a extração feita NESTA execução.
# (Se ficasse no topo, mostraria o valor antigo, porque o script roda de cima para baixo.)
st.sidebar.metric("Extrações nesta sessão", len(st.session_state.historico))
if st.session_state.historico:
    st.subheader("Extrações desta sessão")
    st.dataframe(st.session_state.historico, width="stretch")
