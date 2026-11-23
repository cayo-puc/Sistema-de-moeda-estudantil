"""
Controlador MVC de Autenticação (`AuthController`) — Lab04S01 (HU-05).
"""

from typing import Any, Dict, Tuple

from src.config.database import DatabaseManager
from src.services.auth_service import AuthService


class AuthController:
    def __init__(self, db_manager: DatabaseManager, auth_service: AuthService):
        self.db = db_manager
        self.auth_service = auth_service

    def login(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        email = str(payload.get("email") or "").strip()
        senha = str(payload.get("senha") or "")
        if not email or not senha:
            return 400, {"sucesso": False, "erro": "Informe e-mail e senha para autenticar."}

        resultado = self.auth_service.autenticar(email, senha)
        if not resultado:
            return 401, {"sucesso": False, "erro": "Credenciais inválidas. Verifique e-mail e senha."}

        return 200, {
            "sucesso": True,
            "mensagem": f"Bem-vindo(a), {resultado['usuario']['nome']}!",
            "dados": resultado,
        }

    def perfil_atual(self, usuario_id: str) -> Tuple[int, Dict[str, Any]]:
        usuario = self.auth_service.buscar_usuario_por_id(usuario_id)
        if not usuario:
            return 404, {"sucesso": False, "erro": "Usuário autenticado não encontrado."}
        return 200, {"sucesso": True, "dados": usuario}
