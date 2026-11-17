# Documentação dos Gráficos — Envelhecimento Populacional

Para cada parte da tela, este documento explica: **por que existe**, **como é calculada** e **onde está o código**. Também registra **o que saiu do painel, e por quê**.

---

## 01 · Onde estão os 60+

**Por que existe:** é a primeira coisa que a pessoa vê. Mostra, de relance, **onde no Brasil a proporção de pessoas com 60+ é maior**.

**Como é calculado:**
- `src/charts.py` → `processar_dados()` soma, para cada estado, `total` (todas as idades) e `idosos` (60 anos ou mais), e calcula `pct_idosos = idosos ÷ total × 100`.
- O mapa é desenhado com o `GeoJsonLayer` do deck.gl (via pydeck). A cor de cada estado é calculada em Python, numa **rampa roxa de 6 tons**, do `#BFA1DB` (mais claro) ao `#3D1A5C` (mais escuro). O mapa liga o dado ao desenho pela sigla do estado.

**Código:** `src/mapa.py` → `deck()`. A legenda fica em `src/mapa.py` → `legenda()`.

### Quatro cores, com cortes fixos

O mapa tem **quatro classes de cor**, com cortes em **11,4% / 19,7% / 29,9%**. Esses cortes foram calculados **uma vez só, sobre todos os anos (2000 a 2070) e todos os estados** juntos. Não mudam por ano e não mudam com o filtro.

**Por que não calcular por ano:** o quartil é uma medida relativa e **sempre coloca um quarto dos estados em cada cor**. O mapa de 2010 e o de 2050 sairiam iguais, e o envelhecimento do país ficaria invisível. **Com corte fixo, o mapa escurece década a década**, e é para isso que ele existe.

**Os cortes foram refeitos em 15/set/2026**, quando a base passou de 2010–2025 para 2000–2070. No período todo, a proporção de 60+ vai de **4% a 40%**, e quatro cortes que cubram tudo isso separam pouco dentro de um ano só. As opções testadas, contando quantos estados ficam em cada cor (da mais clara para a mais escura):

| Cortes | 2010 | 2025 | 2040 | 2050 | 2070 |
|---|---|---|---|---|---|
| fixos sobre 2010–2025 (os antigos) | 13/11/3/0 | 2/3/4/18 | 0/0/0/27 | 0/0/0/27 | 0/0/0/27 |
| **fixos sobre 2000–2070 (os atuais)** | 23/4/0/0 | 4/22/1/0 | 0/6/21/0 | 0/0/17/10 | 0/0/0/27 |
| calculados a cada ano | sempre 7/7/7/6 | | | | |

- **Os antigos** pintavam tudo de 2040 em diante na cor mais escura: **três décadas de mapa igual**.
- **Os atuais** perdem contraste em 2025 (22 estados na mesma cor), mas **o mapa continua mudando até 2070**.
- **A tabela 02**, ao lado, mostra o valor exato de cada estado no ano. **É ela que separa o que o mapa junta.**

(A linha dos cortes atuais foi recalculada em out/2026 e bateu.)

**Por que não calcular sobre o filtro:** se os cortes fossem recalculados sobre os estados escolhidos, **os estados mudariam de cor a cada filtro**. A cor passaria a dizer **a posição do estado entre os escolhidos**, e não a proporção dele. O teste `test_cortes_nao_mudam_com_o_filtro` garante isso.

**O preço assumido:** menos contraste dentro de um ano, em troca de **poder comparar anos**.

### Clicar num estado

**Clicando num estado, o painel inteiro passa a mostrar os dados dele:** números de destaque, sexo, pirâmide e evolução. O topo da página avisa, por exemplo, "PE em foco". **Clicando de novo** (ou no ✕ que o Streamlit coloca sobre o mapa), volta.

**O mapa e a tabela continuam mostrando o recorte inteiro**: o estado em foco fica forte e com contorno grosso, e os outros ficam apagados (`ALFA_FORA_DE_FOCO`). O motivo: **é no mapa que se escolhe o próximo estado.** Se o mapa mostrasse só o estado clicado, não teria onde clicar para trocar.

**Três decisões de programação que vale saber:**

- **Sem `st.rerun()`.** O clique chega pelo `on_select="rerun"` e é lido no `st.session_state[chave_mapa]` **antes** de o mapa ser desenhado. O Streamlit já entrega, no começo, o que aconteceu na interação anterior. É isso que permite que os números de destaque, que ficam **acima** do mapa, já apareçam filtrados.
- **A "chave" do mapa muda com o recorte.** O Streamlit lembrava a seleção mesmo depois de trocar o recorte. Com MG em foco, ir para "Sul" tirava o foco, mas voltar para "Todos" trazia MG de volta sozinho. Com uma chave nova a cada recorte, o mapa "esquece". **O foco continua ao trocar de ano**, de propósito: comparar 2026 e 2050 do mesmo estado é uma leitura que vale.
- **A página não pula para o topo.** O script do botão de tema rolava a página para o topo a cada clique, e o mapa fica no meio da página: a pessoa clicava e era jogada para longe. Agora isso só acontece no primeiro carregamento.

### A rodinha do mouse não dá zoom

Rolar a página com o mouse em cima do mapa dava zoom e tirava o mapa do lugar. Como o mapa ocupa meia tela, isso acontecia o tempo todo.

**Não tinha jeito "oficial" de desligar:** o Streamlit sempre liga os controles do mapa (`controller={true}`) e ignora a configuração que a gente manda. A solução foi **interceptar a rodinha direto na página**, sem bloquear a rolagem (`sem preventDefault`), para a página continuar rolando normalmente.

**Os botões de zoom também foram escondidos.** Sem a rodinha, eles seriam o único jeito de tirar o mapa do lugar, e zoom num mapa de estados com enquadramento fixo não acrescenta nada.

### O Distrito Federal ampliado

No mapa do Brasil inteiro, o DF tem uns **9 × 5 pixels**. Acertar ele com o mouse era questão de pontaria.

**A opção do deck.gl (`pickingRadius`) não resolve:** ela só procura em volta quando não tem nada embaixo do cursor, e o DF é cercado por Goiás. Medido: a 6 pixels do DF, a dica mostrava GO.

**A solução:** desenhar o DF **ampliado em volta do próprio centro, mantendo o formato**:
- **mesma cor** da classe dele, para não inventar informação;
- **contorno branco**, avisando que aquele desenho está fora de escala, como os "detalhes ampliados" dos mapas impressos.

Quando o recorte aproxima o mapa e o estado já fica grande, a ampliação some sozinha.

**Uma primeira versão usava um círculo.** Resolvia a pontaria, mas trocava o formato conhecido do DF por uma bolinha e descaracterizava o mapa sem necessidade.

### Sem mapa de fundo

Antes, o mapa era um `choropleth_mapbox` em cima das imagens de fundo da **CARTO** (`carto-positron`). Até que a CARTO passou a exigir chave de acesso, e **o painel no ar mostrava "API KEY REQUIRED" repetido embaixo do mapa.**

Trocar de fornecedor só adiaria o problema. **Um mapa por estado não precisa de rua nem de rio embaixo: a informação é a cor do estado.** Sem imagem de fundo, não tem chave, não tem pedido a serviço de terceiro e não tem fornecedor que possa repetir isso.

### O contorno é preparado antes

O `scripts/preparar_geometria.py` roda uma vez e grava o `data/ufs.geojson`:
- simplifica o contorno sem abrir buracos entre estados vizinhos (de **85.585 para 4.469 pontos**);
- usa 5 casas decimais;
- guarda só a sigla do estado.

**Só os estados escolhidos são enviados ao navegador**, e sem espaços extras. O tamanho caiu de **1.953 KB para 98 KB** no Brasil inteiro, e para **3 KB** num estado só. Veja [Performance](performance.md).

### O enquadramento acompanha o filtro

Antes, o zoom era fixo (`zoom=3.2`). Agora, **o mapa se ajusta aos estados escolhidos.**

Ao calcular o enquadramento, **ilhas no meio do oceano são ignoradas**. Por exemplo: **Fernando de Noronha é de Pernambuco**. Sem esse cuidado, escolher PE desenharia um mapa quase todo de oceano.

### Sem plano B

O painel antigo tinha um gráfico de barras de reserva, porque o Mapbox dependia de um serviço externo pela internet e podia falhar. **Sem imagem de fundo, essa falha não existe.** Manter um segundo mapa em Plotly seria manter código que nunca roda.

---

## 02 · Estados mais envelhecidos (a tabela)

**Por que existe:** no mapa dá para ver o padrão, mas não o valor exato. **A tabela mostra os valores certinhos.**

**Como é calculado:** ordena os estados pela proporção de 60+, do maior para o menor, e mostra os **15 primeiros**. Se o filtro tiver menos de 15 estados, mostra todos.

**Código:** a ordenação é feita no `app.py`, e a tabela é montada em `src/utils.py` → `html_top5()`. O nome diz "top 5", mas ela mostra até 15.

---

## 03 · Homens e mulheres

**Por que existe:** mostra a divisão entre homens e mulheres na população toda, ou só entre quem tem 60+ (com a chave ligada).

**Como é calculado:** soma a população de cada sexo. Com a chave **"Apenas ≥ 60 anos"** ligada, tira quem tem menos de 60 antes de somar.

**Código:** `src/charts.py` → `fig_pizza()`.

---

## 04 · Pirâmide etária

**Por que existe:** é o gráfico clássico da demografia. **O formato conta a história:** base larga e topo fino = população jovem; base estreitando e topo engordando = população envelhecendo.

**Como é calculado:** o `processar_dados()` junta as idades em faixas de 5 anos (`0-4`, `5-9`, …, `85-89`) e a última é **`90+`**. Os homens ficam à esquerda (desenhados como números negativos) e as mulheres à direita.

**Por que a última faixa é "90+":** o dado do IBGE **termina em "90 ou mais"**, e a última faixa da pirâmide tem que combinar com isso. O `IDADE_TOPO`, em `src/charts.py`, garante.

**A lição veio da base anterior, que parava em "80 ou mais":** a pirâmide desenhava faixas até "100+". Os **4,96 milhões** de pessoas com 80 ou mais caíam todos em "80-84" (1,8 vez o valor real dessa faixa), e as faixas de cima ficavam zeradas, **como se ninguém passasse dos 85**. Veja a [Conferência dos dados](historico/conferencia-dados.md).

> ⚠️ **Esse mesmo problema continua no `dashboard-demografico`**, que ainda usa a base antiga. A correção feita aqui é o modelo para corrigir lá.

**Código:** `src/charts.py` → `fig_piramide()`.

---

## 05 · Evolução da população (2000–2070)

**Por que existe:** é o **único gráfico que mostra para onde a população vai**. E a projeção do IBGE conta uma história que nenhum retrato de um ano só conta:
- o Brasil **cresce até 2041** (220,4 milhões);
- e **chega em 2070 com menos gente do que tem hoje** (199,2 milhões).

Cada estado chega ao pico num ano: **RS e Alagoas em 2026, RJ em 2027, SP em 2036**. E **Mato Grosso ainda cresce em 2070**.

### Três linhas, um eixo

As linhas são: **população total**, pessoas de **0 a 14 anos** e pessoas com **60 anos ou mais**.
- `src/data.py` → `carregar_evolucao()` soma as três para cada estado e ano, de uma vez só. O resultado fica na memória e **não muda com o filtro de ano**.
- `fig_evolucao()` soma os estados escolhidos e mostra **em milhões**.

**O cruzamento das linhas é a informação principal.** No Brasil, é **2029**: o ano em que passa a haver **mais gente com 60+ do que crianças**. O RS já cruzou (2020), SP cruza em 2026 e Roraima só em 2047. O índice de envelhecimento (número de destaque do topo) mostra a **razão** entre os dois grupos. **Só aqui dá para ver quando** essa razão passa de 100.

**Por que num eixo só:** as três linhas medem a mesma coisa (pessoas), e os dois grupos são **partes** do total. Usar um segundo eixo seria o erro clássico: duas escalas no mesmo desenho fazem a gente comparar alturas que não são comparáveis.

**Por que "0 a 14" e não "até 15":** é o grupo padrão do IBGE e é o mesmo do índice de envelhecimento. Incluir quem tem 15 daria outro número, e o painel teria **duas definições de "jovem"**.

### Estimativa e projeção na mesma linha

- **Linha cheia até 2022**, o último ano que o IBGE chama de estimativa.
- **Linha tracejada de 2023 em diante**, que é projeção.
- **Uma linha vertical com nome marca a divisão.** Tracejado sem explicação parece só estilo, não significado.
- **O ponto de 2022 entra nas duas linhas**, para não ficar um buraco.

**Antes da troca de base,** o gráfico ia até 2025 em linha cheia, apresentando **três anos de projeção como se fossem contagem**.

### Por que o eixo começa no zero

Desde que as três linhas passaram a dividir o mesmo desenho, **o eixo precisa começar no zero**. Com o eixo cortado, a distância entre as linhas deixaria de ser comparável, e é justamente essa distância que mostra **os 60+ alcançando as crianças**.

**O preço:** o eixo precisa caber os 15 milhões de pessoas com 60+ de 2000, e o pico da população total vira uma curva suave, bem menos dramática do que quando a linha estava sozinha. Por isso **o pico vem anotado com o ano e o valor**, em vez de ficar para o olho perceber.

### Duas cores, não três

A **população total** é a soma dos dois grupos mais a faixa de 15 a 59 anos. Ela é **o todo**, não uma terceira categoria. Por isso fica em **cinza neutro**, e **só os dois grupos de idade ganham cor**.

Além de ser a leitura certa, isso resolveu um problema medido: com três cores (roxo + azul + terracota), **no tema escuro o roxo claro e o azul ficavam quase iguais para quem tem daltonismo** do tipo deuteranopia (ΔE 4,5). Com duas cores, os dois temas passam com folga (validado com o validador do skill `dataviz`):

| Tema | Cores | Diferença (ΔE) |
|---|---|---|
| claro | `#0F8FCC` + `#C0663C` | 20,8 (protanopia) |
| escuro | `#3598CC` + `#EA630E` | 25,0 (deuteranopia) |

**Código:** `src/charts.py` → `fig_evolucao()`.

---

## Os números de destaque (os 4 cartões do topo)

Calculados no `app.py` → `_indicadores()`, sobre os estados escolhidos. Cada um tem a comparação com o ano anterior, montada pelo `src/utils.py` → `_delta_html()`. **Se não tiver ano anterior, a comparação não aparece.**

| Cartão | O que é |
|---|---|
| **Pessoas com 60+** | Quantas pessoas. O total do país aparece embaixo, como referência |
| **Proporção de 60+** | Essas pessoas ÷ população total |
| **Índice de envelhecimento** | Pessoas com 60+ para cada 100 crianças de 0 a 14 anos |
| **Esperança de vida aos 60** | Quantos anos, em média, ainda vive quem chegou aos 60. É o valor oficial do IBGE (`e60`, tab4), não uma conta nossa. Para um grupo de estados, é a média dando mais peso a quem tem mais gente com 60+, e reproduz o valor oficial do Brasil com até 0,02 ano de diferença |

### Três cartões que saíram, e por quê

**"Idade média"** saiu em 15/set/2026, e a **esperança de vida aos 60** entrou no lugar. A idade média não estava errada: com a base até 90+, ela passou até a bater com o IBGE no centésimo. Mas ela fala da **população inteira**, e um painel sobre 60+ precisa do número que fala do **seu público**. O `e60` vai de **21,6 anos (AL) a 24,5 (DF)** em 2025, e é a única medida de **longevidade** de verdade no painel.

**"Proporção feminina"** mostrava 51,2% de mulheres. Tinha dois problemas:
- **não fala de envelhecimento**, é um dado geral da população;
- **praticamente não se mexe.** Medido: 51,09% em 2010 e 51,25% em 2025, só 0,16 ponto em quinze anos. O "▲ 0,0% vs ano anterior" que aparecia não era coisa do ano, era do indicador.

Um cartão que nunca se mexe ocupa um quarto da parte mais visível do painel para não informar nada. **O índice de envelhecimento entrou no lugar**: foi de **43 para 85** no mesmo período, ou seja, **dobrou**.

**"População total"** virou o texto de baixo do primeiro cartão. O painel é sobre a população com 60+, que merece o primeiro lugar. O total do país serve melhor como **referência** do que como indicador próprio.

### Uma cor só

Os quatro cartões usam **o roxo da marca**. Antes, cada um tinha uma cor (azul, laranja, roxo, verde) que **não queria dizer nada**: era decoração, e o olho tenta achar um significado que não existe. E, depois da troca de marca, a classe chamada `.blue` já pintava de roxo.

---

## Por que não tem um ranking de estados em barras

**Tinha**, na seção 06: um gráfico de barras com a proporção de 60+ por estado, ordenado. **Saiu porque mostrava o mesmo número** do mapa (01) e da tabela (02). Era a mesma informação em três formatos, na mesma página.

**A tabela ficou** porque é ela que completa o mapa: o mapa mostra **o padrão** e não mostra o valor exato; a tabela mostra **o valor exato** e não mostra o padrão. As barras não acrescentavam um terceiro olhar, só repetiam o segundo.

**O sinal de alerta foi o texto:** os três títulos precisavam dizer "proporção de idosos por estado" de jeitos um pouco diferentes, só para não parecerem repetidos. **Quando o texto precisa se contorcer assim, normalmente o problema é o conteúdo, não a palavra.**

---

## Vocabulário

O painel diz **"60+"** e **"pessoas com 60 anos ou mais"**, e não "idosos", em tudo que aparece na tela: títulos, cartões, legenda do mapa, cabeçalho da tabela e dicas do mouse.

**Não é preciosismo, é consistência.** Durante um tempo o painel usou as duas formas: os títulos diziam "60+" e a legenda do mapa dizia "% Idosos". Misturar palavras faz a pessoa parar para conferir se é a mesma coisa, e isso custa mais atenção do que a palavra economiza.

**Nos nomes internos do código** (`pct_idosos`, `df_idosos`), o termo continua. Ali ninguém de fora lê, e trocar mexeria em toda a parte de dados sem ganho nenhum.
