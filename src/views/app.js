// Camada View (MVC) — Sistema de Moeda Estudantil (Release 2: Lab04S01 / Lab04S02)

const API_BASE = window.MOEDA_API_BASE || "";

const state = {
  token: localStorage.getItem("moeda_token") || null,
  usuario: null,
  instituicoes: [],
  cursos: [],
  alunos: [],
  empresas: [],
  vantagens: [],
  resgates: [],
  notificacoes: [],
};

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }
  return headers;
}

async function apiFetch(path, options = {}) {
  const res = await fetch(apiUrl(path), {
    ...options,
    headers: authHeaders(options.headers || {}),
  });
  const data = await res.json();
  return { status: res.status, data };
}

function showAlert(message, type = "success") {
  const box = document.getElementById("alert-box");
  box.textContent = message;
  box.className = `alert alert-${type}`;
  box.classList.remove("hidden");
  clearTimeout(showAlert._timer);
  showAlert._timer = setTimeout(() => box.classList.add("hidden"), 6000);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

// =============================================================================
// Autenticação (HU-05)
// =============================================================================
function renderAuthBar() {
  const loggedOut = document.getElementById("auth-logged-out");
  const loggedIn = document.getElementById("auth-logged-in");

  if (!state.usuario) {
    loggedOut.classList.remove("hidden");
    loggedIn.classList.add("hidden");
    return;
  }

  loggedOut.classList.add("hidden");
  loggedIn.classList.remove("hidden");
  document.getElementById("auth-user-role").textContent = state.usuario.tipoUsuario;
  document.getElementById("auth-user-name").textContent = state.usuario.nome;
  document.getElementById("auth-user-email").textContent = state.usuario.email;

  const saldoBox = document.getElementById("auth-saldo-box");
  if (state.usuario.tipoUsuario === "ALUNO" || state.usuario.tipoUsuario === "PROFESSOR") {
    saldoBox.classList.remove("hidden");
    document.getElementById("auth-user-saldo").textContent = state.usuario.saldoMoedas ?? 0;
  } else {
    saldoBox.classList.add("hidden");
  }
}

async function carregarSessao() {
  if (!state.token) {
    state.usuario = null;
    renderAuthBar();
    return;
  }
  try {
    const { status, data } = await apiFetch("/api/auth/me");
    if (status === 200 && data.sucesso) {
      state.usuario = data.dados;
    } else {
      state.token = null;
      state.usuario = null;
      localStorage.removeItem("moeda_token");
    }
  } catch {
    state.usuario = null;
  }
  renderAuthBar();
}

async function fazerLogin(email, senha) {
  const { status, data } = await apiFetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });
  if (status !== 200 || !data.sucesso) {
    showAlert(data.erro || "Falha ao autenticar.", "error");
    return;
  }
  state.token = data.dados.token;
  state.usuario = data.dados.usuario;
  localStorage.setItem("moeda_token", state.token);
  renderAuthBar();
  showAlert(data.mensagem, "success");
  await Promise.all([carregarExtrato(), carregarVantagens(), carregarResgates(), carregarNotificacoes()]);
}

function logout() {
  state.token = null;
  state.usuario = null;
  localStorage.removeItem("moeda_token");
  renderAuthBar();
  carregarExtrato();
  carregarResgates();
  showAlert("Sessão encerrada.", "success");
}

// =============================================================================
// Abas
// =============================================================================
function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".tab-panel");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      buttons.forEach((b) => b.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(target).classList.add("active");
    });
  });
}

// =============================================================================
// Catálogo Acadêmico, Alunos e Empresas (Lab03S02)
// =============================================================================
async function carregarInstituicoes() {
  const { data } = await apiFetch("/api/instituicoes");
  state.instituicoes = data.dados || [];
  document.getElementById("stat-instituicoes").textContent = state.instituicoes.length;
  const select = document.getElementById("aluno-instituicao");
  select.innerHTML = `<option value="">Selecione a instituição...</option>`;
  state.instituicoes.forEach((inst) => {
    const opt = document.createElement("option");
    opt.value = inst.id;
    opt.textContent = `${inst.sigla} — ${inst.nome}`;
    select.appendChild(opt);
  });
}

async function carregarCursosPorInstituicao(instId, selectedCursoId = "") {
  const selectCurso = document.getElementById("aluno-curso");
  if (!instId) {
    selectCurso.innerHTML = `<option value="">Selecione a instituição primeiro...</option>`;
    selectCurso.disabled = true;
    return;
  }
  const { data } = await apiFetch(`/api/cursos?instituicaoId=${encodeURIComponent(instId)}`);
  state.cursos = data.dados || [];
  selectCurso.disabled = false;
  selectCurso.innerHTML = `<option value="">Selecione o curso...</option>`;
  state.cursos.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.nome;
    if (c.id === selectedCursoId) opt.selected = true;
    selectCurso.appendChild(opt);
  });
}

async function carregarAlunos() {
  const { data } = await apiFetch("/api/alunos");
  state.alunos = data.dados || [];
  document.getElementById("stat-alunos").textContent = state.alunos.length;
  renderTabelaAlunos();
  renderSelectAlunosTransferencia();
}

function renderSelectAlunosTransferencia() {
  const select = document.getElementById("transf-aluno");
  const current = select.value;
  select.innerHTML = `<option value="">Selecione o aluno...</option>`;
  state.alunos.forEach((a) => {
    const opt = document.createElement("option");
    opt.value = a.id;
    opt.textContent = `${a.nome} (${a.instituicaoSigla || ""} • Saldo: ${a.saldoMoedas} moedas)`;
    if (a.id === current) opt.selected = true;
    select.appendChild(opt);
  });
}

function renderTabelaAlunos(filtro = "") {
  const tbody = document.getElementById("tabela-alunos-body");
  const termo = filtro.trim().toLowerCase();
  const filtrados = state.alunos.filter(
    (a) =>
      !termo ||
      a.nome.toLowerCase().includes(termo) ||
      a.email.toLowerCase().includes(termo) ||
      a.cpf.toLowerCase().includes(termo)
  );
  if (!filtrados.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Nenhum aluno encontrado.</td></tr>`;
    return;
  }
  tbody.innerHTML = filtrados
    .map(
      (a) => `
    <tr>
      <td><strong>${escapeHtml(a.nome)}</strong><br><small class="text-muted">${escapeHtml(a.email)}</small></td>
      <td>${escapeHtml(a.cpf)}<br><small class="text-muted">RG: ${escapeHtml(a.rg)}</small></td>
      <td><strong>${escapeHtml(a.instituicaoSigla || a.instituicaoNome)}</strong><br><small class="text-muted">${escapeHtml(a.cursoNome)}</small></td>
      <td><span class="badge badge-blue">${a.saldoMoedas} moedas</span></td>
      <td class="text-right">
        <button class="btn btn-sm btn-secondary" onclick="editarAluno('${a.id}')">Editar</button>
        <button class="btn btn-sm btn-danger" onclick="excluirAluno('${a.id}')">Excluir</button>
      </td>
    </tr>`
    )
    .join("");
}

window.editarAluno = async (id) => {
  const a = state.alunos.find((item) => item.id === id);
  if (!a) return;
  document.getElementById("aluno-id").value = a.id;
  document.getElementById("aluno-nome").value = a.nome;
  document.getElementById("aluno-cpf").value = a.cpf;
  document.getElementById("aluno-rg").value = a.rg;
  document.getElementById("aluno-email").value = a.email;
  document.getElementById("aluno-endereco").value = a.endereco;
  document.getElementById("aluno-instituicao").value = a.instituicaoId;
  await carregarCursosPorInstituicao(a.instituicaoId, a.cursoId);
  document.getElementById("aluno-senha").value = "";
  document.getElementById("aluno-senha").required = false;
  document.getElementById("form-aluno-titulo").textContent = "Editar Aluno";
  document.getElementById("form-aluno-modo").textContent = "Modo: Edição (PUT)";
  document.getElementById("btn-salvar-aluno").textContent = "Salvar Alterações";
  document.getElementById("btn-cancelar-aluno").classList.remove("hidden");
};

function resetFormAluno() {
  document.getElementById("form-aluno").reset();
  document.getElementById("aluno-id").value = "";
  document.getElementById("aluno-curso").disabled = true;
  document.getElementById("aluno-senha").required = true;
  document.getElementById("form-aluno-titulo").textContent = "Novo Cadastro de Aluno";
  document.getElementById("form-aluno-modo").textContent = "Modo: Criação (POST)";
  document.getElementById("btn-salvar-aluno").textContent = "Cadastrar Aluno";
  document.getElementById("btn-cancelar-aluno").classList.add("hidden");
}

window.excluirAluno = async (id) => {
  if (!confirm("Confirma a exclusão deste aluno?")) return;
  const { status, data } = await apiFetch(`/api/alunos/${id}`, { method: "DELETE" });
  if (status === 200) {
    showAlert(data.mensagem, "success");
    await carregarAlunos();
  } else {
    showAlert(data.erro || "Erro ao excluir aluno.", "error");
  }
};

async function carregarEmpresas() {
  const { data } = await apiFetch("/api/empresas");
  state.empresas = data.dados || [];
  document.getElementById("stat-empresas").textContent = state.empresas.length;
  renderTabelaEmpresas();
}

function renderTabelaEmpresas(filtro = "") {
  const tbody = document.getElementById("tabela-empresas-body");
  const termo = filtro.trim().toLowerCase();
  const filtradas = state.empresas.filter(
    (e) =>
      !termo ||
      e.nome.toLowerCase().includes(termo) ||
      e.nomeLegal.toLowerCase().includes(termo) ||
      e.identificador.toLowerCase().includes(termo)
  );
  if (!filtradas.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Nenhuma empresa encontrada.</td></tr>`;
    return;
  }
  tbody.innerHTML = filtradas
    .map(
      (e) => `
    <tr>
      <td><strong>${escapeHtml(e.nome)}</strong><br><small class="text-muted">${escapeHtml(e.email)}</small></td>
      <td>${escapeHtml(e.nomeLegal)}</td>
      <td>${escapeHtml(e.identificador)}</td>
      <td>${escapeHtml(e.descricao || "—")}</td>
      <td class="text-right">
        <button class="btn btn-sm btn-secondary" onclick="editarEmpresa('${e.id}')">Editar</button>
        <button class="btn btn-sm btn-danger" onclick="excluirEmpresa('${e.id}')">Excluir</button>
      </td>
    </tr>`
    )
    .join("");
}

window.editarEmpresa = (id) => {
  const e = state.empresas.find((item) => item.id === id);
  if (!e) return;
  document.getElementById("empresa-id").value = e.id;
  document.getElementById("empresa-nome").value = e.nome;
  document.getElementById("empresa-nome-legal").value = e.nomeLegal;
  document.getElementById("empresa-identificador").value = e.identificador;
  document.getElementById("empresa-email").value = e.email;
  document.getElementById("empresa-descricao").value = e.descricao || "";
  document.getElementById("empresa-senha").value = "";
  document.getElementById("empresa-senha").required = false;
  document.getElementById("form-empresa-titulo").textContent = "Editar Empresa Parceira";
  document.getElementById("form-empresa-modo").textContent = "Modo: Edição (PUT)";
  document.getElementById("btn-salvar-empresa").textContent = "Salvar Alterações";
  document.getElementById("btn-cancelar-empresa").classList.remove("hidden");
};

function resetFormEmpresa() {
  document.getElementById("form-empresa").reset();
  document.getElementById("empresa-id").value = "";
  document.getElementById("empresa-senha").required = true;
  document.getElementById("form-empresa-titulo").textContent = "Nova Empresa Parceira";
  document.getElementById("form-empresa-modo").textContent = "Modo: Criação (POST)";
  document.getElementById("btn-salvar-empresa").textContent = "Cadastrar Empresa";
  document.getElementById("btn-cancelar-empresa").classList.add("hidden");
}

window.excluirEmpresa = async (id) => {
  if (!confirm("Confirma a exclusão desta empresa parceira?")) return;
  const { status, data } = await apiFetch(`/api/empresas/${id}`, { method: "DELETE" });
  if (status === 200) {
    showAlert(data.mensagem, "success");
    await carregarEmpresas();
  } else {
    showAlert(data.erro || "Erro ao excluir empresa.", "error");
  }
};

// =============================================================================
// Mérito & Extrato (Lab04S01)
// =============================================================================
async function carregarExtrato() {
  const resumo = document.getElementById("extrato-resumo");
  const tbody = document.getElementById("tabela-extrato-body");

  if (!state.usuario || (state.usuario.tipoUsuario !== "ALUNO" && state.usuario.tipoUsuario !== "PROFESSOR")) {
    resumo.innerHTML = `Faça login como <strong>Aluno</strong> ou <strong>Professor</strong> para visualizar seu saldo e extrato.`;
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Nenhuma movimentação exibida.</td></tr>`;
    return;
  }

  const { status, data } = await apiFetch("/api/extrato");
  if (status !== 200 || !data.sucesso) {
    resumo.textContent = data.erro || "Não foi possível carregar o extrato.";
    return;
  }

  const ext = data.dados;
  state.usuario.saldoMoedas = ext.saldoAtual;
  renderAuthBar();
  resumo.innerHTML = `Titular: <strong>${escapeHtml(state.usuario.nome)}</strong> (${ext.tipoUsuario}) • Saldo atual: <strong>${ext.saldoAtual} moedas</strong> • Total de lançamentos: <strong>${ext.transacoes.length}</strong>`;

  if (!ext.transacoes.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Nenhuma movimentação registrada até o momento.</td></tr>`;
    return;
  }

  tbody.innerHTML = ext.transacoes
    .map(
      (t) => `
    <tr>
      <td><small>${escapeHtml(t.instante)}</small></td>
      <td><span class="${t.direcao === "ENTRADA" ? "badge-entrada" : "badge-saida"}">${t.direcao === "ENTRADA" ? "+" : "-"}${t.quantidade}</span></td>
      <td><strong>${escapeHtml(t.descricao)}</strong><br><small class="text-muted">${escapeHtml(t.motivo || "")}</small></td>
      <td class="text-right"><strong>${t.direcao === "ENTRADA" ? "+" : "-"}${t.quantidade} moedas</strong></td>
    </tr>`
    )
    .join("");
}

// =============================================================================
// Vantagens & Resgates / Cupons (Lab04S01)
// =============================================================================
async function carregarVantagens() {
  const { data } = await apiFetch("/api/vantagens");
  state.vantagens = data.dados || [];
  document.getElementById("stat-vantagens").textContent = state.vantagens.length;
  renderVantagens();
}

function renderVantagens() {
  const grid = document.getElementById("catalogo-vantagens-grid");
  if (!state.vantagens.length) {
    grid.innerHTML = `<p class="empty-row">Nenhuma vantagem cadastrada no catálogo.</p>`;
    return;
  }
  const isAluno = state.usuario && state.usuario.tipoUsuario === "ALUNO";
  const isEmpresa = state.usuario && state.usuario.tipoUsuario === "EMPRESA";

  grid.innerHTML = state.vantagens
    .map((v) => {
      const dono = isEmpresa && state.usuario.id === v.empresaId;
      return `
      <div class="vantagem-card">
        <img class="vantagem-img" src="${escapeHtml(v.fotografiaUri)}" alt="${escapeHtml(v.titulo)}" onerror="this.src='https://via.placeholder.com/400x200?text=Vantagem'" />
        <div class="vantagem-body">
          <div class="vantagem-title">${escapeHtml(v.titulo)}</div>
          <div class="vantagem-empresa">🏢 ${escapeHtml(v.empresaNome || "")}</div>
          <div class="vantagem-desc">${escapeHtml(v.descricao)}</div>
          <div class="vantagem-footer">
            <span class="vantagem-custo">${v.custoMoedas} moedas</span>
            <div>
              ${isAluno ? `<button class="btn btn-sm btn-primary" onclick="resgatarVantagem('${v.id}')">Resgatar</button>` : ""}
              ${dono ? `<button class="btn btn-sm btn-secondary" onclick="editarVantagem('${v.id}')">Editar</button> <button class="btn btn-sm btn-danger" onclick="excluirVantagem('${v.id}')">Excluir</button>` : ""}
            </div>
          </div>
        </div>
      </div>`;
    })
    .join("");
}

window.resgatarVantagem = async (vantagemId) => {
  const { status, data } = await apiFetch(`/api/vantagens/${vantagemId}/resgatar`, { method: "POST" });
  if (status === 201 && data.sucesso) {
    showAlert(data.mensagem, "success");
    await Promise.all([carregarSessao(), carregarExtrato(), carregarResgates(), carregarNotificacoes(), carregarAlunos()]);
  } else {
    showAlert(data.erro || "Não foi possível resgatar a vantagem.", "error");
  }
};

window.editarVantagem = (id) => {
  const v = state.vantagens.find((item) => item.id === id);
  if (!v) return;
  document.getElementById("vantagem-id").value = v.id;
  document.getElementById("vantagem-titulo").value = v.titulo;
  document.getElementById("vantagem-custo").value = v.custoMoedas;
  document.getElementById("vantagem-foto").value = v.fotografiaUri;
  document.getElementById("vantagem-oferta").value = v.dadosOferta || "";
  document.getElementById("vantagem-descricao").value = v.descricao;
  document.getElementById("form-vantagem-titulo").textContent = "Editar Vantagem";
  document.getElementById("btn-cancelar-vantagem").classList.remove("hidden");
};

window.excluirVantagem = async (id) => {
  if (!confirm("Remover esta vantagem do catálogo?")) return;
  const { status, data } = await apiFetch(`/api/vantagens/${id}`, { method: "DELETE" });
  if (status === 200) {
    showAlert(data.mensagem, "success");
    await carregarVantagens();
  } else {
    showAlert(data.erro || "Erro ao remover vantagem.", "error");
  }
};

async function carregarResgates() {
  const tbody = document.getElementById("tabela-resgates-body");
  if (!state.usuario || (state.usuario.tipoUsuario !== "ALUNO" && state.usuario.tipoUsuario !== "EMPRESA")) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Faça login como Aluno ou Empresa para consultar os cupons.</td></tr>`;
    return;
  }
  const { status, data } = await apiFetch("/api/resgates");
  if (status !== 200 || !data.sucesso) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">${escapeHtml(data.erro || "Erro ao carregar cupons.")}</td></tr>`;
    return;
  }
  state.resgates = data.dados || [];
  if (!state.resgates.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Nenhum resgate/cupom registrado até o momento.</td></tr>`;
    return;
  }
  tbody.innerHTML = state.resgates
    .map(
      (r) => `
    <tr>
      <td><span class="cupom-code">${escapeHtml(r.codigoConferencia)}</span></td>
      <td><strong>${escapeHtml(r.vantagemTitulo)}</strong></td>
      <td>${escapeHtml(r.alunoNome)}<br><small class="text-muted">${escapeHtml(r.empresaNome)}</small></td>
      <td>${r.custoAplicado} moedas</td>
      <td><small>${escapeHtml(r.instante)}</small></td>
    </tr>`
    )
    .join("");
}

// =============================================================================
// Notificações por E-mail
// =============================================================================
async function carregarNotificacoes() {
  const container = document.getElementById("lista-notificacoes");
  const { status, data } = await apiFetch("/api/notificacoes");
  if (status !== 200 || !data.sucesso) {
    container.innerHTML = `<p class="empty-row">Não foi possível carregar as notificações.</p>`;
    return;
  }
  state.notificacoes = data.dados || [];
  if (!state.notificacoes.length) {
    container.innerHTML = `<p class="empty-row">Nenhum e-mail enviado ainda. Realize uma transferência de moedas ou um resgate de vantagem.</p>`;
    return;
  }
  container.innerHTML = state.notificacoes
    .map(
      (n) => `
    <div class="notif-item">
      <div class="notif-header">
        <div>
          <span class="badge badge-blue">${escapeHtml(n.tipo)}</span>
          <strong>${escapeHtml(n.assunto)}</strong>
        </div>
        <small class="text-muted">Para: ${escapeHtml(n.destinatarioNome)} (${escapeHtml(n.destinatarioEmail)}) • ${escapeHtml(n.criadoEm)}</small>
      </div>
      <div class="notif-body">${escapeHtml(n.corpo)}</div>
    </div>`
    )
    .join("");
}

// =============================================================================
// Event Listeners & Inicialização
// =============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  initTabs();

  // Login
  document.getElementById("form-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    await fazerLogin(
      document.getElementById("login-email").value,
      document.getElementById("login-senha").value
    );
  });

  document.querySelectorAll("[data-demo-role]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const role = btn.dataset.demoRole;
      const creds = {
        ALUNO: ["pedro.queiroz@sga.pucminas.br", "Aluno@2026"],
        PROFESSOR: ["milena.adao@pucminas.br", "Prof@2026"],
        EMPRESA: ["contato@livrariauniversitaria.com.br", "Parceiro@2026"],
      }[role];
      if (creds) await fazerLogin(creds[0], creds[1]);
    });
  });

  document.getElementById("btn-logout").addEventListener("click", logout);

  // Transferência de moedas (Professor)
  document.getElementById("form-transferencia").addEventListener("submit", async (e) => {
    e.preventDefault();
    const { status, data } = await apiFetch("/api/merito/transferir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        alunoId: document.getElementById("transf-aluno").value,
        quantidade: Number(document.getElementById("transf-quantidade").value),
        motivo: document.getElementById("transf-motivo").value,
      }),
    });
    if (status === 201 && data.sucesso) {
      showAlert(data.mensagem, "success");
      document.getElementById("transf-motivo").value = "";
      await Promise.all([carregarSessao(), carregarExtrato(), carregarAlunos(), carregarNotificacoes()]);
    } else {
      showAlert((data.detalhes && data.detalhes.join(" ")) || data.erro || "Erro ao enviar moedas.", "error");
    }
  });

  // Crédito semestral (Professor)
  document.getElementById("form-credito-semestral").addEventListener("submit", async (e) => {
    e.preventDefault();
    const { status, data } = await apiFetch("/api/merito/credito-semestral", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ periodo: document.getElementById("credito-periodo").value }),
    });
    if (status === 201 && data.sucesso) {
      showAlert(data.mensagem, "success");
      await Promise.all([carregarSessao(), carregarExtrato()]);
    } else {
      showAlert(data.erro || "Erro ao conceder crédito semestral.", "error");
    }
  });

  document.getElementById("btn-atualizar-extrato").addEventListener("click", carregarExtrato);
  document.getElementById("btn-atualizar-notifs").addEventListener("click", carregarNotificacoes);

  // Vantagem (Empresa)
  document.getElementById("form-vantagem").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("vantagem-id").value;
    const payload = {
      titulo: document.getElementById("vantagem-titulo").value,
      custoMoedas: Number(document.getElementById("vantagem-custo").value),
      fotografiaUri: document.getElementById("vantagem-foto").value,
      dadosOferta: document.getElementById("vantagem-oferta").value,
      descricao: document.getElementById("vantagem-descricao").value,
    };
    const { status, data } = await apiFetch(id ? `/api/vantagens/${id}` : "/api/vantagens", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if ((status === 200 || status === 201) && data.sucesso) {
      showAlert(data.mensagem, "success");
      document.getElementById("form-vantagem").reset();
      document.getElementById("vantagem-id").value = "";
      document.getElementById("form-vantagem-titulo").textContent = "Cadastrar Vantagem (Empresa)";
      document.getElementById("btn-cancelar-vantagem").classList.add("hidden");
      await carregarVantagens();
    } else {
      showAlert((data.detalhes && data.detalhes.join(" ")) || data.erro || "Erro ao salvar vantagem.", "error");
    }
  });

  document.getElementById("btn-cancelar-vantagem").addEventListener("click", () => {
    document.getElementById("form-vantagem").reset();
    document.getElementById("vantagem-id").value = "";
    document.getElementById("form-vantagem-titulo").textContent = "Cadastrar Vantagem (Empresa)";
    document.getElementById("btn-cancelar-vantagem").classList.add("hidden");
  });

  // Aluno CRUD
  document.getElementById("aluno-instituicao").addEventListener("change", (e) => {
    carregarCursosPorInstituicao(e.target.value);
  });
  document.getElementById("busca-aluno").addEventListener("input", (e) => renderTabelaAlunos(e.target.value));
  document.getElementById("btn-cancelar-aluno").addEventListener("click", resetFormAluno);
  document.getElementById("form-aluno").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("aluno-id").value;
    const payload = {
      nome: document.getElementById("aluno-nome").value,
      cpf: document.getElementById("aluno-cpf").value,
      rg: document.getElementById("aluno-rg").value,
      email: document.getElementById("aluno-email").value,
      endereco: document.getElementById("aluno-endereco").value,
      instituicaoId: document.getElementById("aluno-instituicao").value,
      cursoId: document.getElementById("aluno-curso").value,
      senha: document.getElementById("aluno-senha").value,
    };
    const { status, data } = await apiFetch(id ? `/api/alunos/${id}` : "/api/alunos", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if ((status === 200 || status === 201) && data.sucesso) {
      showAlert(data.mensagem, "success");
      resetFormAluno();
      await carregarAlunos();
    } else {
      showAlert((data.detalhes && data.detalhes.join(" ")) || data.erro || "Erro ao salvar aluno.", "error");
    }
  });

  // Empresa CRUD
  document.getElementById("busca-empresa").addEventListener("input", (e) => renderTabelaEmpresas(e.target.value));
  document.getElementById("btn-cancelar-empresa").addEventListener("click", resetFormEmpresa);
  document.getElementById("form-empresa").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("empresa-id").value;
    const payload = {
      nome: document.getElementById("empresa-nome").value,
      nomeLegal: document.getElementById("empresa-nome-legal").value,
      identificador: document.getElementById("empresa-identificador").value,
      email: document.getElementById("empresa-email").value,
      descricao: document.getElementById("empresa-descricao").value,
      senha: document.getElementById("empresa-senha").value,
    };
    const { status, data } = await apiFetch(id ? `/api/empresas/${id}` : "/api/empresas", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if ((status === 200 || status === 201) && data.sucesso) {
      showAlert(data.mensagem, "success");
      resetFormEmpresa();
      await carregarEmpresas();
    } else {
      showAlert((data.detalhes && data.detalhes.join(" ")) || data.erro || "Erro ao salvar empresa.", "error");
    }
  });

  // Carga inicial
  await Promise.all([
    carregarSessao(),
    carregarInstituicoes(),
    carregarAlunos(),
    carregarEmpresas(),
    carregarVantagens(),
    carregarNotificacoes(),
  ]);
  await Promise.all([carregarExtrato(), carregarResgates()]);
});
