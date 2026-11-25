"""Entrega do Encontro 3: identificação, Trabalho Orientado, quiz e reflexão sobre a interface.

Preencha os campos abaixo e rode:
    python praticas/quiz_encontro3.py
As perguntas estão em praticas/QUIZ3.md.
"""

ALUNO = "Tales Rodrigo Ferreira Kerschner e Tiago Rafael Ferreira Kerschner"   # seu nome completo
MATRICULA = ""        # opcional

# Trabalho Orientado: o tema (pode ter mudado desde o Encontro 2) e a interface que você imagina.
TEMA_TRABALHO = ("Assistente que lê fotos de rótulos e etiquetas de produtos e responde a perguntas sobre eles, "
                 "como ingredientes, alergênicos, validade ou especificações técnicas. "
                 "As imagens são fotos de embalagens que nós mesmos tiramos, sem dados pessoais.")
INTERFACE = ("A pessoa envia a foto de um rótulo e escreve ou grava uma pergunta; vê de volta a transcrição "
             "do que perguntou, a resposta em texto (e em voz, se pedir) e a linha de consumo da chamada.")

RESPOSTAS = {
    1: "b",   # a, b, c ou d
    2: "c",
    3: "a",
    4: "a",
    5: "d",
    6: "c",
    7: "b",
    8: "a",
    9: "b",
    10: "c",
    11: "b",
}

# Prática 4: qual estratégia de memória você usaria no seu Trabalho Orientado, e por quê? (custo e o que precisa ser lembrado)
ESTRATEGIA_MEMORIA = ("Completa. As conversas sobre um rótulo são curtas, poucas perguntas sobre a mesma foto, "
                      "e a foto precisa continuar no contexto. Na Prática 4, a janela perdeu a imagem a partir da "
                      "quarta pergunta e o modelo inventou outro estabelecimento, enquanto a completa acertou com "
                      "11.064 tokens de entrada no total, contra 7.076 da janela. Para limitar o custo, cada foto "
                      "nova começa uma conversa nova.")


if __name__ == "__main__":
    faltando = [q for q, r in RESPOSTAS.items() if str(r).strip().lower() not in ("a", "b", "c", "d")]
    print("Aluno:", ALUNO or "NOME NÃO PREENCHIDO")
    print("Tema do Trabalho Orientado:", TEMA_TRABALHO or "AINDA NÃO DEFINIDO")
    print("Interface imaginada:", INTERFACE or "FALTANDO")
    print("Respostas:", {q: str(r).strip().lower() for q, r in RESPOSTAS.items()})
    print("Estratégia de memória:", "preenchida" if ESTRATEGIA_MEMORIA.strip() else "FALTANDO")
    if faltando:
        print("Atenção, perguntas sem resposta válida:", faltando)
    elif ALUNO and INTERFACE.strip() and ESTRATEGIA_MEMORIA.strip():
        print("Entrega completa. Envie o link do seu repositório (ou o .zip, sem .env e sem .venv) pelo portal.")
