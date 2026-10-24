# Catálogo de categorias do OrganizaApps

Um arquivo público que diz a que **categoria** pertence cada app Android, por
nome de pacote. O app [OrganizaApps](https://github.com/Roquinho45) baixa este
arquivo para reconhecer apps que a base embutida nele ainda não conhece.

> **Nada é enviado para este repositório.** O app faz um `GET` de um arquivo
> estático, igual a você abrir o endereço no navegador, e resolve os pacotes
> **no próprio aparelho**. Quem hospeda não tem como saber quais apps você tem.

---

## O que tem aqui

| arquivo | o que é |
|---|---|
| `category_rules.json` | **o catálogo**: pacote → categoria |
| `categories.json` | a lista fechada de categorias válidas, com o nome em português |
| `scripts/check_rules.py` | o validador. Rode antes de abrir um PR |

Números da versão atual: **1607 pacotes** em **95 categorias**.

---

## O formato

```json
{
  "formatVersion": 1,
  "catalog": "organizaapps-catalogo",
  "updatedAt": "2026-10-24",
  "packageCount": 1607,
  "categoryCount": 95,
  "license": "CC0-1.0",

  "byCategory": {
    "calculators": [
      "com.google.android.calculator",
      "org.solovyev.android.calculator"
    ],
    "radio_sdr": [
      "org.sdrpp.sdrpp"
    ]
  },

  "provenance": {
    "com.google.android.calculator": { "origem": "conhecimento", "confianca": 90 }
  }
}
```

### `byCategory` — a parte que importa

Um objeto de `chave de categoria` → **lista de pacotes**, ordenada
alfabeticamente.

Agrupado por categoria, e não `pacote → categoria`, por um motivo prático:
acrescentar um app é **uma linha**, no meio de uma lista que você consegue ler.
No formato invertido, o arquivo seria 1607 linhas soltas sem nenhuma
organização visível.

O app inverte o mapa ao carregar — a pergunta que ele faz é "qual a categoria
deste pacote?".

### `provenance` — de onde veio cada regra (opcional)

Só os pacotes que têm registro aparecem aqui. Quem não aparece assume
confiança 95.

| origem | confiança típica | o que significa |
|---|---|---|
| `verificado` | 100 | alguém abriu o app e viu o que ele faz |
| `pesquisa_web` | 95 | pesquisado e confirmado em fonte pública |
| `conhecimento` | 80–90 | app conhecido; 90 quando a categoria é óbvia, 80 quando é razoável mas poderia ser uma vizinha |
| `curadoria` | 95 (padrão) | da curadoria original, sem registro individual |

Isso não é enfeite: o app **usa** a confiança para destacar as regras fracas na
tela de revisão, em vez de tratar um palpite e um fato como a mesma coisa.

### `formatVersion`

Sobe só quando a estrutura mudar de um jeito que um app antigo **não entenda**.
Acrescentar uma chave no topo não conta — o app lê apenas `byCategory` e ignora
o resto, então chave nova é compatível para trás.

### `categories.json`

A lista fechada de chaves que uma regra pode usar. Uma categoria **nasce no
app**, não aqui: a chave precisa existir no `AppCategory.kt` do OrganizaApps,
porque é ela que carrega o ícone, a cor e o nome traduzido nos 20 idiomas.

Se faltar uma categoria para o app que você quer classificar, abra uma issue
no repositório do app antes de abrir o PR aqui.

---

## Como corrigir ou acrescentar uma regra

### 1. Confira se o pacote está certo

**Nome de pacote nunca sai de saída cortada no terminal.** Essa regra está
aqui porque oito pacotes já entraram errados assim, e um nome errado é
invisível: ele simplesmente nunca casa com app nenhum.

Jeitos confiáveis de obter o nome:

```bash
# com o aparelho ligado por USB
adb shell pm list packages | grep -i parte-do-nome

# ou na URL da Play Store:
# play.google.com/store/apps/details?id=  <-- o que vem depois do id= é o pacote
```

### 2. Escolha a categoria

Veja `categories.json`. Prefira a mais **específica** que couber: uma
calculadora científica vai em `calculators`, não em `tools`.

### 3. Edite `category_rules.json`

Acrescente o pacote na lista da categoria, **em ordem alfabética**. Se quiser,
registre a procedência:

```json
"provenance": {
  "com.exemplo.meuapp": { "origem": "pesquisa_web", "confianca": 95 }
}
```

Atualize `packageCount` e `categoryCount` no topo — o validador cobra.

### 4. Rode o validador

```bash
python scripts/check_rules.py
```

Ele confere categoria inexistente, pacote em duas categorias, pacote repetido,
nome implausível, procedência órfã, contadores errados e ordenação. **PR que
não passa no validador não entra.**

### 5. Abra o pull request

Explique **por que** aquela categoria, principalmente se o app não for óbvio.
"É um app de bordado" vale mais que "mudei a categoria".

---

## O que NÃO entra aqui

- **Pacote que não existe publicamente.** Build de desenvolvimento, app
  interno de empresa, APK de teste. Um pacote que só existe no celular de uma
  pessoa, listado num arquivo público, conta a todo mundo que essa pessoa
  existe e no que ela trabalha.
- **Lista de apps instalados de alguém.** Este catálogo é uma afirmação sobre
  *apps*, nunca sobre *pessoas*.
- **App removido da Play por malware.** Classificar não é endossar, mas também
  não vamos ajudar ninguém a organizá-lo bonitinho.
- **Opinião.** "Este app é ruim" não é categoria.

---

## Licença: CC0 1.0

O conteúdo deste repositório está em **domínio público** pela
[CC0 1.0](LICENSE). Use, copie, modifique e redistribua, inclusive
comercialmente, sem pedir permissão e sem precisar dar crédito.

### CC0 ou MIT? A diferença em duas linhas

- **CC0** é uma renúncia de direitos feita para **dados e conteúdo**: quem usa
  não precisa fazer nada, nem manter aviso de copyright.
- **MIT** é uma licença de **software**: permite quase tudo, mas obriga a
  manter o aviso de copyright junto — o que é estranho numa lista de pacotes e
  atrapalha quem quiser misturar este catálogo com outro.

**Escolhi CC0** porque isto é uma base de dados factual, não um programa, e o
objetivo é que ela circule sem atrito. Se você preferir MIT, é trocar o
arquivo `LICENSE` e a chave `"license"` do JSON.

---

## Como o app usa isto

```
https://raw.githubusercontent.com/Roquinho45/organizaapps-catalogo/main/category_rules.json
```

- baixado **uma vez por sessão**, só quando há app não reconhecido;
- **opcional**: o app pergunta antes, e o padrão é perguntar sempre;
- o resultado vai para um cache local de 30 dias;
- **se este endereço estiver fora do ar ou não existir, o app segue offline**,
  sem travar e sem erro na tela. A base embutida continua funcionando.

Esse último ponto é deliberado: o catálogo é um **bônus**, nunca um requisito.
O OrganizaApps organiza 100% offline desde a primeira versão.
