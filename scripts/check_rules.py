#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confere a integridade de category_rules.json.

Rode isto ANTES de abrir um pull request. Se ele reclamar, o PR não entra.

Por que este script existe
--------------------------
Na curadoria original do app, oito pacotes foram digitados a partir de uma
listagem **truncada** no terminal. Um nome de pacote errado não quebra nada —
ele simplesmente nunca casa com app nenhum — e por isso o erro é invisível.
Este script o torna visível.

O que ele confere
-----------------
  1. toda chave de categoria existe em categories.json
  2. nenhum pacote aparece em duas categorias
  3. nenhum pacote repetido na mesma categoria
  4. nome de pacote com forma plausível
  5. todo pacote em `provenance` existe em `byCategory` e vice-versa
  6. origem e confiança válidas
  7. os contadores do topo batem com o conteúdo
  8. as listas estão ordenadas (o que mantém o `git diff` legível)
  9. (opcional) cruzamento com uma exportação de aparelho

Como usar
---------
    python scripts/check_rules.py
    python scripts/check_rules.py meus_apps.csv

Sai com código 1 se achar erro.

Adaptado do script homônimo do app OrganizaApps. A diferença: lá as chaves de
categoria são lidas do `AppCategory.kt`; aqui vêm de `categories.json`, porque
este repositório não tem código Kotlin. O `categories.json` é o contrato — a
lista fechada de chaves que uma regra pode usar.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RULES = RAIZ / "category_rules.json"
CATEGORIES = RAIZ / "categories.json"

# Um pacote Android: segmentos separados por ponto. Não exigimos um mínimo de
# segmentos porque existem casos reais curtos ("exa.lnx.a" mostra que segmento
# de uma letra acontece).
PACOTE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")

# As origens que uma entrada pode declarar.
#
# `dono_projeto` NÃO está aqui de propósito: é um rótulo interno do projeto do
# app, que se refere a uma pessoa específica. No catálogo público ele vira
# `verificado`. Ver gen_catalogo_publico.py no repositório do app.
ORIGENS = {
    "curadoria",     # da curadoria original, sem registro individual
    "conhecimento",  # app conhecido, categoria reconhecida
    "pesquisa_web",  # pesquisado e confirmado em fonte pública
    "verificado",    # alguém abriu o app e viu o que ele faz
}


def carregar(caminho: Path, o_que: str):
    if not caminho.is_file():
        print(f"ERRO: não achei {o_que} em {caminho}")
        raise SystemExit(1)
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERRO: {o_que} não é um JSON válido: {e}")
        raise SystemExit(1)


def main() -> int:
    regras = carregar(RULES, "category_rules.json")
    catalogo_cats = carregar(CATEGORIES, "categories.json")

    validas = {c["key"] for c in catalogo_cats["categories"]}
    por_categoria = regras.get("byCategory", {})
    procedencia = regras.get("provenance", {})

    problemas: list[str] = []
    avisos: list[str] = []

    # ---- 1. categoria conhecida ----
    for cat in sorted(por_categoria):
        if cat not in validas:
            problemas.append(
                f"categoria '{cat}' não existe em categories.json. "
                f"As válidas estão lá; se faltar uma, ela precisa nascer no app primeiro."
            )

    # ---- 2, 3, 4. pacotes ----
    onde: dict[str, str] = {}
    total = 0
    for cat in sorted(por_categoria):
        vistos_aqui: set[str] = set()
        anterior = None
        for pkg in por_categoria[cat]:
            pkg = pkg.strip()
            total += 1

            if pkg in vistos_aqui:
                problemas.append(f"'{pkg}' repetido dentro de '{cat}'")
            vistos_aqui.add(pkg)

            if pkg in onde and onde[pkg] != cat:
                problemas.append(
                    f"'{pkg}' está em duas categorias: '{onde[pkg]}' e '{cat}'"
                )
            onde[pkg] = cat

            if not PACOTE.match(pkg):
                problemas.append(
                    f"'{pkg}' (em '{cat}') não parece um nome de pacote Android. "
                    f"Nome truncado no terminal é a causa mais comum."
                )

            # ---- 8. ordenação ----
            if anterior is not None and pkg < anterior:
                avisos.append(
                    f"'{cat}' fora de ordem: '{pkg}' vem depois de '{anterior}'. "
                    f"A ordem alfabética é o que mantém o git diff legível."
                )
            anterior = pkg

    # ---- 5, 6. procedência ----
    for pkg, meta in sorted(procedencia.items()):
        if pkg not in onde:
            problemas.append(
                f"'{pkg}' tem procedência mas não está em nenhuma categoria"
            )
        if not isinstance(meta, dict):
            problemas.append(f"procedência de '{pkg}' não é um objeto")
            continue
        origem = meta.get("origem")
        if origem not in ORIGENS:
            problemas.append(
                f"'{pkg}' tem origem '{origem}'; as válidas são {sorted(ORIGENS)}"
            )
        conf = meta.get("confianca")
        if not isinstance(conf, int) or not 0 <= conf <= 100:
            problemas.append(f"'{pkg}' tem confiança inválida: {conf!r}")

    # ---- 7. contadores do topo ----
    if regras.get("packageCount") not in (None, total):
        problemas.append(
            f"packageCount diz {regras['packageCount']} mas há {total} pacotes"
        )
    n_cats = len([c for c in por_categoria if por_categoria[c]])
    if regras.get("categoryCount") not in (None, n_cats):
        problemas.append(
            f"categoryCount diz {regras['categoryCount']} mas há {n_cats} categorias"
        )

    # ---- 9. cruzamento opcional com um aparelho ----
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.is_absolute():
            csv_path = RAIZ / sys.argv[1]
        if not csv_path.is_file():
            problemas.append(f"não achei a exportação {csv_path}")
        else:
            with io.open(csv_path, encoding="utf-8") as f:
                no_aparelho = {
                    (linha.get("pkg") or linha.get("packageName") or "").strip()
                    for linha in csv.DictReader(f)
                }
            no_aparelho.discard("")
            print(f"\nconferindo contra {csv_path.name} ({len(no_aparelho)} apps)")
            cobertos = len(no_aparelho & set(onde))
            if no_aparelho:
                print(
                    f"  desses, o catálogo cobre: {cobertos} "
                    f"({100 * cobertos // len(no_aparelho)}%)"
                )

    # ---- relatório ----
    print(
        f"\ncategorias: {n_cats}    pacotes: {total}    "
        f"com procedência: {len(procedencia)}"
    )

    for a in avisos:
        print(f"  aviso: {a}")

    if problemas:
        print(f"\nFALHOU: {len(problemas)} problema(s)")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print("\nOK: o catálogo está consistente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
