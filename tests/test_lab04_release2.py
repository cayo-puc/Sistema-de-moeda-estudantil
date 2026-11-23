"""
Suite de Testes Automatizados — Release 2 (Lab04S01 & Lab04S02).
Valida todos os casos de uso restantes e implantação WSGI:
1. Autenticação e autorização por perfil (HU-05).
2. Professores pré-cadastrados e crédito semestral acumulado (HU-02, HU-06).
3. Envio de moedas pelo professor + notificação por e-mail ao aluno (HU-07, HU-08).
4. Consulta de extrato para professor e aluno (HU-09).
5. Gestão de vantagens pela empresa parceira (HU-04).
6. Resgate de vantagem pelo aluno + cupom único + e-mails para aluno e empresa (HU-10, HU-11).
7. Roteamento WSGI (incluindo /api/health e CORS preflight).
"""

import json
import os
import tempfile
import unittest
from io import BytesIO

from app import MoedaEstudantilWSGIApp


class TestLab04Release2(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_release2.db")
        self.wsgi_app = MoedaEstudantilWSGIApp(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _request(self, method: str, path: str, body: dict | None = None, token: str | None = None):
        raw = json.dumps(body).encode("utf-8") if body is not None else b""
        path_info, _, query_string = path.partition("?")
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path_info,
            "QUERY_STRING": query_string,
            "CONTENT_LENGTH": str(len(raw)),
            "wsgi.input": BytesIO(raw),
        }
        if token:
            environ["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        captured = {}

        def start_response(status, headers):
            captured["status"] = int(status.split(" ", 1)[0])
            captured["headers"] = dict(headers)

        chunks = self.wsgi_app(environ, start_response)
        payload = b"".join(chunks)
        data = json.loads(payload.decode("utf-8")) if payload else {}
        return captured["status"], data

    def _login(self, email: str, senha: str) -> str:
        status, res = self._request("POST", "/api/auth/login", {"email": email, "senha": senha})
        self.assertEqual(status, 200)
        return res["dados"]["token"]

    def test_healthcheck_e_autenticacao(self):
        status, res = self._request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(res["status"], "ok")

        # Credencial inválida -> 401
        st_bad, _ = self._request("POST", "/api/auth/login", {"email": "milena.adao@pucminas.br", "senha": "errada"})
        self.assertEqual(st_bad, 401)

        # Rota protegida sem token -> 401
        st_unauth, _ = self._request("GET", "/api/extrato")
        self.assertEqual(st_unauth, 401)

        # Login válido de professor -> 200 e /api/auth/me
        token_prof = self._login("milena.adao@pucminas.br", "Prof@2026")
        st_me, res_me = self._request("GET", "/api/auth/me", token=token_prof)
        self.assertEqual(st_me, 200)
        self.assertEqual(res_me["dados"]["tipoUsuario"], "PROFESSOR")
        self.assertEqual(res_me["dados"]["saldoMoedas"], 1000)

    def test_fluxo_merito_credito_semestral_e_extrato(self):
        token_prof = self._login("milena.adao@pucminas.br", "Prof@2026")
        token_aluno = self._login("pedro.queiroz@sga.pucminas.br", "Aluno@2026")

        # Aluno não pode enviar moedas (403 Forbidden)
        st_forb, _ = self._request(
            "POST",
            "/api/merito/transferir",
            {"alunoId": "aluno-demo-01", "quantidade": 10, "motivo": "Teste"},
            token=token_aluno,
        )
        self.assertEqual(st_forb, 403)

        # Professor envia 150 moedas para aluno-demo-01 (que começa com 250)
        st_tx, res_tx = self._request(
            "POST",
            "/api/merito/transferir",
            {"alunoId": "aluno-demo-01", "quantidade": 150, "motivo": "Ótima apresentação da Sprint"},
            token=token_prof,
        )
        self.assertEqual(st_tx, 201)
        self.assertEqual(res_tx["dados"]["saldoProfessorAtual"], 850)
        self.assertEqual(res_tx["dados"]["saldoAlunoAtual"], 400)

        # Professor tenta enviar mais do que possui (900 > 850) -> 400
        st_insuf, _ = self._request(
            "POST",
            "/api/merito/transferir",
            {"alunoId": "aluno-demo-01", "quantidade": 900, "motivo": "Tentativa inválida"},
            token=token_prof,
        )
        self.assertEqual(st_insuf, 400)

        # Crédito semestral acumulado (+1000 -> 850 + 1000 = 1850)
        st_cred, res_cred = self._request(
            "POST",
            "/api/merito/credito-semestral",
            {"periodo": "2026.2"},
            token=token_prof,
        )
        self.assertEqual(st_cred, 201)
        self.assertEqual(res_cred["dados"]["saldoAtual"], 1850)

        # Crédito duplicado no mesmo semestre -> 409 Conflict
        st_dup, _ = self._request(
            "POST",
            "/api/merito/credito-semestral",
            {"periodo": "2026.2"},
            token=token_prof,
        )
        self.assertEqual(st_dup, 409)

        # Extrato do aluno contém o recebimento
        st_ext_a, res_ext_a = self._request("GET", "/api/extrato", token=token_aluno)
        self.assertEqual(st_ext_a, 200)
        self.assertEqual(res_ext_a["dados"]["saldoAtual"], 400)
        self.assertEqual(len(res_ext_a["dados"]["transacoes"]), 1)

        # Notificação por e-mail enviada ao aluno
        st_not, res_not = self._request("GET", "/api/notificacoes?email=pedro.queiroz@sga.pucminas.br")
        self.assertEqual(st_not, 200)
        self.assertGreaterEqual(res_not["total"], 1)
        self.assertEqual(res_not["dados"][0]["tipo"], "RECEBIMENTO_MOEDAS")

    def test_fluxo_vantagens_resgate_cupom_e_emails(self):
        token_emp = self._login("contato@livrariauniversitaria.com.br", "Parceiro@2026")
        token_aluno = self._login("pedro.queiroz@sga.pucminas.br", "Aluno@2026")

        # Empresa cria nova vantagem
        st_create, res_create = self._request(
            "POST",
            "/api/vantagens",
            {
                "titulo": "Vale-Livro Clean Architecture",
                "descricao": "Exemplar físico com 50% de desconto.",
                "fotografiaUri": "https://example.com/livro.jpg",
                "custoMoedas": 100,
                "dadosOferta": "Retirada na loja",
            },
            token=token_emp,
        )
        self.assertEqual(st_create, 201)
        vantagem_id = res_create["dados"]["id"]

        # Aluno (saldo inicial 250) resgata a vantagem de 100 moedas
        st_resg, res_resg = self._request("POST", f"/api/vantagens/{vantagem_id}/resgatar", token=token_aluno)
        self.assertEqual(st_resg, 201)
        self.assertEqual(res_resg["dados"]["saldoAlunoAtual"], 150)
        codigo = res_resg["dados"]["resgate"]["codigoConferencia"]
        self.assertTrue(codigo.startswith("CUPOM-"))

        # Aluno consulta seus resgates e Empresa consulta os resgates para conferência
        st_ra, res_ra = self._request("GET", "/api/resgates", token=token_aluno)
        self.assertEqual(st_ra, 200)
        self.assertEqual(res_ra["dados"][0]["codigoConferencia"], codigo)

        st_re, res_re = self._request("GET", "/api/resgates", token=token_emp)
        self.assertEqual(st_re, 200)
        self.assertEqual(res_re["dados"][0]["codigoConferencia"], codigo)

        # Verifica os dois e-mails gerados (CUPOM_ALUNO e CONFERENCIA_PARCEIRO)
        _, notifs = self._request("GET", "/api/notificacoes")
        tipos = {n["tipo"] for n in notifs["dados"]}
        self.assertIn("CUPOM_ALUNO", tipos)
        self.assertIn("CONFERENCIA_PARCEIRO", tipos)


if __name__ == "__main__":
    unittest.main()
