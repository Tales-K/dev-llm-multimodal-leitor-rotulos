"""Prática 4 · A API não tem memória: comparando estratégias de contexto (Encontro 3, bloco 3.2).

Modo roteiro (padrão): a mesma conversa de 5 perguntas sobre um cupom, repetida com cada estratégia
de memória. No fim, uma tabela com os tokens de entrada por pergunta e a resposta da última pergunta,
que testa se o assistente ainda lembra do começo da conversa.

Modo chat: conversa livre no terminal, com a resposta aparecendo aos poucos (streaming).

Como rodar, a partir da pasta raiz do projeto:
    python praticas/p4_conversa.py                              # roteiro com as 4 estratégias
    python praticas/p4_conversa.py --estrategias completa janela
    python praticas/p4_conversa.py --chat --estrategia janela   # conversa livre
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cliente import chamar_modelo, chamar_modelo_stream  # noqa: E402
from src.config import PASTA_DADOS  # noqa: E402
from src.contexto import ESTRATEGIAS, Memoria  # noqa: E402
from src.midia import gerar_cupom, mensagem  # noqa: E402
from src.prompts import carregar  # noqa: E402

SISTEMA, _ = carregar("assistente_v1")

CUPOM = PASTA_DADOS / "exemplos" / "cupom_conversa.png"
ROTEIRO = [
    ("Leia este cupom: qual é o estabelecimento e qual é o total?", True),
    ("Qual foi o item mais caro?", False),
    ("Quanto fica para cada um se dividirmos a conta entre 3 pessoas?", False),
    ("Sugira uma gorjeta de 10% sobre o total, arredondando para cima.", False),
    ("Para fechar: qual era o nome do estabelecimento e a data da compra?", False),   # teste de memória
]


def rodar_roteiro(estrategia, max_turnos, pausa):
    """Executa as 5 perguntas com uma estratégia; devolve os tokens de entrada por turno e a última resposta."""
    memoria = Memoria(estrategia, max_turnos=max_turnos)
    tokens, resposta = [], ""
    for pergunta, com_imagem in ROTEIRO:
        imagens = [CUPOM] if com_imagem else []
        conteudo = mensagem(pergunta, imagens) if imagens else pergunta
        r = chamar_modelo(conteudo, sistema=SISTEMA, historico=memoria.historico(), max_tokens=300,
                          etiqueta=f"p4-{estrategia}")
        resposta = r.conteudo
        tokens.append(r.tok_entrada)
        memoria.registrar(pergunta, resposta, imagens)
        print(f"  {estrategia:<9} pergunta {len(tokens)}: {r.tok_entrada:>5} tokens de entrada"
              f"{' (cache)' if r.do_cache else ''}")
        time.sleep(pausa)
    return tokens, resposta, memoria.chamadas_de_resumo


def modo_roteiro(estrategias, max_turnos, pausa):
    gerar_cupom("CANTINA DONA ROSA LTDA", "07/11/2026",
                [("LASANHA", 46.90), ("SUCO UVA", 11.00), ("AGUA", 6.00), ("PUDIM", 14.50)], CUPOM)
    print(f"Cupom de exemplo: {CUPOM}\n")
    resultados = {}
    for e in estrategias:
        print(f"Estratégia: {e}")
        resultados[e] = rodar_roteiro(e, max_turnos, pausa)
        print()

    print("Tokens de entrada por pergunta (o que você paga a cada envio):\n")
    print("pergunta " + "".join(f"{e:>11}" for e in estrategias))
    for i in range(len(ROTEIRO)):
        print(f"{i + 1:>8} " + "".join(f"{resultados[e][0][i]:>11}" for e in estrategias))
    print("   total " + "".join(f"{sum(resultados[e][0]):>11}" for e in estrategias))
    print("\nResposta à pergunta 5 (o assistente ainda lembra do começo?):")
    for e in estrategias:
        tokens, resposta, resumos = resultados[e]
        extra = f" [+{resumos} chamada(s) de resumo]" if resumos else ""
        print(f"\n[{e}]{extra}\n  {resposta.strip()[:300]}")
    print("\nTodas as chamadas foram registradas em logs/uso.csv, com a etiqueta p4-<estratégia>.")


def modo_chat(estrategia, max_turnos):
    """Conversa livre. Comandos: /imagem caminho, /memoria, /sair."""
    memoria = Memoria(estrategia, max_turnos=max_turnos)
    imagens = []
    print(f"Conversa com memória '{estrategia}'. Comandos: /imagem caminho  /memoria  /sair\n")
    while True:
        try:
            pergunta = input("você> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not pergunta:
            continue
        if pergunta == "/sair":
            break
        if pergunta.startswith("/imagem"):
            caminho = pergunta.split(maxsplit=1)[-1]
            if Path(caminho).exists():
                imagens = [caminho]
                print(f"(imagem anexada à próxima pergunta: {caminho})")
            else:
                print("(arquivo não encontrado)")
            continue
        if pergunta == "/memoria":
            for m in memoria.historico():
                print(f"  {m['role']}: {str(m['content'])[:90]}")
            print(f"  resumo: {memoria.resumo or '(nenhum)'}")
            continue
        conteudo = mensagem(pergunta, imagens) if imagens else pergunta
        info = {}
        print("assistente> ", end="", flush=True)
        for pedaco in chamar_modelo_stream(conteudo, sistema=SISTEMA, historico=memoria.historico(),
                                           etiqueta=f"p4-chat-{estrategia}", info=info):
            print(pedaco, end="", flush=True)
        print(f"\n  ({info['tok_entrada']} tokens de entrada · primeiro pedaço em {info['ttft']:.1f} s"
              f" · total {info['latencia']:.1f} s)\n")
        memoria.registrar(pergunta, info["texto"], imagens)
        imagens = []


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estrategias", nargs="+", default=list(ESTRATEGIAS), choices=ESTRATEGIAS)
    ap.add_argument("--max-turnos", type=int, default=2, help="trocas mantidas pela janela e pelo resumo")
    ap.add_argument("--pausa", type=float, default=2.0, help="segundos entre chamadas (limite por minuto)")
    ap.add_argument("--chat", action="store_true", help="conversa livre no terminal")
    ap.add_argument("--estrategia", default="janela", choices=ESTRATEGIAS, help="estratégia do modo chat")
    a = ap.parse_args()
    if a.chat:
        modo_chat(a.estrategia, a.max_turnos)
    else:
        modo_roteiro(a.estrategias, a.max_turnos, a.pausa)
