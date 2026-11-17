# Arquitetura — Envelhecimento Populacional

Este documento explica como o painel funciona por dentro, do começo ao fim. É para quem vai rodar, mudar ou cuidar do projeto sem ter a pessoa que construiu do lado.

## Como o dado chega na tela

```
IBGE: Projeções da População, revisão 2024 (planilhas do site/FTP)
  tab1_idade_simples.xlsx · tab4_indicadores.xlsx
        │
        │  scripts/preparar_projecao.py   (roda uma vez a cada revisão do IBGE)
        ▼
data/pop_uf.parquet ─────────► src/data.py → _carregar_base()
data/indicadores_uf.parquet ─► src/data.py → carregar_indicadores()
        │
        ▼
src/data.py → carregar_dados(), carregar_evolucao(), anos_disponiveis(),
              ano_padrao(), esperanca_aos_60()
        │  guardam o resultado na memória (cache), para não reler a cada clique
        ▼
src/charts.py → processar_dados()
        │  junta as idades em faixas de 5 anos e calcula a parte 60+ de cada estado
        │
        ├─► src/mapa.py → deck()   o mapa, em pydeck, pintado por quartis
        │                          (cortes vindos de src/data.py → cortes_quartis())
        ▼
app.py → monta a linha de filtros e chama:
        │   src/charts.py → fig_*()   para cada gráfico
        │   src/utils.py              para os cartões de destaque e as tabelas
        │   src/themes.py             para as cores e a marca
        ▼
Streamlit mostra tudo no navegador
```

### Atualizar os dados

Quando o IBGE publicar uma revisão nova:

1. baixe as planilhas novas;
2. rode `python scripts/preparar_projecao.py <pasta com as planilhas>`;
3. faça commit dos dois arquivos `.parquet` gerados.

**O que o script faz com as planilhas:**
- **fica só com os estados**: as planilhas trazem Brasil e regiões misturados nas mesmas linhas;
- **descarta a linha "Ambos"**, que é só a soma de homens e mulheres (manter faria contar em dobro);
- **lê os anos do cabeçalho como valor** (`data_only`), porque na planilha eles são fórmulas (`=F6+1`).

**Dois pontos que podem mudar numa revisão nova:**

| Se mudar… | Ajuste em… | Quem avisa |
|---|---|---|
| a idade máxima (hoje **90 ou mais**) | `IDADE_TOPO`, em `src/charts.py` | `tests/test_numeros.py` |
| o último ano de estimativa (hoje **2022**; depois disso é projeção) | `ESTIMATIVA_ATE`, em `src/data.py` | — |

**Até 15/set/2026, a base era por município** (23 MB) e vinha de um processo fora deste repositório. Ela foi trocada pela tabela do próprio IBGE depois de conferida número por número. Veja o [Levantamento das projeções](historico/levantamento-projecoes.md).

## Para que serve cada arquivo

| Arquivo | O que faz |
|---|---|
| `app.py` | Arquivo principal. Monta os filtros e a página e chama os outros módulos. |
| `src/data.py` | Lê os arquivos de dados e guarda na memória. **É o único que lê do disco.** |
| `src/charts.py` | Prepara os dados (`processar_dados`) e desenha os três gráficos Plotly: rosca (sexo), pirâmide e linha (evolução). |
| `src/mapa.py` | O mapa, em pydeck/deck.gl, sem mapa de fundo. Veja [Performance](performance.md). |
| `src/utils.py` | Formata números, monta os cartões de destaque e as tabelas em HTML e aplica o visual padrão dos gráficos. |
| `src/themes.py` | Cores do tema claro e escuro, o estilo (CSS) da página, a marca escrita (wordmark), o botão de tema e a trava da rodinha do mouse no mapa. |
| `scripts/preparar_geometria.py` | Simplifica o contorno dos estados **uma vez** e salva em `data/ufs.geojson`. |
| `scripts/medir_performance.py` | Mede o tempo e o tamanho de cada gráfico, sem a memória do Streamlit. |
| `tests/` | **113 testes**: números do IBGE, contorno dos estados, mapa, identidade visual e tempo. |

**Não tem API nem banco de dados.** Tudo roda dentro do Streamlit, lendo os arquivos `.parquet` da pasta `data/`.

## Configuração

**Não precisa de nenhuma variável de ambiente.** O painel não usa senha, banco nem serviço externo.

O `.streamlit/config.toml` define duas coisas:
- **`baseUrlPath = "cenarios/demografico-longevidade"`**: o "endereço" do painel dentro do site. **Precisa ser igual à rota do nginx no servidor.**
- **o tema do próprio Streamlit**: a "moldura" que ele desenha em volta do painel (cabeçalho, caixas de seleção, botões).

### Cuidado: são dois temas

É fácil esquecer o segundo:

| Tema | Onde fica | O que pinta |
|---|---|---|
| do **conteúdo** | `src/themes.py` | os cartões, os gráficos e o texto do painel |
| do **Streamlit** | `.streamlit/config.toml` | o cabeçalho, os botões e as caixas de seleção |

**Isso já deu problema:** quando a marca foi trocada, só o primeiro foi mudado. Por um tempo, o painel ficou com uma faixa escura no topo e as caixas de seleção azuis do Cenários.

**O painel não tem barra lateral:** os filtros ficam numa linha, no meio da página.

## Publicação (deploy)

- **Imagem Docker:** o `docker-compose.yml` monta a imagem a partir do `Dockerfile` (Python 3.11-slim + Streamlit).
- **O código vai dentro da imagem** (`COPY . .`). Só a pasta `data/` fica de fora: ela é ligada ao container de fora para dentro, **somente leitura**.
- **Container:** `dashboard-demografico-longevidade`. A porta **8508** do servidor leva à **8501** do container. (A 8501 do servidor já é do painel `demografico`, que continua no ar.)
- **No servidor:** a pasta é `~/dashboard-demografico-longevidade/`, e o nginx publica em `https://painel.cenarios.unb.br/cenarios/demografico-longevidade` (repassando para `localhost:8508`).

### A "pegadinha" do nginx

A rota `/cenarios/demografico` (do outro painel) também "casaria" com `/cenarios/demografico-longevidade`, porque uma começa igual à outra. **Quem resolve é a regra do nginx de escolher a rota mais longa**, e é por isso que a deste painel vence.

**Mas as duas rotas precisam existir**, e **mexer em uma exige testar a outra.**

### Mudou o código? Tem que reconstruir a imagem

Como o código vai copiado para dentro da imagem, editar `app.py` ou `src/` **não muda o painel que está rodando**. É preciso rodar:

```bash
docker compose up -d --build
```

## O que o painel ainda não faz (ou faz com limitação)

- **Só tem estados, de 2000 a 2070.** Não tem município: o IBGE não faz projeção por município, e a base deixou de ter município em 15/set/2026.
- **De 2023 em diante é projeção, inclusive o ano em que o painel abre.** O limite (`ESTIMATIVA_ATE`) aparece no seletor de ano, no topo da página e na linha tracejada da evolução. **Quando sair uma revisão nova do IBGE, os números projetados mudam**, e o painel não guarda a revisão anterior.
- **O tema escuro não muda as cores dos gráficos.** O botão de tema só marca a página como escura e coloca um CSS por cima. A escolha **nunca chega ao Python** (`st.session_state.theme` fica sempre "light"), então as cores escuras (`THEMES["dark"]`) nunca são usadas. Resultado: o fundo escurece, mas o mapa, a rosca e a pirâmide continuam com as cores do tema claro. **Isso vem de antes deste painel** e acontece também no `dashboard-demografico`.
- **A marca escrita (wordmark) é uma reprodução.** A flor e a disposição são fiéis, mas a fonte da imagem oficial não dá para reproduzir com as fontes do sistema. O arquivo vetorial do Observatório resolveria. Veja [Identidade visual](identidade.md).

## Atualizar a imagem do README

A imagem `docs/preview.png` **fica velha sem ninguém perceber**, até alguém abrir o README e ver uma versão antiga do painel. Para gerar uma nova, com o painel rodando no seu computador:

```bash
chrome --headless=new --disable-gpu --hide-scrollbars --window-size=1440,1600 --virtual-time-budget=90000 --screenshot=docs/_preview_raw.png http://localhost:8508/cenarios/demografico-longevidade/
```

```bash
python -c "from PIL import Image; Image.open('docs/_preview_raw.png').crop((0,52,1440,1558)).save('docs/preview.png', optimize=True)"
```

**Por que cortar a imagem:**
- **em cima, os primeiros 52 pixels** são a faixa do cabeçalho do Streamlit (botão de tema e menu ⋮). Numa imagem de README, isso só ocupa espaço e faz o painel parecer começar com um vazio. Cortando ali, **a barra roxa da marca vira a primeira coisa da imagem**;
- **embaixo, o corte em 1558** fica logo depois da linha que fecha a seção do mapa. Terminar numa dessas linhas evita cortar um gráfico no meio. Com a janela em 1440 de largura, as linhas ficam em **762 · 1550 · 2429 · 3024**. Escolha outra se quiser uma imagem mais curta ou mais longa.

**Confira o arquivo antes de fazer commit.** Duas armadilhas:

- **O tempo do Chrome (`--virtual-time-budget`) pode acabar antes de o painel carregar.** Aí a imagem sai mostrando a tela de carregamento, **e escura**. Isso não é o tema escuro do painel: o Chrome sem janela finge que o sistema está no modo escuro, e a tela de carregamento do Streamlit segue o sistema. **Uma imagem escura é uma imagem vazia.** Se acontecer, aumente o tempo.
- **O tamanho do arquivo já entrega o problema:** a imagem boa tem uns **250 KB**; a da tela de carregamento, uns **12 KB**.

## Testes

```bash
pytest                 # os 113 testes
pytest -m "not tempo"  # os 110 que o CI roda (sem os de tempo)
```

**Por que os testes de tempo ficam fora do CI:** eles medem o tempo no relógio e comparam com um limite fixo. Numa máquina compartilhada do GitHub, o tempo diz mais sobre **quanto a máquina está ocupada com outras coisas** do que sobre o nosso código. A explicação completa está no `pytest.ini`.

O CI (`.github/workflows/ci.yml`) roda a checagem de código, os testes e a montagem da imagem, e confere se a imagem instala **exatamente** o que está no lock.
