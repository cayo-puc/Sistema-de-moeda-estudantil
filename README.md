# Sistema de Moeda Estudantil — PUC Minas (Laboratório de Desenvolvimento de Software)

Sistema web desenvolvido em arquitetura **MVC (Model-View-Controller)** para estimular o reconhecimento do mérito estudantil através de uma moeda virtual distribuída por professores e trocada por produtos e descontos em empresas parceiras.

---

## 📦 Entregas por Sprint

### Sprint 01 (`Lab03S01`) — Modelagem do Sistema
- **Diagrama de Casos de Uso:** [casos-de-uso.puml](casos-de-uso.puml) | [casos-de-uso.svg](casos-de-uso.svg)
- **Diagrama de Classes de Domínio:** [diagrama-classes.puml](diagrama-classes.puml) | [diagrama-classes.svg](diagrama-classes.svg)
- **Diagrama de Componentes (Arquitetura Lógica MVC):** [diagrama-componentes.puml](diagrama-componentes.puml) | [diagrama-componentes.svg](diagrama-componentes.svg)
- **Histórias do Usuário (`HU-01` a `HU-11`):** [historias-usuario.md](historias-usuario.md)
- **PDFs Consolidados da Sprint 01:**
  - [diagramas-sprint1.pdf](diagramas-sprint1.pdf) *(3 páginas com os diagramas UML)*
  - [entrega-sprint1-completa.pdf](entrega-sprint1-completa.pdf) *(5 páginas com os 3 diagramas + Histórias de Usuário)*

### Sprint 02 (`Lab03S02`) — Modelo ER, Persistência (ORM/DAO) e CRUDs Iniciais
- **Modelo Entidade-Relacionamento (MER):** [modelo-er.puml](modelo-er.puml) | [modelo-er.svg](modelo-er.svg) | [modelo-er-sprint2.pdf](modelo-er-sprint2.pdf)
- **Script DDL Relacional e Seed Inicial:** [database/schema.sql](database/schema.sql)
- **Documentação da Estratégia ORM & Padrão DAO:** [estrategia-persistencia-e-mer.md](estrategia-persistencia-e-mer.md)
- **Camada de Persistência e Domínio (ORM + Padrão DAO):**
  - Gerenciador de Conexão e Transações (*Unit of Work*): [src/config/database.py](src/config/database.py)
  - Entidades Mapeadas (*Joined Table Inheritance*): [src/models/entities.py](src/models/entities.py) e [src/models/sqlalchemy_models.py](src/models/sqlalchemy_models.py)
  - Objetos de Acesso a Dados (Padrão DAO): [src/dao/base_dao.py](src/dao/base_dao.py), [src/dao/aluno_dao.py](src/dao/aluno_dao.py), [src/dao/empresa_dao.py](src/dao/empresa_dao.py), [src/dao/catalogo_dao.py](src/dao/catalogo_dao.py)
- **Controladores MVC (Back-end):** [src/controllers/aluno_controller.py](src/controllers/aluno_controller.py) e [src/controllers/empresa_controller.py](src/controllers/empresa_controller.py)
- **Front-end Web (View MVC — CRUDs de Aluno e Empresa Parceira):** [src/views/index.html](src/views/index.html), [src/views/styles.css](src/views/styles.css), [src/views/app.js](src/views/app.js)

---

## 🚀 Como Executar o Sistema (Front-end + Back-end + SQLite)

Não é necessária nenhuma configuração externa de banco de dados — ao iniciar o servidor, o banco relacional SQLite (`database/moeda_estudantil.db`) é criado e populado automaticamente com as Instituições de Ensino e Cursos pré-cadastrados:

```bash
python3 app.py
```

Em seguida, acesse no navegador:
👉 **http://localhost:8000**

## 🧪 Como Executar os Testes Automatizados

```bash
python3 -m unittest discover -s tests -v
```
