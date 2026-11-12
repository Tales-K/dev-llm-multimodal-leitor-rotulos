"""Cliente de LLM: a única porta de saída para os provedores (Encontro 2, blocos 2.1 a 2.3).

Reúne o que uma chamada em produção precisa:
- retentativa só para erros temporários, com backoff exponencial e jitter;
- respeito ao cabeçalho retry-after;
- timeout em toda chamada;
- provedor reserva;
- cache de respostas;
- saída estruturada (JSON Schema a partir de uma classe Pydantic), com descida de nível se o provedor recusar;
- registro de uso (tokens, latência e custo) em logs/uso.csv.
"""
import hashlib
import json
import random
import re
import time
from dataclasses import dataclass

from openai import OpenAI

from src import uso
from src.config import PROVEDOR, PROVEDORES, ler_chave

REPETIR = {408, 429, 500, 502, 503, 504}        # erros temporários: vale tentar de novo
CACHE = {}

# Um cliente por provedor com chave cadastrada; ORDEM = principal primeiro, depois as reservas
clientes = {nome: OpenAI(api_key=ler_chave(cfg["chave"]), base_url=cfg["base_url"])
            for nome, cfg in PROVEDORES.items() if ler_chave(cfg["chave"])}
ORDEM = [PROVEDOR] + [p for p in clientes if p != PROVEDOR] if PROVEDOR in clientes else list(clientes)


@dataclass
class Resposta:
    conteudo: object          # texto ou objeto Pydantic
    tok_entrada: int
    tok_saida: int
    provedor: str
    modelo: str
    latencia: float
    do_cache: bool = False
    bruto: str = ""            # texto exatamente como o modelo devolveu, antes da validação


def _codigo(erro):
    return getattr(erro, "status_code", None)


def _retry_after(erro):
    """Segundos indicados pelo provedor no cabeçalho retry-after, se houver."""
    try:
        return float(erro.response.headers.get("retry-after"))
    except Exception:
        return None


def _espera(erro, tentativa, base=1.0):
    """retry-after tem prioridade; senão, sorteio entre 0 e base × 2^tentativa (full jitter)."""
    ra = _retry_after(erro)
    return ra if ra is not None else random.uniform(0, base * 2 ** tentativa)


def _extrair_json(texto):
    """Lê JSON mesmo quando o modelo o envolve em texto ou em blocos de código."""
    try:
        return json.loads(texto)
    except Exception:
        achado = re.search(r"\{.*\}", texto or "", re.S)
        return json.loads(achado.group(0)) if achado else {}


def _formatos(esquema):
    """Níveis de saída estruturada, do mais forte ao mais fraco (slide 'Três níveis de garantia')."""
    if esquema is None:
        return [None]
    return [{"type": "json_schema", "json_schema": {"name": esquema.__name__, "schema": esquema.model_json_schema()}},
            {"type": "json_object"},
            None]


def chamar_modelo(conteudo, esquema=None, sistema=None, max_tokens=600, tentativas=4,
                  usar_cache=True, etiqueta="", timeout=60):
    """Envia uma mensagem (texto ou lista com texto e imagens) e devolve um objeto Resposta.

    conteudo: texto, ou lista de partes {"type": "text"|"image_url", ...}
    esquema:  classe Pydantic; se informada, a resposta volta como objeto validado
    sistema:  instruções fixas da aplicação (mensagem de sistema)
    """
    if not clientes:
        raise RuntimeError("Nenhuma chave encontrada. Copie .env.example para .env e preencha GROQ_API_KEY ou GEMINI_API_KEY.")
    mensagens = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": conteudo}]

    # 1. Cache: mesmo pedido -> mesma impressão digital (hash) -> resposta guardada
    chave_cache = hashlib.sha256(json.dumps([mensagens, esquema.__name__ if esquema else None]).encode()).hexdigest()
    if usar_cache and chave_cache in CACHE:
        r = CACHE[chave_cache]
        return Resposta(r.conteudo, r.tok_entrada, r.tok_saida, r.provedor, r.modelo, 0.0, do_cache=True, bruto=r.bruto)

    ultimo_erro = None
    for prov in ORDEM:                                         # 2. principal, depois reservas
        modelo = PROVEDORES[prov]["modelo"]
        formatos = _formatos(esquema)
        nivel = 0
        t = 0
        while t < tentativas:                                  # 3. tentativas para erros temporários
            args = dict(model=modelo, messages=mensagens, max_tokens=max_tokens, timeout=timeout)
            if formatos[nivel] is not None:
                args["response_format"] = formatos[nivel]
            inicio = time.time()
            try:
                r = clientes[prov].chat.completions.create(**args)
            except Exception as erro:
                ultimo_erro = erro
                cod = _codigo(erro)
                if cod == 400 and esquema is not None and nivel < len(formatos) - 1:
                    nivel += 1                                 # 4. provedor recusou o formato: desce um nível
                    print(f"[{prov}] formato não aceito; tentando nível de saída {nivel + 1}")
                    continue
                if cod in REPETIR and t < tentativas - 1:
                    espera = _espera(erro, t)
                    print(f"[{prov}] erro {cod}; nova tentativa em {espera:.1f} s")
                    uso.registrar(prov, modelo, 0, 0, time.time() - inicio, status=f"erro {cod}", etiqueta=etiqueta)
                    time.sleep(espera)
                    t += 1
                    continue
                print(f"[{prov}] erro {cod or type(erro).__name__}: passando para o próximo provedor")
                uso.registrar(prov, modelo, 0, 0, time.time() - inicio, status=f"erro {cod}", etiqueta=etiqueta)
                break
            latencia = time.time() - inicio
            texto = r.choices[0].message.content
            tok_in, tok_out = r.usage.prompt_tokens, r.usage.completion_tokens
            uso.registrar(prov, modelo, tok_in, tok_out, latencia, etiqueta=etiqueta)   # 5. registro de uso
            saida = esquema.model_validate(_extrair_json(texto)) if esquema else texto   # 6. validação Pydantic
            resp = Resposta(saida, tok_in, tok_out, prov, modelo, latencia, bruto=texto)
            CACHE[chave_cache] = resp
            return resp
    raise RuntimeError(f"Nenhum provedor respondeu. Último erro: {ultimo_erro}")
