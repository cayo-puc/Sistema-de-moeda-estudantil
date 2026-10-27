"""
DAO de Aluno (`AlunoDAO`) — Lab03S02.
Implementa o Padrão DAO com mapeamento Objeto-Relacional (Joined Table Inheritance)
entre as tabelas `usuarios`, `alunos`, `contas_moedas`, `instituicoes_ensino` e `cursos`.
"""

from typing import List, Optional

from src.dao.base_dao import GenericDAO
from src.models.entities import Aluno, ContaMoedas, gerar_uuid, instante_atual_iso


class AlunoDAO(GenericDAO[Aluno]):
    """Data Access Object para persistência e consulta de Alunos."""

    _SELECT_BASE = """
        SELECT
            u.id,
            u.nome,
            u.email,
            u.hash_senha,
            u.tipo_usuario,
            u.criado_em,
            u.atualizado_em,
            a.cpf,
            a.rg,
            a.endereco,
            a.instituicao_id,
            a.curso_id,
            i.nome AS instituicao_nome,
            i.sigla AS instituicao_sigla,
            c.nome AS curso_nome,
            cm.id AS conta_id,
            cm.saldo_atual AS saldo_atual
        FROM alunos a
        INNER JOIN usuarios u ON u.id = a.usuario_id
        INNER JOIN instituicoes_ensino i ON i.id = a.instituicao_id
        INNER JOIN cursos c ON c.id = a.curso_id
        LEFT JOIN contas_moedas cm ON cm.usuario_id = u.id
    """

    def criar(self, aluno: Aluno) -> Aluno:
        """
        Persiste um novo Aluno em transação atômica:
        1. Insere registro base em `usuarios`
        2. Insere registro especializado em `alunos`
        3. Cria automaticamente a `ContaMoedas` (composição 1..1) com saldo inicial 0
        """
        agora = instante_atual_iso()
        aluno.criado_em = agora
        aluno.atualizado_em = agora
        conta_id = aluno.conta.id if aluno.conta else gerar_uuid()
        saldo_inicial = aluno.conta.saldo_atual if aluno.conta else 0

        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO usuarios (id, nome, email, hash_senha, tipo_usuario, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, 'ALUNO', ?, ?)
                """,
                (aluno.id, aluno.nome, aluno.email, aluno.hash_senha, aluno.criado_em, aluno.atualizado_em),
            )
            cur.execute(
                """
                INSERT INTO alunos (usuario_id, cpf, rg, endereco, instituicao_id, curso_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    aluno.id,
                    aluno.cpf,
                    aluno.rg,
                    aluno.endereco,
                    aluno.instituicao_id,
                    aluno.curso_id,
                ),
            )
            cur.execute(
                """
                INSERT INTO contas_moedas (id, usuario_id, saldo_atual, atualizado_em)
                VALUES (?, ?, ?, ?)
                """,
                (conta_id, aluno.id, saldo_inicial, agora),
            )

        return self.buscar_por_id(aluno.id)

    def buscar_por_id(self, id_entidade: str) -> Optional[Aluno]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE u.id = ?", (id_entidade,))
            row = cur.fetchone()
            return Aluno.from_row(row) if row else None

    def buscar_por_cpf(self, cpf: str) -> Optional[Aluno]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE a.cpf = ?", (cpf,))
            row = cur.fetchone()
            return Aluno.from_row(row) if row else None

    def buscar_por_email(self, email: str) -> Optional[Aluno]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " WHERE lower(u.email) = lower(?)", (email,))
            row = cur.fetchone()
            return Aluno.from_row(row) if row else None

    def listar_todos(self) -> List[Aluno]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self._SELECT_BASE + " ORDER BY u.nome ASC")
            rows = cur.fetchall()
            return [Aluno.from_row(r) for r in rows]

    def atualizar(self, aluno: Aluno) -> Optional[Aluno]:
        agora = instante_atual_iso()
        aluno.atualizado_em = agora
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE usuarios
                SET nome = ?, email = ?, hash_senha = ?, atualizado_em = ?
                WHERE id = ? AND tipo_usuario = 'ALUNO'
                """,
                (aluno.nome, aluno.email, aluno.hash_senha, agora, aluno.id),
            )
            if cur.rowcount == 0:
                return None

            cur.execute(
                """
                UPDATE alunos
                SET cpf = ?, rg = ?, endereco = ?, instituicao_id = ?, curso_id = ?
                WHERE usuario_id = ?
                """,
                (
                    aluno.cpf,
                    aluno.rg,
                    aluno.endereco,
                    aluno.instituicao_id,
                    aluno.curso_id,
                    aluno.id,
                ),
            )

        return self.buscar_por_id(aluno.id)

    def remover(self, id_entidade: str) -> bool:
        """
        Remove o registro em `usuarios`; devido ao `ON DELETE CASCADE` na chave
        estrangeira de `alunos` e `contas_moedas`, a exclusão ocorre atomicamente.
        """
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM usuarios WHERE id = ? AND tipo_usuario = 'ALUNO'",
                (id_entidade,),
            )
            return cur.rowcount > 0

