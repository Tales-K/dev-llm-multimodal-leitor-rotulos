"""Prática 6 · Assistente multimodal com gr.ChatInterface (Encontro 3, blocos 3.1 a 3.4).

O que este assistente faz:
- recebe texto, imagens, PDFs e áudio (arquivo ou microfone);
- transcreve o áudio (Whisper) e mostra ao usuário o que entendeu;
- lembra da conversa com a estratégia de memória escolhida na tela;
- mostra a resposta enquanto o modelo escreve (streaming);
- opcionalmente, lê a resposta em voz alta (síntese de fala);
- mostra, a cada resposta, quantos tokens foram enviados e quanto custou.

Como rodar, a partir da pasta raiz do projeto:
    python app/assistente.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr  # noqa: E402

from src.audio import sintetizar, transcrever  # noqa: E402
from src.cliente import chamar_modelo_stream  # noqa: E402
from src.config import PASTA_DADOS  # noqa: E402
from src.contexto import eh_audio, eh_imagem, eh_pdf, ler_historico_gradio, montar_historico  # noqa: E402
from src.documentos import preparar_pdf  # noqa: E402
from src.midia import gerar_cupom, mensagem  # noqa: E402
from src.prompts import carregar  # noqa: E402

SISTEMA, _ = carregar("assistente_v1")
MAX_TURNOS = 4                 # janela: as últimas 4 trocas (pergunta e resposta)

CUPOM = PASTA_DADOS / "exemplos" / "cupom_exemplo.png"
gerar_cupom("LANCHONETE EXEMPLO LTDA", "31/10/2026",
            [("X-SALADA", 24.90), ("SUCO LARANJA", 9.00), ("PAO DE QUEIJO", 9.00)], CUPOM)


def responder(message, history, memoria, ler_em_voz):
    """Chamada pelo Gradio a cada mensagem.

    message:  {"text": "...", "files": ["caminho", ...]}   (a mensagem nova)
    history:  as mensagens anteriores, guardadas pelo próprio Gradio
    memoria, ler_em_voz: valores dos controles extras (additional_inputs)
    Cada 'yield' atualiza a tela: (texto da resposta, áudio, painel de consumo).
    """
    texto = (message.get("text") or "").strip()
    arquivos = message.get("files") or []
    imagens = [a for a in arquivos if eh_imagem(a)]
    prefixo, extra = "", ""

    # 1. Áudio: transcrever e mostrar o que foi entendido (o usuário confere antes de confiar)
    for a in [a for a in arquivos if eh_audio(a)][:1]:
        yield "_Transcrevendo o áudio..._", None, ""
        try:
            fala = transcrever(a)
        except RuntimeError as erro:
            raise gr.Error(str(erro), title="Erro")
        prefixo = f"_Você disse:_ «{fala}»\n\n"
        texto = f"{texto} {fala}".strip()

    # 2. PDF: texto extraído das páginas digitais; páginas escaneadas vão como imagem
    for p in [a for a in arquivos if eh_pdf(a)][:1]:
        conteudo_pdf, paginas = preparar_pdf(p, max_paginas=3)
        imagens += paginas
        extra = f"\n\nConteúdo do documento {Path(p).name}:\n{conteudo_pdf}"
        prefixo += f"_Documento lido: {Path(p).name}._\n\n"

    if not texto and not imagens:
        raise gr.Error("Escreva uma pergunta ou envie uma imagem, um PDF ou um áudio.", title="Erro")
    pergunta = texto or "Descreva o que você vê e o que pode ser útil para mim."

    # 3. Memória: o Gradio entrega o histórico inteiro; nós escolhemos o que reenviar
    historico = montar_historico(ler_historico_gradio(history), estrategia=memoria, max_turnos=MAX_TURNOS)
    conteudo = mensagem(pergunta + extra, imagens) if imagens else pergunta + extra

    # 4. Streaming: cada pedaço novo atualiza a resposta na tela
    info, resposta = {}, prefixo
    try:
        for pedaco in chamar_modelo_stream(conteudo, sistema=SISTEMA, historico=historico,
                                           etiqueta="p6-assistente", info=info):
            resposta += pedaco
            yield resposta, None, "_Escrevendo..._"
    except RuntimeError as erro:
        raise gr.Error(f"O modelo não respondeu agora. {erro}", title="Erro")

    # 5. Painel de consumo e, se pedido, a resposta em voz alta
    painel = (f"Memória **{memoria}**: {len(historico)} mensagens reenviadas · "
              f"{info['tok_entrada']} tokens de entrada · {info['tok_saida']} de saída · "
              f"primeiro pedaço em {info['ttft']:.1f} s · total {info['latencia']:.1f} s · "
              f"US$ {info['custo']:.5f} · {info['provedor']}")
    audio = sintetizar(info["texto"]) if ler_em_voz else None
    if ler_em_voz and audio is None:
        gr.Warning("A síntese de fala não está disponível agora; a resposta segue só em texto.", title="Atenção")
    yield resposta, audio, painel


with gr.Blocks(title="Assistente multimodal") as demo:
    audio_saida = gr.Audio(label="Resposta em voz", autoplay=True, interactive=False, render=False)
    painel = gr.Markdown(render=False)
    gr.ChatInterface(
        responder,
        multimodal=True,
        textbox=gr.MultimodalTextbox(file_types=["image", ".pdf", "audio"], sources=["upload", "microphone"],
                                     placeholder="Pergunte, anexe uma imagem ou PDF, ou grave um áudio"),
        additional_inputs=[gr.Radio(["nenhuma", "completa", "janela"], value="janela", label="Memória", render=False),
                           gr.Checkbox(False, label="Ler a resposta em voz alta", render=False)],
        additional_inputs_accordion=gr.Accordion("Configurações", open=True, render=False),
        additional_outputs=[audio_saida, painel],
        examples=[[{"text": "Qual é o total deste cupom e qual item foi o mais caro?", "files": [str(CUPOM)]}],
                  [{"text": "Explique em duas frases o que é uma API stateless.", "files": []}]],
        title="Assistente multimodal",
        description="Imagens, PDFs e áudio. Não envie dados pessoais: as mensagens vão para uma API de plano gratuito.",
        save_history=True,
        api_name="conversar",
    )
    painel.render()
    audio_saida.render()


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="cyan"))
