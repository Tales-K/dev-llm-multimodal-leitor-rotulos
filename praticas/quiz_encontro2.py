"""Entrega do Encontro 2: identificação, tema do Trabalho Orientado, quiz e justificativa da Prática 3.

Preencha os campos abaixo e rode:
    python praticas/quiz_encontro2.py
As perguntas estão em praticas/QUIZ.md.
"""

ALUNO = "Tales Rodrigo Ferreira Kerschner"   # seu nome completo
MATRICULA = ""        # opcional

# Trabalho Orientado: comece a pensar no tema. Uma ou duas frases bastam por enquanto.
# ex.: "assistente que lê laudos de vistoria de imóveis e resume os problemas"
TEMA_TRABALHO = ("Assistente que lê fotos de rótulos e etiquetas de produtos e responde a perguntas sobre eles, "
                 "como ingredientes, alergênicos, validade ou especificações técnicas. "
                 "As imagens são fotos de embalagens que eu mesmo tiro, sem dados pessoais.")

RESPOSTAS = {
    1: "b",   # a, b, c ou d
    2: "c",
    3: "a",
    4: "b",
    5: "d",
    6: "a",
    7: "c",
    8: "b",
}

# Prática 3: qual variante você escolheria para produção, e por quê? (acurácia e tokens)
JUSTIFICATIVA_P3 = ""


if __name__ == "__main__":
    faltando = [q for q, r in RESPOSTAS.items() if str(r).strip().lower() not in ("a", "b", "c", "d")]
    print("Aluno:", ALUNO or "NOME NÃO PREENCHIDO")
    print("Tema do Trabalho Orientado:", TEMA_TRABALHO or "AINDA NÃO DEFINIDO: comece a pensar nele")
    print("Respostas:", {q: str(r).strip().lower() for q, r in RESPOSTAS.items()})
    print("Justificativa da Prática 3:", "preenchida" if JUSTIFICATIVA_P3.strip() else "FALTANDO")
    if faltando:
        print("Atenção, perguntas sem resposta válida:", faltando)
    elif ALUNO and JUSTIFICATIVA_P3.strip():
        print("Entrega completa. Envie o link do seu repositório (ou o .zip, sem o arquivo .env) pelo portal.")
