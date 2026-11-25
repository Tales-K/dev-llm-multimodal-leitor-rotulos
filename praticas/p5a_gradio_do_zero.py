"""Prática 5A · Gradio do zero, em três passos (Encontro 3, bloco 3.3).

Antes de abrir o extrator pronto (app/extrator.py), você monta três interfaces pequenas,
cada uma um degrau acima da anterior, e a terceira já conversa com o modelo pela API.

    Passo 1  gr.Interface      uma função comum vira uma página (sem API, sem chave)
    Passo 2  gr.ChatInterface  um chat de verdade, ligado ao modelo, com resposta em streaming
    Passo 3  gr.Blocks         layout próprio: imagem + pergunta + botão, e a linha de consumo

Como rodar, a partir da pasta raiz do projeto, com o ambiente ativado:
    python praticas/p5a_gradio_do_zero.py 1
    python praticas/p5a_gradio_do_zero.py 2
    python praticas/p5a_gradio_do_zero.py 3
Abra o endereço do terminal (normalmente http://127.0.0.1:7860). Para trocar de passo: Ctrl+C e rode o próximo.

Ao final de cada passo há uma sugestão de MELHORIA, com a solução logo abaixo, comentada.
Tente primeiro sozinho (ou com o Copilot) e só depois descomente a solução para comparar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr  # noqa: E402


# =============================================================================
# PASSO 1 · gr.Interface: a função vem primeiro, a interface é consequência
# =============================================================================
def contar(texto):
    """Uma função Python comum: não sabe nada de interface e pode ser testada sozinha."""
    palavras = len(texto.split())
    tokens = len(texto) // 4                # aproximação: ~4 caracteres por token em português
    return palavras, tokens


def passo1():
    demo = gr.Interface(
        fn=contar,                                          # a função
        inputs=gr.Textbox(label="Cole um texto", lines=6),  # um componente por PARÂMETRO
        outputs=[gr.Number(label="Palavras"),               # um componente por VALOR DEVOLVIDO
                 gr.Number(label="Tokens (estimativa)")],
        title="Contador de tokens",
        description="Quanto custa este texto em tokens? Regra prática: cerca de 4 caracteres por token.",
        examples=[["A API não tem memória: cada chamada começa do zero."]],
    )
    demo.launch()

    # MELHORIA 1: mostrar também o custo estimado em US$ com o preço do provedor (src/uso.py).
    # Solução: acrescente um terceiro valor devolvido e um terceiro componente de saída.
    #   from src.uso import custo
    #   from src.config import PROVEDOR
    #   def contar(texto):
    #       tokens = len(texto) // 4
    #       return len(texto.split()), tokens, f"US$ {custo(PROVEDOR, tokens, 0):.6f}"
    #   outputs=[gr.Number(label="Palavras"), gr.Number(label="Tokens"), gr.Textbox(label="Custo de entrada")]


# =============================================================================
# PASSO 2 · gr.ChatInterface: o chat ligado à API, com streaming
# =============================================================================
def passo2():
    from src.cliente import chamar_modelo_stream
    from src.contexto import ler_historico_gradio, montar_historico

    SISTEMA = "Você é um assistente didático. Responda em português, em no máximo 5 frases."

    def responder(mensagem, history):
        """O Gradio chama esta função a cada mensagem e entrega o histórico da conversa.

        mensagem: o texto que o usuário acabou de enviar
        history:  as mensagens anteriores, no formato do Gradio (lista de dicionários role/content)
        """
        turnos = ler_historico_gradio(history)                    # formato do Gradio -> turnos do projeto
        historico = montar_historico(turnos, estrategia="janela", max_turnos=4)   # o que reenviar à API
        parcial = ""
        for pedaco in chamar_modelo_stream(mensagem, sistema=SISTEMA, historico=historico, etiqueta="p5a-chat"):
            parcial += pedaco
            yield parcial            # yield em vez de return: a tela atualiza a cada pedaço (streaming)

    demo = gr.ChatInterface(
        fn=responder,
        title="Meu primeiro chat com LLM",
        description="Converse e depois pergunte algo sobre uma mensagem anterior: ele lembra? Por quê?",
        examples=["Explique o que é uma janela de contexto", "E qual a diferença para a memória?"],
    )
    demo.launch()

    # MELHORIA 2: deixar o usuário escolher a "personalidade" do assistente.
    # Solução: additional_inputs passa componentes extras como parâmetros adicionais da função.
    #   def responder(mensagem, history, estilo):
    #       sistema = {"Didático": SISTEMA, "Técnico": "Responda como engenheiro sênior, com termos técnicos.",
    #                  "Bem curto": "Responda em uma frase."}[estilo]
    #       ...  # mesmo corpo, usando sistema=sistema
    #   gr.ChatInterface(fn=responder, additional_inputs=[gr.Radio(["Didático", "Técnico", "Bem curto"],
    #                    value="Didático", label="Estilo", render=False)])


# =============================================================================
# PASSO 3 · gr.Blocks: o seu layout, os seus eventos
# =============================================================================
def passo3():
    from src.cliente import chamar_modelo
    from src.midia import mensagem
    from src.uso import custo

    def perguntar_sobre_imagem(imagem, pergunta):
        """Recebe o caminho da imagem e a pergunta; devolve a resposta e a linha de consumo."""
        if not imagem:
            raise gr.Error("Envie uma imagem primeiro.", title="Erro")
        r = chamar_modelo(mensagem(pergunta or "Descreva a imagem.", [imagem], lado_max=768),
                          max_tokens=300, etiqueta="p5a-blocks")
        consumo = (f"`{r.modelo}` · {r.tok_entrada} tokens de entrada · {r.tok_saida} de saída · "
                   f"{r.latencia:.1f} s · US$ {custo(r.provedor, r.tok_entrada, r.tok_saida):.5f}")
        return r.conteudo, consumo

    with gr.Blocks(title="Pergunte à imagem") as demo:
        gr.Markdown("# Pergunte à imagem\nNão envie fotos com pessoas ou dados pessoais: a API é de plano gratuito.")
        with gr.Row():                                     # duas colunas lado a lado
            with gr.Column():
                imagem = gr.Image(type="filepath", label="Imagem")
                pergunta = gr.Textbox(label="Pergunta", value="O que aparece nesta imagem?")
                with gr.Row():
                    botao = gr.Button("Perguntar", variant="primary")
                    limpar = gr.Button("Limpar")
            with gr.Column():
                resposta = gr.Markdown()
                consumo = gr.Markdown()
        # O evento liga o botão à função: entradas -> função -> saídas, na ordem
        botao.click(perguntar_sobre_imagem, inputs=[imagem, pergunta], outputs=[resposta, consumo])
        pergunta.submit(perguntar_sobre_imagem, inputs=[imagem, pergunta], outputs=[resposta, consumo])  # Enter também
        limpar.click(lambda: (None, "", "", ""), inputs=None, outputs=[imagem, pergunta, resposta, consumo])
    demo.launch()

    # MELHORIA 3: um botão "Limpar" que apaga imagem, pergunta e respostas.
    # Solução: um evento sem função Python, que só devolve valores vazios.
    #   limpar = gr.Button("Limpar")
    #   limpar.click(lambda: (None, "", "", ""), inputs=None, outputs=[imagem, pergunta, resposta, consumo])


if __name__ == "__main__":
    passo = sys.argv[1] if len(sys.argv) > 1 else "1"
    {"1": passo1, "2": passo2, "3": passo3}.get(passo, passo1)()
