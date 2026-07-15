/* ══════════════════════════════════════════════════════════
   Fitness Buddy — Frontend JavaScript
   All backend communication goes through the API object.
   ══════════════════════════════════════════════════════════ */

// ─────────────────────────────────────────────────────────
//  API Configuration — change BASE_URL for production
// ─────────────────────────────────────────────────────────
const API = {
  BASE_URL: "http://localhost:8000",

  // Build full URL for an API path
  url(path) {
    return `${this.BASE_URL}${path}`;
  },

  // Generic fetch wrapper with error handling
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (body) opts.body = JSON.stringify(body);

    try {
      const response = await fetch(this.url(path), opts);
      const data = await response.json();

      if (!response.ok) {
        // Return error details so callers can show friendly messages
        throw new APIError(
          data.detail || "Something went wrong. Please try again.",
          response.status,
          data.code
        );
      }
      return data;
    } catch (err) {
      if (err instanceof APIError) throw err;
      // Network error (backend not running, etc.)
      throw new APIError(
        "Cannot connect to Fitness Buddy server. Make sure the backend is running on port 8000.",
        0
      );
    }
  },

  get:    (path)        => API.request("GET", path),
  post:   (path, body)  => API.request("POST", path, body),
  put:    (path, body)  => API.request("PUT", path, body),
  patch:  (path, body)  => API.request("PATCH", path, body),
};

// Custom error class for API errors
class APIError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code   = code;
  }
}


// ─────────────────────────────────────────────────────────
//  App State
// ─────────────────────────────────────────────────────────
const State = {
  profileId:  null,   // currently loaded profile ID
  sessionId:  null,   // unique chat session identifier
  profile:    null,   // full profile object
};

// Generate a random session ID per page load
State.sessionId = "session_" + Math.random().toString(36).slice(2, 11);


// ─────────────────────────────────────────────────────────
//  Dark Mode
// ─────────────────────────────────────────────────────────
function initDarkMode() {
  const saved = localStorage.getItem("fb_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  updateDarkModeBtn(saved);
}

function toggleDarkMode() {
  const current = document.documentElement.getAttribute("data-theme");
  const next    = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("fb_theme", next);
  updateDarkModeBtn(next);
}

function updateDarkModeBtn(theme) {
  const btn = document.getElementById("dark-mode-toggle");
  if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
}


// ─────────────────────────────────────────────────────────
//  Navigation (Single Page App)
// ─────────────────────────────────────────────────────────
function showView(viewId) {
  document.querySelectorAll(".fb-view").forEach(v => v.classList.remove("active"));
  const target = document.getElementById(viewId);
  if (target) target.classList.add("active");

  // Update navbar active state
  document.querySelectorAll(".nav-link[data-view]").forEach(link => {
    link.classList.toggle("active", link.dataset.view === viewId);
  });

  // Always call loadDashboard/loadHabits — they handle the no-profile case internally
  if (viewId === "view-dashboard") loadDashboard();
  if (viewId === "view-habits")    loadHabits();
}


// ─────────────────────────────────────────────────────────
//  Alert Helper
// ─────────────────────────────────────────────────────────
function showAlert(containerId, message, type = "info") {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `<div class="fb-alert fb-alert-${type}">${escHtml(message)}</div>`;
  setTimeout(() => { container.innerHTML = ""; }, 5000);
}

function escHtml(str) {
  const d = document.createElement("div");
  d.appendChild(document.createTextNode(str));
  return d.innerHTML;
}


// ─────────────────────────────────────────────────────────
//  Profile Management
// ─────────────────────────────────────────────────────────
async function saveProfile() {
  const form = document.getElementById("profile-form");
  if (!form.checkValidity()) { form.reportValidity(); return; }

  const payload = {
    name:             document.getElementById("p-name").value.trim() || "Fitness Buddy User",
    age:              parseInt(document.getElementById("p-age").value) || null,
    gender:           document.getElementById("p-gender").value || null,
    height_cm:        parseFloat(document.getElementById("p-height").value) || null,
    weight_kg:        parseFloat(document.getElementById("p-weight").value) || null,
    fitness_level:    document.getElementById("p-level").value,
    fitness_goal:     document.getElementById("p-goal").value,
    workout_duration: parseInt(document.getElementById("p-duration").value) || 30,
    equipment:        document.getElementById("p-equipment").value,
    activity_level:   document.getElementById("p-activity").value,
    dietary_pref:     document.getElementById("p-diet").value,
  };

  try {
    let profile;
    if (State.profileId) {
      profile = await API.put(`/api/profile/${State.profileId}`, payload);
      showAlert("profile-alert", "Profile updated successfully! 🎉", "success");
    } else {
      profile = await API.post("/api/profile", payload);
      State.profileId = profile.id;
      showAlert("profile-alert", "Profile created! Welcome to Fitness Buddy 🏋️", "success");
    }
    State.profile = profile;
    localStorage.setItem("fb_profile_id", profile.id);
    updateProfileDisplay(profile);
  } catch (err) {
    showAlert("profile-alert", err.message, "error");
  }
}

async function loadProfileById(id) {
  try {
    const profile = await API.get(`/api/profile/${id}`);
    State.profileId = profile.id;
    State.profile   = profile;
    populateProfileForm(profile);
    updateProfileDisplay(profile);
    return profile;
  } catch (err) {
    // Profile ID in storage is stale — clear it
    localStorage.removeItem("fb_profile_id");
    State.profileId = null;
    return null;
  }
}

function populateProfileForm(p) {
  document.getElementById("p-name").value     = p.name || "";
  document.getElementById("p-age").value      = p.age || "";
  document.getElementById("p-gender").value   = p.gender || "";
  document.getElementById("p-height").value   = p.height_cm || "";
  document.getElementById("p-weight").value   = p.weight_kg || "";
  document.getElementById("p-level").value    = p.fitness_level || "beginner";
  document.getElementById("p-goal").value     = p.fitness_goal || "general_fitness";
  document.getElementById("p-duration").value = p.workout_duration || 30;
  document.getElementById("p-equipment").value = p.equipment || "no_equipment";
  document.getElementById("p-activity").value = p.activity_level || "sedentary";
  document.getElementById("p-diet").value     = p.dietary_pref || "non_vegetarian";
}

function updateProfileDisplay(p) {
  const nameEls = document.querySelectorAll(".user-name-display");
  nameEls.forEach(el => { el.textContent = p.name || "Fitness Buddy User"; });
  const goalEls = document.querySelectorAll(".user-goal-display");
  goalEls.forEach(el => { el.textContent = formatGoal(p.fitness_goal); });
}

function formatGoal(goal) {
  const map = {
    weight_loss:     "Weight Loss",
    muscle_gain:     "Muscle Gain",
    general_fitness: "General Fitness",
    stamina:         "Better Stamina",
    flexibility:     "Flexibility",
    active_lifestyle:"Active Lifestyle",
  };
  return map[goal] || goal;
}


// ─────────────────────────────────────────────────────────
//  BMI Calculator
// ─────────────────────────────────────────────────────────
async function calculateBMI() {
  const heightEl = document.getElementById("bmi-height");
  const weightEl = document.getElementById("bmi-weight");

  const height = parseFloat(heightEl.value);
  const weight = parseFloat(weightEl.value);

  if (!height || !weight || height <= 0 || weight <= 0) {
    showAlert("bmi-alert", "Please enter valid height and weight values.", "error");
    return;
  }

  try {
    const result = await API.get(`/api/fitness/bmi?height_cm=${height}&weight_kg=${weight}`);
    renderBMI(result);
  } catch (err) {
    showAlert("bmi-alert", err.message, "error");
  }
}

function renderBMI(data) {
  const container = document.getElementById("bmi-result");
  if (!container) return;

  const catClass = {
    "Underweight":    "bmi-underweight",
    "Normal weight":  "bmi-normal",
    "Overweight":     "bmi-overweight",
    "Obesity Class I":"bmi-obese",
    "Obesity Class II":"bmi-obese",
    "Obesity Class III":"bmi-obese",
  }[data.category] || "bmi-normal";

  // Compute rough bar position (BMI scale 10–40)
  const pct = Math.min(100, Math.max(0, ((data.bmi - 10) / 30) * 100));

  container.innerHTML = `
    <div class="text-center mb-3">
      <div class="bmi-value">${data.bmi}</div>
      <span class="bmi-category ${catClass}">${data.category}</span>
    </div>
    <div class="fb-progress mb-1">
      <div class="fb-progress-bar" style="width:${pct}%"></div>
    </div>
    <div class="d-flex justify-content-between" style="font-size:0.75rem;color:var(--fb-text-muted)">
      <span>Underweight<br>&lt;18.5</span>
      <span>Normal<br>18.5–24.9</span>
      <span>Overweight<br>25–29.9</span>
      <span>Obese<br>&gt;30</span>
    </div>
    <p class="mt-3 mb-0" style="font-size:0.8rem;color:var(--fb-text-muted)">
      <strong>Healthy range:</strong> ${data.healthy_range}<br>
      ⚠️ ${data.disclaimer}
    </p>
  `;
}


// ─────────────────────────────────────────────────────────
//  AI Chat
// ─────────────────────────────────────────────────────────
async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  const sendBtn = document.getElementById("chat-send-btn");
  input.value = "";
  sendBtn.disabled = true;

  // Display the user's message
  appendChatBubble(message, "user");

  // Show typing indicator
  const typingEl = showTypingIndicator();

  try {
    const payload = {
      message,
      session_id: State.sessionId,
      profile_id: State.profileId || null,
    };
    const data = await API.post("/api/chat", payload);
    typingEl.remove();
    appendChatBubble(data.reply, "ai");
  } catch (err) {
    typingEl.remove();
    appendChatBubble(`⚠️ ${err.message}`, "ai");
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function appendChatBubble(text, role) {
  const container = document.getElementById("chat-container");
  if (!container) return;

  const div = document.createElement("div");
  div.className = `chat-bubble ${role === "user" ? "chat-user" : "chat-ai"}`;
  // Render newlines as <br>
  div.innerHTML = escHtml(text).replace(/\n/g, "<br>");
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
  const container = document.getElementById("chat-container");
  const el = document.createElement("div");
  el.className = "typing-indicator";
  el.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
  return el;
}

// Allow pressing Enter to send
function handleChatKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChatMessage();
  }
}

// Quick prompt buttons in chat panel
function sendQuickPrompt(text) {
  const input = document.getElementById("chat-input");
  input.value = text;
  sendChatMessage();
}


// ─────────────────────────────────────────────────────────
//  Workout Generator
// ─────────────────────────────────────────────────────────
async function generateWorkout() {
  const btn = document.getElementById("generate-workout-btn");
  const resultEl = document.getElementById("workout-result");
  btn.disabled = true;
  resultEl.innerHTML = renderSkeleton(3);

  const payload = {
    profile_id:    State.profileId || null,
    fitness_level: document.getElementById("w-level").value,
    fitness_goal:  document.getElementById("w-goal").value,
    duration_min:  parseInt(document.getElementById("w-duration").value) || 30,
    equipment:     document.getElementById("w-equipment").value,
    modification:  document.getElementById("w-modification").value.trim() || null,
  };

  try {
    const data = await API.post("/api/workouts/generate", payload);
    renderWorkout(data.workout, resultEl);
  } catch (err) {
    resultEl.innerHTML = `<div class="fb-alert fb-alert-error">⚠️ ${escHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function renderWorkout(workout, container) {
  if (!workout || typeof workout !== "object") {
    // Fallback: plain text response
    container.innerHTML = `<div class="fb-card p-3">${escHtml(String(workout)).replace(/\n/g,"<br>")}</div>`;
    return;
  }

  let html = `
    <div class="fb-card p-3 mb-3">
      <h5 class="mb-1">${escHtml(workout.title || "Your Workout Plan")}</h5>
      <div class="d-flex gap-2 flex-wrap mt-1 mb-0" style="font-size:0.82rem;color:var(--fb-text-muted)">
        <span>⏱ ${workout.total_duration_min || "?"} min</span>
        <span>🎯 ${formatGoal(workout.goal || "")}</span>
        <span>💪 ${(workout.fitness_level || "").charAt(0).toUpperCase() + (workout.fitness_level||"").slice(1)}</span>
        <span>🏠 ${(workout.equipment||"").replace(/_/g," ")}</span>
        ${workout.calories_burned_estimate ? `<span>🔥 ~${workout.calories_burned_estimate}</span>` : ""}
      </div>
    </div>
  `;

  if (workout.warm_up?.length) {
    html += `<div class="workout-section"><h6>🔥 Warm-Up</h6>`;
    workout.warm_up.forEach(e => {
      html += `<div class="exercise-row">
        <span class="exercise-name">${escHtml(e.exercise)}</span>
        <span class="exercise-meta">${escHtml(e.duration || "")} — ${escHtml(e.instructions || "")}</span>
      </div>`;
    });
    html += `</div>`;
  }

  if (workout.main_workout?.length) {
    html += `<div class="workout-section"><h6>💪 Main Workout</h6>`;
    workout.main_workout.forEach(e => {
      html += `<div class="exercise-row">
        <span class="exercise-name">${escHtml(e.exercise)}</span>
        <span class="exercise-meta">
          ${e.sets ? `${e.sets} sets` : ""}
          ${e.reps ? `× ${e.reps} reps` : ""}
          ${e.rest_sec ? `| Rest: ${e.rest_sec}s` : ""}
        </span>
        <span class="exercise-meta">${escHtml(e.instructions || "")}</span>
        ${e.safety_tip ? `<span class="exercise-safety">⚠️ ${escHtml(e.safety_tip)}</span>` : ""}
      </div>`;
    });
    html += `</div>`;
  }

  if (workout.cool_down?.length) {
    html += `<div class="workout-section"><h6>🧘 Cool-Down</h6>`;
    workout.cool_down.forEach(e => {
      html += `<div class="exercise-row">
        <span class="exercise-name">${escHtml(e.exercise)}</span>
        <span class="exercise-meta">${escHtml(e.duration || "")} — ${escHtml(e.instructions || "")}</span>
      </div>`;
    });
    html += `</div>`;
  }

  if (workout.general_tips?.length) {
    html += `<div class="workout-section"><h6>💡 General Tips</h6><ul class="mb-0 ps-3">`;
    workout.general_tips.forEach(tip => {
      html += `<li style="font-size:0.88rem">${escHtml(tip)}</li>`;
    });
    html += `</ul></div>`;
  }

  container.innerHTML = html;
}


// ─────────────────────────────────────────────────────────
//  Meal Suggestions
// ─────────────────────────────────────────────────────────
async function suggestMeals() {
  const btn = document.getElementById("suggest-meals-btn");
  const resultEl = document.getElementById("meals-result");
  btn.disabled = true;
  resultEl.innerHTML = renderSkeleton(4);

  const payload = {
    profile_id:      State.profileId || null,
    dietary_pref:    document.getElementById("m-diet").value,
    fitness_goal:    document.getElementById("m-goal").value,
    special_request: document.getElementById("m-special").value.trim() || null,
  };

  try {
    const data = await API.post("/api/meals/suggest", payload);
    renderMeals(data.meals, resultEl);
  } catch (err) {
    resultEl.innerHTML = `<div class="fb-alert fb-alert-error">⚠️ ${escHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function renderMeals(meals, container) {
  if (!meals || typeof meals !== "object") {
    container.innerHTML = `<div class="fb-card p-3">${escHtml(String(meals)).replace(/\n/g,"<br>")}</div>`;
    return;
  }

  const sections = [
    { key: "breakfast", label: "🌅 Breakfast",     icon: "🌅" },
    { key: "lunch",     label: "☀️ Lunch",          icon: "☀️" },
    { key: "dinner",    label: "🌙 Dinner",          icon: "🌙" },
    { key: "snacks",    label: "🍎 Healthy Snacks",  icon: "🍎" },
  ];

  let html = "";
  sections.forEach(s => {
    if (!meals[s.key]?.length) return;
    html += `<div class="meal-section-title">${s.label}</div>`;
    meals[s.key].forEach(item => {
      html += `<div class="meal-card">
        <div class="meal-name">${escHtml(item.item || item.name || "")}</div>
        <div class="meal-desc">${escHtml(item.description || "")}</div>
        ${item.protein_note ? `<div class="meal-protein">🥩 ${escHtml(item.protein_note)}</div>` : ""}
      </div>`;
    });
  });

  if (meals.hydration_tip) {
    html += `<div class="fb-alert fb-alert-info mt-2">💧 <strong>Hydration:</strong> ${escHtml(meals.hydration_tip)}</div>`;
  }
  if (meals.nutrition_note) {
    html += `<p style="font-size:0.82rem;color:var(--fb-text-muted);margin-top:0.5rem">${escHtml(meals.nutrition_note)}</p>`;
  }

  container.innerHTML = html;
}


// ─────────────────────────────────────────────────────────
//  Motivation
// ─────────────────────────────────────────────────────────
async function getMotivation(context = null) {
  const btn = document.getElementById("motivate-btn");
  const resultEl = document.getElementById("motivation-result");
  if (btn) btn.disabled = true;
  if (resultEl) resultEl.innerHTML = renderSkeleton(1);

  try {
    let data;
    if (context) {
      data = await API.post("/api/motivation", {
        profile_id: State.profileId || null,
        context,
      });
    } else {
      const qp = State.profileId ? `?profile_id=${State.profileId}` : "";
      data = await API.get(`/api/motivation${qp}`);
    }
    renderMotivation(data, resultEl);
  } catch (err) {
    if (resultEl) resultEl.innerHTML = `<div class="fb-alert fb-alert-error">⚠️ ${escHtml(err.message)}</div>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderMotivation(data, container) {
  if (!container) return;
  container.innerHTML = `
    <div class="motivation-card">
      <div>${escHtml(data.message || "Keep going — every step forward counts!")}</div>
      ${data.tip ? `<div class="motivation-tip">💡 <strong>Tip:</strong> ${escHtml(data.tip)}</div>` : ""}
    </div>
  `;
}


// ─────────────────────────────────────────────────────────
//  Habit Tracker
// ─────────────────────────────────────────────────────────
const HABITS = [
  { key: "workout_done",   label: "Workout Completed",      icon: "🏋️" },
  { key: "water_goal_met", label: "Water Goal Met (2L+)",   icon: "💧" },
  { key: "healthy_meal",   label: "Ate Healthy Meals",      icon: "🥗" },
  { key: "good_sleep",     label: "Good Sleep (7-8 hrs)",   icon: "😴" },
  { key: "daily_movement", label: "Daily Movement/Walk",    icon: "🚶" },
];

let habitData = null;

async function loadHabits() {
  if (!State.profileId) {
    document.getElementById("habits-container").innerHTML = `
      <div class="fb-alert fb-alert-info">Please create a profile first to track habits.</div>
    `;
    return;
  }

  const today = getTodayDate();
  try {
    habitData = await API.get(`/api/habits/${State.profileId}?date=${today}`);
    renderHabits(habitData);
  } catch (err) {
    showAlert("habits-alert", err.message, "error");
  }
}

function renderHabits(data) {
  const container = document.getElementById("habits-container");
  if (!container) return;
  habitData = data;

  const pct = data.completion_pct || 0;

  let html = `
    <div class="d-flex justify-content-between align-items-center mb-2">
      <span style="font-size:0.85rem;font-weight:600;">Today's Progress</span>
      <span class="streak-badge">🔥 ${data.streak} day streak</span>
    </div>
    <div class="fb-progress mb-3">
      <div class="fb-progress-bar" style="width:${pct}%"></div>
    </div>
    <div class="text-center mb-3" style="font-size:0.85rem;color:var(--fb-text-muted)">${pct}% complete</div>
  `;

  HABITS.forEach(h => {
    const checked = data[h.key] ? "checked" : "";
    const done    = data[h.key] ? "completed" : "";
    html += `
      <div class="habit-item ${done}" id="habit-row-${h.key}">
        <span class="habit-icon">${h.icon}</span>
        <input type="checkbox" id="habit-${h.key}" ${checked}
          onchange="toggleHabit('${h.key}', this.checked)">
        <label for="habit-${h.key}">${h.label}</label>
      </div>
    `;
  });

  container.innerHTML = html;
}

async function toggleHabit(key, value) {
  if (!State.profileId) return;

  const today = getTodayDate();
  try {
    const update = { date: today, [key]: value };
    habitData = await API.post(`/api/habits/${State.profileId}`, update);
    // Update progress bar without full re-render
    const pct = habitData.completion_pct;
    const bar = document.querySelector("#habits-container .fb-progress-bar");
    if (bar) bar.style.width = pct + "%";
    const pctText = document.querySelector("#habits-container .text-center");
    if (pctText) pctText.textContent = pct + "% complete";
    // Update streak
    const streakEl = document.querySelector(".streak-badge");
    if (streakEl) streakEl.textContent = `🔥 ${habitData.streak} day streak`;
    // Update row class
    const row = document.getElementById(`habit-row-${key}`);
    if (row) row.classList.toggle("completed", value);
  } catch (err) {
    showAlert("habits-alert", err.message, "error");
  }
}


// ─────────────────────────────────────────────────────────
//  Dashboard
// ─────────────────────────────────────────────────────────
async function loadDashboard() {
  if (!State.profileId) {
    document.getElementById("dashboard-content").innerHTML = `
      <div class="row justify-content-center">
        <div class="col-md-6 text-center py-5">
          <div style="font-size:4rem">🏋️</div>
          <h4 class="mt-3">Welcome to Fitness Buddy!</h4>
          <p class="text-muted">Create your fitness profile to unlock your personalised dashboard.</p>
          <button class="btn-fb-primary" onclick="showView('view-profile')">Create My Profile</button>
        </div>
      </div>
    `;
    return;
  }

  document.getElementById("dashboard-content").innerHTML = renderSkeleton(5);

  try {
    const data = await API.get(`/api/dashboard/${State.profileId}`);
    renderDashboard(data);
  } catch (err) {
    document.getElementById("dashboard-content").innerHTML =
      `<div class="fb-alert fb-alert-error">⚠️ ${escHtml(err.message)}</div>`;
  }
}

function renderDashboard(data) {
  const p = data.profile;
  const b = data.bmi;
  const h = data.today_habits;
  const pct = h ? h.completion_pct : 0;

  let bmiHtml = `<div class="text-muted" style="font-size:0.85rem">Add height & weight in your profile</div>`;
  if (b) {
    const catClass = b.category === "Normal weight" ? "bmi-normal" :
      b.category === "Underweight" ? "bmi-underweight" :
      b.category === "Overweight"  ? "bmi-overweight"  : "bmi-obese";
    bmiHtml = `
      <div class="bmi-value">${b.bmi}</div>
      <span class="bmi-category ${catClass}">${b.category}</span>
    `;
  }

  const goalLabel = p ? formatGoal(p.fitness_goal) : "Set your goal";

  const html = `
    <!-- Hero card -->
    <div class="fb-hero-card mb-4">
      <div class="row align-items-center">
        <div class="col">
          <div style="font-size:0.85rem;opacity:0.85">Good ${getTimeOfDay()},</div>
          <h3 class="mb-1 user-name-display">${escHtml(p?.name || "Fitness Buddy User")}</h3>
          <div class="user-goal-display" style="opacity:0.88">🎯 ${goalLabel}</div>
        </div>
        <div class="col-auto text-end">
          <div style="font-size:3.5rem">💪</div>
        </div>
      </div>
    </div>

    <!-- Stats row -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3">
        <div class="fb-card fb-card-primary p-3 text-center">
          <div class="fb-stat-label">BMI</div>
          <div class="mt-1">${bmiHtml}</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="fb-card fb-card-accent p-3 text-center">
          <div class="fb-stat-label">Habits Today</div>
          <div class="fb-stat mt-1">${pct.toFixed(0)}%</div>
          <div class="fb-progress mt-2">
            <div class="fb-progress-bar" style="width:${pct}%"></div>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="fb-card fb-card-warm p-3 text-center">
          <div class="fb-stat-label">Streak</div>
          <div class="fb-stat mt-1">${data.streak}🔥</div>
          <div style="font-size:0.78rem;color:var(--fb-text-muted)">days</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="fb-card fb-card-secondary p-3 text-center">
          <div class="fb-stat-label">Level</div>
          <div class="fb-stat mt-1" style="font-size:1.5rem">
            ${p?.fitness_level === "advanced" ? "🏆" : p?.fitness_level === "intermediate" ? "⚡" : "🌱"}
          </div>
          <div style="font-size:0.82rem;color:var(--fb-text-muted)">
            ${(p?.fitness_level || "beginner").charAt(0).toUpperCase() + (p?.fitness_level||"beginner").slice(1)}
          </div>
        </div>
      </div>
    </div>

    <!-- Motivation -->
    <div class="fb-card mb-4">
      <div class="card-header">✨ Today's Motivation</div>
      <div class="p-3">
        <div class="motivation-card">
          ${escHtml(data.motivation || "Keep going — every step counts!")}
          ${data.quick_tip ? `<div class="motivation-tip">💡 <strong>Tip:</strong> ${escHtml(data.quick_tip)}</div>` : ""}
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="fb-card mb-4">
      <div class="card-header">⚡ Quick Actions</div>
      <div class="p-3">
        <div class="row g-2">
          <div class="col-6 col-md-3">
            <div class="quick-action-btn w-100" onclick="showView('view-chat')">
              <span class="qa-icon">🤖</span>Ask Fitness Buddy
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="quick-action-btn w-100" onclick="showView('view-workouts')">
              <span class="qa-icon">🏋️</span>Generate Workout
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="quick-action-btn w-100" onclick="showView('view-meals')">
              <span class="qa-icon">🥗</span>Suggest a Meal
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="quick-action-btn w-100" onclick="getMotivationAndShow()">
              <span class="qa-icon">⚡</span>Motivate Me!
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById("dashboard-content").innerHTML = html;
}

async function getMotivationAndShow() {
  showView("view-motivation");
  await getMotivation("I need a boost of motivation right now");
}


// ─────────────────────────────────────────────────────────
//  Utility Helpers
// ─────────────────────────────────────────────────────────
function getTodayDate() {
  return new Date().toISOString().slice(0, 10);
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "Morning";
  if (h < 17) return "Afternoon";
  return "Evening";
}

function renderSkeleton(count = 3) {
  let html = "";
  for (let i = 0; i < count; i++) {
    html += `
      <div class="fb-card p-3 mb-3">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text" style="width:75%"></div>
      </div>
    `;
  }
  return html;
}


// ─────────────────────────────────────────────────────────
//  Initialisation
// ─────────────────────────────────────────────────────────
async function init() {
  // 1. Restore dark mode preference
  initDarkMode();

  // 2. Try to load previously saved profile
  const savedId = localStorage.getItem("fb_profile_id");
  if (savedId) {
    const profile = await loadProfileById(parseInt(savedId));
    if (profile) {
      State.profileId = profile.id;
      // Sync workout/meal/habits forms with saved profile
      syncFormsFromProfile(profile);
    }
  }

  // 3. Show dashboard as default view
  showView("view-dashboard");

  // 4. Wire up nav links
  document.querySelectorAll(".nav-link[data-view]").forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      showView(link.dataset.view);
    });
  });

  // 5. Dark mode toggle
  const toggleBtn = document.getElementById("dark-mode-toggle");
  if (toggleBtn) toggleBtn.addEventListener("click", toggleDarkMode);

  // 6. Chat Enter key
  const chatInput = document.getElementById("chat-input");
  if (chatInput) chatInput.addEventListener("keydown", handleChatKeydown);
}

function syncFormsFromProfile(p) {
  // Sync workout form defaults from profile
  const wLevel = document.getElementById("w-level");
  const wGoal  = document.getElementById("w-goal");
  const wEq    = document.getElementById("w-equipment");
  const wDur   = document.getElementById("w-duration");
  if (wLevel) wLevel.value = p.fitness_level || "beginner";
  if (wGoal)  wGoal.value  = p.fitness_goal  || "general_fitness";
  if (wEq)    wEq.value    = p.equipment     || "no_equipment";
  if (wDur)   wDur.value   = p.workout_duration || 30;

  // Sync meal form defaults
  const mDiet = document.getElementById("m-diet");
  const mGoal = document.getElementById("m-goal");
  if (mDiet) mDiet.value = p.dietary_pref  || "non_vegetarian";
  if (mGoal) mGoal.value = p.fitness_goal  || "general_fitness";
}

// Start the app when DOM is ready
document.addEventListener("DOMContentLoaded", init);
