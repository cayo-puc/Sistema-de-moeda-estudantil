"""
DAO de Catálogo Acadêmico (`CatalogoDAO`) — Lab03S02.
Consulta Instituições de Ensino e Cursos pré-cadastrados (regra de negócio HU-01 / RF01:
'As instituições participantes já estão pré-cadastradas no sistema, para que o aluno selecione').
"""

from typing import List, Optional

from src.config.database import DatabaseManager
from src.models.entities import Curso, InstituicaoEnsino


class CatalogoDAO:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def listar_instituicoes(self) -> List[InstituicaoEnsino]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, nome, sigla, criado_em FROM instituicoes_ensino ORDER BY nome ASC")
            return [
                InstituicaoEnsino(
                    id=row["id"],
                    nome=row["nome"],
                    sigla=row["sigla"],
                    criado_em=row["criado_em"],
                )
                for row in cur.fetchall()
            ]

    def buscar_instituicao_por_id(self, instituicao_id: str) -> Optional[InstituicaoEnsino]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, nome, sigla, criado_em FROM instituicoes_ensino WHERE id = ?", (instituicao_id,))
            row = cur.fetchone()
            if not row:
                return None
            return InstituicaoEnsino(
                id=row["id"],
                nome=row["nome"],
                sigla=row["sigla"],
                criado_em=row["criado_em"],
            )

    def listar_cursos(self, instituicao_id: Optional[str] = None) -> List[Curso]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if instituicao_id:
                cur.execute(
                    "SELECT id, instituicao_id, nome FROM cursos WHERE instituicao_id = ? ORDER BY nome ASC",
                    (instituicao_id,),
                )
            else:
                cur.execute("SELECT id, instituicao_id, nome FROM cursos ORDER BY nome ASC")
            return [
                Curso(
                    id=row["id"],
                    instituicao_id=row["instituicao_id"],
                    nome=row["nome"],
                )
                for row in cur.fetchall()
            ]

    def buscar_curso_por_id(self, curso_id: str) -> Optional[Curso]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, instituicao_id, nome FROM cursos WHERE id = ?", (curso_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Curso(
                id=row["id"],
                instituicao_id=row["instituicao_id"],
                nome=row["nome"],
            )

    def email_ja_cadastrado(self, email: str, ignorar_usuario_id: Optional[str] = None) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if ignorar_usuario_id:
                cur.execute(
                    "SELECT 1 FROM usuarios WHERE lower(email) = lower(?) AND id != ?",
                    (email, ignorar_usuario_id),
                )
            else:
                cur.execute("SELECT 1 FROM usuarios WHERE lower(email) = lower(?)", (email,))
            return cur.fetchone() is not None

