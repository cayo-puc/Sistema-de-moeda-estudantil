#!/usr/bin/env python3
"""
Servidor Web e API RESTful MVC — Sistema de Moeda Estudantil (Lab03S02).
Integra a camada View (`src/views`), os Controladores MVC (`AlunoController`,
`EmpresaParceiraController`) e a camada de Persistência (`AlunoDAO`, `EmpresaParceiraDAO`,
`CatalogoDAO`) sobre SQLite3.

Execução:
    python3 app.py
Acesse no navegador:
    http://localhost:8000
"""

import json
import mimetypes
import os
import re
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from src.config.database import DatabaseManager
from src.controllers.aluno_controller import AlunoController
from src.controllers.empresa_controller import EmpresaParceiraController
from src.dao.catalogo_dao import CatalogoDAO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_DIR = os.path.join(BASE_DIR, "src", "views")


class MoedaEstudantilWSGIApp:
    """Aplicação Web MVC compatível com WSGI (funciona nativamente ou via Gunicorn/Flask)."""

    def __init__(self, db_path: str | None = None):
        self.db_manager = DatabaseManager(db_path) if db_path else DatabaseManager()
        self.db_manager.init_database()
        self.aluno_controller = AlunoController(self.db_manager)
        self.empresa_controller = EmpresaParceiraController(self.db_manager)
        self.catalogo_dao = CatalogoDAO(self.db_manager)

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        query_params = parse_qs(environ.get("QUERY_STRING", ""))

        try:
            # 1. Rotas da View (Front-end MVC e Arquivos Estáticos)
            if method == "GET" and path in ("/", "/index.html"):
                return self._serve_file(os.path.join(VIEWS_DIR, "index.html"), "text/html; charset=utf-8", start_response)

            if method == "GET" and path.startswith("/static/"):
                rel_name = path.replace("/static/", "", 1)
                safe_path = os.path.normpath(os.path.join(VIEWS_DIR, rel_name))
                if safe_path.startswith(VIEWS_DIR) and os.path.isfile(safe_path):
                    ctype, _ = mimetypes.guess_type(safe_path)
                    return self._serve_file(safe_path, f"{ctype or 'text/plain'}; charset=utf-8", start_response)

            if method == "GET" and path == "/modelo-er.svg":
                svg_path = os.path.join(BASE_DIR, "modelo-er.svg")
                if os.path.isfile(svg_path):
                    return self._serve_file(svg_path, "image/svg+xml; charset=utf-8", start_response)

            # 2. Rotas de Catálogo Acadêmico Pré-Cadastrado
            if method == "GET" and path == "/api/instituicoes":
                insts = [i.to_dict() for i in self.catalogo_dao.listar_instituicoes()]
                return self._json_response(200, {"sucesso": True, "dados": insts}, start_response)

            if method == "GET" and path == "/api/cursos":
                inst_id = query_params.get("instituicaoId", [None])[0]
                cursos = [c.to_dict() for c in self.catalogo_dao.listar_cursos(inst_id)]
                return self._json_response(200, {"sucesso": True, "dados": cursos}, start_response)

            # 3. Rotas REST CRUD de Aluno (`/api/alunos` e `/api/alunos/<id>`)
            if path == "/api/alunos":
                if method == "GET":
                    status, res = self.aluno_controller.listar_todos()
                    return self._json_response(status, res, start_response)
                if method == "POST":
                    payload = self._read_json_body(environ)
                    status, res = self.aluno_controller.criar(payload)
                    return self._json_response(status, res, start_response)

            match_aluno = re.match(r"^/api/alunos/([^/]+)$", path)
            if match_aluno:
                aluno_id = match_aluno.group(1)
                if method == "GET":
                    status, res = self.aluno_controller.buscar_por_id(aluno_id)
                    return self._json_response(status, res, start_response)
                if method == "PUT":
                    payload = self._read_json_body(environ)
                    status, res = self.aluno_controller.atualizar(aluno_id, payload)
                    return self._json_response(status, res, start_response)
                if method == "DELETE":
                    status, res = self.aluno_controller.remover(aluno_id)
                    return self._json_response(status, res, start_response)

            # 4. Rotas REST CRUD de Empresa Parceira (`/api/empresas` e `/api/empresas/<id>`)
            if path == "/api/empresas":
                if method == "GET":
                    status, res = self.empresa_controller.listar_todos()
                    return self._json_response(status, res, start_response)
                if method == "POST":
                    payload = self._read_json_body(environ)
                    status, res = self.empresa_controller.criar(payload)
                    return self._json_response(status, res, start_response)

            match_empresa = re.match(r"^/api/empresas/([^/]+)$", path)
            if match_empresa:
                empresa_id = match_empresa.group(1)
                if method == "GET":
                    status, res = self.empresa_controller.buscar_por_id(empresa_id)
                    return self._json_response(status, res, start_response)
                if method == "PUT":
                    payload = self._read_json_body(environ)
                    status, res = self.empresa_controller.atualizar(empresa_id, payload)
                    return self._json_response(status, res, start_response)
                if method == "DELETE":
                    status, res = self.empresa_controller.remover(empresa_id)
                    return self._json_response(status, res, start_response)

            return self._json_response(404, {"sucesso": False, "erro": f"Rota não encontrada: {method} {path}"}, start_response)

        except json.JSONDecodeError:
            return self._json_response(400, {"sucesso": False, "erro": "Corpo da requisição não é um JSON válido."}, start_response)
        except Exception as exc:
            return self._json_response(500, {"sucesso": False, "erro": f"Erro interno no servidor: {exc}"}, start_response)

    def _read_json_body(self, environ) -> dict:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = environ["wsgi.input"].read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _json_response(self, status_code: int, data: dict, start_response):
        status_map = {
            200: "200 OK",
            201: "201 Created",
            400: "400 Bad Request",
            404: "404 Not Found",
            409: "409 Conflict",
            500: "500 Internal Server Error",
        }
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
        ]
        start_response(status_map.get(status_code, f"{status_code} OK"), headers)
        return [body]

    def _serve_file(self, filepath: str, content_type: str, start_response):
        with open(filepath, "rb") as f:
            content = f.read()
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(content))),
        ]
        start_response("200 OK", headers)
        return [content]


def main():
    port = int(os.environ.get("PORT", "8000"))
    app = MoedaEstudantilWSGIApp()
    print("=" * 72)
    print(" Sistema de Moeda Estudantil — Lab03S02 (MVC + ORM + Padrão DAO)")
    print(f" Banco de Dados SQLite inicializado em: {app.db_manager.db_path}")
    print(f" Servidor Web / API REST disponível em: http://localhost:{port}")
    print("=" * 72)
    with make_server("0.0.0.0", port, app) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()

