"""Demonstração · Uma prévia do Pydantic AI (Encontro 3, apresentado pelo professor; aprofundado no Encontro 4).

O que já fazemos à mão em src/cliente.py (esquema Pydantic, validação, retentativa) é exatamente o que
um framework de agentes como o Pydantic AI empacota. Compare:

    Nosso projeto:  chamar_modelo(mensagem(...), esquema=NotaFiscal)  ->  r.conteudo (NotaFiscal)
    Pydantic AI:    agente.run_sync([...])                             ->  resultado.output (NotaFiscal)

O que o Pydantic AI acrescenta:
  - output_type: a saída já volta validada; se o modelo errar o formato, o agente devolve o erro de
    validação ao modelo e pede de novo, sozinho (retries);
  - ferramentas (tools): funções Python que o modelo pode decidir chamar, com parâmetros validados;
  - o mesmo código para vários provedores.

Instalação (opcional, não está no requirements.txt):
    pip install "pydantic-ai-slim[openai]"
Como rodar, a partir da pasta raiz do projeto:
    python praticas/demo_pydantic_ai.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, BinaryContent  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402

from src.config import PASTA_DADOS, PROVEDOR, PROVEDORES, ler_chave  # noqa: E402
from src.esquemas import NotaFiscal  # noqa: E402
from src.midia import gerar_cupom  # noqa: E402
from src.validacao import conferir  # noqa: E402

# 1. O modelo: o mesmo provedor do projeto, pelo formato compatível com a OpenAI (endereço + chave do .env)
cfg = PROVEDORES[PROVEDOR]
modelo = OpenAIChatModel(cfg["modelo"], provider=OpenAIProvider(base_url=cfg["base_url"],
                                                                api_key=ler_chave(cfg["chave"])))

# 2. O agente: instruções + tipo de saída. A classe NotaFiscal é a mesma de src/esquemas.py.
agente = Agent(
    modelo,
    output_type=NotaFiscal,
    instructions="Você extrai dados de cupons fiscais brasileiros. Use null para o que não estiver legível.",
    retries=2,                         # quantas vezes pode pedir ao modelo para corrigir um formato inválido
)


# 3. Uma ferramenta: o modelo PODE chamar esta função se julgar útil. A docstring vira a descrição.
@agente.tool_plain
def somar_itens(valores: list[float]) -> float:
    """Soma os valores dos itens do cupom, para conferir o total."""
    return round(sum(valores), 2)


if __name__ == "__main__":
    cupom = PASTA_DADOS / "exemplos" / "cupom_pydantic_ai.png"
    gerar_cupom("PADARIA EXEMPLO", "10/11/2026", [("CAFE", 6.50), ("PAO NA CHAPA", 8.00)], cupom)   # cupom fictício
    imagem = BinaryContent(data=cupom.read_bytes(), media_type="image/png")

    resultado = agente.run_sync(["Extraia os dados deste cupom.", imagem])

    nota = resultado.output                      # já é um objeto NotaFiscal, validado
    print("Tipo da saída:", type(nota).__name__)
    print(nota.model_dump_json(indent=2))
    print("Problemas pelas regras de negócio:", conferir(nota) or "nenhum")
    print(f"Uso: {resultado.usage.input_tokens} tokens de entrada, {resultado.usage.output_tokens} de saída, "
          f"{resultado.usage.requests} chamada(s) ao modelo")
