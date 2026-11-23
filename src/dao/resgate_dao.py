"""
DAO de Resgates e Cupons (`ResgateDAO`) — Lab04S01.
Implementa o resgate atômico de vantagens pelo aluno (HU-10) e a geração
do cupom com código de conferência único (HU-11).
"""

import secrets
from typing import Any, Dict, List

from src.config.database import DatabaseManager
from src.dao.movimentacao_dao import SaldoInsuficienteError
from src.models.entities import Resgate, StatusResgate, TipoMovimentacao, gerar_uuid, instante_atual_iso


class VantagemIndisponivelError(ValueError):
    """Lançada quando a vantagem não existe ou está inativa."""


class ResgateDAO:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def resgatar_vantagem(self, aluno_id: str, vantagem_id: str) -> Dict[str, Any]:
        """Executa o resgate em transação atômica: débito, movimentação, resgate e cupom."""
        agora = instante_atual_iso()
        mov_id = gerar_uuid()
        resgate_id = gerar_uuid()
        cupom_id = gerar_uuid()
        codigo_conferencia = f"CUPOM-{secrets.token_hex(4).upper()}"

        with self.db.transaction() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT v.id, v.titulo, v.custo_moedas, v.ativa, v.fotografia_uri,
                       v.empresa_id, u_emp.nome AS empresa_nome, u_emp.email AS empresa_email
                FROM vantagens v
                INNER JOIN usuarios u_emp ON u_emp.id = v.empresa_id
                WHERE v.id = ?
                """,
                (vantagem_id,),
            )
            vantagem = cur.fetchone()
            if not vantagem or not bool(vantagem["ativa"]):
                raise VantagemIndisponivelError("Vantagem não encontrada ou indisponível para resgate.")

            cur.execute(
                """
                SELECT cm.id AS conta_id, cm.saldo_atual, u.nome AS aluno_nome, u.email AS aluno_email
                FROM contas_moedas cm
                INNER JOIN alunos a ON a.usuario_id = cm.usuario_id
                INNER JOIN usuarios u ON u.id = cm.usuario_id
                WHERE cm.usuario_id = ?
                """,
                (aluno_id,),
            )
            conta_aluno = cur.fetchone()
            if not conta_aluno:
                raise LookupError("Conta de moedas do aluno não encontrada.")

            custo = int(vantagem["custo_moedas"])
            cur.execute(
                """
                UPDATE contas_moedas
                SET saldo_atual = saldo_atual - ?, atualizado_em = ?
                WHERE id = ? AND saldo_atual >= ?
                """,
                (custo, agora, conta_aluno["conta_id"], custo),
            )
            if cur.rowcount == 0:
                raise SaldoInsuficienteError(
                    f"Saldo insuficiente para resgate. Necessário: {custo} moedas; disponível: {conta_aluno['saldo_atual']}."
                )

            cur.execute(
                """
                INSERT INTO movimentacoes (id, tipo, quantidade, instante)
                VALUES (?, ?, ?, ?)
                """,
                (mov_id, TipoMovimentacao.DEBITO_RESGATE.value, custo, agora),
            )
            cur.execute(
                """
                INSERT INTO debitos_resgate (movimentacao_id, conta_origem_id)
                VALUES (?, ?)
                """,
                (mov_id, conta_aluno["conta_id"]),
            )
            cur.execute(
                """
                INSERT INTO resgates (id, aluno_id, vantagem_id, debito_movimentacao_id, instante, custo_aplicado, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (resgate_id, aluno_id, vantagem_id, mov_id, agora, custo, StatusResgate.CONFIRMADO.value),
            )
            cur.execute(
                """
                INSERT INTO cupons (id, resgate_id, codigo_conferencia, instante_geracao)
                VALUES (?, ?, ?, ?)
                """,
                (cupom_id, resgate_id, codigo_conferencia, agora),
            )

            return {
                "resgate": Resgate(
                    id=resgate_id,
                    aluno_id=aluno_id,
                    vantagem_id=vantagem_id,
                    debito_movimentacao_id=mov_id,
                    instante=agora,
                    custo_aplicado=custo,
                    status=StatusResgate.CONFIRMADO.value,
                    codigo_conferencia=codigo_conferencia,
                    vantagem_titulo=vantagem["titulo"],
                    vantagem_fotografia_uri=vantagem["fotografia_uri"],
                    empresa_id=vantagem["empresa_id"],
                    empresa_nome=vantagem["empresa_nome"],
                    aluno_nome=conta_aluno["aluno_nome"],
                    aluno_email=conta_aluno["aluno_email"],
                ).to_dict(),
                "empresaEmail": vantagem["empresa_email"],
                "saldoAlunoAtual": int(conta_aluno["saldo_atual"]) - custo,
            }

    def listar_por_aluno(self, aluno_id: str) -> List[Resgate]:
        return self._listar_com_filtro("r.aluno_id = ?", (aluno_id,))

    def listar_por_empresa(self, empresa_id: str) -> List[Resgate]:
        return self._listar_com_filtro("v.empresa_id = ?", (empresa_id,))

    def _listar_com_filtro(self, where_sql: str, params: tuple) -> List[Resgate]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    r.id,
                    r.aluno_id,
                    r.vantagem_id,
                    r.debito_movimentacao_id,
                    r.instante,
                    r.custo_aplicado,
                    r.status,
                    c.codigo_conferencia,
                    v.titulo AS vantagem_titulo,
                    v.fotografia_uri AS vantagem_fotografia_uri,
                    v.empresa_id,
                    u_emp.nome AS empresa_nome,
                    u_alu.nome AS aluno_nome,
                    u_alu.email AS aluno_email
                FROM resgates r
                INNER JOIN vantagens v ON v.id = r.vantagem_id
                INNER JOIN usuarios u_emp ON u_emp.id = v.empresa_id
                INNER JOIN usuarios u_alu ON u_alu.id = r.aluno_id
                LEFT JOIN cupons c ON c.resgate_id = r.id
                WHERE {where_sql}
                ORDER BY r.instante DESC
                """,
                params,
            )
            return [
                Resgate(
                    id=row["id"],
                    aluno_id=row["aluno_id"],
                    vantagem_id=row["vantagem_id"],
                    debito_movimentacao_id=row["debito_movimentacao_id"],
                    instante=row["instante"],
                    custo_aplicado=row["custo_aplicado"],
                    status=row["status"],
                    codigo_conferencia=row["codigo_conferencia"],
                    vantagem_titulo=row["vantagem_titulo"],
                    vantagem_fotografia_uri=row["vantagem_fotografia_uri"],
                    empresa_id=row["empresa_id"],
                    empresa_nome=row["empresa_nome"],
                    aluno_nome=row["aluno_nome"],
                    aluno_email=row["aluno_email"],
                )
                for row in cur.fetchall()
            ]
