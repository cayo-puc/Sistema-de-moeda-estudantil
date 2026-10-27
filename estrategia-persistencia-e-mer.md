# Modelo ER e Estratégia de Acesso ao Banco de Dados — Lab03S02

## 1. Visão Geral da Arquitetura de Persistência

Para atender aos requisitos da **Sprint 2 (`Lab03S02`)** e manter o alinhamento estrito com os diagramas UML da **Sprint 1 (`Lab03S01`)**, a camada de persistência do **Sistema de Moeda Estudantil** foi projetada combinando:

1. **Modelo Entidade-Relacionamento (MER / DER)** normalizado na **3ª Forma Normal (3FN)**, definido formalmente em [modelo-er.puml](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/modelo-er.puml), renderizado em [modelo-er.svg](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/modelo-er.svg) e implementado em [database/schema.sql](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/database/schema.sql).
2. **Mapeamento Objeto-Relacional (ORM)** baseado na estratégia **Joined Table Inheritance** (*Herança por Tabelas Juntadas*), documentado em [src/models/entities.py](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/models/entities.py) e [src/models/sqlalchemy_models.py](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/models/sqlalchemy_models.py).
3. **Padrão DAO (Data Access Object)** parametrizado pela interface abstrata [`GenericDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/base_dao.py) e concretizado por [`AlunoDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/aluno_dao.py), [`EmpresaParceiraDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/empresa_dao.py) e [`CatalogoDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/catalogo_dao.py).
4. **Gerenciamento Transacional (Unit of Work)** em [`DatabaseManager`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/config/database.py), garantindo atomicidade (`COMMIT` / `ROLLBACK`) e integridade referencial (`PRAGMA foreign_keys = ON`).

---

## 2. Decisões de Mapeamento Objeto-Relacional (ORM)

### 2.1 Mapeamento de Herança (`Usuario` → `Aluno`, `Professor`, `EmpresaParceira`)
No Diagrama de Classes de Domínio, `Usuario` é uma classe abstrata especializada por `Aluno`, `Professor` e `EmpresaParceira`. No banco de dados relacional, adotou-se a estratégia **Joined Table Inheritance**:
- A tabela-pai `usuarios` concentra `id (PK)`, `nome`, `email (UNIQUE)`, `hash_senha`, `tipo_usuario` (`ALUNO`, `PROFESSOR`, `EMPRESA`), `criado_em` e `atualizado_em`.
- As tabelas-filhas `alunos`, `professores` e `empresas_parceiras` utilizam `usuario_id` simultaneamente como **Chave Primária (`PK`)** e **Chave Estrangeira (`FK`)** referenciando `usuarios(id)` com `ON DELETE CASCADE`.
- **Vantagens:** Elimina colunas nulas desnecessárias (*Single Table Inheritance*), preserva constraints `NOT NULL` e `UNIQUE` específicas de cada perfil (ex.: `cpf` e `rg` para aluno; `nome_legal` e `identificador`/CNPJ para empresa parceira) e garante polimorfismo na autenticação (`UC3`).

### 2.2 Mapeamento de Composição (`ContaMoedas` e `Movimentacao`)
- Cada `Aluno` e cada `Professor` possui exatamente uma `ContaMoedas` (`contas_moedas.usuario_id UNIQUE NOT NULL`), criada na mesma transação do cadastro do titular com `CHECK (saldo_atual >= 0)`.
- A hierarquia abstrata `Movimentacao` (`movimentacoes`) também utiliza **Joined Table Inheritance** com as tabelas especializadas `transferencias`, `creditos_semestrais` (`UNIQUE (professor_id, periodo)`) e `debitos_resgate`.

---

## 3. Implementação do Padrão DAO (Data Access Object)

| Classe / Arquivo | Responsabilidade na Camada de Persistência |
| :--- | :--- |
| [`GenericDAO[T]`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/base_dao.py) | Define o contrato padrão (`criar`, `buscar_por_id`, `listar_todos`, `atualizar`, `remover`), desacoplando os Controladores MVC do mecanismo de banco de dados. |
| [`AlunoDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/aluno_dao.py) | Realiza o CRUD transacional de `Aluno` (inserindo/atualizando em `usuarios`, `alunos` e inicializando `contas_moedas`), além de hidratar o objeto `Aluno` com `InstituicaoEnsino`, `Curso` e `ContaMoedas` via `JOIN`. |
| [`EmpresaParceiraDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/empresa_dao.py) | Realiza o CRUD transacional de `EmpresaParceira` (`usuarios` + `empresas_parceiras`) e contabiliza vantagens vinculadas. |
| [`CatalogoDAO`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/dao/catalogo_dao.py) | Consulta as `InstituicaoEnsino` e `Curso` pré-cadastrados para seleção no formulário do aluno (`HU-01`) e verifica unicidade de e-mail entre perfis. |

---

## 4. Endpoints REST e Comunicação Front-end ↔ Back-end

A camada **View** ([src/views/index.html](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/views/index.html) e [src/views/app.js](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/views/app.js)) consome a API REST JSON provida pelos controladores MVC ([`AlunoController`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/controllers/aluno_controller.py) e [`EmpresaParceiraController`](file:///home/pedroqueiroz/dev/Faculdade/LDS/Sistema-de-moeda-estudantil/src/controllers/empresa_controller.py)):

- `GET /api/instituicoes` — Lista as instituições de ensino pré-cadastradas.
- `GET /api/cursos?instituicaoId=<id>` — Lista os cursos vinculados à instituição selecionada.
- `GET /api/alunos` — Lista todos os alunos cadastrados com saldo de moedas e dados acadêmicos.
- `POST /api/alunos` — Cadastra um novo aluno e inicializa sua conta de moedas (`201 Created`).
- `GET /api/alunos/<id>` — Consulta os dados detalhados de um aluno específico.
- `PUT /api/alunos/<id>` — Atualiza dados pessoais, acadêmicos e/ou credenciais do aluno.
- `DELETE /api/alunos/<id>` — Remove o aluno e sua conta de moedas em cascata.
- `GET /api/empresas` — Lista todas as empresas parceiras cadastradas.
- `POST /api/empresas` — Cadastra uma nova empresa parceira (`201 Created`).
- `GET /api/empresas/<id>` — Consulta os dados de uma empresa parceira específica.
- `PUT /api/empresas/<id>` — Atualiza dados cadastrais e/ou credenciais da empresa parceira.
- `DELETE /api/empresas/<id>` — Remove a empresa parceira.

