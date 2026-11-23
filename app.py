#!/usr/bin/env python3
"""
Servidor Web e API RESTful MVC — Sistema de Moeda Estudantil (Lab03S02 -> Lab04S02).
Integra a camada View (`src/views`), os Controladores MVC (`AlunoController`,
`EmpresaParceiraController`, `AuthController`, `MeritoController`, `VantagemController`),
os Serviços (`AuthService`, `NotificacaoService`) e a camada de Persistência (DAOs) sobre SQLite3.

Execução local:
    python3 app.py
Execução em produção (Render / Gunicorn):
    gunicorn app:application
"""

import json
import mimetypes
import os
import re
from typing import Optional
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from src.config.database import DatabaseManager
from src.controllers.aluno_controller import AlunoController
from src.controllers.auth_controller import AuthController
from src.controllers.empresa_controller import EmpresaParceiraController
from src.controllers.merito_controller import MeritoController
from src.controllers.vantagem_controller import VantagemController
from src.dao.catalogo_dao import CatalogoDAO
from src.services.auth_service import AuthService
from src.services.notificacao_service import NotificacaoService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_DIR = os.path.join(BASE_DIR, "src", "views")
PUBLIC_SVGS = {
    "/modelo-er.svg",
    "/casos-de-uso.svg",
    "/diagrama-classes.svg",
    "/diagrama-componentes.svg",
    "/diagrama-sequencia.svg",
    "/diagrama-visao-geral-interacao.svg",
    "/diagrama-implantacao.svg",
}


class MoedaEstudantilWSGIApp:
    """Aplicação Web MVC compatível com WSGI (funciona nativamente ou via Gunicorn)."""

    def __init__(self, db_path: Optional[str] = None):
        resolved_db_path = db_path or os.environ.get("DATABASE_PATH") or None
        self.db_manager = DatabaseManager(resolved_db_path) if resolved_db_path else DatabaseManager()
        self.db_manager.init_database()

        self.auth_service = AuthService(self.db_manager)
        self.notificacao_service = NotificacaoService(self.db_manager)

        self.aluno_controller = AlunoController(self.db_manager)
        self.empresa_controller = EmpresaParceiraController(self.db_manager)
        self.auth_controller = AuthController(self.db_manager, self.auth_service)
        self.merito_controller = MeritoController(self.db_manager, self.notificacao_service)
        self.vantagem_controller = VantagemController(self.db_manager, self.notificacao_service)
        self.catalogo_dao = CatalogoDAO(self.db_manager)

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        query_params = parse_qs(environ.get("QUERY_STRING", ""))

        if method == "OPTIONS":
            return self._cors_preflight(start_response)

        try:
            # 1. Rotas da View (Front-end MVC e Arquivos Estáticos)
            if method == "GET" and path in ("/", "/index.html"):
                return self._serve_file(os.path.join(VIEWS_DIR, "index.html"), "text/html; charset=utf-8", start_response)

            if method == "GET" and path in ("/styles.css", "/app.js"):
                safe_path = os.path.join(VIEWS_DIR, path.lstrip("/"))
                if os.path.isfile(safe_path):
                    ctype, _ = mimetypes.guess_type(safe_path)
                    return self._serve_file(safe_path, f"{ctype or 'text/plain'}; charset=utf-8", start_response)

            if method == "GET" and path.startswith("/static/"):
                rel_name = path.replace("/static/", "", 1)
                safe_path = os.path.normpath(os.path.join(VIEWS_DIR, rel_name))
                if safe_path.startswith(VIEWS_DIR) and os.path.isfile(safe_path):
                    ctype, _ = mimetypes.guess_type(safe_path)
                    return self._serve_file(safe_path, f"{ctype or 'text/plain'}; charset=utf-8", start_response)

            if method == "GET" and path in PUBLIC_SVGS:
                svg_path = os.path.join(BASE_DIR, path.lstrip("/"))
                if os.path.isfile(svg_path):
                    return self._serve_file(svg_path, "image/svg+xml; charset=utf-8", start_response)

            # Healthcheck (para Render / monitoramento)
            if method == "GET" and path == "/api/health":
                return self._json_response(200, {"sucesso": True, "status": "ok"}, start_response)

            # 2. Rotas de Autenticação (HU-05)
            if method == "POST" and path == "/api/auth/login":
                payload = self._read_json_body(environ)
                status, res = self.auth_controller.login(payload)
                return self._json_response(status, res, start_response)

            if method == "GET" and path == "/api/auth/me":
                usuario, erro = self._exigir_autenticacao(environ)
                if erro:
                    return self._json_response(erro[0], erro[1], start_response)
                status, res = self.auth_controller.perfil_atual(usuario["sub"])
                return self._json_response(status, res, start_response)

            # 3. Rotas de Catálogo Acadêmico Pré-Cadastrado
            if method == "GET" and path == "/api/instituicoes":
                insts = [i.to_dict() for i in self.catalogo_dao.listar_instituicoes()]
                return self._json_response(200, {"sucesso": True, "dados": insts}, start_response)

            if method == "GET" and path == "/api/cursos":
                inst_id = query_params.get("instituicaoId", [None])[0]
                cursos = [c.to_dict() for c in self.catalogo_dao.listar_cursos(inst_id)]
                return self._json_response(200, {"sucesso": True, "dados": cursos}, start_response)

            if method == "GET" and path == "/api/professores":
                status, res = self.merito_controller.listar_professores()
                return self._json_response(status, res, start_response)

            # 4. Rotas REST CRUD de Aluno (`/api/alunos` e `/api/alunos/<id>`)
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

            # 5. Rotas REST CRUD de Empresa Parceira (`/api/empresas` e `/api/empresas/<id>`)
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

            # 6. Rotas de Mérito e Extrato (HU-06, HU-07, HU-08, HU-09)
            if method == "POST" and path == "/api/merito/transferir":
                usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("PROFESSOR",))
                if erro:
                    return self._json_response(erro[0], erro[1], start_response)
                payload = self._read_json_body(environ)
                status, res = self.merito_controller.transferir_moedas(usuario["sub"], payload)
                return self._json_response(status, res, start_response)

            if method == "POST" and path == "/api/merito/credito-semestral":
                usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("PROFESSOR",))
                if erro:
                    return self._json_response(erro[0], erro[1], start_response)
                payload = self._read_json_body(environ)
                status, res = self.merito_controller.conceder_credito_semestral(usuario["sub"], payload)
                return self._json_response(status, res, start_response)

            if method == "GET" and path == "/api/extrato":
                usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("ALUNO", "PROFESSOR"))
                if erro:
                    return self._json_response(erro[0], erro[1], start_response)
                status, res = self.merito_controller.consultar_extrato(usuario["sub"], usuario["tipoUsuario"])
                return self._json_response(status, res, start_response)

            # 7. Rotas de Vantagens e Resgates (HU-04, HU-10, HU-11)
            if path == "/api/vantagens":
                if method == "GET":
                    empresa_id = query_params.get("empresaId", [None])[0]
                    apenas_ativas = query_params.get("todas", ["0"])[0] != "1"
                    status, res = self.vantagem_controller.listar_vantagens(
                        empresa_id=empresa_id,
                        apenas_ativas=apenas_ativas,
                    )
                    return self._json_response(status, res, start_response)
                if method == "POST":
                    usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("EMPRESA",))
                    if erro:
                        return self._json_response(erro[0], erro[1], start_response)
                    payload = self._read_json_body(environ)
                    status, res = self.vantagem_controller.criar(usuario["sub"], payload)
                    return self._json_response(status, res, start_response)

            match_resgate = re.match(r"^/api/vantagens/([^/]+)/resgatar$", path)
            if match_resgate and method == "POST":
                usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("ALUNO",))
                if erro:
                    return self._json_response(erro[0], erro[1], start_response)
                vantagem_id = match_resgate.group(1)
                status, res = self.vantagem_controller.resgatar(usuario["sub"], vantagem_id)
                return self._json_response(status, res, start_response)

            match_vantagem = re.match(r"^/api/vantagens/([^/]+)$", path)
            if match_vantagem:
                vantagem_id = match_vantagem.group(1)
                if method == "GET":
                    status, res = self.vantagem_controller.buscar_por_id(vantagem_id)
                    return self._json_response(status, res, start_response)
                if method == "PUT":
                    usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("EMPRESA",))
                    if erro:
                        return self._json_response(erro[0], erro[1], start_response)
                    payload = self._read_json_body(environ)
                    status, res = self.vantagem_controller.atualizar(usuario["sub"], vantagem_id, payload)
                    return self._json_response(status, res, start_response)
                if method == "DELETE":
                    usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("EMPRESA",))
                    if erro:
                        return self._json_response(erro[0], erro[1], start_response)
                    status, res = self.vantagem_controller.remover(usuario["sub"], vantagem_id)
                    return self._json_response(status, res, start_response)

            if method == "GET" and path == "/api/resgates":
                usuario, erro = self._exigir_autenticacao(environ, perfis_permitidos=("ALUNO", "EMPRESA"))
                if erro:
                    return self._json_response(erro[0], erro[1], start_response)
                if usuario["tipoUsuario"] == "ALUNO":
                    status, res = self.vantagem_controller.listar_resgates_aluno(usuario["sub"])
                else:
                    status, res = self.vantagem_controller.listar_resgates_empresa(usuario["sub"])
                return self._json_response(status, res, start_response)

            # 8. Caixa de Notificações por E-mail
            if method == "GET" and path == "/api/notificacoes":
                usuario = self._obter_usuario_opcional(environ)
                filtro_email = query_params.get("email", [None])[0]
                if usuario and query_params.get("minhas", ["0"])[0] == "1":
                    filtro_email = usuario["email"]
                notifs = [n.to_dict() for n in self.notificacao_service.listar_notificacoes(filtro_email)]
                return self._json_response(200, {"sucesso": True, "total": len(notifs), "dados": notifs}, start_response)

            return self._json_response(404, {"sucesso": False, "erro": f"Rota não encontrada: {method} {path}"}, start_response)

        except json.JSONDecodeError:
            return self._json_response(400, {"sucesso": False, "erro": "Corpo da requisição não é um JSON válido."}, start_response)
        except Exception as exc:
            return self._json_response(500, {"sucesso": False, "erro": f"Erro interno no servidor: {exc}"}, start_response)

    def _obter_usuario_opcional(self, environ) -> Optional[dict]:
        auth_header = environ.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return self.auth_service.validar_token(token)
        return None

    def _exigir_autenticacao(self, environ, perfis_permitidos: tuple[str, ...] = ()):
        usuario = self._obter_usuario_opcional(environ)
        if not usuario:
            return None, (401, {"sucesso": False, "erro": "Autenticação obrigatória. Faça login para continuar."})
        if perfis_permitidos and usuario.get("tipoUsuario") not in perfis_permitidos:
            return None, (
                403,
                {
                    "sucesso": False,
                    "erro": f"Acesso negado para o perfil '{usuario.get('tipoUsuario')}'.",
                },
            )
        return usuario, None

    def _read_json_body(self, environ) -> dict:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = environ["wsgi.input"].read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _cors_preflight(self, start_response):
        headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
            ("Content-Length", "0"),
        ]
        start_response("204 No Content", headers)
        return [b""]

    def _json_response(self, status_code: int, data: dict, start_response):
        status_map = {
            200: "200 OK",
            201: "201 Created",
            400: "400 Bad Request",
            401: "401 Unauthorized",
            403: "403 Forbidden",
            404: "404 Not Found",
            409: "409 Conflict",
            500: "500 Internal Server Error",
        }
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
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


# Instância WSGI para deploy em produção (Gunicorn / Render)
application = MoedaEstudantilWSGIApp()


def main():
    port = int(os.environ.get("PORT", "8000"))
    print("=" * 72)
    print(" Sistema de Moeda Estudantil — Release 2 (Lab04S01 / Lab04S02)")
    print(f" Banco de Dados SQLite inicializado em: {application.db_manager.db_path}")
    print(f" Servidor Web / API REST disponível em: http://localhost:{port}")
    print("=" * 72)
    with make_server("0.0.0.0", port, application) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
