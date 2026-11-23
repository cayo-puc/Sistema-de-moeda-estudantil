#!/usr/bin/env python3
"""
Gera os diagramas vetoriais SVG da Release 2 (Lab04S01 e Lab04S02):
- diagrama-sequencia.svg (SD-01 Autenticação, SD-02 Envio de Moedas, SD-03 Resgate + Cupom)
- diagrama-visao-geral-interacao.svg (Interaction Overview Diagram UML)
- diagrama-implantacao.svg (Deployment Diagram UML: Vercel + Render + SQLite + SMTP)
"""

from html import escape
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _svg_header(width: int, height: int, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#1e3a8a"/>
    </marker>
    <marker id="arrow-dashed" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <rect x="0" y="0" width="{width}" height="48" fill="#0f172a"/>
  <text x="24" y="30" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" fill="#ffffff">{escape(title)}</text>
'''


def gerar_diagrama_sequencia():
    w, h = 1120, 760
    parts = [_svg_header(w, h, "Diagramas de Sequência UML — Sistema de Moeda Estudantil (Lab04S01)")]

    # Lifelines
    lifelines = [
        (110, "Usuário\n(Aluno/Prof/Empresa)"),
        (310, "View\n(HTML/JS)"),
        (530, "Controllers\n(Auth/Merit/Vant)"),
        (760, "DAOs & Services\n(DAO / Notif)"),
        (990, "SQLite3 DB\n& SMTP"),
    ]
    for x, label in lifelines:
        lines = label.split("\n")
        parts.append(f'<rect x="{x-85}" y="68" width="170" height="46" rx="8" fill="#eff6ff" stroke="#1e3a8a" stroke-width="1.8"/>')
        parts.append(f'<text x="{x}" y="88" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="700" fill="#0f172a">{escape(lines[0])}</text>')
        parts.append(f'<text x="{x}" y="104" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#475569">{escape(lines[1])}</text>')
        parts.append(f'<line x1="{x}" y1="114" x2="{x}" y2="730" stroke="#94a3b8" stroke-dasharray="6,5" stroke-width="1.5"/>')

    def msg(y, x1, x2, text, dashed=False):
        stroke = "#475569" if dashed else "#1e3a8a"
        dash = ' stroke-dasharray="5,4"' if dashed else ""
        marker = "url(#arrow-dashed)" if dashed else "url(#arrow)"
        tx = (x1 + x2) / 2
        parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{stroke}" stroke-width="1.8"{dash} marker-end="{marker}"/>')
        parts.append(f'<rect x="{tx-120}" y="{y-17}" width="240" height="15" fill="#f8fafc" opacity="0.9"/>')
        parts.append(f'<text x="{tx}" y="{y-5}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="600" fill="#0f172a">{escape(text)}</text>')

    def group_box(y1, y2, title):
        parts.append(f'<rect x="25" y="{y1}" width="1070" height="{y2-y1}" rx="6" fill="none" stroke="#334155" stroke-width="1.5"/>')
        parts.append(f'<rect x="25" y="{y1}" width="380" height="22" rx="4" fill="#1e3a8a"/>')
        parts.append(f'<text x="35" y="{y1+15}" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="700" fill="#ffffff">{escape(title)}</text>')

    # SD-01
    group_box(130, 295, "SD-01: Autenticação e Autorização (HU-05)")
    msg(170, 110, 310, "1. Informa e-mail e senha")
    msg(200, 310, 530, "2. POST /api/auth/login")
    msg(230, 530, 760, "3. AuthService.autenticar()")
    msg(255, 760, 990, "4. SELECT usuarios + PBKDF2")
    msg(280, 530, 110, "5. 200 OK {token HMAC, usuario}", dashed=True)

    # SD-02
    group_box(315, 510, "SD-02: Envio de Moedas e Notificação (HU-07 / HU-08)")
    msg(355, 110, 310, "1. Seleciona aluno, qtd e motivo")
    msg(385, 310, 530, "2. POST /api/merito/transferir (Bearer)")
    msg(415, 530, 760, "3. MovimentacaoDAO.transferir_moedas()")
    msg(445, 760, 990, "4. TX Atômica: debita Prof / credita Aluno")
    msg(475, 760, 990, "5. NotificacaoService -> Email + DB")
    msg(500, 530, 110, "6. 201 Created + saldo atualizado", dashed=True)

    # SD-03
    group_box(530, 725, "SD-03: Resgate de Vantagem e Emissão de Cupom (HU-10 / HU-11)")
    msg(570, 110, 310, "1. Seleciona vantagem e confirma")
    msg(600, 310, 530, "2. POST /api/vantagens/{id}/resgatar")
    msg(630, 530, 760, "3. ResgateDAO.resgatar_vantagem()")
    msg(660, 760, 990, "4. TX Atômica: debita + resgate + cupom")
    msg(690, 760, 990, "5. Envia 2 e-mails (Aluno + Empresa)")
    msg(715, 530, 110, "6. 201 Created {codigoConferencia}", dashed=True)

    parts.append("</svg>")
    with open(os.path.join(BASE_DIR, "diagrama-sequencia.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def gerar_diagrama_visao_geral_interacao():
    w, h = 1040, 560
    parts = [_svg_header(w, h, "Diagrama de Visão Geral de Interação UML (Lab04S01)")]

    def box(x, y, bw, bh, title, subtitle="", fill="#ffffff", stroke="#1e3a8a"):
        parts.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        parts.append(f'<text x="{x+bw/2}" y="{y+22}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="700" fill="#0f172a">{escape(title)}</text>')
        if subtitle:
            parts.append(f'<text x="{x+bw/2}" y="{y+40}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#475569">{escape(subtitle)}</text>')

    def arrow(x1, y1, x2, y2, label=""):
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1e3a8a" stroke-width="2" marker-end="url(#arrow)"/>')
        if label:
            parts.append(f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2 - 6}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="700" fill="#1e3a8a">{escape(label)}</text>')

    # Start node
    parts.append('<circle cx="520" cy="76" r="12" fill="#0f172a"/>')
    arrow(520, 88, 520, 118)

    box(350, 118, 340, 56, "Ref: SD-01 Autenticação (HU-05)", "POST /api/auth/login → Token HMAC-SHA256", "#eff6ff")
    arrow(520, 174, 520, 210)

    # Decision diamond
    parts.append('<polygon points="520,210 610,248 520,286 430,248" fill="#fef9c3" stroke="#854d0e" stroke-width="2"/>')
    parts.append('<text x="520" y="252" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" font-weight="700" fill="#854d0e">Perfil?</text>')

    # Branches
    arrow(430, 248, 175, 320, "PROFESSOR")
    arrow(520, 286, 520, 320, "ALUNO")
    arrow(610, 248, 865, 320, "EMPRESA")

    # Professor flow
    box(40, 320, 270, 56, "Ref: SD-02 Distribuir Moedas", "Debita Prof + Credita Aluno + E-mail", "#ffffff")
    box(40, 392, 270, 56, "Crédito Semestral + Extrato", "+1.000 moedas/semestre (HU-06 / HU-09)", "#ffffff")

    # Aluno flow
    box(385, 320, 270, 56, "Ref: SD-03 Resgatar Vantagem", "Debita saldo + Gera Cupom + 2 E-mails", "#ffffff")
    box(385, 392, 270, 56, "Extrato & Meus Cupons", "Recebimentos e códigos (HU-09 / HU-11)", "#ffffff")

    # Empresa flow
    box(730, 320, 270, 56, "Gerenciar Vantagens (HU-04)", "CRUD com foto, descrição e custo", "#ffffff")
    box(730, 392, 270, 56, "Conferência de Cupons (HU-11)", "Validação presencial via código", "#ffffff")

    # Merge to end
    arrow(175, 448, 505, 515)
    arrow(520, 448, 520, 503)
    arrow(865, 448, 535, 515)

    parts.append('<circle cx="520" cy="520" r="13" fill="none" stroke="#0f172a" stroke-width="2"/>')
    parts.append('<circle cx="520" cy="520" r="8" fill="#0f172a"/>')
    parts.append("</svg>")

    with open(os.path.join(BASE_DIR, "diagrama-visao-geral-interacao.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def gerar_diagrama_implantacao():
    w, h = 1080, 460
    parts = [_svg_header(w, h, "Diagrama de Implantação UML (Deployment Diagram — Lab04S02)")]

    def node_box(x, y, nw, nh, stereotype, title, items, fill="#ffffff", header_fill="#e2e8f0"):
        # 3D-like UML Node effect
        parts.append(f'<polygon points="{x},{y} {x+12},{y-10} {x+nw+12},{y-10} {x+nw},{y}" fill="{header_fill}" stroke="#334155" stroke-width="1.5"/>')
        parts.append(f'<polygon points="{x+nw},{y} {x+nw+12},{y-10} {x+nw+12},{y+nh-10} {x+nw},{y+nh}" fill="{header_fill}" stroke="#334155" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" fill="{fill}" stroke="#334155" stroke-width="1.8"/>')
        parts.append(f'<text x="{x+nw/2}" y="{y+22}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#475569">&lt;&lt;{escape(stereotype)}&gt;&gt;</text>')
        parts.append(f'<text x="{x+nw/2}" y="{y+40}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{escape(title)}</text>')
        iy = y + 62
        for item in items:
            parts.append(f'<rect x="{x+14}" y="{iy}" width="{nw-28}" height="34" rx="6" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.2"/>')
            parts.append(f'<text x="{x+nw/2}" y="{iy+21}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11" font-weight="600" fill="#1e293b">{escape(item)}</text>')
            iy += 44

    node_box(30, 95, 220, 175, "device", "Dispositivo do Usuário", ["Navegador Web", "HTML5 / CSS3 / Fetch API"], "#ffffff")
    node_box(310, 95, 230, 175, "cloud: Vercel", "Vercel Edge Hosting", ["src/views/ (Estático)", "vercel.json (/api/* rewrite)"], "#eff6ff", "#dbeafe")
    node_box(600, 80, 250, 260, "cloud: Render", "Render Web Service", ["Gunicorn (app:application)", "API REST MVC (Python)", "DAOs & AuthService", "SQLite3 (moeda_estudantil.db)"], "#f0fdf4", "#dcfce7")
    node_box(895, 130, 160, 150, "cloud", "Serviço SMTP", ["Envio de E-mails", "Cupons & Mérito"], "#fefce8", "#fef9c3")

    # Connections
    parts.append('<line x1="262" y1="175" x2="310" y2="175" stroke="#1e3a8a" stroke-width="2" marker-end="url(#arrow)"/>')
    parts.append('<text x="286" y="165" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10" font-weight="700" fill="#1e3a8a">HTTPS</text>')

    parts.append('<line x1="552" y1="175" x2="600" y2="175" stroke="#1e3a8a" stroke-width="2" marker-end="url(#arrow)"/>')
    parts.append('<text x="576" y="165" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10" font-weight="700" fill="#1e3a8a">REST</text>')

    parts.append('<line x1="862" y1="205" x2="895" y2="205" stroke="#1e3a8a" stroke-width="2" marker-end="url(#arrow)"/>')
    parts.append('<text x="878" y="195" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10" font-weight="700" fill="#1e3a8a">TLS</text>')

    parts.append('<text x="540" y="420" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#475569">Configuração declarativa: vercel.json (Front-end Edge) + render.yaml (Back-end WSGI Gunicorn + SQLite)</text>')
    parts.append("</svg>")

    with open(os.path.join(BASE_DIR, "diagrama-implantacao.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    gerar_diagrama_sequencia()
    gerar_diagrama_visao_geral_interacao()
    gerar_diagrama_implantacao()
    print("SVGs da Release 2 (Lab04S01 / Lab04S02) gerados com sucesso.")
