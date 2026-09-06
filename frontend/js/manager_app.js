// Manager Portal Analytics & Visual Reporting Engine

let allCandidatesList = [];
let radarChartInstance = null;
let barChartInstance = null;

// ---- Manager authentication (password-gated portal) ----
function getMgrToken() {
  try { return sessionStorage.getItem("mgr_token") || ""; } catch (e) { return ""; }
}
function setMgrToken(t) {
  try { sessionStorage.setItem("mgr_token", t); } catch (e) { /* ignore */ }
}
function clearMgrToken() {
  try { sessionStorage.removeItem("mgr_token"); } catch (e) { /* ignore */ }
}
function mgrHeaders() {
  return { "X-Manager-Token": getMgrToken() };
}

// Show / hide the password prompt for the manager portal.
function showManagerLogin() {
  document.getElementById("managerLoginWrap")?.classList.remove("d-none");
  document.getElementById("managerDashboardWrap")?.classList.add("d-none");
  const err = document.getElementById("mgrLoginError");
  if (err) err.classList.add("d-none");
  setTimeout(() => document.getElementById("mgrPassword")?.focus(), 150);
}
function showManagerDashboard() {
  document.getElementById("managerLoginWrap")?.classList.add("d-none");
  document.getElementById("managerDashboardWrap")?.classList.remove("d-none");
}

// Called when the password form is submitted.
async function handleManagerLogin(event) {
  event.preventDefault();
  const pw = document.getElementById("mgrPassword").value;
  const errEl = document.getElementById("mgrLoginError");
  const btn = document.getElementById("btnMgrLogin");
  if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Verifying...`; }
  try {
    const res = await fetch("/api/manager/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pw })
    });
    if (res.ok) {
      const data = await res.json();
      setMgrToken(data.token);
      document.getElementById("mgrPassword").value = "";
      showManagerDashboard();
      loadManagerDashboard();
    } else {
      if (errEl) errEl.classList.remove("d-none");
    }
  } catch (e) {
    if (errEl) { errEl.textContent = "Connection error. Please try again."; errEl.classList.remove("d-none"); }
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = `<i class="fa-solid fa-unlock-keyhole me-2"></i> Unlock Manager Portal`; }
  }
}

function managerLogout() {
  clearMgrToken();
  showManagerLogin();
}

async function loadManagerDashboard() {
  // Gate: without a valid token, show the password prompt instead of fetching data.
  if (!getMgrToken()) {
    showManagerLogin();
    return;
  }
  try {
    const res = await fetch("/api/manager/candidates", { headers: mgrHeaders() });
    if (res.status === 401) {
      clearMgrToken();
      showManagerLogin();
      return;
    }
    allCandidatesList = await res.json();
    showManagerDashboard();
    renderCandidateTable(allCandidatesList);
    updateManagerKPIs(allCandidatesList);
  } catch (err) {
    console.error("Error loading candidates:", err);
  }
}

// Delete a single candidate (with confirmation), then refresh the dashboard.
async function deleteCandidate(sessionId, name) {
  const label = name ? `"${name}"` : "this candidate";
  if (!confirm(`Delete ${label}?\n\nThis permanently removes their submission, answers and proctoring log. This cannot be undone.`)) return;
  try {
    const res = await fetch(`/api/manager/candidate/${sessionId}`, { method: "DELETE", headers: mgrHeaders() });
    if (res.status === 401) { clearMgrToken(); showManagerLogin(); return; }
    if (res.ok) {
      loadManagerDashboard();
    } else {
      const d = await res.json().catch(() => ({}));
      alert(d.detail || "Could not delete this candidate.");
    }
  } catch (e) {
    alert("Connection error while deleting. Please try again.");
  }
}

// Delete every candidate record (with a strong confirmation), then refresh.
async function deleteAllCandidates() {
  const n = (allCandidatesList || []).length;
  if (n === 0) { alert("There are no candidate records to delete."); return; }
  if (!confirm(`Delete ALL ${n} candidate record(s)?\n\nThis permanently removes every submission, answer and proctoring log, and cannot be undone.`)) return;
  try {
    const res = await fetch(`/api/manager/candidates`, { method: "DELETE", headers: mgrHeaders() });
    if (res.status === 401) { clearMgrToken(); showManagerLogin(); return; }
    if (res.ok) {
      loadManagerDashboard();
    } else {
      alert("Could not delete the candidate records.");
    }
  } catch (e) {
    alert("Connection error while deleting. Please try again.");
  }
}

function updateManagerKPIs(candidates) {
  const total = candidates.length;
  // Count only genuine positive verdicts. Must exclude "Do Not Hire" (which contains the
  // substring "Hire") and "Pending Review" (candidate hasn't submitted yet).
  const hires = candidates.filter(c => {
    const v = (c.role_fit_verdict || "").toLowerCase();
    if (!v || v.includes("do not hire") || v.includes("pending")) return false;
    return v.includes("hired") || v.includes("great fit") || v.includes("qualified") || v.includes("strong");
  }).length;
  // Average only over candidates who actually submitted (a pending 0% is not a real score).
  const scored = candidates.filter(c => (c.role_fit_verdict || "").toLowerCase().indexOf("pending") === -1 && c.role_fit_verdict);
  const avgScore = scored.length > 0 ? Math.round(scored.reduce((acc, c) => acc + c.percentage, 0) / scored.length) : 0;
  const flagged = candidates.filter(c => c.integrity_score < 70).length;

  document.getElementById("mgrKpiTotal").textContent = total;
  document.getElementById("mgrKpiHires").textContent = hires;
  document.getElementById("mgrKpiAvgScore").textContent = `${avgScore}%`;
  document.getElementById("mgrKpiFlags").textContent = flagged;
}

function renderCandidateTable(candidates) {
  const tbody = document.getElementById("candidateTableBody");
  tbody.innerHTML = "";

  if (candidates.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No candidate submissions recorded yet.</td></tr>`;
    return;
  }

  candidates.forEach(c => {
    const verdictBadgeClass = getVerdictBadgeClass(c.role_fit_verdict);
    const integrityBadgeClass = c.integrity_score >= 80 ? "bg-success-subtle text-success" : (c.integrity_score >= 60 ? "bg-warning-subtle text-warning" : "bg-danger-subtle text-danger");

    // The report can only be opened once the candidate has actually submitted.
    // Non-submitted rows stay "Pending Review" with a locked action.
    const submitted = c.status === "submitted";
    const actionBtn = submitted
      ? `<button class="btn btn-primary btn-sm px-3 fw-semibold" onclick="viewCandidateReport('${c.session_id}')">
           <i class="fa-solid fa-chart-line me-1"></i> View Report
         </button>`
      : `<button class="btn btn-outline-secondary btn-sm px-3 fw-semibold" disabled title="Locked until the candidate submits the assessment">
           <i class="fa-solid fa-lock me-1"></i> Pending Review
         </button>`;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="ps-3">
        <div class="fw-bold text-dark">${c.full_name}</div>
        <div class="fs-8 text-muted">${c.email} • ${c.phone}</div>
      </td>
      <td><span class="badge bg-secondary-subtle text-secondary fs-8">${c.applied_role}</span></td>
      <td>${c.years_of_experience} yrs</td>
      <td>
        <div class="fw-bold text-primary fs-6">${c.percentage}%</div>
        <div class="fs-8 text-muted">${c.total_score} / ${c.max_score}</div>
      </td>
      <td><span class="badge ${verdictBadgeClass} fs-8 px-2 py-1">${c.role_fit_verdict}</span></td>
      <td><span class="badge ${integrityBadgeClass} fs-8">${c.integrity_score}%</span></td>
      <td class="fs-8 text-muted">${c.created_at}</td>
      <td class="text-end pe-3">
        <div class="d-inline-flex gap-2">
          ${actionBtn}
          <button class="btn btn-outline-danger btn-sm" title="Delete this candidate"
                  onclick="deleteCandidate('${c.session_id}', '${(c.full_name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'")}')">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function getVerdictBadgeClass(verdict) {
  if (!verdict) return "bg-light text-secondary";
  if (verdict.includes("Great Fit") || verdict.includes("Strong")) return "bg-success text-white";
  if (verdict.includes("Hired for") || verdict.includes("Hired")) return "bg-primary text-white";
  if (verdict.includes("Junior") || verdict.includes("Training")) return "bg-warning text-dark";
  return "bg-danger text-white";
}

function filterCandidates() {
  const roleFilter = document.getElementById("mgrFilterRole").value;
  const searchFilter = document.getElementById("mgrSearchName").value.toLowerCase();

  const filtered = allCandidatesList.filter(c => {
    const matchesRole = roleFilter === "" || c.applied_role === roleFilter;
    const matchesSearch = searchFilter === "" || c.full_name.toLowerCase().includes(searchFilter) || c.email.toLowerCase().includes(searchFilter);
    return matchesRole && matchesSearch;
  });

  renderCandidateTable(filtered);
}

// Open Detailed Intelligence Report Modal
async function viewCandidateReport(sessionId) {
  try {
    const res = await fetch(`/api/manager/candidate/${sessionId}/report`, { headers: mgrHeaders() });
    if (res.status === 401) {
      clearMgrToken();
      showManagerLogin();
      return;
    }
    const data = await res.json();
    if (!res.ok) {
      // e.g. 409 when the candidate has not submitted yet — do not open the analysis.
      alert(data.detail || "This report is not available yet.");
      return;
    }
    const rep = data.report;

    // Populate Headers
    document.getElementById("modalCandidateName").textContent = data.candidate.full_name;
    document.getElementById("modalCandidateRole").textContent = data.candidate.applied_role;
    document.getElementById("modalCandidateExp").textContent = `${data.candidate.years_of_experience} Years Experience`;
    document.getElementById("modalCandidateCompany").textContent = data.candidate.current_company || "N/A";

    // Verdict Card
    document.getElementById("modalVerdictHeading").textContent = rep.hiring_verdict;
    document.getElementById("modalVerdictBadge").textContent = rep.recommended_role || "Assessment Completed";
    document.getElementById("modalVerdictBadge").className = `badge bg-${rep.verdict_badge} fs-6 px-3 py-2 mb-2`;
    document.getElementById("modalVerdictRationale").textContent = rep.placement_advice || rep.summary_rationale;
    document.getElementById("modalScoreDisplay").textContent = `${rep.overall_score}%`;

    // 1. Populate Cross-Role Suitability Gauges
    const roleContainer = document.getElementById("modalRoleSuitabilityContainer");
    if (roleContainer) {
      roleContainer.innerHTML = "";
      if (rep.role_suitability) {
        Object.values(rep.role_suitability).forEach(r => {
          const item = document.createElement("div");
          // Only the role the candidate applied for is highlighted; the others are shown
          // plainly for context (no alarming colour on roles they did not apply to).
          item.className = r.applied
            ? "p-3 rounded-3 border border-primary border-2 bg-primary-subtle"
            : "p-3 rounded-3 border bg-light";
          const appliedTag = r.applied
            ? `<span class="badge bg-primary fs-9 ms-1">Applied For</span>`
            : "";
          item.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="fw-bold text-dark fs-7">${r.role_name}${appliedTag}</span>
              <span class="badge bg-${r.badge} fs-8">${r.fit_percentage}% Fit</span>
            </div>
            <div class="progress mb-2" style="height: 7px;">
              <div class="progress-bar bg-${r.badge}" style="width: ${r.fit_percentage}%"></div>
            </div>
            <div class="fs-9 text-muted">${r.status}</div>
          `;
          roleContainer.appendChild(item);
        });
      }
    }

    // 2. Populate 3-Tier Cognitive Breakdown
    const cogContainer = document.getElementById("modalCognitiveContainer");
    if (cogContainer) {
      cogContainer.innerHTML = "";
      if (rep.cognitive_summary) {
        const cogLevels = [
          { key: "basic", color: "success", icon: "fa-seedling" },
          { key: "intermediate", color: "primary", icon: "fa-gears" },
          { key: "advanced", color: "danger", icon: "fa-chess-king" }
        ];

        cogLevels.forEach(lvl => {
          const c = rep.cognitive_summary[lvl.key];
          if (c) {
            const item = document.createElement("div");
            item.className = "p-3 bg-light rounded-3 border";
            item.innerHTML = `
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-bold text-dark fs-7"><i class="fa-solid ${lvl.icon} text-${lvl.color} me-1"></i> ${c.label}</span>
                <span class="fw-bold text-${lvl.color} fs-7">${c.score}% (${c.correct}/${c.total})</span>
              </div>
              <div class="progress mb-2" style="height: 7px;">
                <div class="progress-bar bg-${lvl.color}" style="width: ${c.score}%"></div>
              </div>
              <div class="fs-9 text-muted">Tier Status: <strong>${c.status}</strong></div>
            `;
            cogContainer.appendChild(item);
          }
        });
      }
    }

    // Render Radar & Bar Charts
    renderRadarChart(rep.radar_scores);
    renderBarChart(rep.topic_breakdown);

    // Resume vs Reality Audit
    document.getElementById("modalResumeScoreBadge").textContent = `Verification Score: ${rep.resume_audit.score_pct}%`;
    const auditBody = document.getElementById("modalResumeAuditBody");
    auditBody.innerHTML = "";
    rep.resume_audit.items.forEach(item => {
      const isPass = item.result === "Passed";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="fw-semibold text-dark">${item.claimed_area}</td>
        <td>${item.tested_concept}</td>
        <td><span class="badge ${isPass ? 'bg-success' : 'bg-danger'}">${item.result}</span></td>
        <td><span class="fw-bold ${isPass ? 'text-success' : 'text-danger'}">${item.status}</span></td>
      `;
      auditBody.appendChild(tr);
    });

    // Proctoring Log
    document.getElementById("modalIntegrityBadge").textContent = `Integrity Score: ${rep.integrity_score}%`;
    const logContainer = document.getElementById("modalProctoringLog");
    logContainer.innerHTML = "";

    if (data.proctoring_logs.length === 0) {
      logContainer.innerHTML = `<div class="text-success"><i class="fa-solid fa-shield-check me-1"></i> Clean test session. Zero tab switches or unauthorized events detected.</div>`;
    } else {
      data.proctoring_logs.forEach(l => {
        const item = document.createElement("div");
        item.className = "py-1 border-bottom d-flex justify-content-between align-items-center";
        item.innerHTML = `
          <span><i class="fa-solid fa-triangle-exclamation text-danger me-1"></i> [${l.time_str}] ${l.details}</span>
          <span class="badge bg-secondary-subtle text-secondary fs-9">${l.created_at}</span>
        `;
        logContainer.appendChild(item);
      });
    }

    // Suggested In-Person Technical Questions
    const questionsContainer = document.getElementById("modalInterviewQuestions");
    questionsContainer.innerHTML = "";
    if (rep.suggested_interview_questions && rep.suggested_interview_questions.length > 0) {
      rep.suggested_interview_questions.forEach((q, idx) => {
        const qDiv = document.createElement("div");
        qDiv.className = "p-3 bg-light rounded-3 border-start border-4 border-primary";
        qDiv.innerHTML = `
          <div class="fw-bold text-dark fs-7 mb-1">${idx + 1}. ${q.suggested_question}</div>
          <div class="fs-8 text-muted"><strong class="text-secondary">Expected Evaluation Criteria:</strong> ${q.key_focus}</div>
        `;
        questionsContainer.appendChild(qDiv);
      });
    }

    const modal = new bootstrap.Modal(document.getElementById("candidateReportModal"));
    modal.show();

  } catch (err) {
    alert("Error fetching candidate intelligence report: " + err.message);
  }
}

// 6-Pillar Radar Chart
function renderRadarChart(radarData) {
  const ctx = document.getElementById("radarChart").getContext("2d");
  if (radarChartInstance) radarChartInstance.destroy();

  const labels = Object.keys(radarData);
  const dataValues = Object.values(radarData);

  radarChartInstance = new Chart(ctx, {
    type: "radar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Candidate Score %",
          data: dataValues,
          backgroundColor: "rgba(37, 99, 235, 0.2)",
          borderColor: "#2563eb",
          pointBackgroundColor: "#2563eb",
          borderWidth: 2
        },
        {
          label: "Company Benchmark %",
          data: [75, 75, 75, 75, 75, 75],
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          borderColor: "#f59e0b",
          borderDash: [4, 4],
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          suggestedMin: 0,
          suggestedMax: 100,
          ticks: { stepSize: 20 }
        }
      },
      plugins: {
        legend: { position: "top" }
      }
    }
  });
}

// Topic-wise Bar Chart
function renderBarChart(topicData) {
  const ctx = document.getElementById("barChart").getContext("2d");
  if (barChartInstance) barChartInstance.destroy();

  const labels = topicData.map(t => t.category.length > 20 ? t.category.substring(0, 18) + "..." : t.category);
  const scores = topicData.map(t => t.percentage);

  barChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Topic Accuracy %",
        data: scores,
        backgroundColor: scores.map(s => s >= 70 ? "#22c55e" : (s >= 50 ? "#f59e0b" : "#ef4444")),
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          suggestedMin: 0,
          suggestedMax: 100
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}


// Dedicated Multi-Page Print Handler for Executive Report

// Dedicated Multi-Page Executive Print Engine (Zero Blank Pages)
function printCandidateReport() {
  const modalElement = document.getElementById("candidateReportModal");
  if (!modalElement) return;

  const modalContent = modalElement.querySelector(".modal-content");
  if (!modalContent) return;

  // Clone modal content cleanly
  const cloned = modalContent.cloneNode(true);

  // Remove interactive buttons and print trigger from cloned version
  cloned.querySelectorAll("button, .btn, .btn-close, .modal-footer").forEach(el => el.remove());

  // Capture Chart.js canvases as high-res images
  const radarCanvas = document.getElementById("radarChart");
  const barCanvas = document.getElementById("barChart");

  let radarDataUrl = "";
  let barDataUrl = "";
  try {
    if (radarCanvas) radarDataUrl = radarCanvas.toDataURL("image/png");
    if (barCanvas) barDataUrl = barCanvas.toDataURL("image/png");
  } catch (e) {
    console.warn("Could not export canvas to image:", e);
  }

  // Create isolated print window
  const printWindow = window.open("", "_blank", "width=1000,height=1200");
  if (!printWindow) {
    alert("Please allow pop-ups for this site to print the executive report.");
    return;
  }

  printWindow.document.open();
  printWindow.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>SmartHire Finance - Executive Assessment Report</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
      <style>
        @page {
          size: A4 portrait;
          margin: 1.2cm 1.2cm 1.2cm 1.2cm;
        }
        body {
          font-family: 'Plus Jakarta Sans', sans-serif;
          color: #1e293b;
          background: #ffffff !important;
          padding: 0;
          margin: 0;
          font-size: 13px;
          line-height: 1.45;
        }
        .modal-header {
          background-color: #0f172a !important;
          color: #ffffff !important;
          padding: 1.25rem 1.5rem !important;
          border-radius: 8px !important;
          margin-bottom: 1.25rem !important;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }
        .modal-header * {
          color: #ffffff !important;
        }
        .card {
          border: 1px solid #cbd5e1 !important;
          box-shadow: none !important;
          margin-bottom: 1.25rem !important;
          background: #ffffff !important;
          border-radius: 8px !important;
          page-break-inside: avoid !important;
          break-inside: avoid !important;
        }
        .bg-light {
          background-color: #f8fafc !important;
        }
        .bg-primary { background-color: #2563eb !important; color: #ffffff !important; }
        .bg-success { background-color: #16a34a !important; color: #ffffff !important; }
        .bg-warning { background-color: #d97706 !important; color: #ffffff !important; }
        .bg-danger { background-color: #dc2626 !important; color: #ffffff !important; }
        
        .badge {
          display: inline-block !important;
          padding: 0.35em 0.65em !important;
          font-size: 0.75em !important;
          font-weight: 700 !important;
          border-radius: 0.25rem !important;
          border: 1px solid #cbd5e1 !important;
        }
        .progress {
          height: 8px !important;
          background-color: #e2e8f0 !important;
          border-radius: 4px !important;
          overflow: hidden !important;
        }
        .progress-bar {
          height: 100% !important;
        }
        table {
          width: 100% !important;
          margin-bottom: 0 !important;
          page-break-inside: auto !important;
        }
        tr {
          page-break-inside: avoid !important;
        }
        thead {
          display: table-header-group !important;
        }
        .chart-img-container {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 240px;
          padding: 10px;
        }
        .chart-img-container img {
          max-width: 100%;
          max-height: 230px;
          object-fit: contain;
        }
        * {
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
          color-adjust: exact !important;
        }
      </style>
    </head>
    <body>
      <div id="printRoot">
        ${cloned.innerHTML}
      </div>
    </body>
    </html>
  `);

  // Replace Canvas elements with generated images in print window
  const printDoc = printWindow.document;

  if (radarDataUrl) {
    const radarElem = printDoc.getElementById("radarChart");
    if (radarElem) {
      const container = printDoc.createElement("div");
      container.className = "chart-img-container";
      const img = printDoc.createElement("img");
      img.src = radarDataUrl;
      img.alt = "6-Pillar Radar Chart";
      container.appendChild(img);
      radarElem.parentNode.replaceChild(container, radarElem);
    }
  }

  if (barDataUrl) {
    const barElem = printDoc.getElementById("barChart");
    if (barElem) {
      const container = printDoc.createElement("div");
      container.className = "chart-img-container";
      const img = printDoc.createElement("img");
      img.src = barDataUrl;
      img.alt = "Topic Accuracy Bar Chart";
      container.appendChild(img);
      barElem.parentNode.replaceChild(container, barElem);
    }
  }

  printDoc.close();

  // Wait for images and fonts to load, then trigger native print
  setTimeout(() => {
    printWindow.focus();
    printWindow.print();
    // Keep window open until user prints or closes
  }, 500);
}
