-- =============================================================================
-- SISTEMA DE MOEDA ESTUDANTIL — SCRIPT DDL E SEED INICIAL (Lab03S02)
-- Banco de Dados Relacional (Compatível com SQLite 3 / PostgreSQL)
-- Estratégia de Herança: Joined Table Inheritance (Tabelas Especializadas)
-- =============================================================================

PRAGMA foreign_keys = ON;

-- 1. Estrutura Acadêmica Pré-Cadastrada
CREATE TABLE IF NOT EXISTS instituicoes_ensino (
    id VARCHAR(36) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    sigla VARCHAR(20) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cursos (
    id VARCHAR(36) PRIMARY KEY,
    instituicao_id VARCHAR(36) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    CONSTRAINT fk_curso_instituicao
        FOREIGN KEY (instituicao_id) REFERENCES instituicoes_ensino (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uk_curso_instituicao UNIQUE (instituicao_id, nome)
);

CREATE TABLE IF NOT EXISTS departamentos (
    id VARCHAR(36) PRIMARY KEY,
    instituicao_id VARCHAR(36) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    CONSTRAINT fk_depto_instituicao
        FOREIGN KEY (instituicao_id) REFERENCES instituicoes_ensino (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uk_depto_instituicao UNIQUE (instituicao_id, nome)
);

-- 2. Hierarquia de Usuários (Joined Table Inheritance: usuarios -> alunos / professores / empresas_parceiras)
CREATE TABLE IF NOT EXISTS usuarios (
    id VARCHAR(36) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    hash_senha VARCHAR(255) NOT NULL,
    tipo_usuario VARCHAR(20) NOT NULL CHECK (tipo_usuario IN ('ALUNO', 'PROFESSOR', 'EMPRESA')),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alunos (
    usuario_id VARCHAR(36) PRIMARY KEY,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    rg VARCHAR(20) NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    instituicao_id VARCHAR(36) NOT NULL,
    curso_id VARCHAR(36) NOT NULL,
    CONSTRAINT fk_aluno_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_aluno_instituicao
        FOREIGN KEY (instituicao_id) REFERENCES instituicoes_ensino (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_aluno_curso
        FOREIGN KEY (curso_id) REFERENCES cursos (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS professores (
    usuario_id VARCHAR(36) PRIMARY KEY,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    instituicao_id VARCHAR(36) NOT NULL,
    departamento_id VARCHAR(36) NOT NULL,
    CONSTRAINT fk_professor_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_professor_instituicao
        FOREIGN KEY (instituicao_id) REFERENCES instituicoes_ensino (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_professor_departamento
        FOREIGN KEY (departamento_id) REFERENCES departamentos (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS empresas_parceiras (
    usuario_id VARCHAR(36) PRIMARY KEY,
    nome_legal VARCHAR(180) NOT NULL,
    identificador VARCHAR(20) NOT NULL UNIQUE, -- CNPJ ou identificador fiscal
    descricao TEXT DEFAULT '',
    CONSTRAINT fk_empresa_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. Conta de Moedas e Movimentações Financeiras/Mérito
CREATE TABLE IF NOT EXISTS contas_moedas (
    id VARCHAR(36) PRIMARY KEY,
    usuario_id VARCHAR(36) NOT NULL UNIQUE,
    saldo_atual INTEGER NOT NULL DEFAULT 0 CHECK (saldo_atual >= 0),
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conta_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS movimentacoes (
    id VARCHAR(36) PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('CREDITO_SEMESTRAL', 'TRANSFERENCIA', 'DEBITO_RESGATE')),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    instante TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transferencias (
    movimentacao_id VARCHAR(36) PRIMARY KEY,
    conta_origem_id VARCHAR(36) NOT NULL,
    conta_destino_id VARCHAR(36) NOT NULL,
    motivo TEXT NOT NULL CHECK (length(trim(motivo)) > 0),
    CONSTRAINT fk_transf_mov
        FOREIGN KEY (movimentacao_id) REFERENCES movimentacoes (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_transf_origem
        FOREIGN KEY (conta_origem_id) REFERENCES contas_moedas (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_transf_destino
        FOREIGN KEY (conta_destino_id) REFERENCES contas_moedas (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS creditos_semestrais (
    movimentacao_id VARCHAR(36) PRIMARY KEY,
    conta_destino_id VARCHAR(36) NOT NULL,
    professor_id VARCHAR(36) NOT NULL,
    periodo VARCHAR(10) NOT NULL,
    quantidade_creditada INTEGER NOT NULL DEFAULT 1000 CHECK (quantidade_creditada = 1000),
    CONSTRAINT fk_cred_mov
        FOREIGN KEY (movimentacao_id) REFERENCES movimentacoes (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_cred_conta
        FOREIGN KEY (conta_destino_id) REFERENCES contas_moedas (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_cred_prof
        FOREIGN KEY (professor_id) REFERENCES professores (usuario_id)
        ON DELETE RESTRICT,
    CONSTRAINT uk_credito_professor_periodo UNIQUE (professor_id, periodo)
);

CREATE TABLE IF NOT EXISTS debitos_resgate (
    movimentacao_id VARCHAR(36) PRIMARY KEY,
    conta_origem_id VARCHAR(36) NOT NULL,
    CONSTRAINT fk_deb_mov
        FOREIGN KEY (movimentacao_id) REFERENCES movimentacoes (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_deb_conta
        FOREIGN KEY (conta_origem_id) REFERENCES contas_moedas (id)
        ON DELETE RESTRICT
);

-- 4. Catálogo de Vantagens, Resgates e Cupons
CREATE TABLE IF NOT EXISTS vantagens (
    id VARCHAR(36) PRIMARY KEY,
    empresa_id VARCHAR(36) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT NOT NULL,
    fotografia_uri VARCHAR(500) NOT NULL,
    custo_moedas INTEGER NOT NULL CHECK (custo_moedas > 0),
    dados_oferta VARCHAR(255) NOT NULL DEFAULT '',
    ativa BOOLEAN NOT NULL DEFAULT 1,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vantagem_empresa
        FOREIGN KEY (empresa_id) REFERENCES empresas_parceiras (usuario_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS resgates (
    id VARCHAR(36) PRIMARY KEY,
    aluno_id VARCHAR(36) NOT NULL,
    vantagem_id VARCHAR(36) NOT NULL,
    debito_movimentacao_id VARCHAR(36) NOT NULL UNIQUE,
    instante TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    custo_aplicado INTEGER NOT NULL CHECK (custo_aplicado > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMADO' CHECK (status IN ('CONFIRMADO')),
    CONSTRAINT fk_resgate_aluno
        FOREIGN KEY (aluno_id) REFERENCES alunos (usuario_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_resgate_vantagem
        FOREIGN KEY (vantagem_id) REFERENCES vantagens (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_resgate_debito
        FOREIGN KEY (debito_movimentacao_id) REFERENCES debitos_resgate (movimentacao_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS cupons (
    id VARCHAR(36) PRIMARY KEY,
    resgate_id VARCHAR(36) NOT NULL UNIQUE,
    codigo_conferencia VARCHAR(40) NOT NULL UNIQUE,
    instante_geracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cupom_resgate
        FOREIGN KEY (resgate_id) REFERENCES resgates (id)
        ON DELETE CASCADE
);

-- 5. Registro de Notificações por E-mail (Auditoria e Caixa de Saída)
CREATE TABLE IF NOT EXISTS notificacoes_email (
    id VARCHAR(36) PRIMARY KEY,
    destinatario_email VARCHAR(150) NOT NULL,
    destinatario_nome VARCHAR(150) NOT NULL DEFAULT '',
    assunto VARCHAR(200) NOT NULL,
    corpo TEXT NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    referencia_id VARCHAR(36),
    enviado_smtp BOOLEAN NOT NULL DEFAULT 0,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Otimização de Consultas nos DAOs
CREATE INDEX IF NOT EXISTS idx_alunos_instituicao ON alunos (instituicao_id);
CREATE INDEX IF NOT EXISTS idx_alunos_curso ON alunos (curso_id);
CREATE INDEX IF NOT EXISTS idx_vantagens_empresa ON vantagens (empresa_id);
CREATE INDEX IF NOT EXISTS idx_resgates_aluno ON resgates (aluno_id);
CREATE INDEX IF NOT EXISTS idx_notificacoes_email_dest ON notificacoes_email (destinatario_email);

