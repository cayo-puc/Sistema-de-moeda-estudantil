"""
Camada de Modelo e Mapeamento Objeto-Relacional (ORM) — Lab03S02.
Alinhada estritamente ao Diagrama de Classes (diagrama-classes.puml) e ao Modelo ER (modelo-er.puml).

Estratégia de Mapeamento de Herança:
- Joined Table Inheritance (Herança por Tabelas Juntadas):
  A classe abstrata `Usuario` mapeia para a tabela `usuarios`, enquanto as subclasses
  `Aluno`, `Professor` e `EmpresaParceira` mapeiam para `alunos`, `professores` e
  `empresas_parceiras`, compartilhando a chave primária/estrangeira (`usuario_id` -> `usuarios.id`).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid

from src.config.database import verificar_senha


class TipoMovimentacao(str, Enum):
    CREDITO_SEMESTRAL = "CREDITO_SEMESTRAL"
    TRANSFERENCIA = "TRANSFERENCIA"
    DEBITO_RESGATE = "DEBITO_RESGATE"


class StatusResgate(str, Enum):
    CONFIRMADO = "CONFIRMADO"


class ResultadoAutenticacao(str, Enum):
    ACEITO = "ACEITO"
    RECUSADO = "RECUSADO"


class TipoUsuario(str, Enum):
    ALUNO = "ALUNO"
    PROFESSOR = "PROFESSOR"
    EMPRESA = "EMPRESA"


def gerar_uuid() -> str:
    return str(uuid.uuid4())


def instante_atual_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# Metadados de Mapeamento Objeto-Relacional (ORM Metadata Descriptors)
# =============================================================================
@dataclass(frozen=True)
class ORMColumn:
    column_name: str
    sql_type: str
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    nullable: bool = False


def orm_table(table_name: str, inheritance: str = "NONE"):
    """Decorator de classe que registra o mapeamento Objeto-Relacional (ORM) da entidade."""
    def decorator(cls):
        cls.__tablename__ = table_name
        cls.__inheritance__ = inheritance
        return cls
    return decorator


# =============================================================================
# Entidades Acadêmicas Pré-Cadastradas
# =============================================================================
@orm_table("instituicoes_ensino")
@dataclass
class InstituicaoEnsino:
    id: str = field(default_factory=gerar_uuid)
    nome: str = ""
    sigla: str = ""
    criado_em: str = field(default_factory=instante_atual_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "sigla": self.sigla,
            "criadoEm": self.criado_em,
        }


@orm_table("cursos")
@dataclass
class Curso:
    id: str = field(default_factory=gerar_uuid)
    instituicao_id: str = ""
    nome: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "instituicaoId": self.instituicao_id,
            "nome": self.nome,
        }


@orm_table("departamentos")
@dataclass
class Departamento:
    id: str = field(default_factory=gerar_uuid)
    instituicao_id: str = ""
    nome: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "instituicaoId": self.instituicao_id,
            "nome": self.nome,
        }


# =============================================================================
# Conta de Moedas (Composição 1..1 com Aluno e Professor)
# =============================================================================
@orm_table("contas_moedas")
@dataclass
class ContaMoedas:
    id: str = field(default_factory=gerar_uuid)
    usuario_id: str = ""
    saldo_atual: int = 0
    atualizado_em: str = field(default_factory=instante_atual_iso)

    def consultar_saldo(self) -> int:
        return self.saldo_atual

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "usuarioId": self.usuario_id,
            "saldoAtual": self.saldo_atual,
            "atualizadoEm": self.atualizado_em,
        }


# =============================================================================
# Hierarquia de Usuário (Joined Table Inheritance)
# =============================================================================
@orm_table("usuarios", inheritance="JOINED_BASE")
@dataclass
class Usuario:
    id: str = field(default_factory=gerar_uuid)
    nome: str = ""
    email: str = ""
    hash_senha: str = ""
    tipo_usuario: str = TipoUsuario.ALUNO.value
    criado_em: str = field(default_factory=instante_atual_iso)
    atualizado_em: str = field(default_factory=instante_atual_iso)

    def autenticar(self, senha_plana: str) -> ResultadoAutenticacao:
        if verificar_senha(senha_plana, self.hash_senha):
            return ResultadoAutenticacao.ACEITO
        return ResultadoAutenticacao.RECUSADO


@orm_table("alunos", inheritance="JOINED_CHILD")
@dataclass
class Aluno(Usuario):
    cpf: str = ""
    rg: str = ""
    endereco: str = ""
    instituicao_id: str = ""
    curso_id: str = ""
    # Relacionamentos carregados via Eager/Join no DAO (ORM Hydration)
    instituicao_nome: Optional[str] = None
    instituicao_sigla: Optional[str] = None
    curso_nome: Optional[str] = None
    conta: Optional[ContaMoedas] = None

    def __post_init__(self):
        self.tipo_usuario = TipoUsuario.ALUNO.value

    @classmethod
    def from_row(cls, row: Any) -> "Aluno":
        keys = row.keys()
        conta = None
        if "conta_id" in keys and row["conta_id"]:
            conta = ContaMoedas(
                id=row["conta_id"],
                usuario_id=row["id"],
                saldo_atual=row["saldo_atual"] if "saldo_atual" in keys and row["saldo_atual"] is not None else 0,
            )
        return cls(
            id=row["id"],
            nome=row["nome"],
            email=row["email"],
            hash_senha=row["hash_senha"],
            tipo_usuario=row["tipo_usuario"],
            criado_em=row["criado_em"],
            atualizado_em=row["atualizado_em"],
            cpf=row["cpf"],
            rg=row["rg"],
            endereco=row["endereco"],
            instituicao_id=row["instituicao_id"],
            curso_id=row["curso_id"],
            instituicao_nome=row["instituicao_nome"] if "instituicao_nome" in keys else None,
            instituicao_sigla=row["instituicao_sigla"] if "instituicao_sigla" in keys else None,
            curso_nome=row["curso_nome"] if "curso_nome" in keys else None,
            conta=conta,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipoUsuario": self.tipo_usuario,
            "cpf": self.cpf,
            "rg": self.rg,
            "endereco": self.endereco,
            "instituicaoId": self.instituicao_id,
            "instituicaoNome": self.instituicao_nome,
            "instituicaoSigla": self.instituicao_sigla,
            "cursoId": self.curso_id,
            "cursoNome": self.curso_nome,
            "saldoMoedas": self.conta.consultar_saldo() if self.conta else 0,
            "contaId": self.conta.id if self.conta else None,
            "criadoEm": self.criado_em,
            "atualizadoEm": self.atualizado_em,
        }


@orm_table("empresas_parceiras", inheritance="JOINED_CHILD")
@dataclass
class EmpresaParceira(Usuario):
    nome_legal: str = ""
    identificador: str = ""
    descricao: str = ""
    total_vantagens: int = 0

    def __post_init__(self):
        self.tipo_usuario = TipoUsuario.EMPRESA.value

    @classmethod
    def from_row(cls, row: Any) -> "EmpresaParceira":
        keys = row.keys()
        return cls(
            id=row["id"],
            nome=row["nome"],
            email=row["email"],
            hash_senha=row["hash_senha"],
            tipo_usuario=row["tipo_usuario"],
            criado_em=row["criado_em"],
            atualizado_em=row["atualizado_em"],
            nome_legal=row["nome_legal"],
            identificador=row["identificador"],
            descricao=row["descricao"] if "descricao" in keys and row["descricao"] else "",
            total_vantagens=row["total_vantagens"] if "total_vantagens" in keys and row["total_vantagens"] else 0,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "nomeLegal": self.nome_legal,
            "identificador": self.identificador,
            "email": self.email,
            "descricao": self.descricao,
            "tipoUsuario": self.tipo_usuario,
            "totalVantagens": self.total_vantagens,
            "criadoEm": self.criado_em,
            "atualizadoEm": self.atualizado_em,
        }

