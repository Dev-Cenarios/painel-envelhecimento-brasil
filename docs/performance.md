# Performance (velocidade)

Este documento é um **diário de medições**. Cada parte tem a data em que foi medida.

**Os números antigos ficam como estão**, mesmo os que já não valem: reescrevê-los seria inventar um passado que não foi medido. O que vale **hoje** está marcado.

**Para medir de novo:**

```bash
python -m scripts.medir_performance
```

(Na época das primeiras medições, o comando rodava dentro do Docker: `docker run --rm -v "$PWD:/app" -w /app demografico:base python -m scripts.medir_performance`. Hoje o painel também roda direto no Python 3.13.)

**Como é medido:** mediana de 5 execuções, em milissegundos (ms), **sem** a memória (cache) do Streamlit. Ano de referência: 2025.

> ms = milissegundos. 1.000 ms = 1 segundo.

---

> **15/set/2026: a base mudou, e carregar os dados ficou 128 vezes mais rápido.**
>
> A base por município (23 MB, 14,4 milhões de linhas) foi trocada pela tabela do IBGE por estado (0,9 MB, 349 mil linhas).
> - `_carregar_base` caiu de **5.770 ms para 45 ms**;
> - os testes caíram de **56 s para 3,5 s**;
> - a espera de **6 a 8 segundos** no primeiro acesso, que acontecia toda vez que o painel reiniciava, **deixou de existir**.
>
> As medições abaixo são de **antes** dessa troca. Elas continuam valendo para o que medem (gráficos e tamanho do mapa), porque isso não depende do tamanho da base.

---

# Ponto de partida — 02/set/2026

Medido **antes de qualquer otimização.**

## Carregar os dados

| Operação | Mediana (ms) | Pior vez (ms) |
|---|---:|---:|
| `carregar_geojson` | 81,8 | 113,1 |
| `_carregar_base` | 5.770,4 | 6.246,0 |
| `carregar_dados(ano)` | 819,6 | 887,4 |
| `carregar_evolucao` | 1.637,6 | 1.740,1 |
| `processar_dados` | 2,2 | 3,0 |

**As quatro primeiras são custo de partida, não de cada clique.** Elas ficam guardadas na memória (`@st.cache_data`/`@st.cache_resource`) e rodam **uma vez** a cada vez que o painel liga. O que a pessoa paga **a cada clique** é o `processar_dados` (2,2 ms, duas vezes: ano atual e anterior) mais a montagem dos gráficos.

## Montar cada gráfico: tempo e tamanho

| Gráfico | Brasil (27 estados) | Sudeste (4) | PE (1) |
|---|---:|---:|---:|
| **`fig_mapa`** | **194,1 ms · 1.953 KB** | **195,5 ms · 1.953 KB** | **172,6 ms · 1.953 KB** |
| `fig_pizza` | 26,3 ms · 5 KB | 26,2 ms · 5 KB | 26,5 ms · 5 KB |
| `fig_piramide` | 18,9 ms · 6 KB | 18,9 ms · 6 KB | 18,5 ms · 5 KB |
| `fig_ranking` | 28,2 ms · 5 KB | 28,3 ms · 4 KB | 28,2 ms · 4 KB |
| `fig_evolucao` | 28,4 ms · 5 KB | 27,9 ms · 5 KB | 27,9 ms · 5 KB |

## O que a medição mostrou

**O mapa era o painel inteiro, em custo.** Levava 194 ms, contra 19 a 28 ms do próximo gráfico, e mandava **1.953 KB** ao navegador, contra 4 a 6 KB dos outros. Eram **350 vezes mais dados** que qualquer outro gráfico. Tudo que não era mapa somava 20 KB.

**O tamanho não mudava com o filtro.** Era 1.953 KB com o Brasil, com o Sudeste e com Pernambuco sozinho. O motivo: o `choropleth_mapbox` recebia o contorno do **país inteiro** e mandava tudo junto. O filtro só mudava quais estados ganhavam cor. **Quem olhava um estado pagava pelo mapa do país.**

**E não era só na primeira vez.** O mapa era reenviado a **cada clique** (troca de ano, de estado ou de tema), porque as cores fazem parte dele. Numa internet de 10 Mbit/s, isso dava **uns 1,6 segundo de espera por clique**, que não aparece testando no próprio computador (`localhost`). É a mesma armadilha anotada em `paineis/sinan/docs/performance.md`: **medir no próprio computador esconde o custo da internet.**

## De onde vinham os 1,9 MB

O `data/brazil-states.geojson` tem **3,4 MB** no disco, e 2,1 MB sem os espaços de recuo. Ou seja, **um terço do arquivo era só espaço em branco.** Dentro dele:

| | |
|---|---:|
| Estados | 27 |
| Pontos do contorno | 85.585 |
| Pontos por estado | ~3.170 |
| Casas decimais | 6 (~10 cm de precisão) |

Num mapa do Brasil com uns 600 pixels de largura, **85 mil pontos é muito mais detalhe do que a tela consegue mostrar.** E cada estado ainda carregava 6 informações extras (`cartodb_id`, `created_at`, `updated_at`, `name`, `regiao_id`, `codigo_ibg`), mas o mapa só usa a `sigla`.

## O mapa de fundo, que além de tudo quebrou

O `mapbox_style="carto-positron"` puxava imagens de fundo da **CARTO**, que passou a exigir chave de acesso. **O painel no ar mostrava "API KEY REQUIRED — docs.carto.com/basemaps" repetido embaixo do mapa.**

Isso não aparece nos números acima (é o navegador que busca as imagens, não o Streamlit que envia), mas **foi o motivo de o mapa ser refeito**.

---

# O que foi feito — 02/set/2026

O mapa saiu do Plotly/CARTO e foi para o **pydeck, sem mapa de fundo** (`map_provider=None`). Foram três mudanças independentes, medidas separadamente.

## 1. O contorno passou a ser preparado antes

O `scripts/preparar_geometria.py` roda **uma vez** e grava o `data/ufs.geojson`. O `brazil-states.geojson` cru continua no repositório como **origem**, mas o painel não lê mais ele.

| | Antes | Depois | |
|---|---:|---:|---:|
| Tamanho do arquivo | 3,38 MB | 0,10 MB | −97% |
| Pontos do contorno | 85.585 | 4.469 | −95% |
| Casas decimais | 6 | 5 | |
| Informações por estado | 6 | 1 | |
| `carregar_geojson` | 81,8 ms | 4,5 ms | −94% |

**Erro de área: 0,006%. Sobreposição entre estados: 0,00 km².**

### Por que simplificar "em conjunto" (`shared_coords=True`)

**O jeito comum de simplificar** (`simplify`, do shapely) trata cada estado sozinho. Aí dois vizinhos simplificam a divisa **cada um do seu jeito**, e aparecem buracos e sobreposições entre eles.

**A simplificação "topológica"** trata cada divisa como uma linha só, compartilhada pelos dois estados, e simplifica **uma vez**. Os vizinhos continuam se encaixando.

O painel `sinan` usa `shared_coords=False`. **Aqui isso estaria errado, e a medição mostrou:** nesta malha, o `False` **cria 99,74 km² de sobreposição** numa malha que não tinha nenhuma, com quase o mesmo número de pontos (4.455 contra 4.469) e o mesmo erro de área. Com `True`, sobreposição zero. **As duas formas foram medidas antes de escolher.**

### O que a simplificação custa

O nível de simplificação foi calculado para **o Brasil inteiro**. Na visão do país, isso dá meio pixel de diferença, e não aparece. Quando se escolhe **um estado sozinho**, dá uns 3 pixels, e o contorno fica visivelmente "quadradinho".

**É uma perda consciente:** na visão de um estado só, o mapa é uma mancha de uma cor só, e o formato não carrega informação. A visão do país, que é a que informa, não mostra o defeito.

**Testado e não aplicado:** dobrar a resolução (`DIVISOR = 2400`; hoje é 1200) leva a 8.643 pontos e ~190 KB no Brasil. Dobra o custo justamente na visão onde o ganho não aparece. Fica anotado como a "alavanca", se alguém quiser.

## 2. Só os estados visíveis, e sem espaços extras

O `choropleth_mapbox` recebia o contorno inteiro. O `GeoJsonLayer` recebe **só os estados do recorte**, e o `mapa._compactar` faz o pydeck mandar o mapa **sem espaços de recuo** (sem `indent=2`).

| Tamanho do mapa | Antes | Depois | |
|---|---:|---:|---:|
| Brasil (27 estados) | 1.953 KB | **98 KB** | −95% |
| Sudeste (4) | 1.953 KB | **19 KB** | −99% |
| PE (1) | 1.953 KB | **3 KB** | −99,8% |

**O tamanho passou a responder ao filtro**, e esse era o defeito principal. Numa internet de 10 Mbit/s, a espera típica no Brasil caiu de **~1,6 s para ~0,08 s** por clique.

## 3. A inversão do custo

| Gráfico (Brasil) | Antes | Depois |
|---|---:|---:|
| **mapa** | **194,1 ms** | **13,5 ms** |
| `fig_pizza` | 26,3 ms | 32,0 ms |
| `fig_piramide` | 18,9 ms | 25,4 ms |
| `fig_ranking` | 28,2 ms | 32,1 ms |
| `fig_evolucao` | 28,4 ms | 34,0 ms |

**O mapa era o gráfico mais caro do painel, 7 vezes mais que os outros. Passou a ser o mais barato.** O teste `test_mapa_deixou_de_ser_a_figura_mais_cara` garante isso.

Os quatro gráficos do Plotly ficaram de 5 a 6 ms mais lentos cada. **É a troca do Plotly da versão 5.24.1 para a 6.3.1**, feita junto porque a versão 6 tirou o `mapbox`. Não valia investigar: os cinco juntos custam menos do que o mapa sozinho custava.

## 4. Dois defeitos achados no caminho

**Fernando de Noronha é de Pernambuco.** O "retângulo" de PE, contando a ilha, tem 9,0° de largura, contra 6,5° do estado no continente. Escolher PE desenharia quase só oceano. O `mapa._limites` agora **ignora pedaços de terra a mais de 1° do corpo principal**, como o `limites_uteis` do sinan, mas em Python puro (o geopandas só é usado para preparar os dados, não no painel). **Foi pego por um teste** que confere o enquadramento.

**O `__MAP_STYLE__`.** Com `map_provider=None`, mas sem `map_style=None`, o pydeck deixava um "marcador" (`__MAP_STYLE__`) no mapa. O deck.gl lia isso como um endereço e **buscava `/cenarios/demografico/__MAP_STYLE__` a cada desenho**. O Streamlit respondia com a página inicial, e o console do navegador enchia de "Unexpected token '<'". Era **um pedido inútil por desenho**, invisível nos testes que existiam, e foi achado no painel de rede do navegador. O teste `test_nao_emite_o_sentinela_de_estilo` existe para que isso não volte sem ninguém ver.

## 5. O mapa de fundo voltou sem ninguém notar, e como foi pego

**Anotado em 03/set/2026, depois que o painel foi ao ar com o defeito.**

A correção do `__MAP_STYLE__` (item 4) passou `map_style=None`. Só que, **no pydeck, `None` não quer dizer "sem mapa de fundo"**: quer dizer "**deixe o Streamlit escolher**". Sem estilo definido, o Streamlit usou o padrão dele (`mapbox://styles/mapbox/light-v8`), e o painel **voltou a buscar imagens de fundo, ícones, fontes e até telemetria** (`events.mapbox.com`), com uma chave de demonstração que vem embutida no Streamlit.

**Trocamos a CARTO por outro fornecedor de imagens sem perceber.** O item 4 tinha resolvido um pedido inútil por desenho e criado nove.

**Por que os testes não pegaram:** eles liam o que o painel **manda**, e o mapa de fundo era colocado depois, pelo navegador. Nenhum teste sobre o que o painel manda podia ver isso. O teste `test_estilo_vazio_e_explicito` passou a exigir um **estilo vazio declarado**, e não a **falta** de estilo, porque a falta é um convite para o padrão dos outros. Mas o problema de verdade só aparece no painel de rede do navegador, e isso está anotado dentro do próprio teste.

**Por que o teste no computador não pegou:** foi testado em `localhost`, numa rede que **bloqueia** o `api.mapbox.com` (a mesma que bloqueia o `github.com`). As imagens falhavam em silêncio, e o mapa aparecia limpo. **Um falso "está tudo certo" causado pela rede bloqueada:** o ambiente de teste era mais fechado que o de produção, e escondeu o defeito em vez de mostrar.

**A correção, em duas tentativas:**
1. Primeiro, um estilo vazio como objeto (`{"version": 8, "sources": {}, "layers": []}`). **Não funcionou:** o servidor mandava certo (conferido dentro do container), mas o navegador descartava o objeto e usava o padrão.
2. O que funcionou: o **mesmo estilo vazio, escrito como texto** num endereço `data:`. Por ser texto, ele chega intacto até o navegador. E, como o conteúdo vai embutido, **o navegador nem precisa buscar o estilo em lugar nenhum.**

| Pedidos a sites de fora, por carregamento | Antes | Depois |
|---|---:|---:|
| `api.mapbox.com` | 8 | **0** |
| `events.mapbox.com` (telemetria) | 1 | **0** |

Medido no **endereço público**, não em `localhost`.

**A lição que fica:** "o painel não pede imagem a ninguém" é uma afirmação sobre o **navegador**, e **só o navegador pode confirmar**. O teste do que mandamos verifica o que mandamos; o painel de rede verifica o que acontece de verdade. Para isso, só o segundo vale, e ele precisa rodar **contra o painel publicado**, ou numa rede que não esconda nada.

---

# Limites conferidos pelos testes (valem hoje)

| O que é limitado | Limite | Medido | Onde fica o teste |
|---|---:|---:|---|
| **Tamanho do mapa**, Brasil | até 200 KB | **98 KB** | `tests/test_mapa.py` |
| **Tamanho do mapa**, um estado | até 20 KB | **3 KB** | `tests/test_mapa.py` |
| **Servidor, por clique** | até 400 ms | **~137 ms** | `tests/test_performance.py` |
| **`processar_dados`** | até 30 ms | — | `tests/test_performance.py` |
| **Contorno**, número de pontos | até 6.000 | **4.469** | `tests/test_geo.py` |
| **Contorno**, tamanho do arquivo | até 200 KB | **~96 KB** | `tests/test_geo.py` |

**"Por clique"** é todo o trabalho de trocar o ano ou a seleção: processar o ano atual e o anterior, montar o mapa e os quatro gráficos.

**Os limites têm folga de propósito.** Prender o número exato faria o teste falhar por variação normal da máquina. O que eles pegam é piora **grande**, de outra ordem de grandeza.

**Conferido em out/2026:** os 72 testes de mapa, contorno e tempo passam. O arquivo do contorno tem hoje ~96 KB (a medição antiga dizia 105 KB).

## Sobre o `fig_ranking`

As tabelas acima ainda medem o `fig_ranking`, que **não existe mais**. O ranking saiu do painel em 04/set/2026, por mostrar a mesma informação do mapa e da tabela de estados (veja a [Documentação dos Gráficos](DOCUMENTACAO_GRAFICOS.md)).

Os números ficam **como registro da medição daquela época**. Na prática, o painel hoje é **mais rápido** do que essas tabelas mostram, porque tem um gráfico de ~30 ms a menos.

## O que ainda não foi medido

- O **tempo que a pessoa sente**, do clique até ver o resultado, no navegador.
- Como o painel se comporta com **várias pessoas usando ao mesmo tempo**.
