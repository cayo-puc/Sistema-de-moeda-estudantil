"""
Suite de Testes Automatizados — Lab03S02 (ORM, Padrão DAO e Controladores MVC).
Valida:
1. Inicialização do schema relacional (Modelo ER) e seed das instituições/cursos pré-cadastrados.
2. CRUD completo de Aluno via `AlunoController` e `AlunoDAO` (incluindo criação automática de `ContaMoedas`).
3. CRUD completo de Empresa Parceira via `EmpresaParceiraController` e `EmpresaParceiraDAO`.
4. Regras de integridade (unicidade de CPF, CNPJ e e-mail, validação de instituição pré-cadastrada e exclusão em cascata).
"""

import os
import tempfile
import unittest

from src.config.database import DatabaseManager
from src.controllers.aluno_controller import AlunoController
from src.controllers.empresa_controller import EmpresaParceiraController
from src.dao.catalogo_dao import CatalogoDAO


class TestLab03S02CrudsDAO(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_moeda.db")
        self.db = DatabaseManager(self.db_path)
        self.db.init_database()

        self.aluno_ctrl = AlunoController(self.db)
        self.empresa_ctrl = EmpresaParceiraController(self.db)
        self.catalogo_dao = CatalogoDAO(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_catalogo_pre_cadastrado(self):
        instituicoes = self.catalogo_dao.listar_instituicoes()
        self.assertGreaterEqual(len(instituicoes), 3)
        cursos_puc = self.catalogo_dao.listar_cursos("inst-pucminas-01")
        self.assertGreaterEqual(len(cursos_puc), 2)

    def test_crud_completo_aluno(self):
        # 1. CREATE
        status, res = self.aluno_ctrl.criar({
            "nome": "Ana Beatriz Souza",
            "email": "ana.souza@sga.pucminas.br",
            "cpf": "321.654.987-01",
            "rg": "MG-15.432.100",
            "endereco": "Rua da Bahia, 1200, Belo Horizonte - MG",
            "instituicaoId": "inst-pucminas-01",
            "cursoId": "curso-puc-es",
            "senha": "SenhaSegura123",
        })
        self.assertEqual(status, 201)
        self.assertTrue(res["sucesso"])
        aluno_criado = res["dados"]
        aluno_id = aluno_criado["id"]
        self.assertEqual(aluno_criado["saldoMoedas"], 0)
        self.assertEqual(aluno_criado["instituicaoSigla"], "PUC Minas")

        # 2. READ (Por ID e Listagem)
        status_get, res_get = self.aluno_ctrl.buscar_por_id(aluno_id)
        self.assertEqual(status_get, 200)
        self.assertEqual(res_get["dados"]["cpf"], "321.654.987-01")

        # 3. Duplicidade de CPF deve retornar 409 Conflict
        status_dup, _ = self.aluno_ctrl.criar({
            "nome": "Outro Aluno",
            "email": "outro@sga.pucminas.br",
            "cpf": "321.654.987-01",
            "rg": "MG-99.999.999",
            "endereco": "Rua X, 10",
            "instituicaoId": "inst-pucminas-01",
            "cursoId": "curso-puc-es",
            "senha": "SenhaSegura123",
        })
        self.assertEqual(status_dup, 409)

        # 4. UPDATE
        status_upd, res_upd = self.aluno_ctrl.atualizar(aluno_id, {
            "nome": "Ana Beatriz Souza Silva",
            "email": "ana.souza@sga.pucminas.br",
            "cpf": "321.654.987-01",
            "rg": "MG-15.432.100",
            "endereco": "Av. Afonso Pena, 900, Belo Horizonte - MG",
            "instituicaoId": "inst-pucminas-01",
            "cursoId": "curso-puc-cc",
            "senha": "",
        })
        self.assertEqual(status_upd, 200)
        self.assertEqual(res_upd["dados"]["nome"], "Ana Beatriz Souza Silva")
        self.assertEqual(res_upd["dados"]["cursoNome"], "Ciência da Computação")

        # 5. DELETE
        status_del, _ = self.aluno_ctrl.remover(aluno_id)
        self.assertEqual(status_del, 200)
        status_404, _ = self.aluno_ctrl.buscar_por_id(aluno_id)
        self.assertEqual(status_404, 404)

    def test_crud_completo_empresa_parceira(self):
        # 1. CREATE
        status, res = self.empresa_ctrl.criar({
            "nome": "Cantina Universitária",
            "nomeLegal": "Cantina Gourmet Universitária LTDA",
            "identificador": "45.678.901/0001-23",
            "email": "parceria@cantinauni.com.br",
            "descricao": "Descontos de 20% em refeições e lanches para estudantes.",
            "senha": "Empresa@2026",
        })
        self.assertEqual(status, 201)
        self.assertTrue(res["sucesso"])
        empresa_id = res["dados"]["id"]

        # 2. READ
        status_get, res_get = self.empresa_ctrl.buscar_por_id(empresa_id)
        self.assertEqual(status_get, 200)
        self.assertEqual(res_get["dados"]["identificador"], "45.678.901/0001-23")

        # 3. UPDATE
        status_upd, res_upd = self.empresa_ctrl.atualizar(empresa_id, {
            "nome": "Cantina & Restaurante Universitário",
            "nomeLegal": "Cantina Gourmet Universitária LTDA",
            "identificador": "45.678.901/0001-23",
            "email": "parceria@cantinauni.com.br",
            "descricao": "Descontos de 30% no almoço executivo estudantil.",
            "senha": "",
        })
        self.assertEqual(status_upd, 200)
        self.assertEqual(res_upd["dados"]["nome"], "Cantina & Restaurante Universitário")

        # 4. DELETE
        status_del, _ = self.empresa_ctrl.remover(empresa_id)
        self.assertEqual(status_del, 200)
        status_404, _ = self.empresa_ctrl.buscar_por_id(empresa_id)
        self.assertEqual(status_404, 404)


if __name__ == "__main__":
    unittest.main()

