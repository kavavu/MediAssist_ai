# MediAssist AI — Complete Student Guide

> **Purpose**: This guide explains every part of the MediAssist AI project in simple, beginner-friendly language. Use it to understand the codebase, prepare for your defense, and explain the system to anyone.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Folder Structure](#2-folder-structure)
3. [How the Backend Works](#3-how-the-backend-works)
4. [How the Frontend Works](#4-how-the-frontend-works)
5. [Authentication Lifecycle](#5-authentication-lifecycle)
6. [AI Prediction Pipeline](#6-ai-prediction-pipeline)
7. [RandomForest Explained Simply](#7-randomforest-explained-simply)
8. [Payment Workflow (M-Pesa)](#8-payment-workflow-m-pesa)
9. [Chat Workflow](#9-chat-workflow)
10. [Database Relationships](#10-database-relationships)
11. [Security Features](#11-security-features)
12. [Demo Tips](#12-demo-tips)

---

## 1. Project Overview

**MediAssist AI** is a telemedicine web application that helps patients:
- Check symptoms using AI
- Get matched with the right doctor
- Book appointments
- Chat with doctors in real-time
- Pay via M-Pesa

### Tech Stack

| Layer | Technology | Why We Chose It |
|-------|-----------|-----------------|
| Frontend | React + Vite | Fast development, modern, component-based |
| Styling | TailwindCSS | Utility-first, responsive, consistent |
| Backend | Flask (Python) | Lightweight, easy to learn, powerful |
| Database | SQLite (dev) / PostgreSQL (prod) | Simple for students, easy to migrate |
| Auth | JWT (JSON Web Tokens) | Stateless, works with SPAs |
| Real-time | Socket.IO | WebSockets for instant chat |
| AI/ML | Custom Rule Engine + RandomForest | Hybrid approach for accuracy |
| Payments | M-Pesa Daraja API | Kenya's dominant mobile payment |

---

## 2. Folder Structure

```
MEDIASSIST-AI/
├── backend/                    ← Flask server
│   ├── app/
│   │   ├── __init__.py         ← App factory (creates the Flask app)
│   │   ├── extensions.py       ← DB, JWT, Migrate (shared objects)
│   │   ├── models/             ← Database tables (User, Consultation, etc.)
│   │   ├── routes/             ← API endpoints (URL handlers)
│   │   ├── services/           ← Business logic (no HTTP here)
│   │   ├── utils/              ← Helper functions (time format, decorators)
│   │   ├── ml/                 ← Machine Learning code
│   │   └── sockets/            ← WebSocket (real-time chat)
│   ├── config.py               ← Settings (DB, secrets, JWT)
│   ├── run.py                  ← Entry point: python backend/run.py
│   └── requirements.txt        ← Python packages
│
├── frontend/                   ← React app
│   ├── src/
│   │   ├── pages/              ← Full pages (Login, Dashboard, etc.)
│   │   ├── components/         ← Reusable pieces (NavBar, Toast, etc.)
│   │   ├── services/           ← API calls (axios wrappers)
│   │   └── App.jsx             ← Routes and layout
│   ├── index.html              ← HTML template
│   └── package.json            ← Node packages
│
├── instance/                   ← SQLite database file
├── migrations/                 ← Database schema versions
└── uploads/                    ← Uploaded files (images, PDFs)
```

### What Each Important File Does

| File | Purpose |
|------|---------|
| `backend/app/__init__.py` | Creates the Flask app, registers all routes, connects DB |
| `backend/config.py` | Stores secrets, DB URL, JWT settings |
| `backend/app/extensions.py` | Creates `db`, `jwt`, `migrate` objects used everywhere |
| `backend/app/models/user.py` | Defines the `users` table (login info, role) |
| `backend/app/routes/auth.py` | Handles `/api/auth/login` and `/api/auth/register` |
| `backend/app/services/auth_service.py` | Checks passwords, creates users |
| `frontend/src/services/api.js` | Axios instance — all API calls go through here |
| `frontend/src/services/auth.js` | Login, logout, get current user from localStorage |
| `frontend/src/App.jsx` | Defines all routes and who can access them |

---

## 3. How the Backend Works

### Step-by-Step: When a Patient Submits Symptoms

```
STEP 1: Patient types symptoms in the browser
        ↓
STEP 2: Frontend sends POST /api/predict { symptoms: "fever, headache" }
        ↓
STEP 3: Backend receives request → checks JWT token
        ↓
STEP 4: Symptom normalization (fixes spelling, Swahili → English)
        ↓
STEP 5: Rule-based tropical disease engine runs first
        ↓
STEP 6: If confidence is low → RandomForest ML fallback activates
        ↓
STEP 7: Results blended → top 3 diseases with confidence scores
        ↓
STEP 8: Backend returns JSON → frontend shows results
        ↓
STEP 9: Patient can create a consultation → matched to best doctor
```

### Blueprints (Route Groups)

Think of blueprints as folders for related URLs:

| Blueprint | URL Prefix | Example Route | What It Does |
|-----------|-----------|---------------|--------------|
| `auth` | `/api/auth` | `POST /register` | Create new account |
| `symptoms` | `/api` | `POST /predict` | AI symptom check |
| `patient` | `/api/patient` | `GET /predictions` | Patient's history |
| `doctor` | `/api/doctor` | `GET /symptom-reports` | Doctor's patients |
| `consultation` | `/api/consultation` | `POST /respond/5` | Doctor replies |
| `appointment` | `/api/appointments` | `POST /book` | Book a visit |
| `payment` | `/api/payments` | `POST /stk-push` | Pay via M-Pesa |
| `admin` | `/api/admin` | `GET /dashboard` | Admin stats |

### Services vs Routes

**Routes** = HTTP layer (receive requests, send responses)
**Services** = Business logic (what the app actually does)

```python
# routes/consultation.py  ← HTTP stuff
@consultation_bp.post("/respond/<id>")
def respond_to_consultation(id):
    data = request.get_json()
    consultation = consultation_service.respond_to_consultation(id, ...)
    return jsonify({"success": True})

# services/consultation_service.py  ← Business logic
def respond_to_consultation(consultation_id, doctor_id, ...):
    consultation = Consultation.query.get(consultation_id)
    consultation.status = "responded"
    db.session.commit()
    return consultation
```

This separation makes the code:
- Easier to test
- Easier to understand
- Less likely to break

---

## 4. How the Frontend Works

### Step-by-Step: Page Load

```
STEP 1: Browser loads index.html → Vite serves React app
        ↓
STEP 2: App.jsx checks routes → shows correct page
        ↓
STEP 3: If route is protected → checks if user is logged in
        ↓
STEP 4: If not logged in → redirects to /login
        ↓
STEP 5: Page component loads data from backend via API
        ↓
STEP 6: Data displayed → user interacts → more API calls
```

### Protected Routes

```jsx
// App.jsx
<ProtectedRoute roles={["patient"]}>
  <PatientDashboard />
</ProtectedRoute>
```

This means:
- Only logged-in users can see PatientDashboard
- Only users with role="patient" can see it
- Doctors and admins get redirected

### API Flow

```
Component needs data
    ↓
service/consultation.js calls api.get("/consultation/doctor")
    ↓
api.js (Axios) adds JWT token to header
    ↓
Request goes to backend
    ↓
Backend verifies JWT → returns data
    ↓
Component receives data → updates state → re-renders
```

---

## 5. Authentication Lifecycle

### Registration

```
User fills form → clicks Register
    ↓
Frontend POST /api/auth/register { name, email, password }
    ↓
Backend validates input → hashes password with scrypt
    ↓
User saved to database → returns success
    ↓
Frontend shows "Registration successful! Please log in."
```

### Login

```
User enters email + password → clicks Login
    ↓
Frontend POST /api/auth/login { email, password }
    ↓
Backend checks password hash → creates JWT token
    ↓
Backend returns { access_token, user }
    ↓
Frontend stores token in localStorage
    ↓
Frontend stores user object in localStorage
    ↓
User redirected to their dashboard
```

### JWT Token Lifecycle

```
User logs in → receives JWT token (valid for 1 hour)
    ↓
Every API call includes token in header: Authorization: Bearer <token>
    ↓
Backend verifies token signature + expiration
    ↓
If token expired → backend returns 401
    ↓
Frontend detects 401 → clears session → redirects to login
```

**Why JWT?**
- No server-side session storage needed
- Works across multiple servers
- Standard format, well-tested

---

## 6. AI Prediction Pipeline

This is the **heart** of the project. Here's how symptom checking works:

### Step 1: Input

Patient types: `"I have fever, headache, and feeling very tired"`

### Step 2: Normalization

```
Raw input → "I have fever, headache, and feeling very tired"
    ↓
Remove extra words → "fever headache tired"
    ↓
Fix spelling → "fever headache fatigue"
    ↓
Swahili translation → "homa kichwa uchovu" → "fever headache fatigue"
    ↓
Extract medical terms → ["fever", "headache", "fatigue"]
```

### Step 3: Rule-Based Engine (Primary)

The system has a **knowledge base** of 15 tropical diseases:

| Disease | Key Symptoms | Weight |
|---------|-------------|--------|
| Malaria | fever, chills, sweating | High |
| Typhoid | fever, abdominal pain, weakness | High |
| Dengue | fever, severe headache, rash | High |
| Common Cold | cough, sore throat, runny nose | Medium |

**How scoring works:**
1. For each disease, count matching symptoms
2. Multiply by symptom weight (some symptoms are more important)
3. Add bonus for red-flag combinations (e.g., fever + stiff neck + confusion = meningitis)
4. Penalize if core symptoms are missing
5. Cap confidence at 92% (never claim 100% certainty)

### Step 4: RandomForest Fallback (Secondary)

If the rule engine is **uncertain** (confidence < 40%), the ML model activates.

See [Section 7](#7-randomforest-explained-simply) for how RandomForest works.

### Step 5: Blending

```
Rule engine: Malaria 65%, Typhoid 20%, Dengue 10%
ML model:    Malaria 55%, Typhoid 30%, Dengue 8%
    ↓
Blended:     Malaria 62%, Typhoid 23%, Dengue 9%
```

The blend gives more weight to the engine with higher confidence.

### Step 6: Output

```json
{
  "predicted_condition": "Malaria",
  "confidence_score": 0.62,
  "top_predictions": [
    { "condition": "Malaria", "confidence": 0.62 },
    { "condition": "Typhoid", "confidence": 0.23 },
    { "condition": "Dengue", "confidence": 0.09 }
  ],
  "severity": "MEDIUM",
  "urgency_message": "See a doctor within 24-48 hours",
  "recommended_tests": ["Malaria Parasite Smear", "Complete Blood Count"]
}
```

**Important**: The system always says "This is NOT a diagnosis. See a real doctor."

---

## 7. RandomForest Explained Simply

### What is RandomForest?

Imagine you have a medical question and you ask **100 different doctors** for their opinion. Each doctor looks at your symptoms and makes a guess. Then you **count the votes** — the disease with the most votes wins.

That's RandomForest!

- **"Random"** = Each doctor (tree) sees a random subset of your symptoms
- **"Forest"** = Many doctors (trees) voting together
- **"Classification"** = Picking the right disease from a list

### Why RandomForest?

| Reason | Explanation |
|--------|-------------|
| **Accurate** | 100 doctors voting is better than 1 doctor guessing |
| **Handles missing data** | If you forget to mention one symptom, other trees still vote |
| **No overfitting** | Each tree is slightly different, so they don't all make the same mistake |
| **Fast prediction** | Once trained, guessing is very quick |
| **Explainable** | Can see which symptoms mattered most |

### How It Works in Our App

```
STEP 1: Training (happens once when app starts)
    - System reads 1000s of past symptom → disease pairs
    - Builds 100 decision trees
    - Each tree learns different patterns
    - Saves the trained model to a file

STEP 2: Prediction (happens every time a patient checks symptoms)
    - Patient enters: "fever, headache, fatigue"
    - System converts to numbers: [1, 1, 1, 0, 0, 0, ...]
    - Each of the 100 trees votes:
        Tree 1: "Malaria!"
        Tree 2: "Malaria!"
        Tree 3: "Typhoid!"
        ...
        Tree 100: "Malaria!"
    - Count votes: Malaria 78, Typhoid 15, Dengue 7
    - Return probabilities: Malaria 78%, Typhoid 15%, Dengue 7%
```

### Symptom Vector

The model can't read text. It needs numbers. So we convert:

```
Symptoms: "fever, headache, fatigue"
    ↓
Vector:   [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
           ↑  ↑  ↑
         fever headache fatigue
         (other 12 symptoms are 0 = not present)
```

### For Your Defense

**If the lecturer asks:** *"Why did you choose RandomForest?"*

> "RandomForest is an ensemble method that combines multiple decision trees. We chose it because:
> 1. It handles the sparse symptom vectors well (most symptoms are 0)
> 2. It's resistant to overfitting, which is important with limited training data
> 3. It provides probability scores, which we use for confidence calibration
> 4. It's fast at prediction time, giving users instant results
> 5. It can work alongside our rule-based engine as a fallback"

---

## 8. Payment Workflow (M-Pesa)

### Step-by-Step: Patient Pays for Appointment

```
STEP 1: Patient books appointment → system creates payment record
        ↓
STEP 2: Patient clicks "Pay with M-Pesa"
        ↓
STEP 3: Frontend sends POST /api/payments/<id>/stk-push { phone_number }
        ↓
STEP 4: Backend talks to Safaricom Daraja API
        ↓
STEP 5: Safaricom sends STK Push to patient's phone
        ↓
STEP 6: Patient enters M-Pesa PIN on their phone
        ↓
STEP 7: Safaricom processes payment → sends callback to backend
        ↓
STEP 8: Backend updates payment status → marks appointment as paid
        ↓
STEP 9: Frontend polls status → shows "Payment successful!"
```

### Demo Mode

For safety during demos, we have `DEMO_PAYMENT_MODE=true`:
- Shows the real price to the user
- But only charges KSh 1
- Prevents accidental large charges

---

## 9. Chat Workflow

### Real-Time Chat Using WebSockets

```
Patient opens chat
    ↓
Frontend connects to WebSocket server
    ↓
Backend verifies JWT token
    ↓
Patient joins "consultation_123" room
    ↓
Doctor joins same room
    ↓
Patient sends message → backend receives → broadcasts to room
    ↓
Doctor sees message instantly (no page refresh!)
```

### Why WebSockets?

| Method | How It Works | Problem |
|--------|-------------|---------|
| Polling | Ask server "any new messages?" every 5 seconds | Wastes bandwidth, slow |
| WebSockets | Keep connection open, push messages instantly | Efficient, real-time |

---

## 10. Database Relationships

### Entity Relationship Diagram (Simple)

```
┌─────────┐       ┌─────────────┐       ┌───────────┐
│  User   │◄──────┤ Consultation├──────►│  Doctor   │
│(Patient)│       │             │       │  (User)   │
└────┬────┘       └──────┬──────┘       └───────────┘
     │                   │
     │            ┌──────┴──────┐
     │            │             │
     │       ┌────┴───┐    ┌────┴───┐
     │       │FollowUp│    │Review  │
     │       │(Chat)  │    │(Rating)│
     │       └────────┘    └────────┘
     │
     │       ┌──────────┐
     └──────►│Appointment│
             └────┬─────┘
                  │
             ┌────┴────┐
             │ Payment │
             └─────────┘
```

### Key Relationships

| Relationship | Type | Meaning |
|-------------|------|---------|
| User → PatientProfile | One-to-One | Each patient has one profile |
| User → Consultations | One-to-Many | A patient can have many consultations |
| Consultation → FollowUps | One-to-Many | A consultation has many chat messages |
| Consultation → Review | One-to-One | One review per consultation |
| User → Appointments | One-to-Many | A patient can book many appointments |
| Appointment → Payment | One-to-One | Each appointment has one payment |

---

## 11. Security Features

### What We Implemented

| Feature | How It Works |
|---------|-------------|
| **Password Hashing** | scrypt algorithm — even we can't read passwords |
| **JWT Tokens** | Signed tokens expire after 1 hour |
| **Role Protection** | `@role_required("doctor")` blocks unauthorized access |
| **CORS** | Only allows requests from approved origins |
| **Input Validation** | Max lengths, type checking, email format |
| **File Upload Security** | Only images and PDFs, max 5MB, UUID filenames |
| **SQL Injection Protection** | SQLAlchemy ORM uses parameterized queries |
| **M-Pesa Callback Safety** | Always returns 200, idempotent processing |
| **Global Error Handlers** | No stack traces leaked to users |

### What Happens on Security Issues

| Attack | Prevention |
|--------|-----------|
| Someone tries to register as admin | Role forced to "patient" |
| Weak password | Minimum 8 chars, must have letter + number |
| XSS (script injection) | Input length limits, no raw HTML rendering |
| SQL Injection | All queries use SQLAlchemy ORM |
| File upload exploit | Type checking, size limits, UUID filenames |
| Brute force login | Can add rate limiting with Flask-Limiter |

---

## 12. Demo Tips

### Before the Demo

1. **Start both servers**:
   ```bash
   # Terminal 1 — Backend
   python backend/run.py
   
   # Terminal 2 — Frontend
   cd frontend && npm run dev
   ```

2. **Test the flow**:
   - Register a patient
   - Submit symptoms
   - Check AI prediction
   - Create consultation
   - Log in as doctor
   - Respond to consultation
   - Test chat

3. **Have test accounts ready**:
   - Patient: `patient@test.com` / password
   - Doctor: `doctor@test.com` / password
   - Admin: `admin2@mediassist.com` / admin123

### During the Demo

1. **Show the symptom checker first** — it's the most impressive feature
2. **Explain the AI pipeline** — rule engine + ML fallback
3. **Show real-time chat** — WebSockets are cool
4. **Mention M-Pesa integration** — shows real-world applicability
5. **Show the admin dashboard** — demonstrates full system control

### If Something Goes Wrong

| Problem | Quick Fix |
|---------|----------|
| Backend won't start | Check `backend_server.log` for errors |
| Frontend blank | Check browser console (F12) |
| 401 errors | Token expired — log out and log back in |
| AI prediction fails | The rule engine works without ML — it's a fallback |
| Chat not working | Refresh page — Socket.IO reconnects automatically |

---

## Quick Reference: Common Questions

**Q: Why SQLite and not PostgreSQL?**
A: SQLite is perfect for development and demos. For production, change `DATABASE_URL` in `.env` to a PostgreSQL connection string.

**Q: Can the AI really diagnose diseases?**
A: No! It's a screening tool that suggests possible conditions. Only a real doctor can diagnose. The app clearly states this disclaimer.

**Q: How does doctor matching work?**
A: The system matches the predicted condition to a doctor's specialization, then picks the available doctor with the lowest patient load.

**Q: What happens if the ML model fails to load?**
A: The rule-based engine works independently. The ML is a fallback, not a requirement.

**Q: Is patient data secure?**
A: Yes. Passwords are hashed, JWT tokens expire, all API endpoints are protected, and file uploads are validated.

---

*Good luck with your defense! You built something impressive. Be confident and explain the WHY, not just the WHAT.*
