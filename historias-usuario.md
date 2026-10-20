# Histórias de usuário — Lab03S01

## HU-01 — Cadastrar aluno

**Ator:** Aluno  
**História:** Como aluno, quero me cadastrar com meus dados acadêmicos e pessoais para participar do sistema de mérito.  
**Critérios de aceitação:**
- O cadastro solicita nome, e-mail, CPF, RG, endereço, instituição e curso.
- A instituição selecionada deve pertencer ao conjunto previamente cadastrado.
- O sistema não aceita dados obrigatórios ausentes.
**Requisitos:** RF01, RF04. **Regras:** instituição pré-cadastrada; credenciais protegidas.

## HU-02 — Disponibilizar professores cadastrados

**Ator:** Instituição (fonte da lista; operação administrativa fora do autoatendimento modelado)  
**História:** Como instituição parceira, quero fornecer a lista de professores vinculada à instituição para que eles possam distribuir moedas.  
**Critérios de aceitação:**
- Cada professor cadastrado contém nome, CPF, departamento e associação explícita à instituição.
- O professor autenticável possui credenciais de acesso associadas ao perfil.
**Requisitos:** RF02, RF04. **Regras:** o cadastro parte de lista fornecida pela instituição; não é autoinscrição docente descrita no enunciado.

## HU-03 — Cadastrar empresa parceira

**Ator:** Empresa parceira  
**História:** Como empresa, quero cadastrar meu perfil e credenciais para acessar as funções de parceria.  
**Critérios de aceitação:**
- O perfil da empresa é associado a uma conta autenticável.
- Acesso às operações é condicionado à autenticação e ao perfil empresarial.
**Requisitos:** RF03, RF04. **Regras:** senha armazenada de forma segura.

## HU-04 — Gerenciar vantagem

**Ator:** Empresa parceira  
**História:** Como empresa parceira, quero cadastrar uma vantagem com descrição, foto e custo em moedas para oferecê-la aos alunos.  
**Critérios de aceitação:**
- Uma vantagem identifica a empresa ofertante e inclui descrição, fotografia, custo e dados de identificação da oferta.
- O custo deve ser um valor de moedas positivo.
- A gestão exige autenticação empresarial.
**Requisitos:** RF03, RF09. **Regras:** a oferta pode representar produto, desconto ou outro benefício.

## HU-05 — Autenticar e autorizar acesso

**Ator:** Aluno, professor ou empresa parceira  
**História:** Como usuário, quero entrar com minhas credenciais para usar apenas as funções do meu perfil.  
**Critérios de aceitação:**
- Credenciais válidas iniciam sessão autenticada; inválidas não concedem acesso.
- Operações protegidas verificam perfil autorizado.
- Senhas não são persistidas em texto puro.
**Requisitos:** RF04. **Regras:** autenticação e autorização por perfil.

## HU-06 — Receber crédito semestral acumulado

**Ator:** Professor  
**História:** Como professor, quero receber o crédito de 1.000 moedas a cada semestre somado ao saldo anterior para continuar reconhecendo alunos.  
**Critérios de aceitação:**
- Para cada período semestral, o lançamento acrescenta 1.000 moedas ao saldo existente.
- Saldo não utilizado permanece disponível e não é substituído pelo novo crédito.
- Cada crédito fica registrado no histórico com referência ao período.
**Requisitos:** RF05. **Regras:** evitar duplicar crédito do mesmo professor/período (restrição de integridade derivada da periodicidade).

## HU-07 — Distribuir moedas a aluno

**Ator:** Professor  
**História:** Como professor, quero transferir moedas a um aluno informando quantidade e motivo para reconhecer seu mérito.  
**Critérios de aceitação:**
- O professor informa aluno, quantidade positiva e motivo não vazio.
- Com saldo suficiente, a operação debita o professor, credita o aluno e registra a transferência consistentemente.
- Com saldo insuficiente, não há débito, crédito nem transferência confirmada.
- A operação requer autenticação de professor.
**Requisitos:** RF06, RF04. **Regras:** saldo suficiente e motivo obrigatório.

## HU-08 — Receber aviso de moedas

**Ator:** Aluno  
**História:** Como aluno, quero receber um e-mail quando uma transferência de moedas for concluída para saber que fui reconhecido.  
**Critérios de aceitação:**
- Após transferência confirmada, o sistema solicita envio de notificação ao e-mail do aluno.
- Transferência recusada por saldo insuficiente não dispara notificação de recebimento.
**Requisitos:** RF06, RF07. **Regras:** notificar somente recebimento efetivado.

## HU-09 — Consultar extrato

**Ator:** Aluno ou professor  
**História:** Como titular da conta, quero consultar meu saldo e histórico para acompanhar minhas moedas.  
**Critérios de aceitação:**
- O titular autenticado vê o próprio saldo atual e histórico.
- Professor visualiza envios e créditos; aluno visualiza recebimentos e resgates.
- O histórico mantém referência e data de cada movimentação.
**Requisitos:** RF05, RF08. **Regras:** extrato restrito ao titular e adequado ao perfil.

## HU-10 — Resgatar vantagem

**Ator:** Aluno  
**História:** Como aluno, quero selecionar uma vantagem e resgatá-la com minhas moedas para obter o benefício oferecido.  
**Critérios de aceitação:**
- O aluno seleciona vantagem cadastrada e confirma o resgate.
- O sistema verifica saldo antes de confirmar.
- Sem saldo suficiente, não debita moedas nem confirma resgate.
- Com saldo suficiente, debita o custo e registra resgate e movimentação.
**Requisitos:** RF08, RF10. **Regras:** custo conforme oferta no momento da confirmação; saldo não negativo.

## HU-11 — Receber cupom e permitir conferência

**Ator:** Aluno e empresa parceira  
**História:** Como aluno, quero receber um cupom com código e, como empresa, quero receber os dados do resgate com o mesmo código para conferir a troca presencial.  
**Critérios de aceitação:**
- Cada resgate confirmado gera um código identificador único no sistema.
- Um e-mail ao aluno inclui o cupom e o código.
- Um e-mail à empresa ofertante inclui os dados necessários à conferência e o mesmo código.
- O código relaciona cupom, resgate e vantagem.
**Requisitos:** RF11. **Regras:** os dois e-mails correspondem ao mesmo resgate confirmado.
