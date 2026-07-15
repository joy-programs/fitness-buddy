# 🏋️ Fitness Buddy — AI-Powered Fitness Coach

> A conversational AI fitness and wellness assistant built with **Python FastAPI** and **IBM watsonx.ai (IBM Granite models)**. Fitness Buddy provides personalised home workout plans, meal suggestions, BMI calculations, habit tracking, and daily motivation — all powered by IBM Granite generative AI.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Fitness Chat** | Conversational coach powered by IBM Granite — ask anything about fitness |
| 🏋️ **Workout Generator** | Personalised home workout plans (JSON structured, beginner → advanced) |
| 🥗 **Meal Suggestions** | Healthy Indian & international meal ideas based on dietary preferences |
| 📏 **BMI Calculator** | Calculate BMI with category, range indicator, and medical disclaimer |
| ✅ **Habit Tracker** | Track 5 daily habits with streak counting and progress bar |
| ⚡ **Daily Motivation** | Instant motivational messages and tips from IBM Granite |
| 📊 **Fitness Dashboard** | Unified dashboard with all stats, quick actions, and daily motivation |
| 👤 **Fitness Profile** | Personalised profile that the AI uses to tailor all responses |
| 🌙 **Dark Mode** | Full dark mode with browser localStorage persistence |

---

## 🏗️ Project Structure

```
fitness-buddy/
├── backend/
│   ├── __init__.py
│   ├── main.py               ← FastAPI app, CORS, routers, lifecycle
│   ├── database.py           ← SQLAlchemy engine, session, get_db()
│   ├── models.py             ← SQLAlchemy ORM models
│   ├── schemas.py            ← Pydantic request/response schemas
│   ├── agent_instructions.py ← AGENT_INSTRUCTIONS config + prompt builder
│   ├── watsonx_service.py    ← IBM watsonx.ai / Granite integration
│   ├── fitness_utils.py      ← BMI, TDEE, streak calculations
│   └── routers/
│       ├── __init__.py
│       ├── profile.py        ← GET/POST/PUT/PATCH /api/profile
│       ├── chat.py           ← POST /api/chat
│       ├── workouts.py       ← POST /api/workouts/generate
│       ├── meals.py          ← POST /api/meals/suggest
│       ├── motivation.py     ← GET/POST /api/motivation
│       ├── habits.py         ← GET/POST /api/habits/{profile_id}
│       ├── fitness.py        ← GET/POST /api/fitness/bmi
│       └── dashboard.py      ← GET /api/dashboard/{profile_id}
├── frontend/
│   ├── index.html            ← Single-page frontend (Bootstrap 5)
│   ├── css/style.css         ← Custom fitness-themed CSS + dark mode
│   └── js/app.js             ← Vanilla JS with fetch API integration
├── .env.example              ← Template for environment variables
├── requirements.txt          ← Python dependencies
└── README.md
```

---

## 🚀 Local Setup

### Prerequisites

- Python 3.10 or newer
- An **IBM Cloud account** (free Lite plan works)
- An **IBM watsonx.ai** project with the Granite model enabled
- Git

---

### Step 1 — Clone the repository

```bash
git clone <your-repo-url>
cd fitness-buddy
```

---

### Step 2 — Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Configure IBM Cloud credentials

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and add your credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-3-8b-instruct
```

---

### Step 5 — Obtain IBM Cloud Credentials

#### Getting your IBM Cloud API Key
1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Go to **Manage → Access (IAM) → API Keys**
3. Click **Create** → give it a name → copy the key
4. Paste it as `IBM_API_KEY` in your `.env`

#### Getting your watsonx.ai Project ID
1. Go to [IBM watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home)
2. Open or create a project
3. Click on **Manage** tab in the project
4. Copy the **Project ID** shown there
5. Paste it as `WATSONX_PROJECT_ID` in your `.env`

#### Service URL (Regional Endpoints)
| Region | URL |
|--------|-----|
| Dallas (us-south) — **Default** | `https://us-south.ml.cloud.ibm.com` |
| London (eu-gb) | `https://eu-gb.ml.cloud.ibm.com` |
| Frankfurt (eu-de) | `https://eu-de.ml.cloud.ibm.com` |
| Tokyo (jp-tok) | `https://jp-tok.ml.cloud.ibm.com` |

#### Granite Model ID
The recommended model for Lite plan users:
```
ibm/granite-3-3-8b-instruct
```
Other available Granite instruct models:
- `ibm/granite-3-1-8b-instruct`
- `ibm/granite-3-2-8b-instruct`
- `ibm/granite-13b-instruct-v2`

---

### Step 6 — Run the FastAPI backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO  🏋️  Fitness Buddy starting up…
INFO  ✅  Database tables ready.
INFO  📄  API docs: http://localhost:8000/docs
INFO  Uvicorn running on http://0.0.0.0:8000
```

---

### Step 7 — Open the frontend

Open `frontend/index.html` directly in your browser, **or** use VS Code Live Server:

1. Install the **Live Server** extension in VS Code
2. Right-click `frontend/index.html` → **Open with Live Server**
3. Live Server defaults to `http://127.0.0.1:5500`

> **Note:** The frontend is pre-configured to call `http://localhost:8000` for the backend. CORS is already set up for all common localhost ports.

---

## 📖 API Documentation

With the backend running, open:

- **Swagger UI (interactive):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/profile` | Create a fitness profile |
| `GET` | `/api/profile/{id}` | Get profile by ID |
| `PUT` | `/api/profile/{id}` | Full profile update |
| `PATCH` | `/api/profile/{id}` | Partial profile update |
| `POST` | `/api/chat` | Chat with AI fitness coach |
| `GET` | `/api/chat/history/{session_id}` | Get chat history |
| `POST` | `/api/workouts/generate` | Generate a workout plan |
| `GET` | `/api/workouts/history/{profile_id}` | Get saved workout history |
| `POST` | `/api/meals/suggest` | Get meal suggestions |
| `GET` | `/api/motivation` | Quick motivational message |
| `POST` | `/api/motivation` | Contextual motivation |
| `GET` | `/api/habits/{profile_id}` | Get today's habits |
| `POST` | `/api/habits/{profile_id}` | Update habit check-ins |
| `GET` | `/api/habits/{profile_id}/streak` | Get streak count |
| `GET` | `/api/fitness/bmi` | BMI calculation (query params) |
| `POST` | `/api/fitness/bmi` | BMI calculation (JSON body) |
| `GET` | `/api/dashboard/{profile_id}` | Full dashboard data |
| `GET` | `/health` | Health check |

---

## 🎛️ Customising the AI Agent

All AI behaviour is controlled from **[`backend/agent_instructions.py`](backend/agent_instructions.py)**.

Edit the `AGENT_INSTRUCTIONS` dictionary to customise:

```python
AGENT_INSTRUCTIONS = {
    "name":             "Fitness Buddy",
    "identity":         "...",   # Who the agent is
    "personality":      "...",   # Tone and communication style
    "coaching_style":   "...",   # Approach to fitness advice
    "workout_focus":    "...",   # What types of workouts to specialise in
    "motivation_style": "...",   # How to motivate users
    "nutrition_guidance": "...", # Nutrition advice boundaries
    "indian_context":   "...",   # Indian food and lifestyle awareness
    "response_format":  "...",   # How to format responses
    "safety_rules":     "...",   # Safety guardrails
    "medical_limits":   "...",   # Medical disclaimer rules
    "beginner_priority":"...",   # Default to beginner guidance
    "scope":            "...",   # Keep agent on-topic
}
```

No changes to routes or service files are needed — the system prompt is built automatically from this config.

---

## 🔧 Testing the API with Swagger

1. Start the server: `uvicorn backend.main:app --reload`
2. Open [http://localhost:8000/docs](http://localhost:8000/docs)
3. Try creating a profile first:
   - Expand **POST /api/profile**
   - Click **Try it out** → fill in the form → **Execute**
   - Copy the returned `id`
4. Test the workout generator:
   - Expand **POST /api/workouts/generate**
   - Set `profile_id` to your profile's ID
   - Execute and see the structured workout JSON
5. Test the chat:
   - Expand **POST /api/chat**
   - Set `session_id` to any string like `"test123"`
   - Set `message` to `"What's a good beginner workout?"` → Execute

---

## 📦 Dependencies

```
fastapi          — Web framework
uvicorn          — ASGI server
python-dotenv    — Load .env variables
sqlalchemy       — ORM for SQLite database
pydantic         — Data validation and schemas
ibm-watsonx-ai   — IBM watsonx.ai Python SDK
httpx            — Async HTTP client
python-multipart — Form data support
aiosqlite        — Async SQLite driver
```

---

## ⚠️ Health & Safety Disclaimer

Fitness Buddy provides **general fitness and wellness information only**. It is NOT:
- A medical professional or doctor
- A registered dietitian
- A physiotherapist

Always consult a qualified healthcare professional before starting a new exercise programme, making significant dietary changes, or if you have any pre-existing medical conditions, injuries, or health concerns.

---

## 🚀 Basic Deployment Notes

### Environment Variables in Production
Set the same environment variables from `.env` as system/platform environment variables. Never commit `.env` to version control.

### Backend (e.g., Railway, Render, Heroku)
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Frontend
Update the `API.BASE_URL` in `frontend/js/app.js` to your deployed backend URL:
```javascript
const API = {
  BASE_URL: "https://your-backend-domain.com",  // change this for production
  ...
```

### CORS
Update `allow_origins` in `backend/main.py` to include your frontend domain in production.

---

## 📝 Notes for Students

- The entire IBM watsonx.ai integration is in **[`backend/watsonx_service.py`](backend/watsonx_service.py)** — study this file to understand how to call IBM Granite.
- The `AGENT_INSTRUCTIONS` system in **[`backend/agent_instructions.py`](backend/agent_instructions.py)** shows how to build configurable AI prompts.
- Each router in `backend/routers/` is independent and demonstrates a different FastAPI pattern.
- FastAPI's automatic validation via Pydantic is shown in every endpoint — check `backend/schemas.py`.
- The `get_db()` dependency injection pattern in `backend/database.py` is the standard FastAPI way to handle database sessions.

---

*Built with ❤️ using FastAPI, IBM watsonx.ai, IBM Granite, Bootstrap 5, and SQLite.*
