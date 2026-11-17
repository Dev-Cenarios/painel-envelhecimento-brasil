# Identidade visual — Plataforma da Longevidade

Este painel **deixou de usar a marca do Cenários+** e passou a usar a do **Observatório da Longevidade / UnB** ([longevidade.unb.br](https://longevidade.unb.br)).

**Nenhuma cor foi escolhida "no olho":**
- **as cores da marca** foram copiadas do código (CSS) do próprio site;
- **as cores dos gráficos** passaram por uma validação de contraste e de diferença entre cores (com simulação de daltonismo), o mesmo critério do manual de identidade dos painéis do Cenários.

---

## As cores da marca

Copiadas das variáveis de cor do site (`--primary` e as outras):

| Para que serve | Cor | Onde aparece no painel |
|---|---|---|
| Principal | `#6B2F96` | a barra do topo, o rodapé e a cor de destaque do tema claro |
| Clara | `#8A4BBF` | um dos tons da rampa do mapa |
| Escura | `#4A1F6E` | (não usada no painel) |
| Fundo suave | `#F3EDF9` · `#F5F0FA` | o fundo do topo da página |
| Borda | `#E4DAF0` | a borda do topo da página |
| **Destaque** | `#AA2DA3` | a flor do logo; segunda cor de destaque |

**O magenta (`#AA2DA3`) não veio do CSS:** foi **medido direto na imagem do logo**, onde ele ocupa 22% dos pixels da flor.

### Contraste: a troca de cor também melhorou a leitura

| | Texto branco sobre a cor |
|---|---:|
| `#6B2F96` (roxo da Longevidade) | **8,49 : 1** |
| `#2B7BB9` (azul do Cenários) | 4,53 : 1 |

**Quanto maior o número, mais fácil de ler.** O mínimo recomendado (norma WCAG, nível AA) é 4,5 : 1. **O azul do Cenários passava raspando; o roxo passa com folga.** E o roxo também funciona como **texto em cima de fundo claro** (7,98 : 1).

(Contrastes recalculados em out/2026: todos batem.)

---

## O logo

No site, o logo é uma **imagem JPEG com fundo branco**, de 823 × 247 pixels (`assets/media9.jpeg`, no site do Observatório; o arquivo não está neste repositório). Ele tem:
- "Plataforma" numa fonte com serifa, fina;
- "Longevidade" em negrito bem pesado;
- uma **flor de cinco pétalas** no lugar do "o".

**Aqui o logo foi redesenhado em SVG** (`themes.FLOR_SVG` + `themes.marca_html`), em vez de recortado da imagem. Três motivos:
1. **aumenta sem ficar serrilhado;**
2. **não leva uma caixa branca** para dentro do tema escuro;
3. **as pétalas pegam a cor do texto** automaticamente (`currentColor`).

### A flor muda de cor na barra

No logo original, a flor é **magenta sobre branco**. Na barra roxa do painel, ela fica **branca com o miolo roxo**.

O motivo: magenta (`#AA2DA3`) em cima do roxo (`#6B2F96`) são dois roxos parecidos, e **a flor sumiria**. Onde o fundo é claro, o magenta continua sendo a cor de destaque.

### A fonte do nome

O nome usa **a fonte do sistema, em negrito forte (peso 800)**, que é o que o próprio site usa (ele não carrega fonte especial).

> **Pendência:** pedir ao Observatório **o arquivo vetorial original** do logo. A reprodução é fiel no formato, mas não na fonte exata da imagem.

---

## As cores dos gráficos

Os critérios, para quem for refazer a validação: contraste de pelo menos
2 : 1 de cada tom contra o fundo (`#f6f8fa` no claro, `#0d1117` no escuro),
brilho mudando sempre na mesma direção ao longo da rampa e diferença (ΔE) de
pelo menos 15 entre cores de categorias, inclusive na simulação de
daltonismo.

### A rampa do mapa (do claro ao escuro)

| Tema | Tons |
|---|---|
| Claro | `#BFA1DB #A177C7 #8A4BBF #6B2F96 #552578 #3D1A5C` |
| Escuro | `#E0CDF2 #C6ACE0 #AE8AD2 #9668C4 #7F4DB8 #6B3F9E` |

**As duas passam nos testes:** o brilho vai mudando sempre na mesma direção, cada tom é bem diferente do vizinho, é tudo do mesmo matiz (roxo) e as pontas aparecem bem contra o fundo.

**São duas rampas diferentes, e não uma o espelho da outra.** A rampa do tema claro **não funciona no fundo escuro** (`#0d1117`): o tom mais escuro fica com contraste de só 1,35 : 1 contra o fundo e some. Por isso cada tema tem os seus tons.

**A primeira tentativa foi reprovada:** começava em `#D9C7EA`, que tem contraste de **1,48 : 1** contra o fundo claro (`#f6f8fa`). O mínimo é 2 : 1, e **o tom mais claro sumia no fundo**.

### Uma inversão que foi corrigida no caminho

O mapa antigo, em Plotly, ia do **azul escuro** (`#084c96`) ao **azul claro** (`#63b3ed`). Ou seja: **quanto mais idosos, mais clara a cor do estado.** Isso é o contrário do que todo mundo espera de um mapa de cores (mais escuro = mais), e **faz o olho ler o mapa ao avesso**.

A rampa nova vai **do claro ao escuro**, e o teste `test_rampa_vai_de_claro_a_escuro` garante isso nos dois temas.

> ⚠️ **O `dashboard-demografico` ainda tem o mapa invertido**, porque não recebeu essa correção.

### Homens e mulheres

| Tema | Homens | Mulheres |
|---|---|---|
| Claro | `#7F4DB8` | `#C0663C` |
| Escuro | `#9E79CC` | `#EA630E` |

**O par "óbvio" foi reprovado.** Roxo da marca + magenta da flor (`#6B2F96` + `#AA2DA3`) tem diferença (ΔE) de só **5,3 para quem tem daltonismo** do tipo protanopia, e **12,7 até para quem enxerga cores normalmente**. O mínimo é 15. **As duas metades da pirâmide ficariam iguais para qualquer pessoa**, não só para quem tem daltonismo.

**Foram tentadas várias formas de deixar as duas cores roxas.** Todas falharam: no tema escuro, o roxo claro perde cor demais e **parece cinza**.

**O que passa nos dois temas é roxo + terracota** (ΔE de 23,3 no tema claro). E esses terracotas são **os mesmos já aprovados no manual do Cenários**, então os painéis da casa continuam conversando entre si.

---

## A regra que fica

O roxo serve para **marca e para quantidade**: a barra, o rodapé, os botões e a rampa do mapa (mais escuro = mais).

O roxo **não serve para separar categorias** (como homem × mulher). Nesse caso, o que importa é que as cores sejam **bem diferentes entre si**, e não que sejam fiéis à marca.

**Confundir essas duas coisas é o que produz um gráfico bonito e ilegível.**
