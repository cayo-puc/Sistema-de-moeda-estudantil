"""
DAO de Movimentações e Extrato (`MovimentacaoDAO`) — Lab04S01.
Implementa transações atômicas de:
- Envio de moedas de Professor para Aluno (HU-07)
- Crédito semestral acumulado de 1.000 moedas para Professor (HU-06)
- Consulta de extrato por perfil (HU-09)
"""

import sqlite3
from typing import Any, Dict, List

from src.config.database import DatabaseManager
from src.models.entities import TipoMovimentacao, gerar_uuid, instante_atual_iso


class SaldoInsuficienteError(ValueError):
    """Lançada quando a conta de origem não possui saldo suficiente."""


class CreditoDuplicadoError(ValueError):
    """Lançada quando o professor já recebeu crédito para o período informado."""


class MovimentacaoDAO:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def consultar_saldo(self, usuario_id: str) -> int:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT saldo_atual FROM contas_moedas WHERE usuario_id = ?", (usuario_id,))
            row = cur.fetchone()
            if not row:
                raise LookupError("Conta de moedas não encontrada para o usuário.")
            return int(row["saldo_atual"])

    def transferir_moedas(
        self,
        professor_id: str,
        aluno_id: str,
        quantidade: int,
        motivo: str,
    ) -> Dict[str, Any]:
        """Executa transferência atômica entre a conta do professor e a conta do aluno."""
        agora = instante_atual_iso()
        mov_id = gerar_uuid()

        with self.db.transaction() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT cm.id AS conta_id, cm.saldo_atual, u.nome, u.email
                FROM contas_moedas cm
                INNER JOIN professores p ON p.usuario_id = cm.usuario_id
                INNER JOIN usuarios u ON u.id = cm.usuario_id
                WHERE cm.usuario_id = ?
                """,
                (professor_id,),
            )
            origem = cur.fetchone()
            if not origem:
                raise LookupError("Conta do professor não encontrada.")

            cur.execute(
                """
                SELECT cm.id AS conta_id, cm.saldo_atual, u.nome, u.email
                FROM contas_moedas cm
                INNER JOIN alunos a ON a.usuario_id = cm.usuario_id
                INNER JOIN usuarios u ON u.id = cm.usuario_id
                WHERE cm.usuario_id = ?
                """,
                (aluno_id,),
            )
            destino = cur.fetchone()
            if not destino:
                raise LookupError("Aluno de destino não encontrado.")

            # Debita somente se houver saldo suficiente (controle atômico no SQL)
            cur.execute(
                """
                UPDATE contas_moedas
                SET saldo_atual = saldo_atual - ?, atualizado_em = ?
                WHERE id = ? AND saldo_atual >= ?
                """,
                (quantidade, agora, origem["conta_id"], quantidade),
            )
            if cur.rowcount == 0:
                raise SaldoInsuficienteError(
                    f"Saldo insuficiente. Saldo atual: {origem['saldo_atual']} moedas."
                )

            cur.execute(
                """
                UPDATE contas_moedas
                SET saldo_atual = saldo_atual + ?, atualizado_em = ?
                WHERE id = ?
                """,
                (quantidade, agora, destino["conta_id"]),
            )

            cur.execute(
                """
                INSERT INTO movimentacoes (id, tipo, quantidade, instante)
                VALUES (?, ?, ?, ?)
                """,
                (mov_id, TipoMovimentacao.TRANSFERENCIA.value, quantidade, agora),
            )
            cur.execute(
                """
                INSERT INTO transferencias (movimentacao_id, conta_origem_id, conta_destino_id, motivo)
                VALUES (?, ?, ?, ?)
                """,
                (mov_id, origem["conta_id"], destino["conta_id"], motivo),
            )

            return {
                "movimentacaoId": mov_id,
                "tipo": TipoMovimentacao.TRANSFERENCIA.value,
                "quantidade": quantidade,
                "motivo": motivo,
                "instante": agora,
                "professorId": professor_id,
                "professorNome": origem["nome"],
                "alunoId": aluno_id,
                "alunoNome": destino["nome"],
                "alunoEmail": destino["email"],
                "saldoProfessorAtual": int(origem["saldo_atual"]) - quantidade,
                "saldoAlunoAtual": int(destino["saldo_atual"]) + quantidade,
            }

    def conceder_credito_semestral(self, professor_id: str, periodo: str) -> Dict[str, Any]:
        """Credita 1.000 moedas acumuláveis ao saldo do professor para o período (ex: '2026.2')."""
        agora = instante_atual_iso()
        mov_id = gerar_uuid()
        quantidade = 1000

        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT cm.id AS conta_id, cm.saldo_atual, u.nome
                FROM contas_moedas cm
                INNER JOIN professores p ON p.usuario_id = cm.usuario_id
                INNER JOIN usuarios u ON u.id = cm.usuario_id
                WHERE cm.usuario_id = ?
                """,
                (professor_id,),
            )
            conta = cur.fetchone()
            if not conta:
                raise LookupError("Conta do professor não encontrada.")

            try:
                cur.execute(
                    """
                    INSERT INTO movimentacoes (id, tipo, quantidade, instante)
                    VALUES (?, ?, ?, ?)
                    """,
                    (mov_id, TipoMovimentacao.CREDITO_SEMESTRAL.value, quantidade, agora),
                )
                cur.execute(
                    """
                    INSERT INTO creditos_semestrais (movimentacao_id, conta_destino_id, professor_id, periodo, quantidade_creditada)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (mov_id, conta["conta_id"], professor_id, periodo, quantidade),
                )
            except sqlite3.IntegrityError as exc:
                raise CreditoDuplicadoError(
                    f"O crédito semestral para o período '{periodo}' já foi concedido a este professor."
                ) from exc

            cur.execute(
                """
                UPDATE contas_moedas
                SET saldo_atual = saldo_atual + ?, atualizado_em = ?
                WHERE id = ?
                """,
                (quantidade, agora, conta["conta_id"]),
            )

            return {
                "movimentacaoId": mov_id,
                "professorId": professor_id,
                "professorNome": conta["nome"],
                "periodo": periodo,
                "quantidadeCreditada": quantidade,
                "saldoAtual": int(conta["saldo_atual"]) + quantidade,
                "instante": agora,
            }

    def consultar_extrato(self, usuario_id: str, tipo_usuario: str) -> Dict[str, Any]:
        """Retorna saldo atual e histórico cronológico de movimentações do titular."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, saldo_atual, atualizado_em FROM contas_moedas WHERE usuario_id = ?",
                (usuario_id,),
            )
            conta = cur.fetchone()
            if not conta:
                raise LookupError("Conta de moedas não encontrada.")

            conta_id = conta["id"]
            transacoes: List[Dict[str, Any]] = []

            if tipo_usuario == "PROFESSOR":
                # Créditos semestrais recebidos
                cur.execute(
                    """
                    SELECT m.id, m.tipo, m.quantidade, m.instante, cs.periodo
                    FROM creditos_semestrais cs
                    INNER JOIN movimentacoes m ON m.id = cs.movimentacao_id
                    WHERE cs.conta_destino_id = ?
                    """,
                    (conta_id,),
                )
                for row in cur.fetchall():
                    transacoes.append({
                        "id": row["id"],
                        "tipo": row["tipo"],
                        "direcao": "ENTRADA",
                        "quantidade": row["quantidade"],
                        "instante": row["instante"],
                        "descricao": f"Crédito semestral acumulado ({row['periodo']})",
                        "contraparte": "Instituição Parceira",
                        "motivo": f"Período {row['periodo']}",
                    })

                # Transferências enviadas pelo professor
                cur.execute(
                    """
                    SELECT m.id, m.tipo, m.quantidade, m.instante, t.motivo, u_dest.nome AS aluno_nome
                    FROM transferencias t
                    INNER JOIN movimentacoes m ON m.id = t.movimentacao_id
                    INNER JOIN contas_moedas cm_dest ON cm_dest.id = t.conta_destino_id
                    INNER JOIN usuarios u_dest ON u_dest.id = cm_dest.usuario_id
                    WHERE t.conta_origem_id = ?
                    """,
                    (conta_id,),
                )
                for row in cur.fetchall():
                    transacoes.append({
                        "id": row["id"],
                        "tipo": row["tipo"],
                        "direcao": "SAIDA",
                        "quantidade": row["quantidade"],
                        "instante": row["instante"],
                        "descricao": f"Envio de reconhecimento para {row['aluno_nome']}",
                        "contraparte": row["aluno_nome"],
                        "motivo": row["motivo"],
                    })

            elif tipo_usuario == "ALUNO":
                # Recebimentos de professores
                cur.execute(
                    """
                    SELECT m.id, m.tipo, m.quantidade, m.instante, t.motivo, u_orig.nome AS professor_nome
                    FROM transferencias t
                    INNER JOIN movimentacoes m ON m.id = t.movimentacao_id
                    INNER JOIN contas_moedas cm_orig ON cm_orig.id = t.conta_origem_id
                    INNER JOIN usuarios u_orig ON u_orig.id = cm_orig.usuario_id
                    WHERE t.conta_destino_id = ?
                    """,
                    (conta_id,),
                )
                for row in cur.fetchall():
                    transacoes.append({
                        "id": row["id"],
                        "tipo": row["tipo"],
                        "direcao": "ENTRADA",
                        "quantidade": row["quantidade"],
                        "instante": row["instante"],
                        "descricao": f"Reconhecimento recebido de {row['professor_nome']}",
                        "contraparte": row["professor_nome"],
                        "motivo": row["motivo"],
                    })

                # Débitos de resgate de vantagens
                cur.execute(
                    """
                    SELECT
                        m.id,
                        m.tipo,
                        m.quantidade,
                        m.instante,
                        v.titulo AS vantagem_titulo,
                        u_emp.nome AS empresa_nome,
                        c.codigo_conferencia
                    FROM debitos_resgate dr
                    INNER JOIN movimentacoes m ON m.id = dr.movimentacao_id
                    INNER JOIN resgates r ON r.debito_movimentacao_id = dr.movimentacao_id
                    INNER JOIN vantagens v ON v.id = r.vantagem_id
                    INNER JOIN usuarios u_emp ON u_emp.id = v.empresa_id
                    LEFT JOIN cupons c ON c.resgate_id = r.id
                    WHERE dr.conta_origem_id = ?
                    """,
                    (conta_id,),
                )
                for row in cur.fetchall():
                    transacoes.append({
                        "id": row["id"],
                        "tipo": row["tipo"],
                        "direcao": "SAIDA",
                        "quantidade": row["quantidade"],
                        "instante": row["instante"],
                        "descricao": f"Resgate: {row['vantagem_titulo']} ({row['empresa_nome']})",
                        "contraparte": row["empresa_nome"],
                        "motivo": f"Cupom {row['codigo_conferencia']}" if row["codigo_conferencia"] else "Resgate confirmado",
                        "codigoConferencia": row["codigo_conferencia"],
                    })

            transacoes.sort(key=lambda item: item["instante"], reverse=True)
            return {
                "contaId": conta_id,
                "usuarioId": usuario_id,
                "tipoUsuario": tipo_usuario,
                "saldoAtual": int(conta["saldo_atual"]),
                "atualizadoEm": conta["atualizado_em"],
                "transacoes": transacoes,
            }
