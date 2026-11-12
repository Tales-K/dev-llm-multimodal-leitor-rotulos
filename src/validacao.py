"""Regras de negócio: a terceira camada de validação (Encontro 2, bloco 2.1).

O esquema garante o formato; estas regras conferem se os valores fazem sentido juntos.
Uma nota com qualquer problema vai para revisão humana.
"""
from datetime import datetime

from src.esquemas import NotaFiscal

LIMITE_REVISAO = 5000.00     # acima deste valor, alguém confere mesmo que tudo pareça certo
TOLERANCIA = 0.05            # diferença aceitável entre o total e a soma dos itens (arredondamentos)


def conferir(nota: NotaFiscal) -> list[str]:
    """Devolve a lista de problemas encontrados; lista vazia = a nota pode seguir automaticamente."""
    problemas = []
    if not nota.emitente:
        problemas.append("emitente não encontrado")
    if nota.valor_total is None:
        problemas.append("total não encontrado")
    try:
        data = datetime.strptime(nota.data or "", "%d/%m/%Y")
        if data > datetime.now():
            problemas.append("data no futuro")
        if data.weekday() >= 5:
            problemas.append("data em fim de semana: revisar")
    except ValueError:
        problemas.append("data ausente ou inválida")
    valores = [i.valor for i in nota.itens if i.valor is not None]
    if nota.valor_total is not None and valores and abs(sum(valores) - nota.valor_total) > TOLERANCIA:
        problemas.append(f"total ({nota.valor_total:.2f}) diferente da soma dos itens ({sum(valores):.2f})")
    if nota.valor_total is not None and nota.valor_total > LIMITE_REVISAO:
        problemas.append("valor alto: revisar")
    return problemas
