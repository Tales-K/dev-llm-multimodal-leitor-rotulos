# Projeto multimodal · Desenvolvimento de Aplicações Interativas com LLMs Multimodais

Modelo de projeto da disciplina (PUC Minas). Ele começa no Encontro 2 e cresce a cada encontro até virar o seu Trabalho Orientado.

**Encontro 3:** memória de conversa, streaming, PDFs, voz e as primeiras interfaces em Gradio e Streamlit (pasta `app/`), com uma prévia do Pydantic AI.

## Estrutura

```
projeto-multimodal/
├── .env.example      nomes das chaves, sem valores (copie para .env)
├── .gitignore        mantém .env, logs e dados privados fora do GitHub
├── requirements.txt  pacotes do projeto
├── AGENTS.md         regras do projeto para o GitHub Copilot e outros agentes
├── REGISTRO_IA.md    registro do uso de assistentes de IA (exigido no trabalho)
├── src/
│   ├── config.py     provedores, modelos, preços e leitura das chaves
│   ├── cliente.py    chamar_modelo, chamar_modelo_stream e transcrever
│   ├── contexto.py   memória da conversa: nenhuma, completa, janela ou resumo
│   ├── documentos.py PDFs: texto extraído ou página como imagem
│   ├── audio.py      transcrição e síntese de fala
│   ├── midia.py      imagens: redução, recorte, marcas, cupons de exemplo
│   ├── esquemas.py   classes Pydantic das respostas
│   ├── validacao.py  regras de negócio
│   ├── prompts.py    leitura dos prompts versionados
│   └── uso.py        registro de tokens, latência e custo em logs/uso.csv
├── prompts/          prompts versionados (.md)
├── praticas/         scripts das aulas e os quizzes
├── app/              interfaces em Gradio (extrator, assistente) e Streamlit (extrator, chat)
├── notebooks/        plano B: as mesmas práticas no Colab
├── dados/exemplos/   imagens de teste (geradas pelos scripts)
└── logs/             uso.csv (criado na primeira chamada)
```

## Como o código se conecta

O caminho de uma chamada da Prática 1 (as outras práticas seguem a mesma ideia):

```
praticas/p1_nota_fiscal.py          o roteiro: chama cada peça na ordem
 │
 ├─1─► src/midia.py      mensagem()       imagem vira data URL (reduzida)
 ├─2─► src/prompts.py    carregar()       lê prompts/extracao_v1.md
 │
 ├─3─► src/cliente.py    chamar_modelo()  a única porta de saída para os modelos
 │        a. já está no cache? devolve
 │        b. escolhe o provedor (principal e reserva)      ◄── src/config.py
 │        c. envia com timeout ───────────────► Groq ou Gemini (API na internet)
 │        d. 429 ou 5xx? espera com jitter e tenta de novo
 │        e. esquema recusado? desce um nível de saída
 │        f. registra o uso                                ──► src/uso.py → logs/uso.csv
 │        g. valida com o esquema                          ◄── src/esquemas.py (NotaFiscal)
 │
 └─4─► src/validacao.py  conferir()       regras de negócio: segue ou revisão humana
```

Cada arquivo tem uma responsabilidade: para trocar de provedor, mexa só em `config.py`; para mudar o formato da resposta, só em `esquemas.py`; para uma regra nova, só em `validacao.py`.

### E no assistente (Encontro 3)

```
você digita, envia imagem, PDF ou áudio no navegador
 │
 ▼
app/assistente.py   responder(message, history, memoria, ler_em_voz)   a interface: só orquestra
 │
 ├─ áudio? ──► src/audio.py      transcrever()      ──► Whisper no Groq (outro endpoint)
 ├─ PDF?   ──► src/documentos.py preparar_pdf()     texto das páginas digitais, imagem das escaneadas
 ├─ history ─► src/contexto.py   ler_historico_gradio() e montar_historico()   o que reenviar
 │
 ├─► src/cliente.py  chamar_modelo_stream()  ──► provedor ──► pedaços de texto ──► yield na tela
 │
 └─ voz?   ──► src/audio.py      sintetizar()       ──► MP3 tocado na interface
```

A API não guarda nada entre uma chamada e outra: o histórico é reenviado a cada pergunta, e `src/contexto.py` decide quanto dele reenviar.

## Preparação (uma vez)

1. Instale o **Python 3.10 ou mais novo** e o **VS Code**, com as extensões **Python** e **GitHub Copilot**.
2. Abra a pasta do projeto no VS Code (**Arquivo > Abrir Pasta**) e abra o terminal (**Terminal > Novo Terminal**).
3. Crie e ative o ambiente virtual:

   | Sistema | Criar | Ativar |
   | --- | --- | --- |
   | Windows | `python -m venv .venv` | `.venv\Scripts\activate` |
   | macOS e Linux | `python3 -m venv .venv` | `source .venv/bin/activate` |

   No Windows, se a ativação for bloqueada, rode uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
4. Instale os pacotes: `pip install -r requirements.txt`
   Depois, no VS Code, **Ctrl+Shift+P > Python: Select Interpreter** e escolha o Python que tem `.venv` no caminho.
5. Copie `.env.example` para `.env` e preencha a sua chave (Groq ou Gemini).
6. Confira tudo: `python praticas/p0_primeira_chamada.py`

## Práticas do Encontro 2

Rode sempre a partir da pasta raiz do projeto, com o ambiente virtual ativado.

| Prática | Comando | O que mostra |
| --- | --- | --- |
| 0 | `python praticas/p0_primeira_chamada.py` | ambiente, chaves e a primeira chamada |
| 1 | `python praticas/p1_nota_fiscal.py` | nota fiscal em JSON validado e regras de negócio |
| 2 | `python praticas/p2_consumo.py` | tokens por resolução, registro de uso e projeção de custo |
| 3 | `python praticas/p3_prompts.py` | três prompts comparados em um conjunto de teste |

Para usar a sua própria foto na Prática 1: `python praticas/p1_nota_fiscal.py dados/minha_nota.jpg` (sem dados pessoais).

**Entrega:** preencha `praticas/quiz_encontro2.py` (nome, tema do Trabalho Orientado, quiz e justificativa da Prática 3), rode-o e envie o link do repositório ou o `.zip` do projeto **sem o arquivo `.env` e sem a pasta `.venv`**.

## Práticas do Encontro 3

Se você já tinha o projeto do Encontro 2, rode de novo `pip install -r requirements.txt` (entraram `gradio`, `streamlit`, `pymupdf` e `edge-tts`).

| Prática | Comando | O que mostra |
| --- | --- | --- |
| 4 | `python praticas/p4_conversa.py` | a API não tem memória: 4 estratégias comparadas em tokens e no que o assistente lembra |
| 4 (livre) | `python praticas/p4_conversa.py --chat --estrategia janela` | conversa no terminal com streaming; `/imagem caminho`, `/memoria`, `/sair` |
| 5A | `python praticas/p5a_gradio_do_zero.py 1` (depois `2` e `3`) | Gradio do zero: Interface, ChatInterface ligado à API e Blocks com imagem; cada passo traz uma melhoria com solução |
| 5 | `python app/extrator.py` | interface em Gradio Blocks para o extrator de notas fiscais |
| 5B | `streamlit run app/extrator_streamlit.py` | o mesmo extrator em Streamlit: compare o modelo de execução e o `session_state` |
| 6 | `python app/assistente.py` | assistente multimodal com ChatInterface: imagem, PDF, áudio, memória, streaming e voz |
| Demo | `python praticas/demo_app_como_api.py` | o app em Gradio chamado como API (com o extrator rodando em outro terminal) |
| Apoio | `streamlit run app/chat_streamlit.py` | o chat de texto em Streamlit, com a memória no `session_state` |
| Demo | `python praticas/demo_pydantic_ai.py` | prévia do Pydantic AI: o extrator como agente com `output_type=NotaFiscal` (requer `pip install "pydantic-ai-slim[openai]"`) |

Os apps em Gradio abrem em `http://127.0.0.1:7860`; os em Streamlit, em `http://localhost:8501`. Para parar, **Ctrl+C** no terminal. A síntese de fala usa o `edge-tts`, gratuito e sem chave, bom para protótipos; a transcrição precisa da chave do Groq.

**Entrega do Encontro 3:** preencha `praticas/quiz_encontro3.py` (nome, tema, interface imaginada, quiz de 11 perguntas e estratégia de memória), rode-o e envie como no Encontro 2.

## Plano B

Se o ambiente local não funcionar, use `notebooks/Plano_B_Colab.ipynb` no Google Colab: ele roda os mesmos scripts, com as chaves nos Secrets do Colab.

## Segurança

- A chave nunca vai no código. Se vazar, apague-a no site do provedor e crie outra.
- Antes de cada `git commit`, confira que o `.env` não aparece em `git status`.
