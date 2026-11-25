"""Prática 5 · Extrator de notas fiscais com interface em Gradio Blocks (Encontro 3, bloco 3.3).

A interface é só uma camada fina: toda a lógica já existe em src/ (Encontro 2).
    src/midia.py      prepara a imagem      src/cliente.py   chama o modelo
    src/esquemas.py   valida o formato      src/validacao.py confere as regras
    src/documentos.py lê PDFs (página como texto ou como imagem)

Como rodar, a partir da pasta raiz do projeto:
    python app/extrator.py
e abra o endereço que aparecer no terminal (normalmente http://127.0.0.1:7860).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr  # noqa: E402
from PIL import Image  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from src.cliente import chamar_modelo  # noqa: E402
from src.config import PASTA_DADOS  # noqa: E402
from src.contexto import eh_imagem, eh_pdf  # noqa: E402
from src.documentos import preparar_pdf  # noqa: E402
from src.esquemas import NotaFiscal  # noqa: E402
from src.midia import gerar_cupom, mensagem  # noqa: E402
from src.prompts import carregar  # noqa: E402
from src.uso import custo  # noqa: E402
from src.validacao import conferir  # noqa: E402

SISTEMA, USUARIO = carregar("extracao_v1")

# Cupons de exemplo: um correto e um com data no futuro (deve ir para revisão humana)
EXEMPLOS = PASTA_DADOS / "exemplos"
gerar_cupom("LANCHONETE EXEMPLO LTDA", "31/10/2026",
            [("X-SALADA", 24.90), ("SUCO LARANJA", 9.00), ("PAO DE QUEIJO", 9.00)], EXEMPLOS / "cupom_exemplo.png")
gerar_cupom("MERCADO BOA VISTA", "15/03/2027",
            [("ARROZ 5KG", 27.90), ("FEIJAO 1KG", 8.49), ("CAFE 500G", 19.90)], EXEMPLOS / "cupom_data_futura.png")


def extrair(arquivo, lado_max):
    """Recebe o caminho do arquivo enviado e devolve as 4 saídas da tela, na ordem de 'outputs'."""
    lado_max = int(lado_max)                                # pela API, o valor do Radio chega como texto
    if not arquivo:
        raise gr.Error("Envie a foto de um cupom ou um PDF antes de clicar em Extrair.", title="Erro")

    # 1. Preparar a entrada: imagem direto; PDF vira texto extraído e/ou páginas como imagem
    pedido = USUARIO
    if eh_pdf(arquivo):
        texto_pdf, imagens = preparar_pdf(arquivo, max_paginas=2)
        pedido += f"\n\nConteúdo do documento:\n{texto_pdf}"
    elif eh_imagem(arquivo):
        imagens = [arquivo]
    else:
        raise gr.Error("Formato não suportado. Use PNG, JPG, WEBP ou PDF.", title="Erro")
    vista = None
    if imagens:
        vista = Image.open(imagens[0]).convert("RGB")
        vista.thumbnail((lado_max, lado_max))              # exatamente o tamanho que vai para a API

    # 2. Chamar o modelo pelo cliente do projeto (retentativa, reserva, cache e registro já estão lá)
    try:
        r = chamar_modelo(mensagem(pedido, imagens, lado_max=lado_max), esquema=NotaFiscal,
                          sistema=SISTEMA, etiqueta="p5-extrator")
    except ValidationError:
        raise gr.Error("O modelo respondeu fora do formato esperado. Tente de novo ou use outra imagem.", title="Erro")
    except RuntimeError as erro:
        raise gr.Error(f"Não foi possível falar com o modelo agora. {erro}", title="Erro")

    # 3. Regras de negócio e decisão
    nota = r.conteudo
    problemas = conferir(nota)
    if problemas:
        decisao = "### ⚠ Revisão humana\n" + "\n".join(f"- {p}" for p in problemas)
        gr.Warning("Esta nota precisa de revisão humana.", title="Atenção")
    else:
        decisao = "### ✔ Segue automaticamente\nNenhum problema nas regras de negócio."

    # 4. Transparência: quanto custou e de onde veio
    lado = f"{vista.width} x {vista.height} px" if vista else "só texto"
    consumo = (f"**{r.provedor}** · `{r.modelo}` · imagem enviada: {lado}  \n"
               f"{r.tok_entrada} tokens de entrada · {r.tok_saida} de saída · {r.latencia:.1f} s · "
               f"US$ {custo(r.provedor, r.tok_entrada, r.tok_saida):.5f}" + (" · resposta do cache" if r.do_cache else ""))
    return vista, decisao, nota.model_dump(), consumo


with gr.Blocks(title="Extrator de notas fiscais") as demo:
    gr.Markdown("# Extrator de notas fiscais\n"
                "Envie a foto de um cupom ou um PDF de nota. **Não envie documentos com dados pessoais:** "
                "as imagens vão para uma API de plano gratuito.")
    with gr.Row():
        with gr.Column(scale=1):
            arquivo = gr.File(label="Cupom (imagem ou PDF)", file_types=["image", ".pdf"], type="filepath")
            lado_max = gr.Radio([512, 768, 1024], value=1024, label="Lado maior da imagem enviada (px)",
                                info="Menos pixels, menos tokens. Até onde dá para reduzir sem perder a leitura?")
            botao = gr.Button("Extrair dados", variant="primary")
            gr.Examples([[str(EXEMPLOS / "cupom_exemplo.png")], [str(EXEMPLOS / "cupom_data_futura.png")]],
                        inputs=[arquivo], label="Exemplos (cupons fictícios)")
        with gr.Column(scale=1):
            vista = gr.Image(label="O que o modelo recebeu", height=280, interactive=False)
            decisao = gr.Markdown()
            nota = gr.JSON(label="Nota extraída (validada pelo Pydantic)")
            consumo = gr.Markdown()

    # Evento: clique no botão -> função extrair -> 4 saídas. api_name expõe a função como API.
    botao.click(extrair, inputs=[arquivo, lado_max], outputs=[vista, decisao, nota, consumo], api_name="extrair")


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="cyan"))
