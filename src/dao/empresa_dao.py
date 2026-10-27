"""
DAO de Empresa Parceira (`EmpresaParceiraDAO`) — Lab03S02.
Implementa o Padrão DAO com mapeamento Objeto-Relacional (Joined Table Inheritance)
entre as tabelas `usuarios`, `empresas_parceiras` e agregação de `vantagens`.
"""

from typing import List, Optional

from src.dao.base_dao import GenericDAO
from src.models.entities import EmpresaParceira, instante_atual_iso


class EmpresaParceiraDAO(GenericDAO[EmpresaParceira]):
    """Data Access Object para persistência e consulta de Empresas Parceiras."""

    _SELECT_BASE = """
        SELECT
            u.id,
            u.nome,
            u.email,
            u.hash_senha,
            u.tipo_usuario,
            u.criado_em,
            u.atualizado_em,
            e.nome_legal,
            e.identificador,
            e.descricao,
            (SELECT COUNT(*) FROM vantagens v WHERE v.empresa_id = u.id) AS total_vantagens
        FROM empresas_parceiras e
        INNER JOIN usuarios u ON u.id = e.usuario_id
    """

    def criar(self, empresa: EmpresaParceira) -> EmpresaParceira:
        """
        Persiste uma nova Empresa Parceira em transação atômica:
        1. Insere registro base em `usuarios` (perfil EMPRESA)
        2. Insere registro especializado em `empresas_parceiras`
        """
        agora = instante_atual_iso()
        empresa.criado_em = agora
        empresa.atualizado_em = agora

        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO usuarios (id, nome, email, hash_senha, tipo_usuario, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, 'EMPRESA', ?, ?)
                """,
                (
                    empresa.id,
                    empresa.nome,
                    empresa.email,
                    empresa.hash_senha,
                    empresa.criado_em,
                    empresa.atualizado_em,
                ),
            )
            cur.execute(
                """
                INSERT INTO empresas_parceiras (usuario_id, nome_legal, identificador, descricao)
                VALUES (?, ?, ?, ?)
                """,
                (
                    empresa.id,
                    empresa.nome_legal,
                    empresa.identificador,
                    empresa.descricao,
                ),
            )

        return self.buscar_por_id(empresa.id)

    def buscar_por_id(self, id_entidade: str) -> Optional[EmpresaParceira]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE u.id = ?", (id_entidade,))
            row = cur.fetchone()
            return EmpresaParceira.from_row(row) if row else None

    def buscar_por_identificador(self, identificador: str) -> Optional[EmpresaParceira]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE e.identificador = ?", (identificador,))
            row = cur.fetchone()
            return EmpresaParceira.from_row(row) if row else None

    def buscar_por_email(self, email: str) -> Optional[EmpresaParceira]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE lower(u.email) = lower(?)", (email,))
            row = cur.fetchone()
            return EmpresaParceira.from_row(row) if row else None

    def listar_todos(self) -> List[EmpresaParceira]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " ORDER BY u.nome ASC")
            rows = cur.fetchall()
            return [EmpresaParceira.from_row(r) for r in rows]

    def atualizar(self, empresa: EmpresaParceira) -> Optional[EmpresaParceira]:
        agora = instante_atual_iso()
        empresa.atualizado_em = agora
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE usuarios
                SET nome = ?, email = ?, hash_senha = ?, atualizado_em = ?
                WHERE id = ? AND tipo_usuario = 'EMPRESA'
                """,
                (empresa.nome, empresa.email, empresa.hash_senha, agora, empresa.id),
            )
            if cur.rowcount == 0:
                return None

            cur.execute(
                """
                UPDATE empresas_parceiras
                SET nome_legal = ?, identificador = ?, descricao = ?
                WHERE usuario_id = ?
                """,
                (
                    empresa.nome_legal,
                    empresa.identificador,
                    empresa.descricao,
                    empresa.id,
                ),
            )

        return self.buscar_por_id(empresa.id)

    def remover(self, id_entidade: str) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM usuarios WHERE id = ? AND tipo_usuario = 'EMPRESA'",
                (id_entidade,),
            )
            return cur.rowcount > 0

