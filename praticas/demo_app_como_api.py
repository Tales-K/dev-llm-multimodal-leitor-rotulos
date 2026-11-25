"""Demonstração · O seu app em Gradio também é uma API (Encontro 3).

Todo evento com api_name vira um endpoint. O pacote gradio_client chama esse endpoint
de outro programa, sem abrir o navegador: o seu protótipo vira um serviço.

Como rodar:
    1. Em um terminal:  python app/extrator.py          (deixe rodando)
    2. Em outro:        python praticas/demo_app_como_api.py
"""
import sys
from pathlib import Path

from gradio_client import Client, handle_file

RAIZ = Path(__file__).resolve().parents[1]
ENDERECO = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7860/"

cliente = Client(ENDERECO, verbose=False)
print("Endpoints disponíveis (o mesmo que o link 'Use via API' no rodapé do app):\n")
cliente.view_api()

cupom = RAIZ / "dados" / "exemplos" / "cupom_exemplo.png"
vista, decisao, nota, consumo = cliente.predict(handle_file(str(cupom)), 768, api_name="/extrair")
print("\nResposta do app, recebida como de qualquer API:")
print("Decisão:", decisao.splitlines()[0].strip("# "))
print("Nota:", nota)
print("Consumo:", consumo.replace("\n", " "))
