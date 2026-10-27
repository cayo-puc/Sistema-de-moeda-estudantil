#!/usr/bin/env python3
"""
Gera o diagrama vetorial `modelo-er.svg` (Modelo Entidade-Relacionamento em notação
Pé de Galinha / Crow's Foot) e o PDF documentado da Sprint 2 (`modelo-er-sprint2.pdf`).
"""

import os
import subprocess
import tempfile
from html import escape


ENTITIES = [
    # Coluna 1: Estrutura Acadêmica
    {
        "id": "instituicoes",
        "name": "instituicoes_ensino",
        "x": 40,
        "y": 50,
        "w": 270,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("UK", "nome", "VARCHAR(150)"),
            ("", "sigla", "VARCHAR(20)"),
            ("", "criado_em", "TIMESTAMP"),
        ],
    },
    {
        "id": "cursos",
        "name": "cursos",
        "x": 40,
        "y": 240,
        "w": 270,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("FK", "instituicao_id", "VARCHAR(36)"),
            ("", "nome", "VARCHAR(150)"),
        ],
    },
    {
        "id": "departamentos",
        "name": "departamentos",
        "x": 40,
        "y": 400,
        "w": 270,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("FK", "instituicao_id", "VARCHAR(36)"),
            ("", "nome", "VARCHAR(150)"),
        ],
    },
    # Coluna 2: Hierarquia de Usuários (Joined Table Inheritance)
    {
        "id": "usuarios",
        "name": "usuarios",
        "x": 400,
        "y": 40,
        "w": 290,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("", "nome", "VARCHAR(150)"),
            ("UK", "email", "VARCHAR(150)"),
            ("", "hash_senha", "VARCHAR(255)"),
            ("", "tipo_usuario", "VARCHAR(20)"),
            ("", "criado_em", "TIMESTAMP"),
            ("", "atualizado_em", "TIMESTAMP"),
        ],
    },
    {
        "id": "alunos",
        "name": "alunos",
        "x": 400,
        "y": 270,
        "w": 290,
        "fields": [
            ("PK,FK", "usuario_id", "VARCHAR(36)"),
            ("UK", "cpf", "VARCHAR(14)"),
            ("", "rg", "VARCHAR(20)"),
            ("", "endereco", "VARCHAR(255)"),
            ("FK", "instituicao_id", "VARCHAR(36)"),
            ("FK", "curso_id", "VARCHAR(36)"),
        ],
    },
    {
        "id": "professores",
        "name": "professores",
        "x": 400,
        "y": 485,
        "w": 290,
        "fields": [
            ("PK,FK", "usuario_id", "VARCHAR(36)"),
            ("UK", "cpf", "VARCHAR(14)"),
            ("FK", "instituicao_id", "VARCHAR(36)"),
            ("FK", "departamento_id", "VARCHAR(36)"),
        ],
    },
    {
        "id": "empresas",
        "name": "empresas_parceiras",
        "x": 400,
        "y": 665,
        "w": 290,
        "fields": [
            ("PK,FK", "usuario_id", "VARCHAR(36)"),
            ("", "nome_legal", "VARCHAR(180)"),
            ("UK", "identificador", "VARCHAR(20)"),
            ("", "descricao", "TEXT"),
        ],
    },
    # Coluna 3: Conta de Moedas, Vantagens e Resgates
    {
        "id": "contas",
        "name": "contas_moedas",
        "x": 790,
        "y": 50,
        "w": 300,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("FK,UK", "usuario_id", "VARCHAR(36)"),
            ("CHK", "saldo_atual", "INTEGER >= 0"),
            ("", "atualizado_em", "TIMESTAMP"),
        ],
    },
    {
        "id": "movimentacoes",
        "name": "movimentacoes",
        "x": 790,
        "y": 235,
        "w": 300,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("", "tipo", "VARCHAR(30)"),
            ("CHK", "quantidade", "INTEGER > 0"),
            ("", "instante", "TIMESTAMP"),
        ],
    },
    {
        "id": "resgates",
        "name": "resgates",
        "x": 790,
        "y": 430,
        "w": 300,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("FK", "aluno_id", "VARCHAR(36)"),
            ("FK", "vantagem_id", "VARCHAR(36)"),
            ("FK,UK", "debito_movimentacao_id", "VARCHAR(36)"),
            ("", "instante", "TIMESTAMP"),
            ("", "custo_aplicado", "INTEGER"),
            ("", "status", "VARCHAR(20)"),
        ],
    },
    {
        "id": "vantagens",
        "name": "vantagens",
        "x": 790,
        "y": 660,
        "w": 300,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("FK", "empresa_id", "VARCHAR(36)"),
            ("", "titulo", "VARCHAR(150)"),
            ("", "descricao", "TEXT"),
            ("", "fotografia_uri", "VARCHAR(500)"),
            ("CHK", "custo_moedas", "INTEGER > 0"),
            ("", "dados_oferta", "VARCHAR(255)"),
            ("", "ativa", "BOOLEAN"),
        ],
    },
    # Coluna 4: Especializações de Movimentação e Cupons
    {
        "id": "transferencias",
        "name": "transferencias",
        "x": 1190,
        "y": 40,
        "w": 310,
        "fields": [
            ("PK,FK", "movimentacao_id", "VARCHAR(36)"),
            ("FK", "conta_origem_id", "VARCHAR(36)"),
            ("FK", "conta_destino_id", "VARCHAR(36)"),
            ("", "motivo", "TEXT NOT NULL"),
        ],
    },
    {
        "id": "creditos",
        "name": "creditos_semestrais",
        "x": 1190,
        "y": 220,
        "w": 310,
        "fields": [
            ("PK,FK", "movimentacao_id", "VARCHAR(36)"),
            ("FK", "conta_destino_id", "VARCHAR(36)"),
            ("FK", "professor_id", "VARCHAR(36)"),
            ("UK", "periodo", "VARCHAR(10)"),
            ("", "quantidade_creditada", "INT = 1000"),
        ],
    },
    {
        "id": "debitos",
        "name": "debitos_resgate",
        "x": 1190,
        "y": 420,
        "w": 310,
        "fields": [
            ("PK,FK", "movimentacao_id", "VARCHAR(36)"),
            ("FK", "conta_origem_id", "VARCHAR(36)"),
        ],
    },
    {
        "id": "cupons",
        "name": "cupons",
        "x": 1190,
        "y": 580,
        "w": 310,
        "fields": [
            ("PK", "id", "VARCHAR(36)"),
            ("FK,UK", "resgate_id", "VARCHAR(36)"),
            ("UK", "codigo_conferencia", "VARCHAR(40)"),
            ("", "instante_geracao", "TIMESTAMP"),
        ],
    },
]


def calc_height(entity: dict) -> int:
    return 32 + len(entity["fields"]) * 20 + 8


def build_mer_svg() -> str:
    width, height = 1540, 895
    ent_map = {}
    for e in ENTITIES:
        eh = calc_height(e)
        ent_map[e["id"]] = {**e, "h": eh}

    # Linhas de relacionamento ortogonais com rótulos de cardinalidade
    rels = [
        # (from_id, to_id, label, card_from, card_to, path_d)
        ("instituicoes", "cursos", "oferece", "1", "0..N", "M 175 186 L 175 240"),
        ("instituicoes", "departamentos", "possui", "1", "0..N", "M 25 110 L 18 110 L 18 450 L 40 450"),
        ("instituicoes", "alunos", "vincula", "1", "0..N", "M 310 120 L 350 120 L 350 320 L 400 320"),
        ("cursos", "alunos", "cursa", "1", "0..N", "M 310 295 L 400 295"),
        ("departamentos", "professores", "lota", "1", "0..N", "M 310 465 L 355 465 L 355 545 L 400 545"),
        ("usuarios", "alunos", "JOINED", "1", "0..1", "M 545 220 L 545 270"),
        ("usuarios", "professores", "JOINED", "1", "0..1", "M 382 120 L 372 120 L 372 515 L 400 515"),
        ("usuarios", "empresas", "JOINED", "1", "0..1", "M 382 145 L 364 145 L 364 715 L 400 715"),
        ("usuarios", "contas", "titular", "1", "0..1", "M 690 105 L 790 105"),
        ("contas", "transferencias", "origem/destino", "1", "0..N", "M 1090 95 L 1190 95"),
        ("contas", "creditos", "credita", "1", "0..N", "M 1090 135 L 1140 135 L 1140 265 L 1190 265"),
        ("movimentacoes", "transferencias", "especializa", "1", "0..1", "M 1090 265 L 1155 265 L 1155 135 L 1190 135"),
        ("movimentacoes", "creditos", "especializa", "1", "0..1", "M 1090 295 L 1190 295"),
        ("movimentacoes", "debitos", "especializa", "1", "0..1", "M 1090 325 L 1155 325 L 1155 465 L 1190 465"),
        ("alunos", "resgates", "realiza", "1", "0..N", "M 690 365 L 745 365 L 745 495 L 790 495"),
        ("empresas", "vantagens", "oferece", "1", "0..N", "M 690 735 L 790 735"),
        ("vantagens", "resgates", "selecionada", "1", "0..N", "M 940 660 L 940 610"),
        ("debitos", "resgates", "gera débito", "1", "1", "M 1190 490 L 1090 490"),
        ("resgates", "cupons", "emite cupom", "1", "1", "M 1090 565 L 1145 565 L 1145 635 L 1190 635"),
    ]

    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}">',
        f'  <rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>',
        '  <defs>',
        '    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 8 5 L 0 9 z" fill="#475569"/>',
        '    </marker>',
        '  </defs>',
    ]

    # Desenhar linhas de relacionamento
    for _, _, label, c_from, c_to, path_d in rels:
        svg_parts.append(
            f'  <path d="{path_d}" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>'
        )
        # Ponto médio aproximado para o texto
        coords = [float(v) for v in path_d.replace("M", "").replace("L", "").split()]
        if len(coords) >= 4:
            mx = (coords[0] + coords[-2]) / 2.0
            my = (coords[1] + coords[-1]) / 2.0
            svg_parts.append(
                f'  <rect x="{mx - 42:.1f}" y="{my - 9:.1f}" width="84" height="15" rx="3" fill="#FFFFFF" opacity="0.9"/>'
            )
            svg_parts.append(
                f'  <text x="{mx:.1f}" y="{my + 2:.1f}" font-family="sans-serif" font-size="9.5" font-weight="600" fill="#334155" text-anchor="middle">{escape(label)} ({c_from}:{c_to})</text>'
            )

    # Desenhar tabelas (Entidades Relacionais)
    for e in ENTITIES:
        x, y, w = e["x"], e["y"], e["w"]
        h = calc_height(e)
        svg_parts.append(
            f'  <g id="table-{e["id"]}">'
            f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" ry="5" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.4"/>'
            f'    <rect x="{x}" y="{y}" width="{w}" height="28" rx="5" ry="5" fill="#1E3A8A"/>'
            f'    <rect x="{x}" y="{y + 20}" width="{w}" height="8" fill="#1E3A8A"/>'
            f'    <text x="{x + 12}" y="{y + 19}" font-family="sans-serif" font-size="12.5" font-weight="700" fill="#FFFFFF">{escape(e["name"])}</text>'
        )

        fy = y + 46
        for badge, fname, ftype in e["fields"]:
            if badge:
                badge_color = "#DBEAFE" if "PK" in badge else ("#FEF3C7" if "FK" in badge else "#F1F5F9")
                text_color = "#1E3A8A" if "PK" in badge else ("#92400E" if "FK" in badge else "#475569")
                svg_parts.append(
                    f'    <rect x="{x + 8}" y="{fy - 11}" width="38" height="14" rx="3" fill="{badge_color}"/>'
                    f'    <text x="{x + 27}" y="{fy - 1}" font-family="sans-serif" font-size="8.5" font-weight="700" fill="{text_color}" text-anchor="middle">{escape(badge)}</text>'
                )
            weight = "700" if "PK" in badge else "400"
            svg_parts.append(
                f'    <text x="{x + 52}" y="{fy}" font-family="sans-serif" font-size="11" font-weight="{weight}" fill="#0F172A">{escape(fname)}</text>'
                f'    <text x="{x + w - 10}" y="{fy}" font-family="monospace" font-size="10" fill="#475569" text-anchor="end">{escape(ftype)}</text>'
            )
            fy += 20

        svg_parts.append("  </g>")

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def build_sprint2_pdf(base_dir: str, mer_svg_content: str):
    # Envolve o MER em uma página A4 Paisagem padronizada PUC Minas
    inner = mer_svg_content.split(">", 2)[2].rsplit("</svg>", 1)[0]
    page_w, page_h = 1191, 842
    margin_x = 42
    header_top = 34
    header_h = 96
    footer_h = 36
    content_top = header_top + header_h + 12
    avail_w = page_w - 2 * margin_x
    avail_h = page_h - footer_h - 10 - content_top

    orig_w, orig_h = 1540.0, 895.0
    pad = 12
    scale = min((avail_w - 2 * pad) / orig_w, (avail_h - 2 * pad) / orig_h)
    tx = margin_x + pad + ((avail_w - 2 * pad) - orig_w * scale) / 2.0
    ty = content_top + pad + ((avail_h - 2 * pad) - orig_h * scale) / 2.0

    page_svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{page_w}pt" height="{page_h}pt" viewBox="0 0 {page_w} {page_h}">
  <rect x="0" y="0" width="{page_w}" height="{page_h}" fill="#FFFFFF"/>

  <rect x="{margin_x}" y="{header_top}" width="{avail_w}" height="{header_h}" rx="6" ry="6"
        fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1"/>
  <rect x="{margin_x}" y="{header_top}" width="6" height="{header_h}" rx="3" ry="3" fill="#1E3A8A"/>

  <text x="{margin_x + 20}" y="{header_top + 22}" font-family="sans-serif" font-size="10"
        font-weight="700" fill="#1E3A8A" letter-spacing="0.4">
    PUC MINAS • ENGENHARIA DE SOFTWARE • PROJETO DE SOFTWARE (LAB 03)
  </text>
  <text x="{page_w - margin_x - 16}" y="{header_top + 22}" font-family="sans-serif" font-size="10"
        font-weight="700" fill="#475569" text-anchor="end">
    Sprint 02 (Lab03S02) — Modelo ER e Persistência
  </text>

  <line x1="{margin_x + 20}" y1="{header_top + 30}" x2="{page_w - margin_x - 16}" y2="{header_top + 30}"
        stroke="#E2E8F0" stroke-width="1"/>

  <text x="{margin_x + 20}" y="{header_top + 52}" font-family="sans-serif" font-size="18"
        font-weight="700" fill="#0F172A">
    Modelo Entidade-Relacionamento (MER) — Sistema de Moeda Estudantil
  </text>
  <text x="{margin_x + 20}" y="{header_top + 71}" font-family="sans-serif" font-size="11.5"
        font-weight="600" fill="#334155">
    Mapeamento Relacional com Joined Table Inheritance (usuarios ⋈ alunos / professores / empresas_parceiras)
  </text>
  <text x="{margin_x + 20}" y="{header_top + 88}" font-family="sans-serif" font-size="10"
        fill="#64748B">
    Implementado em database/schema.sql e acessado via ORM + Padrão DAO (GenericDAO, AlunoDAO, EmpresaParceiraDAO, CatalogoDAO).
  </text>

  <rect x="{margin_x}" y="{content_top}" width="{avail_w}" height="{avail_h}" rx="6" ry="6"
        fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1"/>

  <g transform="translate({tx:.2f}, {ty:.2f}) scale({scale:.5f})">
    {inner}
  </g>

  <line x1="{margin_x}" y1="{page_h - footer_h}" x2="{page_w - margin_x}" y2="{page_h - footer_h}"
        stroke="#E2E8F0" stroke-width="1"/>
  <text x="{margin_x}" y="{page_h - 14}" font-family="sans-serif" font-size="9.5" fill="#64748B">
    Sistema de Moeda Estudantil — Entrega Sprint 02 (Lab03S02: Modelo ER, ORM/DAO e CRUDs) • Profa. Milena Menezes Adão
  </text>
  <text x="{page_w - margin_x}" y="{page_h - 14}" font-family="sans-serif" font-size="9.5"
        font-weight="700" fill="#334155" text-anchor="end">
    Página 1 de 1
  </text>
</svg>
"""
    out_pdf = os.path.join(base_dir, "modelo-er-sprint2.pdf")
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "mer_page.svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(page_svg)
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", out_pdf, p], check=True)
    return out_pdf


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mer_svg = build_mer_svg()
    svg_path = os.path.join(base_dir, "modelo-er.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(mer_svg)
    print(f"[OK] Gerado: {svg_path}")

    pdf_path = build_sprint2_pdf(base_dir, mer_svg)
    print(f"[OK] Gerado: {pdf_path}")


if __name__ == "__main__":
    main()

