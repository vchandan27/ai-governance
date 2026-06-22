const state = {
  frameworks: [],
  selected: new Set(),
  mode: "upload", // upload | paste | sample
  file: null,
  lastResult: null,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const SAMPLE_POLICY = `Acme Corp Responsible AI Policy

1. Purpose and scope
This policy governs the development and deployment of artificial intelligence
systems across Acme Corp. It applies to all employees and contractors.

2. Governance and accountability
The AI Governance Board, chaired by the Chief AI Officer, owns this policy.
Roles and responsibilities for AI risk are assigned across product and legal
teams. The board reviews this policy annually.

3. Risk management
We maintain a risk assessment process for AI systems. Each system is reviewed
for potential harms to individuals before launch and risks are mitigated.

4. Data governance
Training data is reviewed for quality and representativeness. We document the
provenance of datasets and examine them for bias before use.

5. Human oversight
All customer-facing automated decisions include a human-in-the-loop. Operators
can override or stop the system at any time.

6. Transparency
We inform users when they are interacting with an AI system and provide
instructions for use.

7. Monitoring
Deployed systems are monitored in production and incidents are logged and
reviewed by the governance board.`;

async function init() {
  await loadFrameworks();
  wireTabs();
  wireDropzone();
  wireButtons();
}

async function loadFrameworks() {
  const list = $("#framework-list");
  try {
    const res = await fetch("/api/frameworks");
    state.frameworks = await res.json();
    list.innerHTML = "";
    state.frameworks.forEach((fw) => {
      state.selected.add(fw.id);
      const label = document.createElement("label");
      label.className = "framework-item";
      label.innerHTML = `
        <input type="checkbox" value="${fw.id}" checked />
        <div>
          <div class="fw-name">${fw.name}</div>
          <div class="fw-meta">${fw.version} · ${fw.control_count} controls</div>
          <div class="fw-desc">${fw.description}</div>
        </div>`;
      const cb = label.querySelector("input");
      cb.addEventListener("change", () => {
        cb.checked ? state.selected.add(fw.id) : state.selected.delete(fw.id);
      });
      list.appendChild(label);
    });
  } catch (e) {
    list.innerHTML = `<p class="status-msg error">Could not load frameworks: ${e}</p>`;
  }
}

function wireTabs() {
  $$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".tab").forEach((t) => t.classList.remove("active"));
      $$(".tab-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      state.mode = tab.dataset.tab;
      $(`.tab-panel[data-panel="${state.mode}"]`).classList.add("active");
    });
  });
}

function wireDropzone() {
  const dz = $("#dropzone");
  const input = $("#file-input");
  input.addEventListener("change", () => setFile(input.files[0]));
  ["dragover", "dragenter"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); })
  );
  dz.addEventListener("drop", (e) => {
    if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
  });
}

function setFile(file) {
  state.file = file;
  $("#dz-text").textContent = file ? `Selected: ${file.name}` : "Drag & drop or click to select";
}

function wireButtons() {
  $("#analyze-btn").addEventListener("click", analyze);
  $("#load-sample").addEventListener("click", () => {
    $("#text-input").value = SAMPLE_POLICY;
    setStatus("Sample loaded into the paste tab — click Analyze.", "");
    document.querySelector('.tab[data-tab="paste"]').click();
  });
  $("#download-md").addEventListener("click", () => downloadReport("markdown"));
  $("#download-json").addEventListener("click", () => downloadReport("json"));
}

function selectedFrameworks() {
  return Array.from(state.selected).join(",");
}

function setStatus(msg, cls) {
  const el = $("#status-msg");
  el.textContent = msg;
  el.className = "status-msg " + (cls || "");
}

async function analyze() {
  if (state.selected.size === 0) {
    setStatus("Select at least one framework.", "error");
    return;
  }
  let endpoint, body;
  if (state.mode === "upload") {
    if (!state.file) { setStatus("Please choose a file to upload.", "error"); return; }
    body = new FormData();
    body.append("file", state.file);
    body.append("frameworks", selectedFrameworks());
    endpoint = "/api/analyze";
  } else {
    const text = $("#text-input").value.trim();
    if (!text) { setStatus("Paste some policy text (or load the sample).", "error"); return; }
    body = new FormData();
    body.append("text", text);
    body.append("frameworks", selectedFrameworks());
    endpoint = "/api/analyze/text";
  }

  setStatus("Analyzing…", "loading");
  $("#analyze-btn").disabled = true;
  try {
    const res = await fetch(endpoint, { method: "POST", body });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${res.status})`);
    }
    const result = await res.json();
    state.lastResult = result;
    renderResults(result);
    setStatus(`Analyzed ${result.segments_analyzed} segments of "${result.document_name}".`, "");
    $("#download-md").disabled = false;
    $("#download-json").disabled = false;
  } catch (e) {
    setStatus(e.message, "error");
  } finally {
    $("#analyze-btn").disabled = false;
  }
}

async function downloadReport(fmt) {
  if (!state.lastResult) return;
  // Re-run via the report endpoint using text where possible.
  const body = new FormData();
  body.append("fmt", fmt);
  body.append("frameworks", selectedFrameworks());
  if (state.mode === "upload" && state.file) {
    body.append("file", state.file);
    const res = await fetch("/api/report", { method: "POST", body });
    triggerDownload(await res.blob(), fmt);
  } else {
    // For pasted text, build the report client-side from JSON for markdown,
    // or just download the stored JSON.
    if (fmt === "json") {
      const blob = new Blob([JSON.stringify(state.lastResult, null, 2)], { type: "application/json" });
      triggerDownload(blob, "json");
    } else {
      const blob = new Blob([buildMarkdown(state.lastResult)], { type: "text/markdown" });
      triggerDownload(blob, "markdown");
    }
  }
}

function triggerDownload(blob, fmt) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fmt === "json" ? "ai-governance-report.json" : "ai-governance-report.md";
  a.click();
  URL.revokeObjectURL(url);
}

const STATUS_LABEL = { covered: "Covered", partial: "Partial", gap: "Gap" };

function renderResults(r) {
  $("#results").classList.remove("hidden");
  const g = $("#overall-gauge");
  g.style.setProperty("--val", r.summary.overall_score);
  $("#overall-score").textContent = Math.round(r.summary.overall_score);
  $("#stat-covered").textContent = r.summary.covered;
  $("#stat-partial").textContent = r.summary.partial;
  $("#stat-gap").textContent = r.summary.gaps;

  const pg = $("#priority-gaps");
  pg.innerHTML = "";
  if (!r.summary.top_gaps.length) {
    pg.innerHTML = `<li>No outstanding gaps in the selected frameworks. 🎉</li>`;
  }
  r.summary.top_gaps.forEach((c) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="badge ${c.status}">${STATUS_LABEL[c.status]}</span>
      <div>
        <div><strong>${c.title}</strong> <span class="muted">(${c.reference})</span></div>
        ${c.recommendation ? `<div class="rec">${c.recommendation}</div>` : ""}
      </div>`;
    pg.appendChild(li);
  });

  const fwContainer = $("#framework-results");
  fwContainer.innerHTML = "";
  r.frameworks.forEach((fw) => fwContainer.appendChild(renderFramework(fw)));

  renderCrosswalk(r);
  $("#results").scrollIntoView({ behavior: "smooth" });
}

function renderFramework(fw) {
  const block = document.createElement("div");
  block.className = "card fw-block";
  const total = fw.total_controls || 1;
  const pc = (fw.covered / total) * 100;
  const pp = (fw.partial / total) * 100;
  const pg = (fw.gaps / total) * 100;
  block.innerHTML = `
    <div class="fw-header">
      <div>
        <h2 style="margin-bottom:2px">${fw.name}</h2>
        <div class="muted">${fw.version} · <a href="${fw.reference_url}" target="_blank" rel="noopener" style="color:var(--accent)">reference</a></div>
      </div>
      <div style="text-align:right">
        <div class="fw-score">${fw.compliance_score}<small class="muted">/100</small></div>
        <div class="muted">${fw.covered} covered · ${fw.partial} partial · ${fw.gaps} gaps</div>
      </div>
    </div>
    <div class="bar">
      <i class="covered" style="width:${pc}%"></i>
      <i class="partial" style="width:${pp}%"></i>
      <i class="gap" style="width:${pg}%"></i>
    </div>
    <div class="controls"></div>`;
  const cc = block.querySelector(".controls");
  fw.controls.forEach((c) => cc.appendChild(renderControl(c)));
  return block;
}

function renderControl(c) {
  const el = document.createElement("div");
  el.className = "control";
  const evidence = c.evidence
    .map(
      (e) => `<div class="ev">${escapeHtml(e.text)}<div class="sim">similarity ${e.similarity}</div></div>`
    )
    .join("");
  const kws = c.matched_keywords.map((k) => `<span class="kw">${escapeHtml(k)}</span>`).join("");
  el.innerHTML = `
    <div class="control-head">
      <span class="badge ${c.status}">${STATUS_LABEL[c.status]}</span>
      <div class="c-title"><strong>${c.title}</strong> <span class="ref">${c.reference}</span></div>
      <span class="score-pill">score ${c.score.toFixed(2)}</span>
      <span class="muted">▾</span>
    </div>
    <div class="control-body">
      <div class="desc">${escapeHtml(c.description)}</div>
      ${c.recommendation ? `<div class="rec-box">💡 ${escapeHtml(c.recommendation)}</div>` : ""}
      ${kws ? `<div style="margin-bottom:10px">${kws}</div>` : ""}
      ${evidence ? `<div class="evidence"><div class="muted">Supporting evidence from your policy:</div>${evidence}</div>`
        : `<div class="muted">No supporting passages found.</div>`}
    </div>`;
  el.querySelector(".control-head").addEventListener("click", () => el.classList.toggle("open"));
  return el;
}

function renderCrosswalk(r) {
  const table = $("#crosswalk-table");
  const heads = r.frameworks.map((f) => `<th>${f.short_name}</th>`).join("");
  let rows = "";
  r.crosswalk.forEach((theme) => {
    const cells = r.frameworks
      .map((f) => {
        const st = theme.statuses[f.framework_id];
        const cls = st || "none";
        const label = st ? STATUS_LABEL[st] : "—";
        return `<td><span class="cell-status ${cls}">${label}</span></td>`;
      })
      .join("");
    rows += `<tr><td>${theme.title}</td>${cells}<td><span class="cell-status ${theme.overall_status}">${STATUS_LABEL[theme.overall_status]}</span></td></tr>`;
  });
  table.innerHTML = `<thead><tr><th>Theme</th>${heads}<th>Overall</th></tr></thead><tbody>${rows}</tbody>`;
}

// Minimal client-side markdown builder for pasted-text reports.
function buildMarkdown(r) {
  const L = [];
  L.push(`# AI Governance Coverage Report`, "");
  L.push(`- Document: ${r.document_name}`);
  L.push(`- Overall score: ${r.summary.overall_score}/100`);
  L.push(`- Covered ${r.summary.covered} / Partial ${r.summary.partial} / Gaps ${r.summary.gaps}`, "");
  r.frameworks.forEach((fw) => {
    L.push(`## ${fw.name} — ${fw.compliance_score}/100`, "");
    fw.controls.forEach((c) => {
      L.push(`- [${c.status}] ${c.title} (${c.reference}) — score ${c.score.toFixed(2)}`);
      if (c.recommendation) L.push(`  - ${c.recommendation}`);
    });
    L.push("");
  });
  return L.join("\n");
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (m) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])
  );
}

init();
