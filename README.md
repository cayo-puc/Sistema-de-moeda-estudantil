# Sistema de Moeda Estudantil — PUC Minas (Laboratório de Desenvolvimento de Software)

Sistema web desenvolvido em arquitetura **MVC (Model-View-Controller)** para estimular o reconhecimento do mérito estudantil através de uma moeda virtual distribuída por professores e trocada por produtos e descontos em empresas parceiras.

---

## 📦 Entregas por Sprint

### Release 01 (`Lab03S01` a `Lab03S03`)
- **Lab03S01 — Modelagem do Sistema:**
  - Diagrama de Casos de Uso: [casos-de-uso.puml](casos-de-uso.puml) | [casos-de-uso.svg](casos-de-uso.svg)
  - Diagrama de Classes de Domínio: [diagrama-classes.puml](diagrama-classes.puml) | [diagrama-classes.svg](diagrama-classes.svg)
  - Diagrama de Componentes (Arquitetura Lógica MVC): [diagrama-componentes.puml](diagrama-componentes.puml) | [diagrama-componentes.svg](diagrama-componentes.svg)
  - Histórias do Usuário (`HU-01` a `HU-11`): [historias-usuario.md](historias-usuario.md)
  - PDFs Consolidados: [diagramas-sprint1.pdf](diagramas-sprint1.pdf) | [entrega-sprint1-completa.pdf](entrega-sprint1-completa.pdf)
- **Lab03S02 & Lab03S03 — Modelo ER, Persistência (ORM/DAO) e CRUDs:**
  - Modelo Entidade-Relacionamento (MER): [modelo-er.puml](modelo-er.puml) | [modelo-er.svg](modelo-er.svg) | [modelo-er-sprint2.pdf](modelo-er-sprint2.pdf)
  - Script DDL Relacional e Seed Inicial: [database/schema.sql](database/schema.sql)
  - Estratégia ORM & Padrão DAO: [estrategia-persistencia-e-mer.md](estrategia-persistencia-e-mer.md)
  - Persistência & DAOs: [src/config/database.py](src/config/database.py), [src/models/entities.py](src/models/entities.py), [src/models/sqlalchemy_models.py](src/models/sqlalchemy_models.py), [src/dao/base_dao.py](src/dao/base_dao.py), [src/dao/aluno_dao.py](src/dao/aluno_dao.py), [src/dao/empresa_dao.py](src/dao/empresa_dao.py), [src/dao/catalogo_dao.py](src/dao/catalogo_dao.py)
  - Controladores MVC: [src/controllers/aluno_controller.py](src/controllers/aluno_controller.py), [src/controllers/empresa_controller.py](src/controllers/empresa_controller.py)

### Release 02 (`Lab04S01` e `Lab04S02`)
- **Lab04S01 — Diagramas de Interação e Casos de Uso Restantes:**
  - Diagramas de Sequência UML: [diagrama-sequencia.puml](diagrama-sequencia.puml) | [diagrama-sequencia.svg](diagrama-sequencia.svg)
  - Diagrama de Visão Geral de Interação UML: [diagrama-visao-geral-interacao.puml](diagrama-visao-geral-interacao.puml) | [diagrama-visao-geral-interacao.svg](diagrama-visao-geral-interacao.svg)
  - Autenticação e Autorização (`HU-05`): [src/services/auth_service.py](src/services/auth_service.py) e [src/controllers/auth_controller.py](src/controllers/auth_controller.py)
  - Professores, Crédito Semestral, Envio de Moedas e Extrato (`HU-02`, `HU-06`, `HU-07`, `HU-09`): [src/dao/professor_dao.py](src/dao/professor_dao.py), [src/dao/movimentacao_dao.py](src/dao/movimentacao_dao.py), [src/controllers/merito_controller.py](src/controllers/merito_controller.py)
  - Vantagens, Resgates e Cupons (`HU-04`, `HU-10`, `HU-11`): [src/dao/vantagem_dao.py](src/dao/vantagem_dao.py), [src/dao/resgate_dao.py](src/dao/resgate_dao.py), [src/controllers/vantagem_controller.py](src/controllers/vantagem_controller.py)
  - Notificações por E-mail (`HU-08`, `HU-11`): [src/services/notificacao_service.py](src/services/notificacao_service.py)
  - Interface Web Completa (View MVC): [src/views/index.html](src/views/index.html), [src/views/styles.css](src/views/styles.css), [src/views/app.js](src/views/app.js)
- **Lab04S02 — Diagrama de Implantação e Nuvem (Vercel + Render):**
  - Diagrama de Implantação UML: [diagrama-implantacao.puml](diagrama-implantacao.puml) | [diagrama-implantacao.svg](diagrama-implantacao.svg)
  - Configuração de Deploy: [render.yaml](render.yaml) (Back-end WSGI/Gunicorn) e [vercel.json](vercel.json) (Front-end estático + proxy `/api/*`)

---

## 🚀 Como Executar Localmente

Não é necessária nenhuma configuração externa de banco de dados — ao iniciar o servidor, o banco SQLite (`database/moeda_estudantil.db`) é criado e populado automaticamente com instituições, cursos, departamentos, professores pré-cadastrados, contas de demonstração e vantagens iniciais:

```bash
python3 app.py
```

Acesse no navegador: 👉 **http://localhost:8000**

### Credenciais de Demonstração (Seed Inicial)
| Perfil | E-mail | Senha |
| --- | --- | --- |
| **Professor** | `milena.adao@pucminas.br` | `Prof@2026` |
| **Professor (UFMG)** | `carlos.silva@dcc.ufmg.br` | `Prof@2026` |
| **Aluno** | `pedro.queiroz@sga.pucminas.br` | `Aluno@2026` |
| **Empresa Parceira** | `contato@livrariauniversitaria.com.br` | `Parceiro@2026` |

*(Na interface web há também botões de acesso rápido para testar cada perfil em 1 clique.)*

---

## ☁️ Implantação na Nuvem (Render + Vercel)

1. **Back-end no Render:** Conecte o repositório no [Render](https://render.com) utilizando o blueprint [render.yaml](render.yaml) (`gunicorn app:application --bind 0.0.0.0:$PORT`, healthcheck em `/api/health`). Variáveis opcionais de SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`) habilitam envio real de e-mails.
2. **Front-end no Vercel:** Conecte o repositório no [Vercel](https://vercel.com) utilizando [vercel.json](vercel.json), ajustando a URL de destino da regra `/api/(.*)` caso o subdomínio no Render seja diferente de `https://sistema-moeda-estudantil-api.onrender.com`.

---

## 🧪 Como Executar os Testes Automatizados

```bash
python3 -m unittest discover -s tests -v
```
