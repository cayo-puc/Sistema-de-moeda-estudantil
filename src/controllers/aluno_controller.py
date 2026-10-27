"""
Controlador MVC de Aluno (`AlunoController`) — Lab03S02.
Implementa as regras de validação de negócio de HU-01 (Cadastrar aluno) e o CRUD completo:
- Campos obrigatórios: nome, email, CPF, RG, endereço, instituição de ensino, curso e senha.
- Validação de instituição pré-cadastrada e vínculo do curso com a instituição selecionada.
- Unicidade de CPF e e-mail.
- Armazenamento seguro de senha com hash PBKDF2-SHA256.
"""

from typing import Any, Dict, Tuple

from src.config.database import DatabaseManager, gerar_hash_senha
from src.dao.aluno_dao import AlunoDAO
from src.dao.catalogo_dao import CatalogoDAO
from src.models.entities import Aluno, gerar_uuid


class AlunoController:
    def __init__(self, db_manager: DatabaseManager):
        self.aluno_dao = AlunoDAO(db_manager)
        self.catalogo_dao = CatalogoDAO(db_manager)

    def listar_todos(self) -> Tuple[int, Dict[str, Any]]:
        alunos = self.aluno_dao.listar_todos()
        return 200, {
            "sucesso": True,
            "total": len(alunos),
            "dados": [a.to_dict() for a in alunos],
        }

    def buscar_por_id(self, aluno_id: str) -> Tuple[int, Dict[str, Any]]:
        aluno = self.aluno_dao.buscar_por_id(aluno_id)
        if not aluno:
            return 404, {"sucesso": False, "erro": "Aluno não encontrado."}
        return 200, {"sucesso": True, "dados": aluno.to_dict()}

    def criar(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        erros = self._validar_payload(payload, edicao=False)
        if erros:
            return 400, {"sucesso": False, "erro": "Dados inválidos no cadastro de aluno.", "detalhes": erros}

        nome = str(payload["nome"]).strip()
        email = str(payload["email"]).strip().lower()
        cpf = str(payload["cpf"]).strip()
        rg = str(payload["rg"]).strip()
        endereco = str(payload["endereco"]).strip()
        instituicao_id = str(payload["instituicaoId"]).strip()
        curso_id = str(payload["cursoId"]).strip()
        senha = str(payload["senha"])

        # Verifica unicidade de e-mail e CPF
        if self.catalogo_dao.email_ja_cadastrado(email):
            return 409, {"sucesso": False, "erro": "Já existe um usuário cadastrado com este e-mail."}

        if self.aluno_dao.buscar_por_cpf(cpf):
            return 409, {"sucesso": False, "erro": "Já existe um aluno cadastrado com este CPF."}

        # Verifica se a instituição e o curso estão pré-cadastrados e vinculados (HU-01)
        instituicao = self.catalogo_dao.buscar_instituicao_por_id(instituicao_id)
        if not instituicao:
            return 400, {
                "sucesso": False,
                "erro": "A Instituição de Ensino selecionada não pertence ao conjunto pré-cadastrado.",
            }

        curso = self.catalogo_dao.buscar_curso_por_id(curso_id)
        if not curso or curso.instituicao_id != instituicao.id:
            return 400, {
                "sucesso": False,
                "erro": "O curso selecionado é inválido ou não pertence à instituição informada.",
            }

        novo_aluno = Aluno(
            id=gerar_uuid(),
            nome=nome,
            email=email,
            hash_senha=gerar_hash_senha(senha),
            cpf=cpf,
            rg=rg,
            endereco=endereco,
            instituicao_id=instituicao_id,
            curso_id=curso_id,
        )

        criado = self.aluno_dao.criar(novo_aluno)
        return 201, {
            "sucesso": True,
            "mensagem": "Aluno cadastrado com sucesso e conta de moedas inicializada.",
            "dados": criado.to_dict(),
        }

    def atualizar(self, aluno_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        existente = self.aluno_dao.buscar_por_id(aluno_id)
        if not existente:
            return 404, {"sucesso": False, "erro": "Aluno não encontrado para atualização."}

        erros = self._validar_payload(payload, edicao=True)
        if erros:
            return 400, {"sucesso": False, "erro": "Dados inválidos na atualização do aluno.", "detalhes": erros}

        nome = str(payload["nome"]).strip()
        email = str(payload["email"]).strip().lower()
        cpf = str(payload["cpf"]).strip()
        rg = str(payload["rg"]).strip()
        endereco = str(payload["endereco"]).strip()
        instituicao_id = str(payload["instituicaoId"]).strip()
        curso_id = str(payload["cursoId"]).strip()
        nova_senha = str(payload.get("senha") or "").strip()

        if self.catalogo_dao.email_ja_cadastrado(email, ignorar_usuario_id=aluno_id):
            return 409, {"sucesso": False, "erro": "Este e-mail já está em uso por outro usuário."}

        outro_cpf = self.aluno_dao.buscar_por_cpf(cpf)
        if outro_cpf and outro_cpf.id != aluno_id:
            return 409, {"sucesso": False, "erro": "Este CPF já está cadastrado para outro aluno."}

        instituicao = self.catalogo_dao.buscar_instituicao_por_id(instituicao_id)
        if not instituicao:
            return 400, {"sucesso": False, "erro": "Instituição de Ensino pré-cadastrada não encontrada."}

        curso = self.catalogo_dao.buscar_curso_por_id(curso_id)
        if not curso or curso.instituicao_id != instituicao.id:
            return 400, {"sucesso": False, "erro": "O curso selecionado não pertence à instituição informada."}

        existente.nome = nome
        existente.email = email
        existente.cpf = cpf
        existente.rg = rg
        existente.endereco = endereco
        existente.instituicao_id = instituicao_id
        existente.curso_id = curso_id
        if nova_senha:
            existente.hash_senha = gerar_hash_senha(nova_senha)

        atualizado = self.aluno_dao.atualizar(existente)
        return 200, {
            "sucesso": True,
            "mensagem": "Cadastro do aluno atualizado com sucesso.",
            "dados": atualizado.to_dict(),
        }

    def remover(self, aluno_id: str) -> Tuple[int, Dict[str, Any]]:
        removido = self.aluno_dao.remover(aluno_id)
        if not removido:
            return 404, {"sucesso": False, "erro": "Aluno não encontrado para exclusão."}
        return 200, {"sucesso": True, "mensagem": "Aluno e conta de moedas excluídos com sucesso."}

    def _validar_payload(self, payload: Dict[str, Any], edicao: bool = False) -> list[str]:
        erros = []
        campos_obrigatorios = [
            ("nome", "Nome completo"),
            ("email", "E-mail"),
            ("cpf", "CPF"),
            ("rg", "RG"),
            ("endereco", "Endereço"),
            ("instituicaoId", "Instituição de Ensino"),
            ("cursoId", "Curso"),
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

        cpf_digitos = "".join(ch for ch in str(payload.get("cpf") or "") if ch.isdigit())
        if cpf_digitos and len(cpf_digitos) != 11:
            erros.append("O CPF deve conter 11 dígitos numéricos.")

        senha = str(payload.get("senha") or "")
        if (not edicao or senha) and len(senha) < 6:
            erros.append("A senha deve possuir pelo menos 6 caracteres.")

        return erros

