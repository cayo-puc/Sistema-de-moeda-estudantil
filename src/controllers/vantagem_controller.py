"""
Controlador MVC de Vantagens e Resgates (`VantagemController`) — Lab04S01.
Implementa:
- HU-04: Gerenciamento de vantagens pela Empresa Parceira (descrição, foto, custo positivo)
- HU-10: Resgate de vantagem pelo Aluno com validação de saldo
- HU-11: Geração de cupom único e envio de e-mail para Aluno e Empresa Parceira
"""

from typing import Any, Dict, Optional, Tuple

from src.config.database import DatabaseManager
from src.dao.movimentacao_dao import SaldoInsuficienteError
from src.dao.resgate_dao import ResgateDAO, VantagemIndisponivelError
from src.dao.vantagem_dao import VantagemDAO
from src.models.entities import Vantagem, gerar_uuid
from src.services.notificacao_service import NotificacaoService


class VantagemController:
    def __init__(self, db_manager: DatabaseManager, notificacao_service: NotificacaoService | None = None):
        self.vantagem_dao = VantagemDAO(db_manager)
        self.resgate_dao = ResgateDAO(db_manager)
        self.notificacao_service = notificacao_service or NotificacaoService(db_manager)

    def listar_vantagens(
        self,
        empresa_id: Optional[str] = None,
        apenas_ativas: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        vantagens = self.vantagem_dao.listar_todos(apenas_ativas=apenas_ativas, empresa_id=empresa_id)
        return 200, {
            "sucesso": True,
            "total": len(vantagens),
            "dados": [v.to_dict() for v in vantagens],
        }

    def buscar_por_id(self, vantagem_id: str) -> Tuple[int, Dict[str, Any]]:
        vantagem = self.vantagem_dao.buscar_por_id(vantagem_id)
        if not vantagem:
            return 404, {"sucesso": False, "erro": "Vantagem não encontrada."}
        return 200, {"sucesso": True, "dados": vantagem.to_dict()}

    def criar(self, empresa_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        erros = self._validar_payload(payload)
        if erros:
            return 400, {"sucesso": False, "erro": "Dados inválidos no cadastro da vantagem.", "detalhes": erros}

        nova = Vantagem(
            id=gerar_uuid(),
            empresa_id=empresa_id,
            titulo=str(payload["titulo"]).strip(),
            descricao=str(payload["descricao"]).strip(),
            fotografia_uri=str(payload["fotografiaUri"]).strip(),
            custo_moedas=int(payload["custoMoedas"]),
            dados_oferta=str(payload.get("dadosOferta") or "").strip(),
            ativa=True,
        )
        criada = self.vantagem_dao.criar(nova)
        return 201, {
            "sucesso": True,
            "mensagem": "Vantagem cadastrada com sucesso no catálogo.",
            "dados": criada.to_dict(),
        }

    def atualizar(self, empresa_id: str, vantagem_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        existente = self.vantagem_dao.buscar_por_id(vantagem_id)
        if not existente:
            return 404, {"sucesso": False, "erro": "Vantagem não encontrada."}
        if existente.empresa_id != empresa_id:
            return 403, {"sucesso": False, "erro": "Você só pode editar vantagens da sua própria empresa."}

        erros = self._validar_payload(payload)
        if erros:
            return 400, {"sucesso": False, "erro": "Dados inválidos na atualização da vantagem.", "detalhes": erros}

        existente.titulo = str(payload["titulo"]).strip()
        existente.descricao = str(payload["descricao"]).strip()
        existente.fotografia_uri = str(payload["fotografiaUri"]).strip()
        existente.custo_moedas = int(payload["custoMoedas"])
        existente.dados_oferta = str(payload.get("dadosOferta") or "").strip()
        if "ativa" in payload:
            existente.ativa = bool(payload["ativa"])

        atualizada = self.vantagem_dao.atualizar(existente)
        return 200, {
            "sucesso": True,
            "mensagem": "Vantagem atualizada com sucesso.",
            "dados": atualizada.to_dict(),
        }

    def remover(self, empresa_id: str, vantagem_id: str) -> Tuple[int, Dict[str, Any]]:
        existente = self.vantagem_dao.buscar_por_id(vantagem_id)
        if not existente:
            return 404, {"sucesso": False, "erro": "Vantagem não encontrada."}
        if existente.empresa_id != empresa_id:
            return 403, {"sucesso": False, "erro": "Você só pode remover vantagens da sua própria empresa."}

        self.vantagem_dao.remover(vantagem_id)
        return 200, {"sucesso": True, "mensagem": "Vantagem removida do catálogo."}

    def resgatar(self, aluno_id: str, vantagem_id: str) -> Tuple[int, Dict[str, Any]]:
        try:
            resultado = self.resgate_dao.resgatar_vantagem(aluno_id=aluno_id, vantagem_id=vantagem_id)
        except VantagemIndisponivelError as exc:
            return 404, {"sucesso": False, "erro": str(exc)}
        except LookupError as exc:
            return 404, {"sucesso": False, "erro": str(exc)}
        except SaldoInsuficienteError as exc:
            return 400, {"sucesso": False, "erro": str(exc)}

        resgate = resultado["resgate"]
        self.notificacao_service.notificar_resgate_vantagem(
            aluno_email=resgate["alunoEmail"],
            aluno_nome=resgate["alunoNome"],
            empresa_email=resultado["empresaEmail"],
            empresa_nome=resgate["empresaNome"],
            vantagem_titulo=resgate["vantagemTitulo"],
            custo_moedas=resgate["custoAplicado"],
            codigo_conferencia=resgate["codigoConferencia"],
            resgate_id=resgate["id"],
        )

        return 201, {
            "sucesso": True,
            "mensagem": (
                f"Vantagem resgatada! Cupom {resgate['codigoConferencia']} "
                f"enviado por e-mail para você e para {resgate['empresaNome']}."
            ),
            "dados": {
                "resgate": resgate,
                "saldoAlunoAtual": resultado["saldoAlunoAtual"],
            },
        }

    def listar_resgates_aluno(self, aluno_id: str) -> Tuple[int, Dict[str, Any]]:
        resgates = self.resgate_dao.listar_por_aluno(aluno_id)
        return 200, {
            "sucesso": True,
            "total": len(resgates),
            "dados": [r.to_dict() for r in resgates],
        }

    def listar_resgates_empresa(self, empresa_id: str) -> Tuple[int, Dict[str, Any]]:
        resgates = self.resgate_dao.listar_por_empresa(empresa_id)
        return 200, {
            "sucesso": True,
            "total": len(resgates),
            "dados": [r.to_dict() for r in resgates],
        }

    def _validar_payload(self, payload: Dict[str, Any]) -> list[str]:
        erros = []
        if not str(payload.get("titulo") or "").strip():
            erros.append("O título da vantagem é obrigatório.")
        if not str(payload.get("descricao") or "").strip():
            erros.append("A descrição da vantagem é obrigatória.")
        if not str(payload.get("fotografiaUri") or "").strip():
            erros.append("A URL ou URI da fotografia do produto é obrigatória.")
        try:
            custo = int(payload.get("custoMoedas") or 0)
        except (TypeError, ValueError):
            custo = 0
        if custo <= 0:
            erros.append("O custo em moedas deve ser um número inteiro positivo.")
        return erros
