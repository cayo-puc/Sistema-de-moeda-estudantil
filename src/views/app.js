/**
 * Camada de Apresentação / Front-end (View MVC) — Lab03S02.
 * Realiza a comunicação assíncrona via Fetch API com os endpoints REST do Back-end
 * (`/api/alunos`, `/api/empresas`, `/api/instituicoes`, `/api/cursos`).
 */

let estado = {
  instituicoes: [],
  cursos: [],
  alunos: [],
  empresas: [],
};

document.addEventListener("DOMContentLoaded", async () => {
  configurarAbas();
  configurarMascaras();
  configurarEventosAlunos();
  configurarEventosEmpresas();

  await carregarCatalogoAcademico();
  await Promise.all([carregarAlunos(), carregarEmpresas()]);
});

function configurarAbas() {
  const botoes = document.querySelectorAll(".tab-btn");
  const paineis = document.querySelectorAll(".tab-panel");

  botoes.forEach((btn) => {
    btn.addEventListener("click", () => {
      botoes.forEach((b) => b.classList.remove("active"));
      paineis.forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const alvo = document.getElementById(btn.dataset.tab);
      if (alvo) alvo.classList.add("active");
    });
  });
}

function exibirAlerta(mensagem, tipo = "success", detalhes = []) {
  const box = document.getElementById("alert-box");
  box.className = `alert alert-${tipo}`;
  let html = `<strong>${escapeHtml(mensagem)}</strong>`;
  if (Array.isArray(detalhes) && detalhes.length > 0) {
    html += `<ul style="margin-top:6px;margin-left:18px;">${detalhes
      .map((d) => `<li>${escapeHtml(d)}</li>`)
      .join("")}</ul>`;
  }
  box.innerHTML = html;
  box.classList.remove("hidden");

  window.clearTimeout(box._timer);
  box._timer = window.setTimeout(() => {
    box.classList.add("hidden");
  }, 6000);
}

function escapeHtml(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatarCpf(v) {
  const d = v.replace(/\D/g, "").slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9, 11)}`;
}

function formatarCnpj(v) {
  const d = v.replace(/\D/g, "").slice(0, 14);
  if (d.length <= 2) return d;
  if (d.length <= 5) return `${d.slice(0, 2)}.${d.slice(2)}`;
  if (d.length <= 8) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5)}`;
  if (d.length <= 12) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8)}`;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12, 14)}`;
}

function configurarMascaras() {
  const inputCpf = document.getElementById("aluno-cpf");
  inputCpf.addEventListener("input", (e) => {
    e.target.value = formatarCpf(e.target.value);
  });

  const inputCnpj = document.getElementById("empresa-identificador");
  inputCnpj.addEventListener("input", (e) => {
    e.target.value = formatarCnpj(e.target.value);
  });
}

// ============================================================================
// Catálogo Acadêmico Pré-Cadastrado (Instituições e Cursos)
// ============================================================================
async function carregarCatalogoAcademico() {
  try {
    const [resInst, resCursos] = await Promise.all([
      fetch("/api/instituicoes"),
      fetch("/api/cursos"),
    ]);
    const jsonInst = await resInst.json();
    const jsonCursos = await resCursos.json();

    estado.instituicoes = jsonInst.dados || [];
    estado.cursos = jsonCursos.dados || [];

    document.getElementById("stat-instituicoes").textContent = estado.instituicoes.length;

    const selectInst = document.getElementById("aluno-instituicao");
    selectInst.innerHTML =
      `<option value="">Selecione a instituição...</option>` +
      estado.instituicoes
        .map((i) => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.sigla)} — ${escapeHtml(i.nome)}</option>`)
        .join("");

    selectInst.addEventListener("change", () => {
      atualizarSelectCursos(selectInst.value, "");
    });
  } catch (err) {
    exibirAlerta("Erro ao carregar instituições e cursos pré-cadastrados.", "error");
  }
}

function atualizarSelectCursos(instituicaoId, cursoSelecionadoId = "") {
  const selectCurso = document.getElementById("aluno-curso");
  if (!instituicaoId) {
    selectCurso.innerHTML = `<option value="">Selecione primeiro a instituição...</option>`;
    return;
  }
  const filtrados = estado.cursos.filter((c) => c.instituicaoId === instituicaoId);
  selectCurso.innerHTML =
    `<option value="">Selecione o curso...</option>` +
    filtrados
      .map(
        (c) =>
          `<option value="${escapeHtml(c.id)}" ${
            c.id === cursoSelecionadoId ? "selected" : ""
          }>${escapeHtml(c.nome)}</option>`
      )
      .join("");
}

// ============================================================================
// CRUD DE ALUNOS
// ============================================================================
async function carregarAlunos() {
  try {
    const resp = await fetch("/api/alunos");
    const json = await resp.json();
    estado.alunos = json.dados || [];
    document.getElementById("stat-alunos").textContent = estado.alunos.length;
    renderizarTabelaAlunos();
  } catch (err) {
    exibirAlerta("Não foi possível carregar a lista de alunos.", "error");
  }
}

function renderizarTabelaAlunos() {
  const termo = (document.getElementById("busca-aluno").value || "").toLowerCase().trim();
  const tbody = document.getElementById("tabela-alunos-body");

  const filtrados = estado.alunos.filter((a) => {
    if (!termo) return true;
    return (
      (a.nome || "").toLowerCase().includes(termo) ||
      (a.email || "").toLowerCase().includes(termo) ||
      (a.cpf || "").toLowerCase().includes(termo) ||
      (a.cursoNome || "").toLowerCase().includes(termo) ||
      (a.instituicaoSigla || "").toLowerCase().includes(termo)
    );
  });

  if (filtrados.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-row">Nenhum aluno encontrado.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtrados
    .map(
      (a) => `
      <tr>
        <td>
          <div class="cell-primary">${escapeHtml(a.nome)}</div>
          <div class="cell-sub">${escapeHtml(a.email)}</div>
        </td>
        <td>
          <div><strong>CPF:</strong> ${escapeHtml(a.cpf)}</div>
          <div class="cell-sub"><strong>RG:</strong> ${escapeHtml(a.rg)}</div>
        </td>
        <td>
          <div class="cell-primary">${escapeHtml(a.instituicaoSigla || a.instituicaoNome)}</div>
          <div class="cell-sub">${escapeHtml(a.cursoNome)}</div>
        </td>
        <td>
          <div class="cell-sub">${escapeHtml(a.endereco)}</div>
        </td>
        <td>
          <span class="badge-coins">🪙 ${Number(a.saldoMoedas || 0)} moedas</span>
        </td>
        <td class="text-right">
          <div class="action-group">
            <button type="button" class="btn btn-sm btn-edit" onclick="iniciarEdicaoAluno('${escapeHtml(a.id)}')">
              Editar
            </button>
            <button type="button" class="btn btn-sm btn-delete" onclick="excluirAluno('${escapeHtml(a.id)}')">
              Excluir
            </button>
          </div>
        </td>
      </tr>
    `
    )
    .join("");
}

function configurarEventosAlunos() {
  const form = document.getElementById("form-aluno");
  const btnCancelar = document.getElementById("btn-cancelar-aluno");
  const inputBusca = document.getElementById("busca-aluno");

  inputBusca.addEventListener("input", renderizarTabelaAlunos);
  btnCancelar.addEventListener("click", resetarFormularioAluno);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const alunoId = document.getElementById("aluno-id").value.trim();
    const payload = {
      nome: document.getElementById("aluno-nome").value.trim(),
      cpf: document.getElementById("aluno-cpf").value.trim(),
      rg: document.getElementById("aluno-rg").value.trim(),
      email: document.getElementById("aluno-email").value.trim(),
      endereco: document.getElementById("aluno-endereco").value.trim(),
      instituicaoId: document.getElementById("aluno-instituicao").value,
      cursoId: document.getElementById("aluno-curso").value,
      senha: document.getElementById("aluno-senha").value,
    };

    const url = alunoId ? `/api/alunos/${encodeURIComponent(alunoId)}` : "/api/alunos";
    const metodo = alunoId ? "PUT" : "POST";

    try {
      const resp = await fetch(url, {
        method: metodo,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await resp.json();

      if (!resp.ok || !json.sucesso) {
        exibirAlerta(json.erro || "Erro ao salvar aluno.", "error", json.detalhes || []);
        return;
      }

      exibirAlerta(json.mensagem || "Operação concluída com sucesso!", "success");
      resetarFormularioAluno();
      await carregarAlunos();
    } catch (err) {
      exibirAlerta("Erro de comunicação com o servidor Back-end.", "error");
    }
  });
}

window.iniciarEdicaoAluno = function (alunoId) {
  const aluno = estado.alunos.find((a) => a.id === alunoId);
  if (!aluno) return;

  document.getElementById("aluno-id").value = aluno.id;
  document.getElementById("aluno-nome").value = aluno.nome;
  document.getElementById("aluno-cpf").value = aluno.cpf;
  document.getElementById("aluno-rg").value = aluno.rg;
  document.getElementById("aluno-email").value = aluno.email;
  document.getElementById("aluno-endereco").value = aluno.endereco;
  document.getElementById("aluno-instituicao").value = aluno.instituicaoId;
  atualizarSelectCursos(aluno.instituicaoId, aluno.cursoId);
  document.getElementById("aluno-senha").value = "";

  document.getElementById("form-aluno-titulo").textContent = "Editar Aluno";
  const badgeModo = document.getElementById("form-aluno-modo");
  badgeModo.textContent = "Modo: Edição (PUT)";
  badgeModo.className = "badge badge-amber";

  document.getElementById("label-aluno-senha").textContent = "Nova Senha (deixe em branco para manter a atual)";
  document.getElementById("btn-salvar-aluno").textContent = "Salvar Alterações";
  document.getElementById("btn-cancelar-aluno").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
};

function resetarFormularioAluno() {
  document.getElementById("form-aluno").reset();
  document.getElementById("aluno-id").value = "";
  atualizarSelectCursos("", "");

  document.getElementById("form-aluno-titulo").textContent = "Novo Cadastro de Aluno";
  const badgeModo = document.getElementById("form-aluno-modo");
  badgeModo.textContent = "Modo: Criação (POST)";
  badgeModo.className = "badge badge-blue";

  document.getElementById("label-aluno-senha").textContent = "Senha de Acesso * (mín. 6 caracteres)";
  document.getElementById("btn-salvar-aluno").textContent = "Cadastrar Aluno";
  document.getElementById("btn-cancelar-aluno").classList.add("hidden");
}

window.excluirAluno = async function (alunoId) {
  const aluno = estado.alunos.find((a) => a.id === alunoId);
  const nome = aluno ? aluno.nome : alunoId;
  if (!window.confirm(`Deseja realmente excluir o aluno "${nome}" e sua conta de moedas?`)) {
    return;
  }

  try {
    const resp = await fetch(`/api/alunos/${encodeURIComponent(alunoId)}`, {
      method: "DELETE",
    });
    const json = await resp.json();
    if (!resp.ok || !json.sucesso) {
      exibirAlerta(json.erro || "Não foi possível excluir o aluno.", "error");
      return;
    }
    exibirAlerta(json.mensagem || "Aluno excluído com sucesso.", "success");
    if (document.getElementById("aluno-id").value === alunoId) {
      resetarFormularioAluno();
    }
    await carregarAlunos();
  } catch (err) {
    exibirAlerta("Erro de comunicação ao tentar excluir aluno.", "error");
  }
};

// ============================================================================
// CRUD DE EMPRESAS PARCEIRAS
// ============================================================================
async function carregarEmpresas() {
  try {
    const resp = await fetch("/api/empresas");
    const json = await resp.json();
    estado.empresas = json.dados || [];
    document.getElementById("stat-empresas").textContent = estado.empresas.length;
    renderizarTabelaEmpresas();
  } catch (err) {
    exibirAlerta("Não foi possível carregar a lista de empresas parceiras.", "error");
  }
}

function renderizarTabelaEmpresas() {
  const termo = (document.getElementById("busca-empresa").value || "").toLowerCase().trim();
  const tbody = document.getElementById("tabela-empresas-body");

  const filtradas = estado.empresas.filter((e) => {
    if (!termo) return true;
    return (
      (e.nome || "").toLowerCase().includes(termo) ||
      (e.nomeLegal || "").toLowerCase().includes(termo) ||
      (e.identificador || "").toLowerCase().includes(termo) ||
      (e.email || "").toLowerCase().includes(termo)
    );
  });

  if (filtradas.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Nenhuma empresa parceira encontrada.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtradas
    .map(
      (e) => `
      <tr>
        <td>
          <div class="cell-primary">${escapeHtml(e.nome)}</div>
          <div class="cell-sub">${escapeHtml(e.email)}</div>
        </td>
        <td>${escapeHtml(e.nomeLegal)}</td>
        <td><strong>${escapeHtml(e.identificador)}</strong></td>
        <td>
          <div class="cell-sub">${escapeHtml(e.descricao || "—")}</div>
        </td>
        <td class="text-right">
          <div class="action-group">
            <button type="button" class="btn btn-sm btn-edit" onclick="iniciarEdicaoEmpresa('${escapeHtml(e.id)}')">
              Editar
            </button>
            <button type="button" class="btn btn-sm btn-delete" onclick="excluirEmpresa('${escapeHtml(e.id)}')">
              Excluir
            </button>
          </div>
        </td>
      </tr>
    `
    )
    .join("");
}

function configurarEventosEmpresas() {
  const form = document.getElementById("form-empresa");
  const btnCancelar = document.getElementById("btn-cancelar-empresa");
  const inputBusca = document.getElementById("busca-empresa");

  inputBusca.addEventListener("input", renderizarTabelaEmpresas);
  btnCancelar.addEventListener("click", resetarFormularioEmpresa);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const empresaId = document.getElementById("empresa-id").value.trim();
    const payload = {
      nome: document.getElementById("empresa-nome").value.trim(),
      nomeLegal: document.getElementById("empresa-nome-legal").value.trim(),
      identificador: document.getElementById("empresa-identificador").value.trim(),
      email: document.getElementById("empresa-email").value.trim(),
      descricao: document.getElementById("empresa-descricao").value.trim(),
      senha: document.getElementById("empresa-senha").value,
    };

    const url = empresaId ? `/api/empresas/${encodeURIComponent(empresaId)}` : "/api/empresas";
    const metodo = empresaId ? "PUT" : "POST";

    try {
      const resp = await fetch(url, {
        method: metodo,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await resp.json();

      if (!resp.ok || !json.sucesso) {
        exibirAlerta(json.erro || "Erro ao salvar empresa parceira.", "error", json.detalhes || []);
        return;
      }

      exibirAlerta(json.mensagem || "Empresa parceira salva com sucesso!", "success");
      resetarFormularioEmpresa();
      await carregarEmpresas();
    } catch (err) {
      exibirAlerta("Erro de comunicação com o servidor Back-end.", "error");
    }
  });
}

window.iniciarEdicaoEmpresa = function (empresaId) {
  const emp = estado.empresas.find((e) => e.id === empresaId);
  if (!emp) return;

  document.getElementById("empresa-id").value = emp.id;
  document.getElementById("empresa-nome").value = emp.nome;
  document.getElementById("empresa-nome-legal").value = emp.nomeLegal;
  document.getElementById("empresa-identificador").value = emp.identificador;
  document.getElementById("empresa-email").value = emp.email;
  document.getElementById("empresa-descricao").value = emp.descricao || "";
  document.getElementById("empresa-senha").value = "";

  document.getElementById("form-empresa-titulo").textContent = "Editar Empresa Parceira";
  const badgeModo = document.getElementById("form-empresa-modo");
  badgeModo.textContent = "Modo: Edição (PUT)";
  badgeModo.className = "badge badge-amber";

  document.getElementById("label-empresa-senha").textContent = "Nova Senha (deixe em branco para manter a atual)";
  document.getElementById("btn-salvar-empresa").textContent = "Salvar Alterações";
  document.getElementById("btn-cancelar-empresa").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
};

function resetarFormularioEmpresa() {
  document.getElementById("form-empresa").reset();
  document.getElementById("empresa-id").value = "";

  document.getElementById("form-empresa-titulo").textContent = "Nova Empresa Parceira";
  const badgeModo = document.getElementById("form-empresa-modo");
  badgeModo.textContent = "Modo: Criação (POST)";
  badgeModo.className = "badge badge-blue";

  document.getElementById("label-empresa-senha").textContent = "Senha de Acesso * (mín. 6 caracteres)";
  document.getElementById("btn-salvar-empresa").textContent = "Cadastrar Empresa Parceira";
  document.getElementById("btn-cancelar-empresa").classList.add("hidden");
}

window.excluirEmpresa = async function (empresaId) {
  const emp = estado.empresas.find((e) => e.id === empresaId);
  const nome = emp ? emp.nome : empresaId;
  if (!window.confirm(`Deseja realmente excluir a empresa parceira "${nome}"?`)) {
    return;
  }

  try {
    const resp = await fetch(`/api/empresas/${encodeURIComponent(empresaId)}`, {
      method: "DELETE",
    });
    const json = await resp.json();
    if (!resp.ok || !json.sucesso) {
      exibirAlerta(json.erro || "Não foi possível excluir a empresa parceira.", "error");
      return;
    }
    exibirAlerta(json.mensagem || "Empresa parceira excluída com sucesso.", "success");
    if (document.getElementById("empresa-id").value === empresaId) {
      resetarFormularioEmpresa();
    }
    await carregarEmpresas();
  } catch (err) {
    exibirAlerta("Erro de comunicação ao tentar excluir empresa parceira.", "error");
  }
};

