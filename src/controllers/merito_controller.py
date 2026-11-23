"""
Controlador MVC de Mérito e Extrato (`MeritoController`) — Lab04S01.
Implementa:
- HU-02: Consulta de professores pré-cadastrados
- HU-06: Crédito semestral acumulado (1.000 moedas por período)
- HU-07: Distribuição de moedas do professor para o aluno (com motivo obrigatório)
- HU-08: Disparo de notificação por e-mail ao aluno após transferência efetivada
- HU-09: Consulta de extrato de moedas para Professor e Aluno
"""

from typing import Any, Dict, Tuple

from src.config.database import DatabaseManager
from src.dao.movimentacao_dao import (
    CreditoDuplicadoError,
    MovimentacaoDAO,
    SaldoInsuficienteError,
)
from src.dao.professor_dao import ProfessorDAO
from src.services.notificacao_service import NotificacaoService


class MeritoController:
    def __init__(self, db_manager: DatabaseManager, notificacao_service: NotificacaoService | None = None):
        self.professor_dao = ProfessorDAO(db_manager)
        self.movimentacao_dao = MovimentacaoDAO(db_manager)
        self.notificacao_service = notificacao_service or NotificacaoService(db_manager)

    def listar_professores(self) -> Tuple[int, Dict[str, Any]]:
        professores = self.professor_dao.listar_todos()
        return 200, {
            "sucesso": True,
            "total": len(professores),
            "dados": [p.to_dict() for p in professores],
        }

    def transferir_moedas(self, professor_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        aluno_id = str(payload.get("alunoId") or "").strip()
        motivo = str(payload.get("motivo") or "").strip()
        try:
            quantidade = int(payload.get("quantidade") or 0)
        except (TypeError, ValueError):
            quantidade = 0

        erros = []
        if not aluno_id:
            erros.append("Selecione o aluno destinatário.")
        if quantidade <= 0:
            erros.append("A quantidade de moedas deve ser um número inteiro positivo.")
        if not motivo:
            erros.append("O motivo do reconhecimento é obrigatório.")
        if erros:
            return 400, {"sucesso": False, "erro": "Dados inválidos na transferência de moedas.", "detalhes": erros}

        try:
            resultado = self.movimentacao_dao.transferir_moedas(
                professor_id=professor_id,
                aluno_id=aluno_id,
                quantidade=quantidade,
                motivo=motivo,
            )
        except LookupError as exc:
            return 404, {"sucesso": False, "erro": str(exc)}
        except SaldoInsuficienteError as exc:
            return 400, {"sucesso": False, "erro": str(exc)}

        notificacao = self.notificacao_service.notificar_recebimento_moedas(
            aluno_email=resultado["alunoEmail"],
            aluno_nome=resultado["alunoNome"],
            professor_nome=resultado["professorNome"],
            quantidade=quantidade,
            motivo=motivo,
            referencia_id=resultado["movimentacaoId"],
        )
        resultado["notificacaoId"] = notificacao.id

        return 201, {
            "sucesso": True,
            "mensagem": f"{quantidade} moedas enviadas para {resultado['alunoNome']}! E-mail de notificação enviado.",
            "dados": resultado,
        }

    def conceder_credito_semestral(self, professor_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        periodo = str(payload.get("periodo") or "").strip()
        if not periodo:
            return 400, {"sucesso": False, "erro": "Informe o período letivo (ex.: 2026.2)."}

        try:
            resultado = self.movimentacao_dao.conceder_credito_semestral(professor_id, periodo)
        except LookupError as exc:
            return 404, {"sucesso": False, "erro": str(exc)}
        except CreditoDuplicadoError as exc:
            return 409, {"sucesso": False, "erro": str(exc)}

        return 201, {
            "sucesso": True,
            "mensagem": f"Crédito semestral de 1.000 moedas ({periodo}) adicionado ao seu saldo.",
            "dados": resultado,
        }

    def consultar_extrato(self, usuario_id: str, tipo_usuario: str) -> Tuple[int, Dict[str, Any]]:
        if tipo_usuario not in ("ALUNO", "PROFESSOR"):
            return 403, {"sucesso": False, "erro": "Extrato de moedas disponível apenas para Alunos e Professores."}

        try:
            extrato = self.movimentacao_dao.consultar_extrato(usuario_id, tipo_usuario)
        except LookupError as exc:
            return 404, {"sucesso": False, "erro": str(exc)}

        return 200, {"sucesso": True, "dados": extrato}
