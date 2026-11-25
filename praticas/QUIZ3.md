# Quiz do Encontro 3 · Assistentes e chatbots multimodais

Responda no arquivo `praticas/quiz_encontro3.py` com a letra de cada alternativa.

**1.** Um assistente responde bem à primeira pergunta sobre um cupom, mas na segunda ("qual foi o item mais caro?") diz que não vê nenhum cupom. A causa mais provável é:

- a) o modelo tem um limite de uma imagem por dia
- b) a aplicação não reenviou o histórico (nem a imagem) na segunda chamada
- c) o provedor apagou a imagem por segurança
- d) a temperatura estava alta demais

**2.** Por que, na memória "completa", o custo da conversa cresce mais rápido que o número de perguntas?

- a) porque o provedor cobra uma taxa fixa por mensagem
- b) porque as respostas ficam mais longas a cada turno
- c) porque cada pergunta reenvia todas as anteriores, e o total enviado soma 1 + 2 + 3 + ... mensagens
- d) porque o cache é desligado depois da terceira pergunta

**3.** Na Prática 4, a estratégia "resumo" lembrou o nome do estabelecimento, mas não a data da compra. Por quê?

- a) o resumo só guarda o que foi dito na conversa, e a data nunca tinha sido mencionada
- b) o modelo de resumo não lê datas
- c) a janela era grande demais
- d) o resumo apaga números por padrão

**4.** No Gradio, qual a diferença essencial entre `gr.Interface` e `gr.Blocks`?

- a) Interface gera a tela a partir de uma função, com entradas e saídas; Blocks permite montar o layout e ligar vários eventos a várias funções
- b) Interface é para texto e Blocks é para imagens
- c) Blocks só funciona no Colab
- d) Interface não aceita streaming

**5.** Em um `gr.ChatInterface`, quem guarda o histórico da conversa e o entrega à função a cada mensagem?

- a) o provedor do modelo
- b) um banco de dados que precisa ser configurado
- c) ninguém: o histórico se perde a cada mensagem
- d) o próprio componente do Gradio, na sessão do navegador

**6.** Para mostrar a resposta enquanto o modelo escreve (streaming), a função do Gradio deve:

- a) usar `return` com a resposta completa
- b) chamar `demo.refresh()` em um laço
- c) usar `yield` a cada pedaço novo, devolvendo o texto acumulado
- d) ativar `share=True`

**7.** Qual destas práticas de design de interface conversacional ajuda o usuário a confiar no sistema de forma calibrada?

- a) esconder os erros para não assustar o usuário
- b) mostrar o que o sistema entendeu (a transcrição do áudio, a imagem que foi enviada) antes da resposta
- c) responder sempre com a maior confiança possível
- d) não mostrar o custo para não distrair

**8.** Por que uma variável global é uma má ideia para guardar o histórico em um app Gradio publicado?

- a) ela é compartilhada por todos os usuários conectados, que passariam a ver a conversa uns dos outros
- b) variáveis globais são mais lentas
- c) o Gradio apaga variáveis globais a cada minuto
- d) variáveis globais não aceitam imagens

**9.** No Streamlit, um contador `n = 0` seguido de `if st.button("+1"): n += 1` mostra sempre 1 depois de cada clique, nunca 2 ou 3. Por quê?

- a) o `st.button` só funciona uma vez por sessão
- b) a cada clique o script inteiro roda de novo, e `n = 0` é executado outra vez; o valor precisa ficar em `st.session_state`
- c) o Streamlit não aceita números inteiros
- d) falta chamar `demo.launch()`

**10.** Você precisa de um protótipo que, além da tela, outro programa possa chamar como API sem escrever código extra. Pelo que vimos, qual framework entrega isso pronto?

- a) Streamlit, com `st.api()`
- b) nenhum dos dois
- c) Gradio: todo evento com `api_name` vira um endpoint
- d) os dois, da mesma forma

**11.** No Pydantic AI, `Agent(modelo, output_type=NotaFiscal)` faz o quê, de diferente do que já fazemos em `src/cliente.py`?

- a) dispensa o modelo de linguagem
- b) devolve a saída já validada como `NotaFiscal` e, se o formato vier errado, devolve o erro ao modelo e pede a correção sozinho
- c) converte a nota fiscal em PDF
- d) treina um modelo novo com as notas

