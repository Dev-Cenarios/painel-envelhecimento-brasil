import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .data import ESTIMATIVA_ATE
from .utils import H_MEDIUM, H_LARGE, _apply_layout

#: Última idade da base, e balde aberto: 90 é "90 ou mais". A última faixa da
#: pirâmide é este número seguido de "+".
IDADE_TOPO = 90


def processar_dados(df: pd.DataFrame):
    """Deriva faixa etária e o recorte de idosos por UF a partir da base bruta.

    Args:
        df: DataFrame de um único ano, colunas `uf`, `idade`, `sexo`,
            `populacao` (ver `src.data.carregar_dados`).

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            - `df_proc`: mesma base recebida, com a coluna `faixa_etaria`
              (bins de 5 em 5 anos, "90+" no topo) adicionada.
            - `df_idosos`: uma linha por UF, com `total`, `idosos` (idade
              >= 60) e `pct_idosos`.
    """
    # A última faixa é **90+**, porque a base termina em 90 e essa idade não é
    # "quem tem 90": é o balde aberto "90 anos ou mais" da tab1 do IBGE.
    #
    # A faixa final tem que coincidir com o balde da base. Quando a base
    # parava em 80 e a pirâmide desenhava até 100+, os 4,96 milhões de 80+
    # caíam inteiros em "80-84" — 1,8x o valor real — e quatro faixas acima
    # ficavam zeradas, sugerindo que ninguém no Brasil passa dos 85.
    # `IDADE_TOPO` em tests/test_numeros.py prende a coincidência.
    bins   = list(range(0, IDADE_TOPO + 1, 5)) + [200]
    labels = [f"{i}-{i+4}" for i in range(0, IDADE_TOPO, 5)] + [f"{IDADE_TOPO}+"]

    df_proc = df.copy()
    df_proc["faixa_etaria"] = pd.cut(df_proc["idade"], bins=bins, labels=labels, right=False)

    total_uf  = df_proc.groupby("uf")["populacao"].sum().rename("total")
    idosos_uf = (
        df_proc[df_proc["idade"] >= 60]
        .groupby("uf")["populacao"].sum()
        .rename("idosos")
    )
    df_idosos = pd.concat([total_uf, idosos_uf], axis=1).fillna(0).reset_index()
    df_idosos["pct_idosos"] = (df_idosos["idosos"] / df_idosos["total"] * 100).round(2)

    return df_proc, df_idosos


def fig_pizza(df: pd.DataFrame, t: dict, apenas_idosos: bool = False) -> go.Figure:
    """Monta o gráfico de rosca de distribuição por sexo.

    Args:
        df: base processada (ver `processar_dados`), colunas `idade`,
            `sexo`, `populacao`.
        t: dicionário de tema (cores) atual.
        apenas_idosos: quando True, restringe a base a idade >= 60 antes
            de agregar (toggle "Apenas ≥ 60 anos" da UI).

    Returns:
        go.Figure: gráfico de rosca com o total no centro.
    """
    from .utils import _fmt
    df_pie = df[df["idade"] >= 60].copy() if apenas_idosos else df.copy()
    agg = df_pie.groupby("sexo")["populacao"].sum().reset_index()
    agg["label"] = agg["sexo"].map({"M": "Masculino", "F": "Feminino"})
    total = agg["populacao"].sum()

    fig = px.pie(
        agg, names="label", values="populacao", color="label",
        color_discrete_map={"Masculino": t["serie_m"], "Feminino": t["serie_f"]},
        hole=0.55,
    )
    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent:.1%}",
        textfont=dict(size=14, color="#ffffff"),
        insidetextorientation="horizontal",
        hovertemplate="<b>%{label}</b><br>%{value:,} pessoas<br>%{percent:.1%}<extra></extra>",
        marker_line_color=t["bg"],
        marker_line_width=3,
        pull=[0.03, 0.03],
    )
    _apply_layout(fig, t, H_MEDIUM)
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.08,
            xanchor="center", x=0.5,
            font=dict(size=13, color=t["text"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        annotations=[dict(
            text=f"<b>{_fmt(total)}</b><br><span style='font-size:11px'>{('pessoas com 60+' if apenas_idosos else 'pessoas')}</span>",
            x=0.5, y=0.5, font=dict(size=18, color=t["text_title"]),
            showarrow=False, align="center",
        )],
    )
    return fig


def fig_piramide(df: pd.DataFrame, t: dict) -> go.Figure:
    """Monta a pirâmide etária (barras horizontais opostas por sexo).

    Masculino é plotado como valores negativos (`x=-masc.values`) para
    ficar à esquerda do eixo zero, convenção padrão de pirâmide etária.

    Args:
        df: base processada (ver `processar_dados`), precisa da coluna
            `faixa_etaria`.
        t: dicionário de tema (cores) atual.

    Returns:
        go.Figure: pirâmide etária com barras opostas.
    """
    # Termina em "90+" porque a base termina ali — ver `processar_dados`.
    FAIXAS = [f"{i}-{i+4}" for i in range(0, IDADE_TOPO, 5)] + [f"{IDADE_TOPO}+"]
    agg = df.groupby(["faixa_etaria", "sexo"], observed=False)["populacao"].sum().reset_index()
    agg["faixa_etaria"] = agg["faixa_etaria"].astype(str)
    agg = agg[agg["faixa_etaria"].isin(FAIXAS)]

    masc = agg[agg["sexo"] == "M"].set_index("faixa_etaria")["populacao"].reindex(FAIXAS, fill_value=0)
    fem  = agg[agg["sexo"] == "F"].set_index("faixa_etaria")["populacao"].reindex(FAIXAS, fill_value=0)
    max_val   = max(masc.max(), fem.max())
    tick_step = max(1, int(max_val // 5))

    fig = go.Figure([
        go.Bar(
            y=FAIXAS, x=-masc.values, name="Masculino", orientation="h",
            marker_color=t["serie_m"], marker_line_color=t["bar_line"], marker_line_width=0.6,
            hovertemplate="<b>%{y}</b><br>Masculino: %{customdata:,}<extra></extra>",
            customdata=masc.values,
        ),
        go.Bar(
            y=FAIXAS, x=fem.values, name="Feminino", orientation="h",
            marker_color=t["serie_f"], marker_line_color=t["bar_line"], marker_line_width=0.6,
            hovertemplate="<b>%{y}</b><br>Feminino: %{x:,}<extra></extra>",
        ),
    ])
    _apply_layout(fig, t, H_LARGE)
    fig.update_layout(
        barmode="relative", bargap=0.08,
        xaxis=dict(
            title=dict(text="← Masculino  |  Feminino →", font=dict(color=t["text"])),
            tickmode="array",
            tickvals=list(range(-int(max_val * 1.1), int(max_val * 1.1) + 1, tick_step)),
            ticktext=[f"{abs(v):,}" for v in range(-int(max_val * 1.1), int(max_val * 1.1) + 1, tick_step)],
            range=[-max_val * 1.15, max_val * 1.15],
            zeroline=True, zerolinecolor=t["border"], zerolinewidth=2,
            tickfont=dict(color=t["text_muted"]),
        ),
        yaxis=dict(title="", tickfont=dict(size=10, color=t["text"])),
        showlegend=False,
        margin=dict(l=10, r=20, t=30, b=40),
    )
    return fig


def _linha_com_fronteira(fig, df, coluna, nome, cor, hover):
    """Desenha uma série como sólida até `ESTIMATIVA_ATE` e tracejada depois.

    São dois traços com a mesma cor e um `legendgroup` só, para a legenda
    mostrar uma entrada por série e não quatro. O ano da fronteira entra nos
    dois, senão a linha teria um buraco — mas o hover dele fica só no traço
    sólido, porque com `hovermode="x unified"` o ponto repetido apareceria
    duas vezes no tooltip, com o mesmo número.
    """
    est  = df[df["ano"] <= ESTIMATIVA_ATE]
    proj = df[df["ano"] >= ESTIMATIVA_ATE]
    fig.add_trace(go.Scatter(
        x=est["ano"], y=est[coluna], name=nome, legendgroup=nome,
        mode="lines", line=dict(color=cor, width=2.5), hovertemplate=hover,
    ))
    fig.add_trace(go.Scatter(
        x=proj["ano"], y=proj[coluna], name=nome, legendgroup=nome,
        showlegend=False, mode="lines",
        line=dict(color=cor, width=2.5, dash="dash"), hovertemplate=hover,
        hoverinfo=["skip" if a == ESTIMATIVA_ATE else "all" for a in proj["ano"]],
    ))


def _marcar_fronteira(fig, t):
    """A linha vertical entre estimativa e projeção, rotulada.

    Tracejado sem legenda lê como escolha de estilo; a faixa rotulada é o
    que diz que dali para a frente o número é hipótese.
    """
    fig.add_vline(
        x=ESTIMATIVA_ATE + 0.5, line_width=1, line_dash="dot", line_color=t["text_muted"],
    )
    fig.add_annotation(
        x=ESTIMATIVA_ATE + 0.5, y=1, yref="paper", yanchor="top", xanchor="left",
        text="  projeção do IBGE →", showarrow=False,
        font=dict(size=11, color=t["text_muted"]),
    )


def fig_evolucao(df_evo: pd.DataFrame, ufs: list, t: dict) -> go.Figure:
    """A evolução da população em três curvas, 2000-2070, em milhões.

    O **total**, as pessoas de **0 a 14 anos** e as de **60 anos ou mais** —
    as três na mesma escala, que é o número de pessoas. As duas últimas se
    cruzam: no Brasil em **2029**, quando passa a haver mais gente com 60+ do
    que crianças. O cruzamento é a informação que o gráfico existe para dar,
    e vem anotado.

    **Por que as três cabem num eixo só.** São a mesma grandeza — pessoas — e
    os dois grupos são partes do total, não outra medida. Um eixo secundário
    para os grupos etários seria o erro clássico: duas escalas no mesmo
    desenho fazem o leitor comparar alturas que não são comparáveis.

    O preço é o pico do total, que num eixo que precisa alcançar os 15
    milhões de 60+ em 2000 vira um arco suave em vez da curva dramática que
    era quando ele estava sozinho. Por isso o pico vem anotado com o número.

    Cada série é sólida até `ESTIMATIVA_ATE` (2022) e tracejada depois, que é
    projeção — ver `_linha_com_fronteira`.

    Args:
        df_evo: população por UF e ano, com `jovens` e `idosos`
            (ver `src.data.carregar_evolucao`).
        ufs: siglas das UFs selecionadas no filtro; as somas são
            recalculadas sobre esse subconjunto a cada chamada.
        t: dicionário de tema (cores) atual.

    Returns:
        go.Figure: três linhas em milhões de habitantes, com o pico do total
            e o cruzamento entre os grupos etários anotados.
    """
    df = (
        df_evo[df_evo["uf"].isin(ufs)]
        .groupby("ano", as_index=False)[["populacao", "jovens", "idosos"]].sum()
    )
    for coluna in ("populacao", "jovens", "idosos"):
        df[f"{coluna}_M"] = df[coluna] / 1_000_000

    #: (coluna, nome na legenda, rótulo na ponta, cor). A ordem é a de
    #: desenho: o total primeiro, por baixo dos dois grupos.
    SERIES = (
        ("populacao_M", "População total", "total", t["serie_total"]),
        ("jovens_M", "0 a 14 anos", "0-14", t["serie_0_14"]),
        ("idosos_M", "60 anos ou mais", "60+", t["serie_60"]),
    )

    fig = go.Figure()
    for coluna, nome, _, cor in SERIES:
        _linha_com_fronteira(
            fig, df, coluna, nome, cor,
            "<b>%{x}</b><br>%{y:.1f}M pessoas<extra>" + nome + "</extra>",
        )

    # Rótulo direto na ponta de cada linha: com três curvas, a legenda
    # embaixo obriga o olho a ir e voltar para saber qual é qual.
    fim = df.iloc[-1]
    for coluna, _, rotulo, cor in SERIES:
        fig.add_annotation(
            x=fim["ano"], y=fim[coluna], text=f"<b>{rotulo}</b>", showarrow=False,
            xanchor="left", xshift=8, font=dict(size=12, color=cor),
        )

    # O cruzamento entre os dois grupos etários. Pode não existir no recorte
    # — se não existir, não se inventa uma anotação para ele.
    depois = df[df["idosos"] > df["jovens"]]
    if not depois.empty:
        ano_virada = int(depois["ano"].iloc[0])
        fig.add_annotation(
            x=ano_virada, y=float(depois["idosos_M"].iloc[0]),
            xanchor="right", ax=-16, ay=-30,
            text=f"em {ano_virada}, os 60+ passam as crianças",
            showarrow=True, arrowhead=0, arrowcolor=t["text_muted"],
            font=dict(size=11, color=t["text"]),
        )

    # O pico do total: onde a série vira. A âncora depende de onde ele cai —
    # perto da fronteira (RS e AL viram em 2026) ou da borda direita (MT
    # ainda cresce em 2070) o texto colidia ou era cortado.
    pico = df.loc[df["populacao_M"].idxmax()]
    ano_pico = int(pico["ano"])
    x_min, x_max = int(df["ano"].min()), int(df["ano"].max())
    if ESTIMATIVA_ATE < ano_pico <= ESTIMATIVA_ATE + 10 or ano_pico >= x_max - 8:
        xanchor, ax, ay = "right", -14, 28
    elif ano_pico <= x_min + 8:
        xanchor, ax, ay = "left", 14, 28
    else:
        xanchor, ax, ay = "center", 0, -32
    fig.add_annotation(
        x=ano_pico, y=pico["populacao_M"], xanchor=xanchor,
        text=f"pico em {ano_pico}: {pico['populacao_M']:.1f} M",
        showarrow=True, arrowhead=0, arrowcolor=t["text_muted"],
        ax=ax, ay=ay, font=dict(size=11, color=t["text"]),
    )

    _marcar_fronteira(fig, t)
    _apply_layout(fig, t, H_LARGE)
    fig.update_layout(
        xaxis=dict(title="", tickmode="linear", dtick=5, tickfont=dict(color=t["text_muted"])),
        yaxis=dict(
            title=dict(text="Milhões de pessoas", font=dict(color=t["text"])),
            # Do zero, agora que há três curvas: com o eixo cortado, a
            # distância entre as linhas deixaria de ser comparável, e é ela
            # que mostra o quanto os 60+ alcançam as crianças.
            rangemode="tozero",
            tickfont=dict(color=t["text_muted"]),
        ),
        legend=dict(orientation="h", y=-0.15, x=0, font=dict(color=t["text"])),
        hovermode="x unified",
        # r=58: cabem os rótulos diretos à direita do último ponto.
        margin=dict(l=10, r=58, t=20, b=10),
    )
    return fig
