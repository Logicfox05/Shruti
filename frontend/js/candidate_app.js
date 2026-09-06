// Candidate Portal Logic & Background Proctoring Engine

let currentSession = null;
let questionsList = [];        // questions served so far (grows one batch at a time)
let currentQuestionIndex = 0;
let timerInterval = null;
let remainingSeconds = 3600;
let proctoringStartTime = null;

// Adaptive-flow state. The exam is served in batches of 5; earlier batches lock
// (viewable read-only) once the candidate continues. None of this is shown to them.
let totalQuestions = 80;
let activeBatchStart = 1;      // 1-based question_number of the first question in the current batch
let examFinished = false;      // true once the engine has served all 80 and graded the last batch
let batchSubmitInFlight = false;
let proctoringActive = false;  // proctoring only logs while the exam is genuinely in progress

// Instant Resume Upload & Auto-Fill Handler
async function handleFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const fileNameDiv = document.getElementById("selectedFileName");
  fileNameDiv.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-primary me-2"></i> Analyzing ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`;
  fileNameDiv.classList.remove("d-none");

  const formData = new FormData();
  formData.append("resume", file);

  try {
    const res = await fetch("/api/candidate/parse-resume-preview", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      // Auto-fill form fields if empty or extracted with high confidence
      if (data.full_name && !document.getElementById("reg_full_name").value) {
        document.getElementById("reg_full_name").value = data.full_name;
      }
      if (data.email && !document.getElementById("reg_email").value) {
        document.getElementById("reg_email").value = data.email;
      }
      if (data.phone && !document.getElementById("reg_phone").value) {
        document.getElementById("reg_phone").value = data.phone;
      }
      // NOTE: experience is intentionally NOT auto-filled from the resume — it must be
      // entered by the candidate. We never predict/guess years of experience.

      // Display live extracted skills badges
      const skillsHtml = data.detected_skills.map(s => `<span class="badge bg-primary-subtle text-primary border border-primary-subtle fs-8 me-1 mb-1">${s}</span>`).join("");
      const degreeText = data.detected_degrees.length > 0 ? `• Degree: <strong>${data.detected_degrees.join(", ")}</strong>` : "";
      const cgpaText = data.cgpa ? `(${data.cgpa})` : "";

      fileNameDiv.innerHTML = `
        <div class="p-2 bg-success-subtle border border-success rounded text-success-emphasis fs-8 mt-2">
          <div class="fw-bold mb-1"><i class="fa-solid fa-circle-check text-success me-1"></i> Resume Analyzed: <strong>${file.name}</strong></div>
          <div class="mb-1"><strong>Domain:</strong> ${data.primary_domain} ${degreeText} ${cgpaText}</div>
          <div><strong>Extracted Skills:</strong><div class="mt-1 d-flex flex-wrap">${skillsHtml || '<span class="text-muted">General Profile</span>'}</div></div>
        </div>
      `;
    }
  } catch (err) {
    fileNameDiv.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }
}

// Stage 1: Candidate Registration & Resume Upload
async function handleCandidateRegister(event) {
  event.preventDefault();
  const btn = document.getElementById("btnRegisterSubmit");
  const originalBtnHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Parsing Resume & Initializing 80 Questions...`;

  // Years of experience is COMPULSORY: it must be typed by the candidate (never guessed).
  const expInput = document.getElementById("reg_experience");
  const expVal = expInput.value.trim();
  if (expVal === "" || isNaN(parseFloat(expVal)) || parseFloat(expVal) < 0) {
    btn.disabled = false;
    btn.innerHTML = originalBtnHtml;
    expInput.classList.add("is-invalid");
    expInput.focus();
    alert("Please enter your total relevant experience in years (enter 0 if you are a fresher).");
    return;
  }
  expInput.classList.remove("is-invalid");

  const formData = new FormData();
  formData.append("full_name", document.getElementById("reg_full_name").value);
  formData.append("email", document.getElementById("reg_email").value);
  formData.append("phone", document.getElementById("reg_phone").value);
  formData.append("applied_role", document.getElementById("reg_applied_role").value);
  formData.append("years_of_experience", expVal);
  formData.append("current_company", document.getElementById("reg_company").value || "");

  const fileInput = document.getElementById("reg_resume");
  if (fileInput.files[0]) {
    formData.append("resume", fileInput.files[0]);
  }

  try {
    const response = await fetch("/api/candidate/register", {
      method: "POST",
      body: formData
    });
    const data = await response.json();

    if (data.success) {
      currentSession = data;
      // Move to Stage 2: Instructions
      document.getElementById("candidate-stage-register").classList.add("d-none");
      document.getElementById("candidate-stage-instructions").classList.remove("d-none");
    } else {
      alert("Registration failed: " + (data.detail || "Unknown error"));
    }
  } catch (err) {
    alert("Connection error while uploading resume: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `Proceed to Assessment Pre-Check <i class="fa-solid fa-arrow-right ms-2"></i>`;
  }
}

// Stage 2: Start 60-Minute Assessment Session
async function startAssessmentSession() {
  const chk = document.getElementById("chkAgreeRules");
  if (!chk.checked) {
    alert("Please check the box to confirm you agree to the rules and time limit.");
    return;
  }

  // Request Fullscreen
  try {
    if (document.documentElement.requestFullscreen) {
      await document.documentElement.requestFullscreen();
    }
  } catch (e) {
    console.log("Fullscreen request bypassed:", e);
  }

  // Fetch the opening batch (server-driven adaptive delivery)
  try {
    const res = await fetch(`/api/assessment/${currentSession.session_id}/start`);
    const data = await res.json();
    questionsList = data.questions || [];
    totalQuestions = data.total_questions || 80;
    activeBatchStart = data.active_batch_start || 1;
    examFinished = !!data.finished;
    remainingSeconds = data.remaining_seconds || 3600;

    // Set Candidate Headers
    document.getElementById("examCandidateName").textContent = data.candidate_name;
    document.getElementById("examCandidateRole").textContent = data.applied_role;

    // Show Stage 3
    document.getElementById("candidate-stage-instructions").classList.add("d-none");
    document.getElementById("candidate-stage-exam").classList.remove("d-none");

    // Init Proctoring Listeners
    initProctoring();

    // Render Palette & jump to the first question of the current (active) batch
    renderPalette();
    loadQuestion(indexForQuestionNumber(activeBatchStart));

    // Start 60-min timer
    startCountdownTimer();
  } catch (err) {
    alert("Error launching assessment: " + err.message);
  }
}

// Map a 1-based question_number to its index in questionsList (fallback: last served).
function indexForQuestionNumber(qnum) {
  const idx = questionsList.findIndex(q => q.question_number === qnum);
  return idx >= 0 ? idx : Math.max(0, questionsList.length - 1);
}

// A question is locked (read-only) once its batch has been submitted, i.e. it sits
// before the current active batch.
function isLocked(q) {
  return !!q && q.question_number < activeBatchStart;
}

// Countdown Timer Engine
function startCountdownTimer() {
  clearInterval(timerInterval);
  updateTimerDisplay();

  timerInterval = setInterval(() => {
    remainingSeconds--;
    updateTimerDisplay();

    if (remainingSeconds <= 300) {
      document.getElementById("timerContainer").classList.add("timer-danger");
    }

    if (remainingSeconds <= 0) {
      clearInterval(timerInterval);
      alert("Time limit of 60 minutes has expired. Your test will now be submitted automatically.");
      finalizeAndSubmitAssessment();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const m = Math.floor(remainingSeconds / 60);
  const s = remainingSeconds % 60;
  document.getElementById("examTimerDisplay").textContent = 
    `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// Render Question by Index
function loadQuestion(index) {
  if (index < 0 || index >= questionsList.length) return;
  currentQuestionIndex = index;
  const q = questionsList[index];
  const locked = isLocked(q);

  document.getElementById("qNumberBadge").textContent = `Question ${q.question_number} of ${totalQuestions}`;
  document.getElementById("qTextDisplay").textContent = q.question_text;

  // Render Options (read-only if the question's batch is already locked)
  const container = document.getElementById("optionsContainer");
  container.innerHTML = "";

  const options = [
    { key: "A", text: q.option_a },
    { key: "B", text: q.option_b },
    { key: "C", text: q.option_c },
    { key: "D", text: q.option_d }
  ];

  options.forEach(opt => {
    const isSelected = q.selected_option === opt.key;
    const optDiv = document.createElement("div");
    optDiv.className = `option-card p-3 rounded-3 d-flex align-items-center gap-3 ${isSelected ? 'selected' : ''} ${locked ? 'opacity-75' : ''}`;
    if (!locked) {
      optDiv.style.cursor = "pointer";
      optDiv.onclick = () => selectOption(opt.key, optDiv);
    }
    optDiv.innerHTML = `
      <div class="form-check m-0">
        <input class="form-check-input" type="radio" name="optionRadio" id="opt_${opt.key}" value="${opt.key}" ${isSelected ? 'checked' : ''} ${locked ? 'disabled' : ''}>
      </div>
      <div class="fw-bold text-primary font-monospace">${opt.key}.</div>
      <div class="fs-7 text-dark">${opt.text}</div>
    `;
    container.appendChild(optDiv);
  });

  // Flag button — only meaningful for the active batch
  const flagBtn = document.getElementById("btnFlagQuestion");
  if (flagBtn) {
    flagBtn.disabled = locked;
    flagBtn.style.visibility = locked ? "hidden" : "visible";
    if (q.is_flagged) {
      flagBtn.className = "btn btn-warning btn-sm fs-8 fw-semibold";
      flagBtn.innerHTML = `<i class="fa-solid fa-bookmark me-1"></i> Flagged for Review`;
    } else {
      flagBtn.className = "btn btn-outline-warning btn-sm fs-8 fw-semibold";
      flagBtn.innerHTML = `<i class="fa-regular fa-bookmark me-1"></i> Mark for Review`;
    }
  }

  // "Clear Answer" only for the active, unlocked question
  const clearBtn = document.getElementById("btnClearAnswer");
  if (clearBtn) clearBtn.style.visibility = locked ? "hidden" : "visible";

  // Navigation buttons
  document.getElementById("btnPrevQ").disabled = (index === 0);
  const nextBtn = document.getElementById("btnNextQ");
  const isLastServed = (index === questionsList.length - 1);
  if (isLastServed) {
    // End of the current batch: continue to the next set (server picks the level).
    nextBtn.innerHTML = `Save &amp; Continue <i class="fa-solid fa-arrow-right ms-1"></i>`;
  } else {
    nextBtn.innerHTML = `Next <i class="fa-solid fa-chevron-right ms-1"></i>`;
  }

  updatePaletteStatus();
  updateProgress();
}

// Select Answer Option & Trigger Autosave. The clicked element is passed in
// explicitly (no reliance on the implicit global `event`).
async function selectOption(optionKey, el) {
  const q = questionsList[currentQuestionIndex];
  if (isLocked(q)) return;  // earlier batches are read-only
  q.selected_option = optionKey;

  // Update UI selection
  const cards = document.querySelectorAll(".option-card");
  cards.forEach(card => card.classList.remove("selected"));
  if (el) {
    el.classList.add("selected");
    const radio = el.querySelector("input[type=radio]");
    if (radio) radio.checked = true;
  }

  updatePaletteStatus();
  updateProgress();

  // Trigger Background Autosave
  await autosaveCurrentAnswer();
}

// Clear Answer
async function clearCurrentAnswer() {
  const q = questionsList[currentQuestionIndex];
  if (isLocked(q)) return;
  q.selected_option = null;
  loadQuestion(currentQuestionIndex);
  await autosaveCurrentAnswer();
}

// Toggle Flag
async function toggleFlagCurrentQuestion() {
  const q = questionsList[currentQuestionIndex];
  if (isLocked(q)) return;
  q.is_flagged = !q.is_flagged;
  loadQuestion(currentQuestionIndex);
  await autosaveCurrentAnswer();
}

// Background Autosave API Call
async function autosaveCurrentAnswer() {
  const q = questionsList[currentQuestionIndex];
  const statusEl = document.getElementById("autosaveStatus");
  statusEl.innerHTML = `<span class="spinner-border spinner-border-sm text-primary"></span> Saving...`;

  try {
    await fetch(`/api/assessment/${currentSession.session_id}/autosave`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: q.id,
        selected_option: q.selected_option,
        is_flagged: q.is_flagged,
        time_spent_seconds: 2
      })
    });
    statusEl.innerHTML = `<i class="fa-solid fa-cloud-arrow-up text-success"></i> Auto-saved`;
  } catch (err) {
    statusEl.innerHTML = `<i class="fa-solid fa-circle-exclamation text-danger"></i> Offline`;
  }
}

// Question Navigation. Moving forward past the last served question means the
// current batch is complete -> submit it and let the engine serve the next set.
function navigateQuestion(direction) {
  const nextIdx = currentQuestionIndex + direction;
  if (nextIdx < 0) return;
  if (nextIdx < questionsList.length) {
    loadQuestion(nextIdx);
  } else {
    // Past the end of what's been served -> advance to the next adaptive batch.
    submitCurrentBatch();
  }
}

// Submit the current batch. If some questions in the set are blank, show an IN-PAGE
// confirmation modal (NOT a native confirm()). A native dialog blurs the window and drops
// fullscreen, which the proctoring engine would wrongly log as cheating; an in-page modal
// stays inside fullscreen and fires no such events.
function submitCurrentBatch() {
  if (batchSubmitInFlight) return;

  const activeBatch = questionsList.filter(q => q.question_number >= activeBatchStart);
  const blanks = activeBatch.filter(q => !q.selected_option).length;
  if (blanks > 0) {
    document.getElementById("batchBlankCount").textContent = blanks;
    bootstrap.Modal.getOrCreateInstance(document.getElementById("batchConfirmModal")).show();
    return;
  }
  proceedBatchSubmit();
}

// Called either directly (no blanks) or from the in-page "Continue" button.
async function proceedBatchSubmit() {
  const cm = bootstrap.Modal.getInstance(document.getElementById("batchConfirmModal"));
  if (cm) cm.hide();
  if (batchSubmitInFlight) return;

  batchSubmitInFlight = true;
  const nextBtn = document.getElementById("btnNextQ");
  const prevLabel = nextBtn.innerHTML;
  nextBtn.disabled = true;
  nextBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Loading next set...`;

  try {
    const res = await fetch(`/api/assessment/${currentSession.session_id}/submit-batch`, { method: "POST" });
    const data = await res.json();

    examFinished = !!data.finished;
    activeBatchStart = data.active_batch_start || activeBatchStart;

    if (data.new_questions && data.new_questions.length > 0) {
      questionsList = questionsList.concat(data.new_questions);
    }

    if (examFinished || !data.new_questions || data.new_questions.length === 0) {
      // Whole exam served and last batch graded -> go to final submission.
      confirmSubmitModal();
      return;
    }

    // Show the first question of the new batch.
    renderPalette();
    loadQuestion(indexForQuestionNumber(activeBatchStart));
  } catch (err) {
    alert("Could not load the next set of questions. Please check your connection and try again.");
  } finally {
    batchSubmitInFlight = false;
    nextBtn.disabled = false;
    if (nextBtn.innerHTML.includes("spinner")) nextBtn.innerHTML = prevLabel;
  }
}

// Render Palette — 80 fixed slots; unserved ones are locked/greyed to preserve the look.
function renderPalette() {
  const grid = document.getElementById("paletteGrid");
  grid.innerHTML = "";

  for (let idx = 0; idx < totalQuestions; idx++) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "palette-btn";
    btn.id = `palette_btn_${idx}`;
    btn.textContent = idx + 1;
    if (idx < questionsList.length) {
      btn.onclick = () => loadQuestion(idx);
    } else {
      // Not served yet — locked until the candidate reaches it.
      btn.disabled = true;
      btn.style.opacity = "0.4";
      btn.style.cursor = "not-allowed";
    }
    grid.appendChild(btn);
  }
}

function updatePaletteStatus() {
  for (let idx = 0; idx < totalQuestions; idx++) {
    const btn = document.getElementById(`palette_btn_${idx}`);
    if (!btn) continue;

    const q = questionsList[idx];
    btn.className = "palette-btn";
    if (!q) {
      btn.style.opacity = "0.4";
      continue;
    }
    btn.style.opacity = "1";
    if (idx === currentQuestionIndex) {
      btn.classList.add("active");
    }
    if (q.is_flagged) {
      btn.classList.add("flagged");
    } else if (q.selected_option) {
      btn.classList.add("answered");
    }
  }
}

function updateProgress() {
  const answered = questionsList.filter(q => q.selected_option).length;
  document.getElementById("examAnsweredCount").textContent = answered;
  const pct = Math.round((answered / totalQuestions) * 100);
  document.getElementById("examProgressBar").style.width = `${pct}%`;
}

// Confirm Submit Modal
function confirmSubmitModal() {
  const answered = questionsList.filter(q => q.selected_option).length;
  document.getElementById("confirmAnsweredCount").textContent = answered;
  // Reuse a single instance so repeated visits to the last question never stack backdrops.
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById("submitConfirmModal"));
  modal.show();
}

// Forcibly closes any open modal and strips its backdrop / body lock. Bootstrap's hide is
// an async fade whose completion sets the modal to display:none only after the backdrop's
// transition ends. Swapping stages and exiting fullscreen right after calling hide()
// interrupts that sequence, which previously left either the dark full-screen backdrop
// (page blacks out) or the dialog itself frozen on top — both swallowing all clicks. This
// resets everything synchronously so the page is always clean and interactive.
function cleanupModalArtifacts() {
  document.querySelectorAll(".modal").forEach(m => {
    if (m.classList.contains("show") || m.style.display === "block") {
      m.classList.remove("show");
      m.style.display = "none";
      m.setAttribute("aria-hidden", "true");
      m.removeAttribute("aria-modal");
      m.removeAttribute("role");
    }
  });
  document.querySelectorAll(".modal-backdrop").forEach(el => el.remove());
  document.body.classList.remove("modal-open");
  document.body.style.overflow = "";
  document.body.style.paddingRight = "";
}

// Final Submit
async function finalizeAndSubmitAssessment() {
  clearInterval(timerInterval);
  // Stop proctoring immediately: the candidate is finishing, so exiting fullscreen and
  // any resulting blur are intentional and must NOT be logged as violations.
  proctoringActive = false;

  // Exit fullscreen first so the teardown below paints on the normal viewport.
  if (document.fullscreenElement && document.exitFullscreen) {
    try { await document.exitFullscreen(); } catch (e) { /* ignore */ }
  }

  // Tear the confirm modal down and forcibly strip any lingering backdrop/body lock.
  const modalEl = document.getElementById("submitConfirmModal");
  const modalInstance = bootstrap.Modal.getInstance(modalEl);
  if (modalInstance) {
    try { modalInstance.hide(); } catch (e) { /* ignore */ }
    try { modalInstance.dispose(); } catch (e) { /* ignore */ }
  }
  cleanupModalArtifacts();

  try {
    const res = await fetch(`/api/assessment/${currentSession.session_id}/submit`, {
      method: "POST"
    });
    await res.json();
  } catch (err) {
    // Answers were autosaved throughout, so still show the completion screen even if this
    // final call hiccups, rather than trapping the candidate on a darkened exam screen.
    console.warn("Submit request issue:", err);
  }

  // Show Stage 4: Clean Submission Screen (ZERO scores shown) and guarantee a clean page.
  document.getElementById("candidate-stage-exam").classList.add("d-none");
  document.getElementById("candidate-stage-completed").classList.remove("d-none");
  cleanupModalArtifacts();
  window.scrollTo(0, 0);
}

// ==========================================
// BACKGROUND PROCTORING ENGINE
// ==========================================
function initProctoring() {
  proctoringStartTime = Date.now();
  proctoringActive = true;

  function getOffsetSeconds() {
    return Math.floor((Date.now() - proctoringStartTime) / 1000);
  }

  function logEvent(type, details) {
    if (!currentSession || !proctoringActive) return;
    // The candidate's local wall-clock time is sent as its own field (client_time) so the
    // report can show a single, consistent time — not two conflicting ones. The message
    // text stays purely descriptive; timing comes from the elapsed offset + client_time.
    fetch("/api/proctoring/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSession.session_id,
        event_type: type,
        details: details,
        timestamp_seconds: getOffsetSeconds(),
        client_time: new Date().toLocaleTimeString()
      })
    }).catch(e => console.log("Proctoring log error:", e));
  }

  // 1. Tab Switching (Visibility Change)
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      logEvent("tab_switch", "Candidate switched to another browser tab or minimized the window");
    }
  });

  // 2. Window Blur (Application Switching / Alt+Tab)
  window.addEventListener("blur", () => {
    logEvent("window_blur", "Candidate clicked outside the exam window (possible Alt+Tab or multi-monitor)");
  });

  // 3. Fullscreen Exit
  document.addEventListener("fullscreenchange", () => {
    if (!document.fullscreenElement) {
      logEvent("fullscreen_exit", "Candidate exited fullscreen mode");
    }
  });

  // 4. Copy-Paste Detection
  document.addEventListener("copy", (e) => {
    e.preventDefault();
    logEvent("copy_paste_attempt", "Candidate attempted to copy text");
  });

  document.addEventListener("paste", (e) => {
    e.preventDefault();
    logEvent("copy_paste_attempt", "Candidate attempted to paste content");
  });

  // 5. Context Menu Lock
  document.addEventListener("contextmenu", (e) => {
    e.preventDefault();
  });
}
