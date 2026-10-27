"""
Controlador MVC de Empresa Parceira (`EmpresaParceiraController`) — Lab03S02.
Implementa as regras de validação de negócio de HU-03 (Cadastrar empresa parceira) e o CRUD completo:
- Campos obrigatórios: nome (nome fantasia/exibição), nomeLegal (razão social),
  identificador (CNPJ/registro), email e senha.
- Unicidade de identificador (CNPJ) e e-mail.
- Armazenamento seguro de senha com hash PBKDF2-SHA256.
"""

from typing import Any, Dict, Tuple

from src.config.database import DatabaseManager, gerar_hash_senha
from src.dao.catalogo_dao import CatalogoDAO
from src.dao.empresa_dao import EmpresaParceiraDAO
from src.models.entities import EmpresaParceira, gerar_uuid


class EmpresaParceiraController:
    def __init__(self, db_manager: DatabaseManager):
        self.empresa_dao = EmpresaParceiraDAO(db_manager)
        self.catalogo_dao = CatalogoDAO(db_manager)

    def listar_todos(self) -> Tuple[int, Dict[str, Any]]:
        empresas = self.empresa_dao.listar_todos()
        return 200, {
            "sucesso": True,
            "total": len(empresas),
            "dados": [e.to_dict() for e in empresas],
        }

    def buscar_por_id(self, empresa_id: str) -> Tuple[int, Dict[str, Any]]:
        empresa = self.empresa_dao.buscar_por_id(empresa_id)
        if not empresa:
            return 404, {"sucesso": False, "erro": "Empresa parceira não encontrada."}
        return 200, {"sucesso": True, "dados": empresa.to_dict()}

    def criar(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        erros = self._validar_payload(payload, edicao=False)
        if erros:
            return 400, {
                "sucesso": False,
                "erro": "Dados inválidos no cadastro da empresa parceira.",
                "detalhes": erros,
            }

        nome = str(payload["nome"]).strip()
        nome_legal = str(payload["nomeLegal"]).strip()
        identificador = str(payload["identificador"]).strip()
        email = str(payload["email"]).strip().lower()
        descricao = str(payload.get("descricao") or "").strip()
        senha = str(payload["senha"])

        if self.catalogo_dao.email_ja_cadastrado(email):
            return 409, {"sucesso": False, "erro": "Já existe um usuário/parceiro cadastrado com este e-mail."}

        if self.empresa_dao.buscar_por_identificador(identificador):
            return 409, {"sucesso": False, "erro": "Já existe uma empresa parceira cadastrada com este CNPJ/Identificador."}

        nova_empresa = EmpresaParceira(
            id=gerar_uuid(),
            nome=nome,
            email=email,
            hash_senha=gerar_hash_senha(senha),
            nome_legal=nome_legal,
            identificador=identificador,
            descricao=descricao,
        )

        criada = self.empresa_dao.criar(nova_empresa)
        return 201, {
            "sucesso": True,
            "mensagem": "Empresa parceira cadastrada com sucesso.",
            "dados": criada.to_dict(),
        }

    def atualizar(self, empresa_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        existente = self.empresa_dao.buscar_por_id(empresa_id)
        if not existente:
            return 404, {"sucesso": False, "erro": "Empresa parceira não encontrada para atualização."}

        erros = self._validar_payload(payload, edicao=True)
        if erros:
            return 400, {
                "sucesso": False,
                "erro": "Dados inválidos na atualização da empresa parceira.",
                "detalhes": erros,
            }

        nome = str(payload["nome"]).strip()
        nome_legal = str(payload["nomeLegal"]).strip()
        identificador = str(payload["identificador"]).strip()
        email = str(payload["email"]).strip().lower()
        descricao = str(payload.get("descricao") or "").strip()
        nova_senha = str(payload.get("senha") or "").strip()

        if self.catalogo_dao.email_ja_cadastrado(email, ignorar_usuario_id=empresa_id):
            return 409, {"sucesso": False, "erro": "Este e-mail já está em uso por outro usuário."}

        outro_cnpj = self.empresa_dao.buscar_por_identificador(identificador)
        if outro_cnpj and outro_cnpj.id != empresa_id:
            return 409, {"sucesso": False, "erro": "Este CNPJ/Identificador já pertence a outra empresa parceira."}

        existente.nome = nome
        existente.nome_legal = nome_legal
        existente.identificador = identificador
        existente.email = email
        existente.descricao = descricao
        if nova_senha:
            existente.hash_senha = gerar_hash_senha(nova_senha)

        atualizada = self.empresa_dao.atualizar(existente)
        return 200, {
            "sucesso": True,
            "mensagem": "Dados da empresa parceira atualizados com sucesso.",
            "dados": atualizada.to_dict(),
        }

    def remover(self, empresa_id: str) -> Tuple[int, Dict[str, Any]]:
        removida = self.empresa_dao.remover(empresa_id)
        if not removida:
            return 404, {"sucesso": False, "erro": "Empresa parceira não encontrada para exclusão."}
        return 200, {"sucesso": True, "mensagem": "Empresa parceira excluída com sucesso."}

    def _validar_payload(self, payload: Dict[str, Any], edicao: bool = False) -> list[str]:
        erros = []
        campos_obrigatorios = [
            ("nome", "Nome Fantasia / Exibição"),
            ("nomeLegal", "Razão Social (Nome Legal)"),
            ("identificador", "CNPJ / Identificador"),
            ("email", "E-mail corporativo"),
        ]
        if not edicao:
            campos_obrigatorios.append(("senha", "Senha de acesso"))

        for chave, rotulo in campos_obrigatorios:
            valor = str(payload.get(chave) or "").strip()
            if not valor:
                erros.append(f"O campo '{rotulo}' é obrigatório.")

        email = str(payload.get("email") or "").strip()
        if email and "@" not in email:
            erros.append("Informe um endereço de e-mail válido.")

        doc_digitos = "".join(ch for ch in str(payload.get("identificador") or "") if ch.isdigit())
        if doc_digitos and len(doc_digitos) < 11:
            erros.append("O CNPJ/Identificador deve conter ao menos 11 a 14 dígitos numéricos.")

        senha = str(payload.get("senha") or "")
        if (not edicao or senha) and len(senha) < 6:
            erros.append("A senha deve possuir pelo menos 6 caracteres.")

        return erros

