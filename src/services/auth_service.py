"""
Serviço de Autenticação e Autorização (`AuthService`) — Lab04S01.
Implementa HU-05: login com verificação PBKDF2-SHA256 e emissão/validação de
token assinado HMAC-SHA256 para controle de acesso por perfil (ALUNO, PROFESSOR, EMPRESA).
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from src.config.database import DatabaseManager, verificar_senha

_DEFAULT_SECRET = os.environ.get("APP_SECRET_KEY", "moeda-estudantil-pucminas-2026-secret")


class AuthService:
    def __init__(self, db_manager: DatabaseManager, secret_key: str = _DEFAULT_SECRET):
        self.db = db_manager
        self.secret_key = secret_key.encode("utf-8")

    def autenticar(self, email: str, senha: str) -> Optional[Dict[str, Any]]:
        email_norm = (email or "").strip().lower()
        if not email_norm or not senha:
            return None

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT u.id, u.nome, u.email, u.hash_senha, u.tipo_usuario, cm.saldo_atual
                FROM usuarios u
                LEFT JOIN contas_moedas cm ON cm.usuario_id = u.id
                WHERE lower(u.email) = ?
                """,
                (email_norm,),
            )
            row = cur.fetchone()
            if not row or not verificar_senha(senha, row["hash_senha"]):
                return None

            usuario_info = {
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "tipoUsuario": row["tipo_usuario"],
                "saldoMoedas": int(row["saldo_atual"]) if row["saldo_atual"] is not None else None,
            }
            token = self._gerar_token(usuario_info)
            return {"token": token, "usuario": usuario_info}

    def buscar_usuario_por_id(self, usuario_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT u.id, u.nome, u.email, u.tipo_usuario, cm.saldo_atual
                FROM usuarios u
                LEFT JOIN contas_moedas cm ON cm.usuario_id = u.id
                WHERE u.id = ?
                """,
                (usuario_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "tipoUsuario": row["tipo_usuario"],
                "saldoMoedas": int(row["saldo_atual"]) if row["saldo_atual"] is not None else None,
            }

    def validar_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token or "." not in token:
            return None
        try:
            payload_b64, sig_b64 = token.split(".", 1)
            expected_sig = hmac.new(self.secret_key, payload_b64.encode("ascii"), hashlib.sha256).digest()
            actual_sig = self._b64decode(sig_b64)
            if not hmac.compare_digest(expected_sig, actual_sig):
                return None
            payload = json.loads(self._b64decode(payload_b64).decode("utf-8"))
            if int(payload.get("exp", 0)) < int(time.time()):
                return None
            return payload
        except Exception:
            return None

    def _gerar_token(self, usuario_info: Dict[str, Any], ttl_seconds: int = 86400) -> str:
        payload = {
            "sub": usuario_info["id"],
            "nome": usuario_info["nome"],
            "email": usuario_info["email"],
            "tipoUsuario": usuario_info["tipoUsuario"],
            "exp": int(time.time()) + ttl_seconds,
        }
        payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload_b64 = self._b64encode(payload_bytes)
        sig = hmac.new(self.secret_key, payload_b64.encode("ascii"), hashlib.sha256).digest()
        return f"{payload_b64}.{self._b64encode(sig)}"

    @staticmethod
    def _b64encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64decode(text: str) -> bytes:
        padding = "=" * (-len(text) % 4)
        return base64.urlsafe_b64decode(text + padding)
