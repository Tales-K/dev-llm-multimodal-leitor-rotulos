# Registro do uso de assistentes de IA

O Trabalho Orientado pede o registro transparente e crítico do uso de assistentes de IA. Acrescente uma linha a cada uso relevante.

| Data | Ferramenta e modo | O que pedi | O que o assistente fez bem | O que eu corrigi ou recusei |
| --- | --- | --- | --- | --- |
| 11/11/2026 | | Prática 0: explicar o que faz o arquivo src/cliente.py. | Descreveu o fluxo de chamar_modelo na ordem do código: cache por hash, provedor principal e reservas, retentativa com backoff exponencial e jitter só para erros temporários, descida do JSON Schema para json_object e texto livre, registro em logs/uso.csv e validação com Pydantic. | Nada a corrigir. Conferi a explicação com o código e ela corresponde ao arquivo. |
| 11/11/2026 | | Prática 1: criar em src/validacao.py uma regra que mande para revisão humana as notas com data em sábado ou domingo e rodar o script para testar. | Criou a função data_em_fim_de_semana, com docstring e type hints, e a chamou dentro de conferir(), no bloco que já trata a data, sem alterar outros arquivos. Testou sem API com duas notas: a de sábado (08/11/2025) foi para revisão e a de sexta (07/11/2025) seguiu. | Não alterei o código. O assistente não rodou praticas/p1_nota_fiscal.py porque a chave ainda não estava no .env, então o teste com o modelo ficou pendente. Na revisão, notei que o cupom de exemplo da Prática 1 tem data 31/10/2026, um sábado, e por isso passa a ir sempre para revisão. Mantive a regra, que é o comportamento pedido. |
