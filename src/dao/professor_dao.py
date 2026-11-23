"""
DAO de Professor (`ProfessorDAO`) — Lab04S01.
Consulta professores pré-cadastrados (HU-02) com suas respectivas instituições,
departamentos e contas de moedas (Joined Table Inheritance).
"""

from typing import List, Optional

from src.config.database import DatabaseManager
from src.models.entities import Professor


class ProfessorDAO:
    """Data Access Object para consulta de Professores pré-cadastrados."""

    _SELECT_BASE = """
        SELECT
            u.id,
            u.nome,
            u.email,
            u.hash_senha,
            u.tipo_usuario,
            u.criado_em,
            u.atualizado_em,
            p.cpf,
            p.instituicao_id,
            p.departamento_id,
            i.nome AS instituicao_nome,
            i.sigla AS instituicao_sigla,
            d.nome AS departamento_nome,
            cm.id AS conta_id,
            cm.saldo_atual AS saldo_atual
        FROM professores p
        INNER JOIN usuarios u ON u.id = p.usuario_id
        INNER JOIN instituicoes_ensino i ON i.id = p.instituicao_id
        INNER JOIN departamentos d ON d.id = p.departamento_id
        LEFT JOIN contas_moedas cm ON cm.usuario_id = u.id
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def buscar_por_id(self, professor_id: str) -> Optional[Professor]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE u.id = ?", (professor_id,))
            row = cur.fetchone()
            return Professor.from_row(row) if row else None

    def buscar_por_email(self, email: str) -> Optional[Professor]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE lower(u.email) = lower(?)", (email,))
            row = cur.fetchone()
            return Professor.from_row(row) if row else None

    def listar_todos(self) -> List[Professor]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " ORDER BY u.nome ASC")
            return [Professor.from_row(row) for row in cur.fetchall()]
