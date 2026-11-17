# Publicação no servidor (VM)

O servidor é a `cenarios-vm`. O IP e o acesso ficam com o responsável pela infraestrutura, e **ele só abre pela VPN**.

Ele hospeda **todos os painéis do Cenários**, cada um num container. Um **nginx** na própria máquina recebe os acessos e manda cada endereço para o painel certo.

**Painéis no servidor** (conferido em 21/out/2026):

| Painel | Porta no servidor | Endereço |
|---|---:|---|
| demografico | 8501 | `/cenarios/demografico` |
| tbpe | 8504 | `/cenarios/tbpe` |
| Leprosy | 8505 | `/cenarios/Leprosy/` |
| superset | 8506 | `/cenarios/superset/` |
| sinan | 8507 | `/cenarios/sinan` |
| **demografico-longevidade** | **8508** | `/cenarios/demografico-longevidade` |
| dftb | 8509 | `/cenarios/dftb` |
| hansepe | 8510 | `/cenarios/hansepe` |
| tbrecife | 8511 | `/cenarios/tbrecife` |
| tbbrasil | 8521 | `/cenarios/tbbrasil` |

O endereço antigo `/cenarios/tb` (que era a porta 8502) hoje **só redireciona** para o tbbrasil.

**Para atualizar no dia a dia, use o `deploy.sh`**, na raiz do projeto. Ele baixa o código novo (`git pull`), reconstrói a imagem e troca o container. O resto deste documento é a **primeira instalação**, que só se faz uma vez.

---

## 1. Levar o código para o servidor

O repositório é **privado**, então o `git clone` pede login. Antes de escolher como fazer, veja o que o servidor já tem:

```bash
ssh cenarios-vm 'git config --global credential.helper; ls ~/.ssh/*.pub'
```

**Três jeitos**, do mais simples ao mais controlado:

| Jeito | Vantagem | Desvantagem |
|---|---|---|
| **Chave de deploy** (recomendado) | Gera um par de chaves no servidor e cadastra a pública no GitHub (Settings → Deploy keys), **só leitura**. A chave serve para **este repositório e mais nada**. | Um passo a mais de configuração. |
| **`rsync` do seu computador** | Não precisa de login no servidor. | A pasta no servidor deixa de ter `git`, e **o `deploy.sh` para de funcionar**: toda atualização vira um `rsync` novo. |
| **Deixar o repositório público** | Resolve na hora. | **É uma decisão de exposição, não de conveniência.** Só faça se o conteúdo puder ser público. |

Com o login resolvido:

```bash
ssh cenarios-vm
git clone https://github.com/Dev-Cenarios/painel-envelhecimento-brasil.git dashboard-demografico-longevidade
cd dashboard-demografico-longevidade
docker compose up -d --build
docker compose ps        # depois de uns 40 segundos, deve aparecer "healthy"
curl -f http://localhost:8508/cenarios/demografico-longevidade/_stcore/health
```

**Por que esperar 40 segundos:** o container leva um tempo para ler os dados e ficar pronto. Durante esse tempo, ele aparece como `starting` (iniciando), e **não** como quebrado. Esse tempo foi definido quando a base tinha 23 MB; hoje ela tem menos de 1 MB, então o painel costuma ficar pronto antes, mas a margem continua.

> A porta 8508 **só aceita conexão de dentro do próprio servidor** (`127.0.0.1`). Por isso o teste com `curl` acima funciona, mas o painel só fica acessível de fora pelo nginx (passo 2).

---

## 1.5. O cartão na página inicial

**A rota do nginx faz o painel funcionar, mas não faz ninguém encontrá-lo.** Quem entra em `https://painel.cenarios.unb.br/` vê uma grade de cartões. Um painel sem cartão ali só existe para quem já sabe o endereço.

**Essa página não está em nenhum repositório.** É um arquivo HTML solto em `/var/www/frontpage/index.html`. O "histórico" dele são cópias `.bak-<data>` guardadas ao lado. **Editar publica na hora**, não precisa recarregar o nginx.

**Faça uma cópia antes de editar:**

```bash
ssh cenarios-vm 'cp /var/www/frontpage/index.html /var/www/frontpage/index.html.bak-$(date +%Y%m%d-%H%M%S)'
```

O cartão segue o formato dos outros:

```html
    <a class="card" href="/cenarios/demografico-longevidade">
      <div class="icon">🧓</div>
      <h2>Envelhecimento Populacional</h2>
      <p>Pessoas com 60 anos ou mais no Brasil — proporção por estado em quartis, índice de envelhecimento e pirâmide etária. Plataforma da Longevidade / UnB</p>
      <span class="tag new">Novo</span>
    </a>
```

**Ele fica logo depois do `Dashboard Demográfico`.** Os dois usam a mesma base e só mudam a marca e o recorte. Lado a lado, fica fácil escolher entre eles.

**Para conferir, use um "quebra-cache":** abra `https://painel.cenarios.unb.br/?v=2`. Sem o `?v=2`, o navegador pode mostrar a página antiga guardada, e vai parecer que a edição não funcionou.

---

## 2. A rota no nginx

O arquivo é o `/etc/nginx/sites-available/telessaude` (com um atalho em `sites-enabled/`). O bloco novo segue o formato dos outros:

```nginx
    location /cenarios/demografico-longevidade {
        proxy_pass         http://localhost:8508;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection $connection_upgrade;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
```

**Faça uma cópia antes de editar.** A pasta já tem vários `telessaude.bak-*`, sinal de que isso é costume ali:

```bash
sudo cp /etc/nginx/sites-available/telessaude \
        /etc/nginx/sites-available/telessaude.bak-$(date +%Y%m%d-%H%M%S)
sudo nginx -t            # NUNCA recarregue sem isto passar
sudo systemctl reload nginx
```

- **`nginx -t`** confere se o arquivo está escrito certo **antes** de aplicar.
- **`reload`** aplica sem derrubar quem já está conectado (o `restart` derrubaria).

### A "pegadinha" do caminho

As rotas daqui **não têm barra no final**. Então `/cenarios/demografico` também "casa" com `/cenarios/demografico-longevidade`, porque um começa igual ao outro.

**Não dá conflito:** o nginx escolhe **a rota mais longa**, e a deste painel vence. Mas isso acontece "por baixo dos panos", e **quem mexer em uma das duas rotas precisa conferir a outra.**

**Depois de recarregar, teste as duas**, não só a nova:

```bash
curl -sI https://painel.cenarios.unb.br/cenarios/demografico-longevidade | head -1
curl -sI https://painel.cenarios.unb.br/cenarios/demografico             | head -1
```

**Se o painel antigo começar a mostrar a página do novo**, a regra do caminho foi resolvida ao contrário. Nesse caso, volte a cópia de segurança e transforme as duas rotas em **rotas exatas** (`location = `) ou **com barra no final**.

---

## 3. Conferência final

- [ ] `https://painel.cenarios.unb.br/cenarios/demografico-longevidade` abre;
- [ ] o mapa aparece **sem** o aviso "API KEY REQUIRED" (era o defeito que motivou a troca do mapa; veja [Performance](performance.md));
- [ ] o painel `demografico` continua no ar, sem mudança.
