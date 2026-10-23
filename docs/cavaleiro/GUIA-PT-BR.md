# Guia do Cavaleiro Agent Framework

Guia completo, em português, para entender, instalar e usar o Cavaleiro Agent Framework, e para contribuir com ele.

**Sumário:**

1. [O que é e para quem](#o-que-e)
2. [Arquitetura](#arquitetura)
3. [Instalação passo a passo](#instalacao)
4. [Primeiros passos](#primeiros-passos)
5. [Exemplos práticos](#exemplos)
6. [Configuração](#configuracao)
7. [Solução de problemas](#problemas)
8. [Como contribuir](#contribuir)

<a id="o-que-e"></a>

## 1. O que é e para quem

O **Cavaleiro Agent Framework** é um framework em Python para criar aplicações com modelos de linguagem (LLMs) e agentes. Mantém o código, os nomes de pacotes e a API do projeto original e acrescenta correções de bugs verificadas, cada uma com um teste de regressão.

Use o framework para:

- montar *chains* combinando prompt, modelo e parser com o operador `|`;
- trocar de provedor de modelo (OpenAI, Anthropic, Ollama, Groq, …) sem reescrever a aplicação;
- dar ferramentas (*tools*) a um modelo e criar agentes que decidem quando usá-las;
- preparar documentos para busca semântica (dividir textos, gerar embeddings, guardar em vector stores);
- controlar histórico de conversa (cortar, filtrar e juntar mensagens, contar tokens).

**Para quem é:** pessoas desenvolvedoras Python que querem a base do projeto original com estas correções. Também serve para equipes que precisam de evidências de qualidade (testes que reproduzem cada bug) e para quem desenvolve no Windows.

**O que ele não é:** não é um produto oficial do projeto original, e não há afiliação nem endosso. Também não é um serviço hospedado: o código roda na sua máquina ou no seu servidor.

<a id="arquitetura"></a>

## 2. Arquitetura

O repositório é um *monorepo* com vários pacotes Python independentes, cada um em `libs/`:

```text
                   sua aplicação
                        │
        ┌───────────────┴────────────────┐
        ▼                                ▼
  langchain (libs/langchain_v1)     langchain-core (libs/core)
  agentes, middleware,              abstrações base: Runnable,
  init_chat_model                   mensagens, prompts, parsers,
        │                           ferramentas, callbacks,
        ├──► langgraph (externo)    documentos, vector stores
        └──► langchain-core               ▲
                                          │ implementam as abstrações
  langchain-text-splitters ──► core   libs/partners/* (openai,
  langchain-classic (legado) ──► core  anthropic, ollama, groq, …)
  langchain-tests: testes padrão para integrações
  langchain-model-profiles: perfis de modelos + CLI langchain-profiles
```

| Peça | O que faz |
|---|---|
| **Runnables** (`langchain_core.runnables`) | O contrato comum a tudo: `invoke`, `batch`, `stream` e as versões assíncronas (`ainvoke`, …). Combinação com `\|`, execução em paralelo, roteamento (`RouterRunnable`), retentativas (`with_retry`) e fallbacks. |
| **Modelos** (`langchain_core.language_models`) | `BaseChatModel`: converte mensagens, faz streaming, cache, limite de taxa e saída estruturada. Inclui modelos falsos para testes. |
| **Mensagens** (`langchain_core.messages`) | `HumanMessage`, `AIMessage` (com `tool_calls`), `SystemMessage`, `ToolMessage`, … e utilitários como `trim_messages`, `merge_message_runs`, `convert_to_openai_messages` e `count_tokens_approximately`. |
| **Prompts** (`langchain_core.prompts`) | `PromptTemplate` e `ChatPromptTemplate`, nos formatos f-string, mustache e Jinja2 (este em sandbox). |
| **Output parsers** | Transformam a resposta do modelo em texto, JSON, XML, listas ou objetos Pydantic. |
| **Ferramentas** (`langchain_core.tools`) | O decorador `@tool` e `BaseTool`: geram o esquema JSON dos argumentos a partir da assinatura e da docstring. |
| **Callbacks e tracers** | Acompanham cada execução (útil para logs e observabilidade). O tracing para o LangSmith só funciona se você ativar. |
| **Agentes** (`langchain.agents`) | `create_agent` monta o ciclo modelo → ferramentas → modelo sobre o LangGraph, com middleware. |
| **Text splitters** | Dividem documentos em trechos por caractere, de forma recursiva, por título em Markdown, por HTML, por código, por JSON, … |

**Fluxo de uma chain típica** (`prompt | modelo | parser`):

1. O prompt recebe um dicionário e gera mensagens.
2. O modelo envia essas mensagens ao provedor e devolve um `AIMessage`.
3. O parser converte a resposta no valor final.

Cada etapa abre um "run" filho no gerenciador de callbacks, por isso dá para rastrear a árvore inteira. Em `batch`, as entradas rodam em paralelo (threads ou `asyncio`). Com `return_exceptions=True`, cada entrada devolve o próprio erro.

O [relatório de engenharia](ENGINEERING.md#architecture-map) (em inglês) tem o mapa detalhado, incluindo testes e pipeline de build.

<a id="instalacao"></a>

## 3. Instalação passo a passo

Os pacotes mantêm os nomes do projeto original (`langchain-core`, `langchain`, …), e este fork **não publica no PyPI**. Se você rodar `pip install langchain-core`, vai receber o pacote original, sem estas correções. Instale a partir do repositório, como mostrado abaixo.

### Requisitos

- Python 3.10 a 3.14;
- Git;
- [uv](https://docs.astral.sh/uv/), o gerenciador de ambientes e pacotes usado pelo projeto.

### Windows (PowerShell)

1. Instale o Python pelo [python.org](https://www.python.org/downloads/windows/) ou pela Microsoft Store e confirme a instalação com `python --version`.
2. Instale o Git com `winget install --id Git.Git -e`.
3. Instale o uv com `winget install --id astral-sh.uv -e` (ou siga as [instruções oficiais](https://docs.astral.sh/uv/getting-started/installation/)) e abra um terminal novo.
4. Clone o repositório e prepare o pacote principal:

   ```powershell
   git clone https://github.com/cavaleiro-ai/cavaleiro-agent-framework.git
   cd cavaleiro-agent-framework\libs\core
   uv sync --group test
   uv run python -c "import langchain_core; print(langchain_core.__version__)"
   ```

5. Se o Git avisar que os caminhos são longos demais, rode `git config core.longpaths true` dentro do repositório.

### macOS

1. Instale as ferramentas de linha de comando com `xcode-select --install` (o Git vem junto).
2. Instale o uv com `brew install uv`, ou com `curl -LsSf https://astral.sh/uv/install.sh | sh`.
3. Clone e prepare o ambiente:

   ```bash
   git clone https://github.com/cavaleiro-ai/cavaleiro-agent-framework.git
   cd cavaleiro-agent-framework/libs/core
   uv sync --group test
   uv run python -c "import langchain_core; print(langchain_core.__version__)"
   ```

### Linux

1. Instale o Git e o Python pelo gerenciador da sua distribuição, por exemplo `sudo apt install git python3` no Debian/Ubuntu ou `sudo dnf install git python3` no Fedora.
2. Instale o uv com `curl -LsSf https://astral.sh/uv/install.sh | sh` e abra um terminal novo.
3. Use os mesmos comandos de clone e `uv sync` do macOS.

### No seu próprio projeto

Adicione os pacotes como dependência Git. Para builds reproduzíveis, troque `@main` por um commit ou tag:

```bash
uv add "langchain-core @ git+https://github.com/cavaleiro-ai/cavaleiro-agent-framework@main#subdirectory=libs/core"
uv add "langchain-text-splitters @ git+https://github.com/cavaleiro-ai/cavaleiro-agent-framework@main#subdirectory=libs/text-splitters"
```

Com pip, a sintaxe é a mesma: `pip install "langchain-core @ git+https://github.com/cavaleiro-ai/cavaleiro-agent-framework@main#subdirectory=libs/core"`.

Para usar agentes e provedores reais, adicione também `libs/langchain_v1` (pacote `langchain`) e a integração do provedor, por exemplo `libs/partners/openai` (pacote `langchain-openai`).

<a id="primeiros-passos"></a>

## 4. Primeiros passos

### Sua primeira chain (sem chave de API)

O `GenericFakeChatModel` responde com textos definidos por você. É ótimo para aprender e para escrever testes:

```python
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [("system", "Answer in one short sentence."), ("human", "{question}")]
)
model = GenericFakeChatModel(messages=iter(["Runnables compose with |."]))
chain = prompt | model | StrOutputParser()

print(chain.invoke({"question": "What is a runnable?"}))
# Runnables compose with |.
```

### Com um modelo real

Instale `langchain` e a integração do provedor e defina a chave de API em uma variável de ambiente:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5.5")  # precisa de OPENAI_API_KEY
print(model.invoke("Olá!").content)
```

A mesma chain do exemplo anterior funciona trocando `GenericFakeChatModel` pelo modelo real.

<a id="exemplos"></a>

## 5. Exemplos práticos

Todos os exemplos abaixo rodam sem chave de API e foram executados durante a verificação deste fork.

### Lote com retentativa: cada entrada recebe o próprio resultado

```python
from langchain_core.runnables import RunnableLambda

attempts: dict[str, int] = {}

def flaky(x: str) -> str:
    attempts[x] = attempts.get(x, 0) + 1
    if x == "a" and attempts[x] == 1:
        raise ValueError("a fails once")      # se recupera na 2ª tentativa
    if x == "b":
        raise ValueError("b always fails")    # nunca se recupera
    return x.upper()

safe = RunnableLambda(flaky).with_retry(stop_after_attempt=2, wait_exponential_jitter=False)
print(safe.batch(["a", "b", "c"], return_exceptions=True))
# ['A', ValueError('b always fails'), 'C']
```

No projeto original, este código devolvia `['A', 'A', 'C']`: a entrada `b` recebia o resultado de `a` sem nenhum aviso.

### Ferramentas (tools) e o esquema gerado

```python
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool

@tool
def get_weather(city: str) -> str:
    """Return the weather for a city."""
    return f"Sunny in {city}"

print(convert_to_openai_tool(get_weather)["function"]["name"])  # get_weather
print(get_weather.invoke({"city": "Lisboa"}))                    # Sunny in Lisboa
```

### Controlar o tamanho do histórico

```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately

history = [
    SystemMessage("You are a helpful assistant."),
    HumanMessage("Hi!"),
    AIMessage("Hello! How can I help?"),
    HumanMessage("Summarize our chat."),
]
print(count_tokens_approximately(history))  # 37
trimmed = trim_messages(
    history, max_tokens=25, token_counter="approximate", strategy="last", include_system=True
)
print([type(m).__name__ for m in trimmed])  # ['SystemMessage', 'HumanMessage']
```

Neste fork, `count_tokens_approximately` também conta as chamadas de ferramenta quando o conteúdo da mensagem é uma lista, e aceita funções comuns em `tools=[...]`.

### Templates mustache seguros

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    "{{#user}}Hello {{profile.name}}{{/user}}", template_format="mustache"
)
print(prompt.format(user={"profile": {"name": "Ana"}}))  # Hello Ana
```

Se `user.profile` não tiver `name`, o resultado agora é `Hello ` (vazio), como manda a especificação do mustache. Antes, o template buscava um `profile.name` no nível de cima, que podia ser um dado sem relação com o usuário, e o colocava no prompt.

### Dividir um documento Markdown por títulos

```python
from langchain_text_splitters import MarkdownTextSplitter

md = "# Title\nintro\n## Install\nuv sync\n## Usage\nuv run pytest\n"
print(MarkdownTextSplitter(chunk_size=25, chunk_overlap=0).split_text(md))
# ['# Title\nintro', '## Install\nuv sync', '## Usage\nuv run pytest']
```

<a id="configuracao"></a>

## 6. Configuração

| O quê | Como |
|---|---|
| Chaves dos provedores | Variáveis de ambiente como `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ou `GROQ_API_KEY`. Nunca coloque chaves no código ou no Git. |
| Tracing (opcional) | `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` e `LANGSMITH_PROJECT` enviam traces para o LangSmith, um serviço externo. Fica **desligado** por padrão. |
| Por chamada | `RunnableConfig`: `chain.invoke(x, config={"tags": [...], "metadata": {...}, "max_concurrency": 4, "callbacks": [...]})`. |
| Retentativas | `.with_retry(stop_after_attempt=3, retry_if_exception_type=(TimeoutError,))`. |
| Limite de taxa | `InMemoryRateLimiter(requests_per_second=...)`, passado como `rate_limiter=` ao modelo. |
| Ambiente de desenvolvimento | Cada pacote tem o próprio `.venv`, criado com `uv sync`. Os grupos de dependências são `test`, `lint`, `typing` e `dev`. |

Os nomes de variáveis, pacotes e imports são os mesmos do projeto original. A seção [Compatibilidade](../../README.pt-BR.md#compatibilidade) do README explica o que foi mantido.

<a id="problemas"></a>

## 7. Solução de problemas

| Sintoma | Causa e solução |
|---|---|
| `pip install langchain-core` não trouxe as correções | O PyPI tem o pacote original. Instale pelo Git ou por um caminho local, como na [seção 3](#instalacao). Como os números de versão são iguais aos do projeto original, desinstale a versão do PyPI antes, se for preciso. |
| No Windows, quase todos os testes assíncronos falham com `SocketBlockedError` | No Windows, a opção `--disable-socket` bloqueia o `socket.socketpair()` que o asyncio usa. Rode com `--allow-hosts=127.0.0.1,::1`, como explica o [CONTRIBUTING.md](../../CONTRIBUTING.md#windows). |
| `OSError: [WinError 1314]` nos testes de symlink | Criar links simbólicos no Windows exige o Modo de Desenvolvedor ou um terminal de administrador. É uma limitação do ambiente, não do código. |
| Testes de `test_rate_limiting.py` ou `test_index_into_document_index` falham no Windows | São sensíveis ao relógio e à carga da máquina. O [relatório de engenharia](ENGINEERING.md#baseline) explica as causas. |
| `ImportError: cannot import name 'address' from 'langsmith'` no ambiente de `libs/text-splitters` | O `uv.lock` desse pacote está desatualizado em relação ao `libs/core`. Use o ambiente de `libs/core` para código que importa `langchain_core.runnables`, ou rode `uv lock` em `libs/text-splitters` (isso atualiza dependências). |
| `make: command not found` | Os `Makefile`s só repetem comandos `uv run ...`. Rode os comandos direto, como no CONTRIBUTING. |
| Erro de autenticação do provedor | Confira se a variável de ambiente da chave está definida no mesmo terminal que roda o Python. |

<a id="contribuir"></a>

## 8. Como contribuir

1. Abra uma *issue* descrevendo o problema, com um exemplo mínimo que dê para rodar ([formulários](https://github.com/cavaleiro-ai/cavaleiro-agent-framework/issues/new/choose)).
2. Faça um fork, crie um branch e trabalhe dentro do pacote que vai alterar (por exemplo `libs/core`).
3. Para corrigir um bug, escreva primeiro o teste de regressão, confirme que ele falha, aplique a correção e confirme que passa.
4. Rode os testes, o `ruff` e o `mypy` nos arquivos alterados (veja o [CONTRIBUTING.md](../../CONTRIBUTING.md)).
5. Abra o pull request com um título no formato Conventional Commits, por exemplo `fix(core): ...`, e preencha o modelo.
6. Adicione uma linha em **Unreleased** no [CHANGELOG](../../CHANGELOG.md).

Regras importantes:

- não renomeie pacotes nem imports;
- não enfraqueça testes para "ficar verde";
- testes unitários não podem acessar a rede;
- vulnerabilidades devem ser relatadas em privado, conforme a [política de segurança](../../SECURITY.md).

Se o bug também existir no projeto original, considere relatá-lo lá também.

---

Cavaleiro Agent Framework · licença MIT · veja [LICENSE](../../LICENSE). Sem afiliação com o projeto original.
