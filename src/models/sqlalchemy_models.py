"""
Mapeamento Objeto-Relacional Declarativo com SQLAlchemy ORM (Lab03S02).
Implementa o modelo completo do sistema utilizando Joined Table Inheritance
(`polymorphic_on` / `polymorphic_identity`) para a hierarquia de `Usuario` e
`Movimentacao`, além de relacionamentos bidirecionais (`relationship`) e
restrições de integridade (`CheckConstraint`, `UniqueConstraint`).
"""

try:
    from sqlalchemy import (
        Boolean,
        CheckConstraint,
        Column,
        DateTime,
        ForeignKey,
        Integer,
        String,
        Text,
        UniqueConstraint,
        func,
    )
    from sqlalchemy.orm import declarative_base, relationship

    Base = declarative_base()

    class InstituicaoEnsinoORM(Base):
        __tablename__ = "instituicoes_ensino"

        id = Column(String(36), primary_key=True)
        nome = Column(String(150), nullable=False, unique=True)
        sigla = Column(String(20), nullable=False)
        criado_em = Column(DateTime, nullable=False, server_default=func.now())

        cursos = relationship("CursoORM", back_populates="instituicao")
        departamentos = relationship("DepartamentoORM", back_populates="instituicao")
        alunos = relationship("AlunoORM", back_populates="instituicao")
        professores = relationship("ProfessorORM", back_populates="instituicao")

    class CursoORM(Base):
        __tablename__ = "cursos"
        __table_args__ = (UniqueConstraint("instituicao_id", "nome", name="uk_curso_instituicao"),)

        id = Column(String(36), primary_key=True)
        instituicao_id = Column(String(36), ForeignKey("instituicoes_ensino.id", ondelete="RESTRICT"), nullable=False)
        nome = Column(String(150), nullable=False)

        instituicao = relationship("InstituicaoEnsinoORM", back_populates="cursos")
        alunos = relationship("AlunoORM", back_populates="curso")

    class DepartamentoORM(Base):
        __tablename__ = "departamentos"
        __table_args__ = (UniqueConstraint("instituicao_id", "nome", name="uk_depto_instituicao"),)

        id = Column(String(36), primary_key=True)
        instituicao_id = Column(String(36), ForeignKey("instituicoes_ensino.id", ondelete="RESTRICT"), nullable=False)
        nome = Column(String(150), nullable=False)

        instituicao = relationship("InstituicaoEnsinoORM", back_populates="departamentos")
        professores = relationship("ProfessorORM", back_populates="departamento")

    class UsuarioORM(Base):
        __tablename__ = "usuarios"

        id = Column(String(36), primary_key=True)
        nome = Column(String(150), nullable=False)
        email = Column(String(150), nullable=False, unique=True)
        hash_senha = Column(String(255), nullable=False)
        tipo_usuario = Column(String(20), nullable=False)
        criado_em = Column(DateTime, nullable=False, server_default=func.now())
        atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

        __mapper_args__ = {
            "polymorphic_on": tipo_usuario,
            "polymorphic_identity": "USUARIO",
        }

    class AlunoORM(UsuarioORM):
        __tablename__ = "alunos"

        usuario_id = Column(String(36), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
        cpf = Column(String(14), nullable=False, unique=True)
        rg = Column(String(20), nullable=False)
        endereco = Column(String(255), nullable=False)
        instituicao_id = Column(String(36), ForeignKey("instituicoes_ensino.id", ondelete="RESTRICT"), nullable=False)
        curso_id = Column(String(36), ForeignKey("cursos.id", ondelete="RESTRICT"), nullable=False)

        instituicao = relationship("InstituicaoEnsinoORM", back_populates="alunos")
        curso = relationship("CursoORM", back_populates="alunos")
        conta = relationship("ContaMoedasORM", uselist=False, foreign_keys="ContaMoedasORM.usuario_id")
        resgates = relationship("ResgateORM", back_populates="aluno")

        __mapper_args__ = {
            "polymorphic_identity": "ALUNO",
        }

    class ProfessorORM(UsuarioORM):
        __tablename__ = "professores"

        usuario_id = Column(String(36), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
        cpf = Column(String(14), nullable=False, unique=True)
        instituicao_id = Column(String(36), ForeignKey("instituicoes_ensino.id", ondelete="RESTRICT"), nullable=False)
        departamento_id = Column(String(36), ForeignKey("departamentos.id", ondelete="RESTRICT"), nullable=False)

        instituicao = relationship("InstituicaoEnsinoORM", back_populates="professores")
        departamento = relationship("DepartamentoORM", back_populates="professores")
        conta = relationship("ContaMoedasORM", uselist=False, foreign_keys="ContaMoedasORM.usuario_id")

        __mapper_args__ = {
            "polymorphic_identity": "PROFESSOR",
        }

    class EmpresaParceiraORM(UsuarioORM):
        __tablename__ = "empresas_parceiras"

        usuario_id = Column(String(36), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
        nome_legal = Column(String(180), nullable=False)
        identificador = Column(String(20), nullable=False, unique=True)
        descricao = Column(Text, nullable=False, default="")

        vantagens = relationship("VantagemORM", back_populates="empresa", cascade="all, delete-orphan")

        __mapper_args__ = {
            "polymorphic_identity": "EMPRESA",
        }

    class ContaMoedasORM(Base):
        __tablename__ = "contas_moedas"
        __table_args__ = (CheckConstraint("saldo_atual >= 0", name="ck_saldo_nao_negativo"),)

        id = Column(String(36), primary_key=True)
        usuario_id = Column(String(36), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True)
        saldo_atual = Column(Integer, nullable=False, default=0)
        atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    class VantagemORM(Base):
        __tablename__ = "vantagens"
        __table_args__ = (CheckConstraint("custo_moedas > 0", name="ck_custo_positivo"),)

        id = Column(String(36), primary_key=True)
        empresa_id = Column(String(36), ForeignKey("empresas_parceiras.usuario_id", ondelete="CASCADE"), nullable=False)
        titulo = Column(String(150), nullable=False)
        descricao = Column(Text, nullable=False)
        fotografia_uri = Column(String(500), nullable=False)
        custo_moedas = Column(Integer, nullable=False)
        dados_oferta = Column(String(255), nullable=False, default="")
        ativa = Column(Boolean, nullable=False, default=True)

        empresa = relationship("EmpresaParceiraORM", back_populates="vantagens")

    class ResgateORM(Base):
        __tablename__ = "resgates"

        id = Column(String(36), primary_key=True)
        aluno_id = Column(String(36), ForeignKey("alunos.usuario_id", ondelete="RESTRICT"), nullable=False)
        vantagem_id = Column(String(36), ForeignKey("vantagens.id", ondelete="RESTRICT"), nullable=False)
        debito_movimentacao_id = Column(String(36), ForeignKey("debitos_resgate.movimentacao_id"), nullable=False, unique=True)
        instante = Column(DateTime, nullable=False, server_default=func.now())
        custo_aplicado = Column(Integer, nullable=False)
        status = Column(String(20), nullable=False, default="CONFIRMADO")

        aluno = relationship("AlunoORM", back_populates="resgates")

    SQLALCHEMY_AVAILABLE = True

except ImportError:
    SQLALCHEMY_AVAILABLE = False

