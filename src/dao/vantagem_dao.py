"""
DAO de Vantagens (`VantagemDAO`) — Lab04S01.
Gerencia o catálogo de vantagens oferecidas pelas empresas parceiras (HU-04).
"""

import sqlite3
from typing import List, Optional

from src.dao.base_dao import GenericDAO
from src.models.entities import Vantagem, instante_atual_iso


class VantagemDAO(GenericDAO[Vantagem]):
    """Data Access Object para persistência e consulta de Vantagens."""

    _SELECT_BASE = """
        SELECT
            v.id,
            v.empresa_id,
            v.titulo,
            v.descricao,
            v.fotografia_uri,
            v.custo_moedas,
            v.dados_oferta,
            v.ativa,
            v.criado_em,
            u.nome AS empresa_nome
        FROM vantagens v
        INNER JOIN empresas_parceiras ep ON ep.usuario_id = v.empresa_id
        INNER JOIN usuarios u ON u.id = ep.usuario_id
    """

    def criar(self, vantagem: Vantagem) -> Vantagem:
        agora = instante_atual_iso()
        vantagem.criado_em = agora
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO vantagens (id, empresa_id, titulo, descricao, fotografia_uri, custo_moedas, dados_oferta, ativa, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vantagem.id,
                    vantagem.empresa_id,
                    vantagem.titulo,
                    vantagem.descricao,
                    vantagem.fotografia_uri,
                    vantagem.custo_moedas,
                    vantagem.dados_oferta,
                    1 if vantagem.ativa else 0,
                    vantagem.criado_em,
                ),
            )
        return self.buscar_por_id(vantagem.id)

    def buscar_por_id(self, id_entidade: str) -> Optional[Vantagem]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE v.id = ?", (id_entidade,))
            row = cur.fetchone()
            return Vantagem.from_row(row) if row else None

    def listar_todos(self, apenas_ativas: bool = True, empresa_id: Optional[str] = None) -> List[Vantagem]:
        filtros = []
        params = []
        if apenas_ativas:
            filtros.append("v.ativa = 1")
        if empresa_id:
            filtros.append("v.empresa_id = ?")
            params.append(empresa_id)

        where_clause = f" WHERE {' AND '.join(filtros)}" if filtros else ""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + where_clause + " ORDER BY v.criado_em DESC", params)
            return [Vantagem.from_row(row) for row in cur.fetchall()]

    def atualizar(self, vantagem: Vantagem) -> Optional[Vantagem]:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE vantagens
                SET titulo = ?, descricao = ?, fotografia_uri = ?, custo_moedas = ?, dados_oferta = ?, ativa = ?
                WHERE id = ?
                """,
                (
                    vantagem.titulo,
                    vantagem.descricao,
                    vantagem.fotografia_uri,
                    vantagem.custo_moedas,
                    vantagem.dados_oferta,
                    1 if vantagem.ativa else 0,
                    vantagem.id,
                ),
            )
            if cur.rowcount == 0:
                return None
        return self.buscar_por_id(vantagem.id)

    def remover(self, id_entidade: str) -> bool:
        """Remove a vantagem; caso já possua resgates vinculados, desativa para preservar histórico."""
        with self.db.transaction() as conn:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM vantagens WHERE id = ?", (id_entidade,))
                return cur.rowcount > 0
            except sqlite3.IntegrityError:
                cur.execute("UPDATE vantagens SET ativa = 0 WHERE id = ?", (id_entidade,))
                return cur.rowcount > 0
