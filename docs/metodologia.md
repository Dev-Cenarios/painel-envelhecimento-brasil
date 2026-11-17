# Metodologia — de onde vem cada número do painel

Esta página é a referência. Para cada número que aparece na tela, ela responde três perguntas:

1. **de onde vem;**
2. **como é calculado;**
3. **o que ele não diz.**

Aqui está só **o que vale hoje**. A história de como se chegou a cada decisão fica nos outros documentos, indicados ao longo do texto.

**Os exemplos usam o painel aberto em 2026, com todos os estados**, a não ser quando estiver escrito outro recorte. Os valores de referência estão "presos" no `tests/test_numeros.py`: se os dados forem gerados de novo e algum número mudar, o CI avisa.

**Todos os números desta página foram recalculados em out/2026**, direto nos arquivos de dados, e bateram.

---

## 1. A fonte

**Projeções da População: Brasil e Unidades da Federação, revisão 2024**, do IBGE (Diretoria de Pesquisas, Coordenação de População e Indicadores Sociais).

É a **projeção oficial em vigor**, e parte do Censo Demográfico 2022.

| O quê | Onde |
|---|---|
| Planilhas | [ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/](https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/) |
| Metodologia do IBGE | *Série Relatórios Metodológicos*, v. 40, 3ª ed. (na mesma pasta) |
| As duas planilhas usadas | `tab1_idade_simples` (população) e `tab4_indicadores` (esperança de vida) |

**O painel não lê as planilhas direto.** Ele lê dois arquivos em `data/`, gerados pelo `scripts/preparar_projecao.py`. O script:
- fica só com os **27 estados** (as planilhas trazem Brasil e Grandes Regiões misturados nas mesmas linhas);
- **descarta as linhas "Ambos os sexos"**, que são só a soma de homens e mulheres.

| Arquivo | Cada linha é… | Linhas |
|---|---|---:|
| `pop_uf.parquet` | estado × ano × sexo × idade (0 a 90+) | 348.894 |
| `indicadores_uf.parquet` | estado × ano: esperança de vida ao nascer (`e0`) e aos 60 (`e60`), por sexo e total | 1.917 |

**Não tem município.** O IBGE não faz projeção de população por município. O que existe por município são as **Estimativas** anuais (publicadas no Diário Oficial, para o FPM), e só do ano corrente. **Todo número deste painel é por estado, ou soma de estados.**

> ⚠️ **Cuidado com o SIDRA.** A tabela 7358 do SIDRA ("População, por sexo e idade") ainda é a **revisão 2018**. Ela dá **219,0 milhões** para 2025, 5,6 milhões a mais que a revisão atual. Se alguém comparar o painel com ela, vai achar um "erro" que não é nosso.

---

## 2. Estimativa e projeção

O IBGE divide a série em duas partes, e o painel mostra a mesma divisão:

| Anos | O que é | Como aparece no painel |
|---|---|---|
| **2000 a 2022** | **Estimativas**: o IBGE reconstrói o passado a partir dos Censos de 2000, 2010 e 2022 | linha cheia; ano sem marca |
| **2023 a 2070** | **Projeções**: um modelo que parte de hipóteses sobre nascimentos, mortes e migração | linha tracejada; "· projeção" no seletor de ano e no topo da página |

O limite fica em `ESTIMATIVA_ATE = 2022`, no `src/data.py`.

**O ano em que o painel abre (o ano atual) já é projeção**, e o painel avisa. Não é contagem: é **o que o modelo do IBGE espera** para aquele ano.

**Quando o IBGE lançar uma revisão nova, os números projetados mudam.** O painel mostra a revisão em vigor e não guarda a anterior.

---

## 3. Os quatro números de destaque

São calculados no `app.py` → `_indicadores()`, sobre o **recorte** e o **ano** escolhidos. O recorte pode ser: todos os estados, uma região, uma lista de estados ou o estado clicado no mapa.

O **"vs ano anterior"** compara com o mesmo recorte no ano anterior. **Em 2000 não aparece**, porque não tem ano antes.

### Pessoas com 60+

A soma de todo mundo com **60 anos ou mais**, no recorte e no ano.

**2026: 36.570.129 pessoas.**

O painel diz **"60+"** ou **"pessoas com 60 anos ou mais"**, nunca "idosos". O motivo está no [vocabulário](DOCUMENTACAO_GRAFICOS.md#vocabulário).

### Proporção de 60+

    pessoas com 60+ ÷ população total × 100

**2026:** 36.570.129 ÷ 214.211.951 = **17,07%**.

### Índice de envelhecimento

    pessoas com 60+ ÷ pessoas de 0 a 14 anos × 100

**Quantas pessoas com 60+ existem para cada 100 crianças.** É o indicador clássico do envelhecimento de uma população, e o que mais muda no período:

| 2010 | 2025 | **2026** | 2050 |
|---:|---:|---:|---:|
| 43 | 85 | **89** | 220 |

**Por que 60, e não 65.** O IBGE publica as duas versões (`IE60` e `IE65`). O painel usa 60 porque é o corte de todo o resto: **60 anos é a idade legal de pessoa idosa no Brasil** (Estatuto da Pessoa Idosa, Lei 10.741/2003). Fontes que usam 65+ (como a OMS e a OCDE) vão dar números menores. Não é erro: **é definição diferente.**

### Esperança de vida aos 60 (e60)

**Quantos anos, em média, ainda vive quem chegou aos 60.**

**É o valor oficial do IBGE** (`e60_T`, na tab4), e não uma conta do painel. **2026: 21,7 anos em Alagoas e 24,5 no DF.**

**Para um grupo de estados**, o IBGE não publica esse número. Ele publica só por estado e para o Brasil. Então o painel faz a **média dos estados, dando mais peso a quem tem mais gente com 60+**:

    e60 do recorte = soma de (e60 do estado × pessoas com 60+ do estado) ÷ soma de pessoas com 60+

**Conferido com o valor oficial do Brasil:** em 2025, a conta do painel dá **22,73** e o IBGE publica **22,71**. Nos outros anos conferidos (2010, 2050 e 2070), a diferença fica abaixo de 0,01 ano. O teste `test_e60_do_pais_bate_com_o_oficial` confere isso.

**Para um estado só**, é o valor oficial, sem conta nenhuma.

**Por que aos 60 e não ao nascer:** a esperança de vida **ao nascer** (`e0`) fala de recém-nascidos e depende muito da mortalidade infantil. Num painel sobre quem tem 60+, o número que fala desse público é o `e60`.

---

## 4. O mapa: onde estão os 60+

Cada estado é pintado pela sua **proporção de 60+** no ano, em **quatro cores**.

**Os cortes são fixos.** Eles foram calculados uma vez só, sobre **todos os estados e todos os anos (2000 a 2070) juntos**, dividindo tudo em quatro partes iguais (quartis):

| Cor | Proporção de 60+ |
|---|---|
| 1 (mais clara) | até 11,45% |
| 2 | de 11,45% a 19,74% |
| 3 | de 19,74% a 29,94% |
| 4 (mais escura) | 29,94% ou mais |

**Por que fixos:** o mapa existe para mostrar o envelhecimento **ao longo do tempo**.
- Se os cortes mudassem a cada ano, todo ano teria **um quarto dos estados em cada cor**, e 2010 ficaria igual a 2050.
- Com cortes fixos, **em 2000 todos os estados estão na cor 1** e **em 2070 todos estão na cor 4**. Dá para ver o país escurecer.

**O preço:** dentro de um ano só, o mapa separa pouco. **Em 2025, 22 dos 27 estados estão na mesma cor (a 2).** Por isso a **tabela ao lado** mostra o valor exato de cada estado: é ela que separa o que o mapa junta.

**Os cortes não mudam com o filtro.** A cor de um estado depende do valor dele, e não da posição dele entre os estados escolhidos (teste `test_cortes_nao_mudam_com_o_filtro`). As outras opções que foram testadas estão na [Documentação dos Gráficos](DOCUMENTACAO_GRAFICOS.md#01--onde-estão-os-60).

**Estados pequenos demais para clicar** (como o DF, no mapa do Brasil inteiro) são **desenhados maiores**, com contorno branco, como os "detalhes ampliados" dos mapas impressos. **O tamanho dele no mapa é falso, de propósito. O valor, não.**

---

## 5. A pirâmide etária

Faixas de 5 anos, de "0-4" até "85-89", e a última é **"90+"**.

**Por que a última faixa é "90+":** o dado do IBGE **termina em 90**, e esse 90 quer dizer **"90 anos ou mais"**. Em 2025, por exemplo, são 769 mil pessoas com "90", contra 212 mil com 89 anos. Por isso a última faixa da pirâmide também tem que ser aberta. Se ela fosse até "100+", todo mundo com 90 ou mais cairia em "90-94", e as faixas de cima ficariam vazias. O `IDADE_TOPO`, no `src/charts.py`, garante que as duas coisas combinem.

> Esse é exatamente o problema que existe hoje no `dashboard-demografico`, onde o dado termina em "80 ou mais" e a pirâmide vai até "100+". Este painel serve de modelo para a correção de lá.

**Homens à esquerda, mulheres à direita.** A soma de todas as faixas é a população do recorte, sem perder ninguém (teste `test_faixas_somam_a_populacao`).

---

## 6. Homens e mulheres

A soma da população por sexo, no recorte e no ano.

A chave **"Apenas ≥ 60 anos"** tira todo mundo com menos de 60 antes de somar.

O sexo é o da planilha do IBGE (Homens/Mulheres), sem outra categoria.

---

## 7. Evolução da população

Três linhas, ano a ano, de 2000 a 2070, todas em número de pessoas:

| Linha | Quem entra |
|---|---|
| População total | todas as idades |
| 0 a 14 anos | até 14 anos: o grupo padrão do IBGE, e o mesmo do índice de envelhecimento |
| 60 anos ou mais | 60 anos ou mais |

**Linha cheia até 2022** (estimativa) e **tracejada de 2023 em diante** (projeção), com o limite marcado. O **pico** da população total vem anotado: é o ano em que a população do recorte **para de crescer**.

### O cruzamento das linhas

**O ano em que as pessoas com 60+ passam a ser mais numerosas que as crianças** vem anotado:

| Brasil | RS | SP | RR |
|---:|---:|---:|---:|
| **2029** | 2020 | 2026 | 2047 |

O índice de envelhecimento mostra a **razão** entre os dois grupos. O cruzamento é o ano em que essa razão **passa de 100**.

### O pico

**No Brasil, o pico é em 2041, com 220,4 milhões de pessoas.** Em 2070 serão 199,2 milhões, menos do que hoje.

Cada estado chega ao pico num ano diferente: **Alagoas e RS em 2026, RJ em 2027, SP em 2036**. E **Mato Grosso ainda está crescendo em 2070.**

### Por que o eixo começa no zero

As três linhas dividem a mesma escala, e **a distância entre elas precisa ser comparável**. O efeito colateral é que o pico da população total parece menos dramático do que parecia quando a linha estava sozinha. Por isso ele vem anotado com o ano e o valor.

---

## 8. Os recortes

| Recorte | Quem entra |
|---|---|
| Todos os estados | os 27 |
| Norte | AC, AM, AP, PA, RO, RR, TO |
| Nordeste | AL, BA, CE, MA, PB, PE, PI, RN, SE |
| Centro-Oeste | DF, GO, MS, MT |
| Sudeste | ES, MG, RJ, SP |
| Sul | PR, RS, SC |
| Escolher estados… | os marcados. Se nenhum for marcado, mostra todos |
| Estado em foco (clique no mapa) | só ele, dentro do recorte acima |

As regiões são as **Grandes Regiões do IBGE**.

**Todo número do painel é recalculado para o recorte:** números de destaque, gráficos e esperança de vida.

**Exceção:** o **mapa e a tabela** continuam mostrando o recorte inteiro, mesmo com um estado em foco. Assim dá para clicar em outro estado.

---

## 9. O que os números NÃO dizem

- **Projeção é hipótese, não previsão.** De 2023 em diante, os números dependem do que o IBGE supõe sobre nascimentos, mortes e migração. A próxima revisão vai mudá-los.
- **Os estados ficam parecidos no futuro porque o IBGE supõe isso.** A diferença da esperança de vida ao nascer entre o melhor e o pior estado cai de **5,3 anos em 2025** para **1,2 em 2070**. Isso é uma **hipótese** do IBGE (os estados vão se aproximando), não algo que foi observado. **Não leia isso como dado.**
- **Sem município.** Com esta base, não dá para olhar nada abaixo do estado.
- **Sem cor/raça, renda ou escolaridade.** A projeção é só por idade e sexo.
- **De 2024 em diante, o "vs ano anterior" compara projeção com projeção.** Uma variação entre 2025 e 2026 é **a taxa que o modelo supõe**, e não uma medição.

---

## 10. Como conferir

**Os totais por estado e por idade batem com a tab1 do IBGE por construção:** o arquivo **é** a planilha, só que em outro formato.

**As conferências feitas:**

| Quando | Comparado com | Resultado |
|---|---|---|
| 04/set/2026 | Estimativas 2025 (Diário Oficial) e tab1, sobre a base antiga, por município | 27 estados exatos; 60+ com 4 pessoas de diferença |
| 15/set/2026 | base antiga × tab1, de 2010 a 2025, número por número | 8 de 69.984 números diferentes, no máximo 66 pessoas |
| 15/set/2026 | `e60` calculado pelo painel × `e60` oficial do Brasil | no máximo 0,02 ano de diferença (2010, 2025, 2050 e 2070) |
| out/2026 | todos os números desta página, recalculados nos dados atuais | todos batem |

**Para refazer:**

```bash
python scripts/preparar_projecao.py <pasta das planilhas>
pytest tests/test_numeros.py
```

Os valores de referência (população total em 2010, 2025 e 2070; 60+ em 2010 e 2025; pico em 2041; `e60` do Brasil) estão no próprio teste.

Mais detalhes em [Conferência dos dados](historico/conferencia-dados.md) e no [Levantamento das projeções](historico/levantamento-projecoes.md).
