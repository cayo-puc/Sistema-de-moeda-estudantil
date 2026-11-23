"""
Camada de Configuração e Gerenciamento de Conexão ao Banco de Dados (Lab03S02).
Implementa o padrão Unit of Work / Session Manager sobre SQLite3 com suporte a
DDL automático e carga inicial (seed) das Instituições de Ensino, Cursos e Professores
pré-cadastrados conforme exigido na especificação do sistema.
"""

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "database", "moeda_estudantil.db")
SCHEMA_SQL_PATH = os.path.join(BASE_DIR, "database", "schema.sql")


def gerar_hash_senha(senha_plana: str) -> str:
    """Gera hash seguro PBKDF2-HMAC-SHA256 com salt aleatório (RF04 / HU-05)."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha_plana.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"pbkdf2_sha256$100000${salt}${dk.hex()}"


def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    """Verifica uma senha em texto plano contra o hash PBKDF2 armazenado."""
    try:
        alg, iteracoes, salt, hash_hex = hash_armazenado.split("$")
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            senha_plana.encode("utf-8"),
            salt.encode("utf-8"),
            int(iteracoes),
        )
        return secrets.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


class DatabaseManager:
    """Gerenciador de conexões e transações do Banco de Dados (Singleton/Factory)."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self):
        """Context manager de transação atômica (Unit of Work): faz commit ao final ou rollback em erro."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self):
        """Executa o script DDL schema.sql e popula dados pré-cadastrados caso o banco esteja vazio."""
        with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
            ddl_script = f.read()

        with self.transaction() as conn:
            conn.executescript(ddl_script)
            # Reativa foreign_keys após executescript
            conn.execute("PRAGMA foreign_keys = ON;")
            self._seed_initial_data(conn)

    def _seed_initial_data(self, conn: sqlite3.Connection):
        """
        Popula as Instituições de Ensino, Cursos e Professores pré-cadastrados
        (Requisito: 'As instituições participantes já estão pré-cadastradas no sistema,
        para que o aluno selecione. Os professores já estarão pré-cadastrados no sistema').
        """
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM instituicoes_ensino")
        if cur.fetchone()["total"] > 0:
            return

        agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        instituicoes = [
            ("inst-pucminas-01", "Pontifícia Universidade Católica de Minas Gerais", "PUC Minas", agora),
            ("inst-ufmg-02", "Universidade Federal de Minas Gerais", "UFMG", agora),
            ("inst-cefetmg-03", "Centro Federal de Educação Tecnológica de Minas Gerais", "CEFET-MG", agora),
        ]
        cur.executemany(
            "INSERT INTO instituicoes_ensino (id, nome, sigla, criado_em) VALUES (?, ?, ?, ?)",
            instituicoes,
        )

        cursos = [
            ("curso-puc-es", "inst-pucminas-01", "Engenharia de Software"),
            ("curso-puc-cc", "inst-pucminas-01", "Ciência da Computação"),
            ("curso-puc-si", "inst-pucminas-01", "Sistemas de Informação"),
            ("curso-puc-ec", "inst-pucminas-01", "Engenharia de Computação"),
            ("curso-ufmg-cc", "inst-ufmg-02", "Ciência da Computação"),
            ("curso-ufmg-si", "inst-ufmg-02", "Sistemas de Informação"),
            ("curso-ufmg-es", "inst-ufmg-02", "Engenharia de Sistemas"),
            ("curso-cefet-ec", "inst-cefetmg-03", "Engenharia de Computação"),
            ("curso-cefet-si", "inst-cefetmg-03", "Sistemas de Informação"),
        ]
        cur.executemany(
            "INSERT INTO cursos (id, instituicao_id, nome) VALUES (?, ?, ?)",
            cursos,
        )

        departamentos = [
            ("depto-puc-es", "inst-pucminas-01", "Departamento de Engenharia de Software e Computação"),
            ("depto-ufmg-dcc", "inst-ufmg-02", "Departamento de Ciência da Computação (DCC)"),
            ("depto-cefet-decom", "inst-cefetmg-03", "Departamento de Computação (DECOM)"),
        ]
        cur.executemany(
            "INSERT INTO departamentos (id, instituicao_id, nome) VALUES (?, ?, ?)",
            departamentos,
        )

        # Professores pré-cadastrados (enviados na parceria da instituição)
        hash_padrao = gerar_hash_senha("Prof@2026")
        cur.execute(
            """
            INSERT INTO usuarios (id, nome, email, hash_senha, tipo_usuario, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 'PROFESSOR', ?, ?)
            """,
            ("prof-milena-01", "Profa. Milena Menezes Adão", "milena.adao@pucminas.br", hash_padrao, agora, agora),
        )
        cur.execute(
            """
            INSERT INTO professores (usuario_id, cpf, instituicao_id, departamento_id)
            VALUES (?, ?, ?, ?)
            """,
            ("prof-milena-01", "111.222.333-44", "inst-pucminas-01", "depto-puc-es"),
        )
        cur.execute(
            """
            INSERT INTO contas_moedas (id, usuario_id, saldo_atual, atualizado_em)
            VALUES (?, ?, 1000, ?)
            """,
            ("conta-prof-milena", "prof-milena-01", agora),
        )

        # Dados iniciais de demonstração para Aluno e Empresa Parceira
        hash_aluno = gerar_hash_senha("Aluno@2026")
        cur.execute(
            """
            INSERT INTO usuarios (id, nome, email, hash_senha, tipo_usuario, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 'ALUNO', ?, ?)
            """,
            ("aluno-demo-01", "Pedro Queiroz", "pedro.queiroz@sga.pucminas.br", hash_aluno, agora, agora),
        )
        cur.execute(
            """
            INSERT INTO alunos (usuario_id, cpf, rg, endereco, instituicao_id, curso_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "aluno-demo-01",
                "123.456.789-00",
                "MG-18.234.567",
                "Av. Dom José Gaspar, 500 - Coração Eucarístico, Belo Horizonte - MG",
                "inst-pucminas-01",
                "curso-puc-es",
            ),
        )
        cur.execute(
            """
            INSERT INTO contas_moedas (id, usuario_id, saldo_atual, atualizado_em)
            VALUES (?, ?, 250, ?)
            """,
            ("conta-aluno-demo-01", "aluno-demo-01", agora),
        )

        hash_empresa = gerar_hash_senha("Parceiro@2026")
        cur.execute(
            """
            INSERT INTO usuarios (id, nome, email, hash_senha, tipo_usuario, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 'EMPRESA', ?, ?)
            """,
            ("empresa-demo-01", "Livraria & Café Universitário", "contato@livrariauniversitaria.com.br", hash_empresa, agora, agora),
        )
        cur.execute(
            """
            INSERT INTO empresas_parceiras (usuario_id, nome_legal, identificador, descricao)
            VALUES (?, ?, ?, ?)
            """,
            (
                "empresa-demo-01",
                "Livraria e Cafeteria Acadêmica LTDA",
                "12.345.678/0001-90",
                "Descontos em livros técnicos de Engenharia de Software, materiais acadêmicos e cafeteria no campus.",
            ),
        )

        # Segundo professor pré-cadastrado (UFMG)
        cur.execute(
            """
            INSERT INTO usuarios (id, nome, email, hash_senha, tipo_usuario, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 'PROFESSOR', ?, ?)
            """,
            ("prof-carlos-02", "Prof. Carlos Eduardo Silva", "carlos.silva@dcc.ufmg.br", hash_padrao, agora, agora),
        )
        cur.execute(
            """
            INSERT INTO professores (usuario_id, cpf, instituicao_id, departamento_id)
            VALUES (?, ?, ?, ?)
            """,
            ("prof-carlos-02", "222.333.444-55", "inst-ufmg-02", "depto-ufmg-dcc"),
        )
        cur.execute(
            """
            INSERT INTO contas_moedas (id, usuario_id, saldo_atual, atualizado_em)
            VALUES (?, ?, 1000, ?)
            """,
            ("conta-prof-carlos", "prof-carlos-02", agora),
        )

        # Vantagens iniciais de demonstração
        vantagens_demo = [
            (
                "vant-livro-01",
                "empresa-demo-01",
                "Desconto de 25% em Livros Técnicos",
                "Válido para qualquer livro de Engenharia de Software, Arquitetura ou Algoritmos na loja física do campus.",
                "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
                120,
                "Cupom presencial - 25% OFF em livros técnicos",
                1,
                agora,
            ),
            (
                "vant-cafe-02",
                "empresa-demo-01",
                "Combo Café Especial + Pão de Queijo",
                "Um espresso duplo ou cappuccino artesanal acompanhado de pão de queijo mineiro quentinho.",
                "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=600&q=80",
                45,
                "Retirada no balcão da cafeteria universitária",
                1,
                agora,
            ),
            (
                "vant-kit-03",
                "empresa-demo-01",
                "Kit Caderno Universitário + Canetas",
                "Caderno capa dura 10 matérias exclusivo PUC Minas + conjunto de 3 canetas esferográficas.",
                "https://images.unsplash.com/photo-1456735190827-d1262f71b8a3?auto=format&fit=crop&w=600&q=80",
                80,
                "Retirada na papelaria parceira",
                1,
                agora,
            ),
        ]
        cur.executemany(
            """
            INSERT INTO vantagens (id, empresa_id, titulo, descricao, fotografia_uri, custo_moedas, dados_oferta, ativa, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            vantagens_demo,
        )

