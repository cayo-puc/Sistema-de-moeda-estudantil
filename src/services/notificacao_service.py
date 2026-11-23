"""
Serviço de Notificações por E-mail (`NotificacaoService`) — Lab04S01.
Atende às histórias HU-08 (aviso de moedas recebidas) e HU-11 (cupom ao aluno e
conferência à empresa parceira).
Suporta envio real via SMTP quando configurado por variáveis de ambiente e sempre
persiste uma cópia auditável na tabela `notificacoes_email` para consulta na interface.
"""

from email.message import EmailMessage
import os
import smtplib
from typing import List, Optional

from src.config.database import DatabaseManager
from src.models.entities import NotificacaoEmail, gerar_uuid, instante_atual_iso


class NotificacaoService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def notificar_recebimento_moedas(
        self,
        aluno_email: str,
        aluno_nome: str,
        professor_nome: str,
        quantidade: int,
        motivo: str,
        referencia_id: str,
    ) -> NotificacaoEmail:
        assunto = f"Você recebeu {quantidade} moedas estudantis!"
        corpo = (
            f"Olá, {aluno_nome}!\n\n"
            f"O(a) professor(a) {professor_nome} acabou de enviar {quantidade} moedas para a sua conta.\n"
            f"Motivo do reconhecimento: {motivo}\n\n"
            f"Acesse o Sistema de Moeda Estudantil para consultar seu extrato e resgatar vantagens."
        )
        return self._enviar_e_registrar(
            destinatario_email=aluno_email,
            destinatario_nome=aluno_nome,
            assunto=assunto,
            corpo=corpo,
            tipo="RECEBIMENTO_MOEDAS",
            referencia_id=referencia_id,
        )

    def notificar_resgate_vantagem(
        self,
        aluno_email: str,
        aluno_nome: str,
        empresa_email: str,
        empresa_nome: str,
        vantagem_titulo: str,
        custo_moedas: int,
        codigo_conferencia: str,
        resgate_id: str,
    ) -> tuple[NotificacaoEmail, NotificacaoEmail]:
        assunto_aluno = f"Seu cupom de resgate: {vantagem_titulo} [{codigo_conferencia}]"
        corpo_aluno = (
            f"Olá, {aluno_nome}!\n\n"
            f"Seu resgate foi confirmado com sucesso.\n"
            f"Vantagem: {vantagem_titulo}\n"
            f"Empresa Parceira: {empresa_nome}\n"
            f"Valor utilizado: {custo_moedas} moedas\n"
            f"Código do Cupom para troca presencial: {codigo_conferencia}\n\n"
            f"Apresente este código na empresa parceira para validar seu benefício."
        )
        email_aluno = self._enviar_e_registrar(
            destinatario_email=aluno_email,
            destinatario_nome=aluno_nome,
            assunto=assunto_aluno,
            corpo=corpo_aluno,
            tipo="CUPOM_ALUNO",
            referencia_id=resgate_id,
        )

        assunto_empresa = f"Conferência de Troca de Vantagem [{codigo_conferencia}]"
        corpo_empresa = (
            f"Olá, {empresa_nome}!\n\n"
            f"O(a) aluno(a) {aluno_nome} ({aluno_email}) realizou o resgate de uma vantagem:\n"
            f"Vantagem: {vantagem_titulo}\n"
            f"Custo: {custo_moedas} moedas\n"
            f"Código de Conferência: {codigo_conferencia}\n\n"
            f"Utilize este código para conferir a troca presencial."
        )
        email_empresa = self._enviar_e_registrar(
            destinatario_email=empresa_email,
            destinatario_nome=empresa_nome,
            assunto=assunto_empresa,
            corpo=corpo_empresa,
            tipo="CONFERENCIA_PARCEIRO",
            referencia_id=resgate_id,
        )
        return email_aluno, email_empresa

    def listar_notificacoes(self, destinatario_email: Optional[str] = None, limite: int = 30) -> List[NotificacaoEmail]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if destinatario_email:
                cur.execute(
                    """
                    SELECT id, destinatario_email, destinatario_nome, assunto, corpo, tipo, referencia_id, enviado_smtp, criado_em
                    FROM notificacoes_email
                    WHERE lower(destinatario_email) = lower(?)
                    ORDER BY criado_em DESC
                    LIMIT ?
                    """,
                    (destinatario_email, limite),
                )
            else:
                cur.execute(
                    """
                    SELECT id, destinatario_email, destinatario_nome, assunto, corpo, tipo, referencia_id, enviado_smtp, criado_em
                    FROM notificacoes_email
                    ORDER BY criado_em DESC
                    LIMIT ?
                    """,
                    (limite,),
                )
            return [NotificacaoEmail.from_row(row) for row in cur.fetchall()]

    def _enviar_e_registrar(
        self,
        destinatario_email: str,
        destinatario_nome: str,
        assunto: str,
        corpo: str,
        tipo: str,
        referencia_id: Optional[str],
    ) -> NotificacaoEmail:
        enviado_smtp = self._tentar_envio_smtp(destinatario_email, assunto, corpo)
        notif = NotificacaoEmail(
            id=gerar_uuid(),
            destinatario_email=destinatario_email,
            destinatario_nome=destinatario_nome,
            assunto=assunto,
            corpo=corpo,
            tipo=tipo,
            referencia_id=referencia_id,
            enviado_smtp=enviado_smtp,
            criado_em=instante_atual_iso(),
        )
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO notificacoes_email
                    (id, destinatario_email, destinatario_nome, assunto, corpo, tipo, referencia_id, enviado_smtp, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notif.id,
                    notif.destinatario_email,
                    notif.destinatario_nome,
                    notif.assunto,
                    notif.corpo,
                    notif.tipo,
                    notif.referencia_id,
                    1 if notif.enviado_smtp else 0,
                    notif.criado_em,
                ),
            )
        return notif

    def _tentar_envio_smtp(self, destinatario: str, assunto: str, corpo: str) -> bool:
        smtp_host = os.environ.get("SMTP_HOST", "").strip()
        if not smtp_host:
            return False
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "").strip()
        smtp_pass = os.environ.get("SMTP_PASS", "").strip()
        smtp_from = os.environ.get("SMTP_FROM", smtp_user or "no-reply@moedaestudantil.edu.br")

        try:
            msg = EmailMessage()
            msg["Subject"] = assunto
            msg["From"] = smtp_from
            msg["To"] = destinatario
            msg.set_content(corpo)

            with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True
        except Exception:
            return False
