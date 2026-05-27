# MediAssist AI — Complete Project Documentation

> **Last Updated:** 27 May 2026
> **Status:** Production-Ready MVP with Real-Time Chat, AI Predictions, Load-Balanced Doctor Assignment, File Uploads, Payment Integration, Appointment Scheduling, and Complete UI/UX Polish

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [User Roles & Flows](#3-user-roles--flows)
4. [Backend Architecture](#4-backend-architecture)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [AI/ML System](#8-aiml-system)
9. [Symptom Normalization](#9-symptom-normalization)
10. [Doctor Assignment Logic](#10-doctor-assignment-logic)
11. [Real-Time Features](#11-real-time-features)
12. [Two-Way Chat System](#12-two-way-chat-system)
13. [Trust & Credibility](#13-trust--credibility)
14. [Pages & Screens](#14-pages--screens)
15. [Known Limitations & Suggestions](#15-known-limitations--suggestions)
16. [Testing Results](#16-testing-results)

---

## 1. Project Overview

**MediAssist AI** is a full-stack healthcare web application that connects patients with doctors through an AI-assisted clinical workflow. Patients submit symptoms, receive AI-powered condition predictions, and get structured medical responses from verified doctors. The system includes real-time two-way messaging, lab test booking, medicine ordering, doctor marketplace with load balancing, and comprehensive analytics.

### Core Value Proposition
- **For Patients:** Quick AI symptom analysis + transparent doctor selection + direct access to verified doctors + structured medical advice
- **For Doctors:** Organized patient queue with severity prioritization + AI-assisted response generation + real-time chat + workload analytics
- **For Platform:** Scalable specialization-based routing with load balancing + clean audit trails + trust-building features

---

## 2. Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | Flask (Python 3.13) |
| Database | SQLite (via SQLAlchemy ORM) |
| Migrations | Flask-Migrate (Alembic) |
| Authentication | JWT (flask-jwt-extended) |
| ML Model | scikit-learn (Random Forest classifier) |
| CORS | flask-cors |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 (Vite) |
| Styling | Tailwind CSS v4 |
| Routing | react-router-dom |
| HTTP Client | Axios |
| Icons | Emoji + SVG |

### DevOps
| Component | Technology |
|-----------|------------|
| Build Tool | Vite |
| Proxy | Vite dev server proxies `/api` → `localhost:5000` |
| Package Manager | npm (frontend), pip (backend) |

---

## 3. User Roles & Flows

### 3.1 Patient Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Register/     │───▶│  Submit Symptoms │───▶│  AI Predicts    │
│   Login         │    │  (free text)     │    │  Top 3 Conditions│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  View Doctor    │◀───│  Doctor Responds │◀───│  Choose Doctor  │
│  Response +     │    │  (structured)    │    │  + Create       │
│  Chat Back      │    │                  │    │  Consultation   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │
        ▼
┌─────────────────┐    ┌──────────────────┐
│  Book Lab Tests │    │  Order Medicines │
│  (if advised)   │    │  (if prescribed) │
└─────────────────┘    └──────────────────┘
```

**Detailed Steps:**
1. **Register/Login** → Patient creates account (name, email, password, role="patient")
2. **Submit Symptoms** → Types symptoms in natural language (e.g., "headache, fever, body aches")
3. **AI Analysis** → ML model predicts top 3 conditions with confidence scores
4. **Doctor Selection** → Patient sees ALL verified doctors with availability, workload, and specialization. Can override the AI-recommended doctor.
5. **Consultation Created** → System assigns priority (LOW/MEDIUM/HIGH) based on symptom severity keywords. Doctor load is incremented.
6. **Wait for Response** → Patient sees consultation in dashboard with "pending" status
7. **Doctor Responds** → Patient receives structured response (Acknowledgement, Advice, Tests, Urgency)
8. **Two-Way Chat** → Patient can message doctor for follow-up questions (until case resolved)
9. **Book Labs/Order Meds** → Patient can browse and book lab tests or order medicines separately

### 3.2 Doctor Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Register/     │───▶│  View Patient    │───▶│  Review AI       │
│   Login         │    │  Queue (sorted   │    │  Insight +       │
│  (with spec)    │    │  by severity)    │    │  Symptoms        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Mark Resolved  │◀───│  Open Chat for   │◀───│  Submit Structured│
│  or Edit        │    │  Follow-ups      │    │  Response         │
│  Response       │    │                  │    │  (with AI assist) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Detailed Steps:**
1. **Register/Login** → Doctor creates account with specialization (e.g., Cardiologist, Neurologist). Must be verified by admin.
2. **View Dashboard** → Sees analytics (Patients Today, Pending, High Severity, Avg Response Time)
3. **Patient Queue** → Left panel shows all assigned patients, sorted by priority (HIGH → MEDIUM → LOW)
4. **Select Patient** → Right panel shows full details: symptoms, AI insight, patient message, doctor public stats
5. **AI Assist** → Can auto-generate full response, suggest tests, or add urgency
6. **Submit Response** → Fills 4 structured fields: Acknowledgement, Advice, Recommended Tests, Urgency
7. **Edit Response** → Can modify submitted response after the fact
8. **Open Chat** → Real-time chat panel for back-and-forth with patient
9. **Mark Resolved** → Closes the case when treatment is complete. Doctor load is decremented.
10. **Send Follow-up** → Can proactively message patient even after responding

### 3.3 Authentication Flow

```
POST /api/auth/register  → Creates user (patient or doctor)
POST /api/auth/login     → Returns JWT token + user object
JWT stored in localStorage → Attached to every API call via Axios interceptor
Role-based route guards    → Patient routes blocked for doctors, vice versa
```

---

## 4. Backend Architecture

### 4.1 Project Structure
```
backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── extensions.py            # db, migrate, jwt
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py              # User (patient/doctor/admin) + availability + load + verified
│   │   ├── consultation.py      # Consultation (core entity)
│   │   ├── followup.py          # Chat messages
│   │   ├── symptom_report.py    # AI prediction history
│   │   ├── lab_test.py          # Lab test catalog
│   │   ├── medicine.py          # Medicine catalog
│   │   ├── order.py             # Lab/medicine orders
│   │   ├── appointment.py       # Appointments
│   │   └── patient_profile.py   # Extended patient data
│   ├── routes/
│   │   ├── auth.py              # Login/register
│   │   ├── consultation.py      # CRUD + chat + history + doctor preview/stats/recommend
│   │   ├── doctor.py            # Doctor-only routes
│   │   ├── patient.py           # Patient-only routes
│   │   └── symptoms.py          # AI prediction endpoint
│   ├── services/
│   │   ├── consultation_service.py  # Business logic (load balancing, history, stats)
│   │   ├── auth_service.py          # Auth helpers
│   │   ├── prediction_service.py    # ML wrapper
│   │   └── order_service.py         # Order processing
│   ├── utils/
│   │   ├── symptom_utils.py     # Normalization + AI insights + response generation
│   │   ├── time_format.py       # Human-readable timestamps
│   │   ├── decorators.py        # Role-required decorator
│   │   └── seed.py              # Seed data (doctors, lab tests, medicines)
│   └── ml/
│       ├── symptom_model.py     # Model loader/predictor (top-k + spell correction)
│       ├── train_model.py       # Training script
│       └── artifacts/           # Saved model + valid symptoms
├── config.py                    # Environment config
├── run.py                       # Entry point
└── migrations/                  # Alembic migrations
```

### 4.2 Key Design Patterns
- **App Factory Pattern:** `create_app()` builds and configures Flask app
- **Service Layer:** Business logic separated from routes
- **Blueprint Architecture:** Modular route organization
- **ORM Relationships:** Bidirectional relationships with `back_populates`
- **Model Caching:** ML model loaded once and cached in memory

---

## 5. Frontend Architecture

### 5.1 Project Structure
```
frontend/src/
├── App.jsx                      # Root router + layout
├── main.jsx                     # Entry point
├── index.css                    # Tailwind + custom theme
├── components/
│   └── NavBar.jsx               # Top navigation (role-aware)
├── pages/
│   ├── LoginPage.jsx            # Patient/doctor login
│   ├── LoginPage.css            # Custom login styles
│   ├── RegisterPage.jsx         # Registration with specialization
│   ├── PatientDashboard.jsx     # Patient dashboard + chat modal + history
│   ├── DoctorDashboard.jsx      # 2-panel clinical interface + inline chat + edit response
│   ├── SubmitSymptomsPage.jsx   # Symptom input + doctor selection marketplace
│   ├── LabTestsPage.jsx         # Lab test catalog + booking
│   └── MedicinesPage.jsx        # Medicine catalog + ordering
└── services/
    ├── api.js                   # Axios instance with JWT
    ├── auth.js                  # Auth API calls
    └── consultation.js          # Consultation API calls (+ doctors preview/stats/recommend)
```

### 5.2 Route Structure
| Route | Role | Page |
|-------|------|------|
| `/login` | Any | LoginPage |
| `/register` | Any | RegisterPage |
| `/patient/dashboard` | Patient | PatientDashboard |
| `/patient/submit-symptoms` | Patient | SubmitSymptomsPage |
| `/patient/lab-tests` | Patient | LabTestsPage |
| `/patient/medicines` | Patient | MedicinesPage |
| `/doctor/dashboard` | Doctor | DoctorDashboard |

### 5.3 State Management
- **Local component state** via `useState`
- **Side effects** via `useEffect` (data fetching, polling)
- **Callbacks** via `useCallback` (performance optimization)
- **No global state library** — kept simple for MVP scope

---

## 6. Database Schema

### 6.1 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│    users    │◄─────►│  consultations  │◄─────►│  followups  │
│  (patients, │       │                 │       │  (chat msgs)│
│   doctors)  │       │  - symptoms     │       └─────────────┘
└─────────────┘       │  - predicted    │
       │              │    condition    │
       │              │  - priority     │
       ▼              │  - status       │
┌─────────────┐       │  - AI insight   │
│symptom_reports│     │  - structured   │
│             │       │    response     │
└─────────────┘       └─────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  lab_tests  │       │  medicines  │       │   orders    │
│             │       │             │       │             │
└─────────────┘       └─────────────┘       └─────────────┘
```

### 6.2 Table Details

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String(255) | Full name |
| email | String(255) | Unique |
| password_hash | String(255) | Bcrypt hashed |
| role | String(32) | patient / doctor / admin |
| specialization | String(128) | Doctor only |
| is_available | Boolean | Doctor availability status |
| current_load | Integer | Active consultation count |
| is_verified | Boolean | Admin verification status |
| created_at | DateTime | |

#### `consultations` (Core Entity)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| patient_id | FK → users | |
| doctor_id | FK → users | |
| symptoms | Text | Raw input |
| symptoms_clean | Text | Normalized |
| predicted_condition | String(255) | AI output |
| confidence_score | Float | 0.0–1.0 |
| message | Text | Patient free-text message |
| response_acknowledgement | Text | Doctor structured response |
| response_advice | Text | |
| response_tests | Text | |
| response_urgency | Text | |
| ai_insight | Text | AI-generated clinical insight |
| ai_risk_level | String(32) | LOW/MEDIUM/HIGH |
| ai_suggested_steps | Text | |
| status | String(32) | pending / responded / resolved |
| priority | String(32) | LOW / MEDIUM / HIGH |
| created_at | DateTime | |
| responded_at | DateTime | |
| resolved_at | DateTime | |

#### `followups` (Chat Messages)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| consultation_id | FK → consultations | Cascade delete |
| sender_role | String(16) | doctor / patient |
| sender_id | FK → users | |
| message | Text | |
| created_at | DateTime | |

#### `lab_tests`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String(255) | |
| description | Text | |
| price | Float | KSh |

#### `medicines`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String(255) | |
| manufacturer | String(255) | |
| price | Float | KSh |
| stock_level | Integer | |
| requires_prescription | Boolean | |

#### `orders`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | FK → users | |
| order_type | String(32) | lab_test / medicine |
| item_id | Integer | |
| status | String(32) | |
| created_at | DateTime | |

#### `file_attachments`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| consultation_id | FK → consultations | Indexed |
| uploaded_by | FK → users | |
| filename | String(255) | Stored UUID filename |
| original_filename | String(255) | User's original filename |
| file_path | String(500) | Absolute path on disk |
| file_size | Integer | Bytes |
| mime_type | String(128) | e.g., image/jpeg |
| file_category | String(32) | image / document |
| created_at | DateTime | |

---

## 7. API Endpoints

### 7.1 Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | — | Register new user |
| POST | `/api/auth/login` | — | Login, returns JWT |

### 7.2 AI Prediction
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/predict` | JWT + patient | Submit symptoms, get AI predictions (top-k) |

### 7.3 Patient Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/patient/predictions` | JWT + patient | Prediction history |
| GET | `/api/patient/lab-tests` | JWT + patient | List lab tests |
| GET | `/api/patient/medicines` | JWT + patient | List medicines |
| POST | `/api/patient/orders/lab-test` | JWT + patient | Book lab test |
| POST | `/api/patient/orders/medicine` | JWT + patient | Order medicine |

### 7.4 Doctor Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/doctor/symptom-reports` | JWT + doctor | All symptom reports |

### 7.5 Consultation Routes (Core)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/consultation/create` | JWT + patient | Create consultation (with preferred_doctor_id override) |
| GET | `/api/consultation/patient` | JWT + patient | Patient's consultations |
| GET | `/api/consultation/doctor` | JWT + doctor | Doctor's consultations |
| POST | `/api/consultation/respond/<id>` | JWT + doctor | Submit structured response |
| POST | `/api/consultation/respond/<id>/edit` | JWT + doctor | Edit existing response |
| POST | `/api/consultation/followup/<id>` | JWT + any | Send chat message |
| POST | `/api/consultation/resolve/<id>` | JWT + doctor | Mark resolved |
| GET | `/api/consultation/stats` | JWT + doctor | Dashboard analytics |
| GET | `/api/consultation/ai-response/<id>` | JWT + doctor | AI response suggestions |
| GET | `/api/consultation/history/<id>` | JWT + any | Full consultation timeline |
| GET | `/api/consultation/doctors/preview` | JWT + patient | List all verified doctors for selection |
| GET | `/api/consultation/doctors/<id>/stats` | JWT + patient | Public stats for a doctor |
| GET | `/api/consultation/doctors/recommend` | JWT + patient | Get AI-recommended doctor for condition |

### 7.6 File Upload Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/upload` | JWT | Upload file for a consultation (max 5MB, jpg/png/gif/pdf) |
| GET | `/api/upload/consultation/<id>` | JWT | List files for a consultation |
| GET | `/api/upload/file/<id>` | JWT | Download/serve a file |
| DELETE | `/api/upload/file/<id>` | JWT | Delete a file (uploader or doctor only) |

### 7.7 Admin Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/admin/dashboard` | JWT + admin | Platform analytics |
| GET | `/api/admin/doctors` | JWT + admin | List all doctors |
| POST | `/api/admin/doctors/<id>/verify` | JWT + admin | Verify doctor |
| POST | `/api/admin/doctors/<id>/unverify` | JWT + admin | Unverify doctor |
| POST | `/api/admin/doctors/<id>/availability` | JWT + admin | Toggle doctor availability |
| GET | `/api/admin/users` | JWT + admin | List all users |
| GET | `/api/admin/patients` | JWT + admin | List all patients |
| GET | `/api/admin/consultations` | JWT + admin | List all consultations |
| GET | `/api/admin/payments` | JWT + admin | List all payments |
| GET | `/api/admin/reviews` | JWT + admin | List all reviews |

### 7.8 Appointment Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/appointments/doctor/<id>/available-slots` | JWT | Get available time slots |
| POST | `/api/appointments/book` | JWT + patient | Book an appointment |
| GET | `/api/appointments/patient` | JWT + patient | Patient's appointments |
| GET | `/api/appointments/doctor` | JWT + doctor | Doctor's appointments |
| POST | `/api/appointments/<id>/cancel` | JWT | Cancel an appointment |

### 7.9 Payment Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/payments/create` | JWT | Create a payment |
| POST | `/api/payments/<id>/complete` | JWT | Complete a payment |
| GET | `/api/payments/my-payments` | JWT | Get user's payments |

### 7.10 Review Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/reviews/create` | JWT + patient | Create a review |
| GET | `/api/reviews/doctor/<id>` | JWT | Get doctor's reviews |
| GET | `/api/reviews/doctor/<id>/summary` | JWT | Get doctor's review summary |

---

## 8. AI/ML System

### 8.1 Model Details
- **Algorithm:** Random Forest Classifier (scikit-learn)
- **Training Data:** 132 symptoms → 41 diseases (from Kaggle dataset)
- **Accuracy:** 97.6% (on test set)
- **Output:** Top 3 predicted conditions with confidence scores
- **Features:** Spell correction via fuzzy matching (`difflib.get_close_matches`)
- **Caching:** Model loaded once and cached in memory on first use

### 8.2 Prediction Flow
```
Patient inputs: "fever, headache, joint pain"
        │
        ▼
┌─────────────────┐
│ Text Parsing    │ → Split by commas/spaces, normalize
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Spell Correction│ → Fuzzy match against 132 valid symptoms
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Symptom Vector  │ → Binary vector (132 features)
│ Construction    │ → 1 = symptom present, 0 = absent
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Random Forest   │ → Predicts disease probabilities
│ Classifier      │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Top 3 Results   │ → Malaria (82%), Typhoid (45%), Flu (30%)
└─────────────────┘
```

### 8.3 Model Training
- Training script: `backend/app/ml/train_model.py`
- Saved model: `backend/app/ml/artifacts/symptom_model.joblib`
- Valid symptoms: `backend/app/ml/artifacts/valid_symptoms.json`
- Auto-trains on first run if no saved model exists

---

## 9. Symptom Normalization

### 9.1 Problem
Patients type symptoms in inconsistent ways:
- `paininthejoint` → should be `Joint Pain`
- `stomachache` → should be `Abdominal Pain`
- `feverish` → should be `Fever`

### 9.2 Solution
Comprehensive alias mapping in `backend/app/utils/symptom_utils.py`:

```python
_SYMPTOM_ALIASES = {
    "paininthejoint": "Joint Pain",
    "jointpain": "Joint Pain",
    "stomachache": "Abdominal Pain",
    "stomach ache": "Abdominal Pain",
    "feverish": "Fever",
    "high temp": "Fever",
    "coughing": "Cough",
    "nauseous": "Nausea",
    # ... 50+ aliases
}
```

### 9.3 Normalization Process
1. Split by commas, semicolons, or newlines
2. Strip whitespace, lowercase
3. Check alias dictionary
4. If no alias: capitalize each word (`"headache"` → `"Headache"`)
5. Deduplicate
6. Return comma-separated clean string

### 9.4 AI Response Generation
The system auto-generates structured response components:
- **Acknowledgement:** "Thank you for reaching out. I have reviewed your reported symptoms (X, Y, Z)."
- **Advice:** Priority-based (HIGH = prompt attention, MEDIUM = monitor 24-48h, LOW = self-care)
- **Tests:** Condition-specific test recommendations (e.g., malaria → thick/thin smear, RDT, CBC)
- **Urgency:** Priority-based urgency messaging

---

## 10. Doctor Assignment Logic

### 10.1 Smart Doctor Selection with Load Balancing
```python
def find_best_doctor(specialization, preferred_doctor_id=None):
    # Step 0: Patient override
    if preferred_doctor_id:
        return preferred doctor if valid
    
    # Step 1: Match specialization (verified doctors only)
    # Step 2: Filter available doctors
    # Step 3: Sort by least load (current_load)
    # Step 4: Return least busy doctor
    
    # Fallback: General Doctor → Any verified doctor
```

### 10.2 Assignment Flow
```
Patient submits symptoms
        │
        ▼
AI predicts condition (e.g., "diabetes")
        │
        ▼
System maps to specialization ("Endocrinologist")
        │
        ▼
Finds verified doctor with matching specialization
        │
        ▼
Sorts by availability, then by lowest current_load
        │
        ▼
Assigns consultation to least busy matching doctor
        │
        ▼
Doctor current_load incremented
        │
        ▼
Patient can PREVIEW all doctors and OVERRIDE selection
```

### 10.3 Doctor Marketplace (Patient View)
Patients on the Submit Symptoms page see:
- All verified doctors with name, specialization, availability badge
- Current workload (active patient count)
- AI-recommended doctor highlighted
- Click to select any doctor (checkmark appears)

### 10.4 Priority Assignment
Based on symptom/condition keywords:

| Priority | Keywords | Examples |
|----------|----------|----------|
| **HIGH** | chest pain, severe pain, difficulty breathing, unconscious, seizure, bleeding, heart attack, stroke, suicide | Immediate care required |
| **MEDIUM** | fever, vomiting, weakness, dizziness, nausea, diarrhea, cough, headache, fatigue | Visit within 24-48 hours |
| **LOW** | mild symptoms not in above lists | Self-care suggested |

---

## 11. Real-Time Features

### 11.1 Auto-Refresh Polling
| Dashboard | Interval | Behavior |
|-----------|----------|----------|
| Doctor Dashboard | 12 seconds | Refetches consultations + stats silently |
| Patient Dashboard | 15 seconds | Refetches consultations + predictions |

### 11.2 New Case Notifications
- Doctor dashboard compares consultation count between polls
- If new cases detected: shows toast `"3 new patient cases received"`
- Shows red pulse badge with count
- Badge disappears after 5 seconds

### 11.3 Chat Auto-Refresh
- Both patient and doctor chat poll every 5 seconds
- Fetches consultation history and filters for followup messages
- Auto-scrolls to latest message

---

## 12. Two-Way Chat System

### 12.1 Architecture
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Patient   │◄───────►│  FollowUp   │◄───────►│   Doctor    │
│   Chat UI   │         │   Model     │         │   Chat UI   │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ Consultation│
                       │  History    │
                       │  Endpoint   │
                       └─────────────┘
```

### 12.2 Patient Chat Experience
- Click "💬 Message Doctor" on any active consultation
- Modal opens with full chat interface
- Messages shown as bubbles (patient = teal right, doctor = gray left)
- Input field + Send button
- Auto-refreshes every 5 seconds

### 12.3 Doctor Chat Experience
- Click "💬 Open Chat" in the response section
- Inline chat panel appears below the response form
- Same bubble styling but reversed (doctor = teal right, patient = gray left)
- Auto-refreshes every 5 seconds

### 12.4 Security
- `add_followup()` validates sender is part of the consultation
- Patients can only message their own consultations
- Doctors can only message their assigned consultations

---

## 13. Trust & Credibility

### 13.1 Implemented Trust Features
| Feature | Implementation |
|---------|---------------|
| **AI Disclaimer** | "AI-assisted predictions. Not a final medical diagnosis." — shown on both dashboards |
| **Doctor Verification Badge** | Blue "Verified" badge next to doctor name (only `is_verified=True`) |
| **Doctor Availability** | Green/gray dot showing online/offline status |
| **Doctor Workload** | Current patient load visible to patients |
| **Doctor Specialization** | Always displayed with doctor name |
| **Timestamp with Timezone** | Full localized timestamp (e.g., "Apr 23, 2026, 06:45 PM GMT+3") |
| **Structured Responses** | Doctor responses have 4 mandatory fields, not free text |
| **Confidence Scores** | AI predictions show % confidence with color coding |
| **Severity System** | Color-coded badges (Green/Yellow/Red) with clinical meaning |

### 13.2 Severity Color Coding
| Severity | Color | Meaning | Action |
|----------|-------|---------|--------|
| LOW | Green 🟢 | Mild symptoms | Self-care suggested |
| MEDIUM | Yellow 🟡 | Needs attention | Visit within 24-48 hours |
| HIGH | Red 🔴 | Serious condition | Immediate care required |

Applied to: badges, card border tints, background tints, urgency boxes

---

## 14. Pages & Screens

### 14.1 Login Page (`/login`)
- Gradient background with radial accents
- Centered card with medical cross icon
- Email + Password inputs with focus animations
- "Remember me" checkbox + "Forgot password" link
- Loading spinner on submit
- Auto-redirects by role after login

### 14.2 Register Page (`/register`)
- Centered card layout
- Fields: Full Name, Email, Password, Role (dropdown)
- If Role = Doctor: shows Specialization dropdown (11 options)
- Styled error/success alert boxes
- "Already have an account?" link

### 14.3 Patient Dashboard (`/patient/dashboard`)
- **Header:** Title + consultation count
- **Disclaimer banner:** AI not a diagnosis
- **Consultations list:** Expandable cards with:
  - Severity badge + Status badge + Time
  - Predicted condition
  - Symptom chips (first 5)
  - Doctor badge (name + specialization + verified)
  - Expanded view shows: All symptoms, patient message, AI insight, doctor response (structured), action buttons
- **Action buttons:** "💬 Message Doctor" (if active), "View Full History"
- **Prediction History table:** Date, Symptoms, Predicted, Confidence

### 14.4 Doctor Dashboard (`/doctor/dashboard`)
- **Analytics header:** 4 stat cards (Patients Today, Pending, High Severity, Avg Response Time)
- **New case badge:** Red pulse indicator
- **Disclaimer banner**
- **Two-panel layout:**
  - **Left (32%):** Search bar + filter pills (All/Pending/Responded/High Priority) + scrollable patient list with severity tinting
  - **Right (68%):** Selected patient details
    - Header: Name, email, severity, status, timestamp, doctor badge
    - Condition block with confidence
    - Symptoms as chips
    - Patient message
    - AI Clinical Insight with risk level
    - Doctor Response section with AI assist buttons
    - Structured response form (4 fields)
    - Action buttons: Edit Response, Open Chat, View History, Mark Resolved
    - Inline chat panel (when opened)

### 14.5 Submit Symptoms Page (`/patient/submit-symptoms`)
- Header with description
- Symptom textarea with placeholder
- Analyze button with loading spinner
- **Results section:**
  - 3 prediction cards with confidence badges and progress bars
  - "Top Match" label on highest confidence
  - Recommendation banner
  - Disclaimer
- **Doctor Selection section (Marketplace):**
  - AI-recommended doctor highlighted
  - Grid of ALL verified doctor cards with avatar, name, specialization, availability dot, workload
  - Click to select (checkmark appears)
  - Selected doctor banner
  - "Consult Doctor" button + "Go to Dashboard" button

### 14.6 Lab Tests Page (`/patient/lab-tests`)
- Header + description
- Grid of test cards (2 columns on desktop)
- Each card: Test name, description, price badge (primary color), "Book" button
- Loading spinner while fetching
- Empty state if no tests

### 14.7 Medicines Page (`/patient/medicines`)
- Header + description
- Grid of medicine cards (2 columns on desktop)
- Each card: Medicine name, manufacturer, price badge, prescription required badge (red), stock level, "Order" button
- Out-of-stock items: grayed out, disabled button
- Loading spinner while fetching

---

## 15. Known Limitations & Suggestions

### 15.1 Current Limitations

| # | Limitation | Impact |
|---|-----------|--------|
| 1 | ~~No admin dashboard~~ | ✅ Implemented — full admin dashboard with KPIs, doctor management, payments, reviews |
| 2 | ~~No doctor availability status toggle~~ | ✅ Implemented — admin can toggle doctor availability |
| 3 | ~~No appointment scheduling~~ | ✅ Implemented — patients can book appointments with time slots |
| 4 | ~~No payment integration~~ | ✅ Implemented — M-Pesa/Card/Cash payment flow with PaymentModal |
| 5 | ~~No push notifications~~ | ✅ Implemented — toast notification system for user feedback |
| 6 | ~~No file uploads~~ | ✅ Implemented — drag-drop file upload for images and PDFs |
| 7 | ~~No doctor ratings/reviews~~ | ✅ Implemented — patients can leave star ratings and comments |
| 8 | **JWT key is short (28 bytes)** | Security warning — should be 32+ bytes |
| 9 | **No email/SMS notifications** | No external notification system |
| 10 | **SQLite for production** | Won't scale beyond a few concurrent users |

### 15.2 Architectural Suggestions (For ChatGPT Reasoning)

#### Suggestion 1: Admin Dashboard
**Why needed:** As the platform scales beyond 5-10 doctors, manual management becomes impossible.
**Features:**
- Doctor management (approve, suspend, edit specializations)
- Platform analytics (total consultations, revenue, response times)
- Patient management (view history, flag abuse)
- System configuration (severity keywords, specialization mapping)

#### Suggestion 2: WebSocket-Based Real-Time
**Current:** Polling every 5-15 seconds
**Proposed:**
- Socket.IO or native WebSockets for instant chat
- Push notifications for new consultations
- Doctor "typing" indicators
- Reduced server load vs polling

#### Suggestion 3: Appointment Scheduling
**Current:** Consultations are async (submit → wait for response)
**Proposed:**
- Doctor sets available time slots
- Patient books video/voice call appointment
- Calendar integration
- Reminder notifications

#### Suggestion 4: ~~File Attachments~~ ✅ Implemented
**Status:** Patients can upload images (JPG, PNG, GIF) and PDFs up to 5MB per file. Files are stored per-consultation with auth-protected access. Doctors can view patient uploads in the consultation detail panel.

#### Suggestion 5: Payment Integration
**Current:** Prices shown but no payment
**Proposed:**
- M-Pesa / Stripe integration for Kenya market
- Doctor consultation fees
- Lab test and medicine payments
- Commission system for platform revenue

#### Suggestion 6: Multi-Language Support
**Current:** English only
**Proposed:**
- Swahili for Kenyan market
- Symptom normalization in multiple languages
- Localized medical terminology

---

## 16. Testing Results

### 16.1 Backend Tests (Manual)
| Test | Result |
|------|--------|
| App loads without errors | ✅ PASS |
| All 9 database tables exist | ✅ PASS |
| 6 seed doctors created | ✅ PASS |
| 7 lab tests seeded | ✅ PASS |
| 6 medicines seeded | ✅ PASS |
| Symptom normalization works | ✅ PASS (`paininthejoint` → `Joint Pain`) |
| AI insight generation works | ✅ PASS |
| Doctor assignment by specialization | ✅ PASS |
| Load balancing (least busy doctor) | ✅ PASS |
| Priority assignment (MEDIUM for fever) | ✅ PASS |
| Consultation creation | ✅ PASS |
| Structured doctor response | ✅ PASS |
| Two-way followup messages | ✅ PASS |
| History timeline generation | ✅ PASS (4 items: created, responded, 2 followups) |
| Doctor stats calculation | ✅ PASS |
| Public doctor stats endpoint | ✅ PASS |
| Doctor recommendation endpoint | ✅ PASS |
| All 24 API routes registered | ✅ PASS |
| File upload endpoints | ✅ PASS |
| File attachment model | ✅ PASS |

### 16.2 Frontend Tests (Build)
| Test | Result |
|------|--------|
| Production build succeeds | ✅ PASS |
| No compilation errors | ✅ PASS |
| CSS bundle: 55.63 KB | ✅ PASS |
| JS bundle: 410.65 KB | ✅ PASS |
| Toast notification system | ✅ PASS |
| Skeleton loaders | ✅ PASS |
| Empty state components | ✅ PASS |
| Split-screen auth pages | ✅ PASS |
| Mobile responsive NavBar | ✅ PASS |

### 16.3 Integration Tests (End-to-End)
| Test | Result |
|------|--------|
| Patient registers → logs in → submits symptoms → gets predictions | ✅ PASS |
| Patient sees doctor marketplace with availability + workload | ✅ PASS |
| Patient selects doctor → creates consultation | ✅ PASS |
| Doctor logs in → sees consultation in queue | ✅ PASS |
| Doctor submits structured response | ✅ PASS |
| Patient sees response in dashboard | ✅ PASS |
| Patient sends chat message | ✅ PASS |
| Doctor sees chat message | ✅ PASS |
| Doctor replies in chat | ✅ PASS |
| Doctor edits response | ✅ PASS |
| Doctor marks case resolved | ✅ PASS |
| Patient books lab test | ✅ PASS |
| Patient orders medicine | ✅ PASS |
| Patient uploads file to consultation | ✅ PASS |
| Doctor views patient file attachments | ✅ PASS |
| Toast notifications replace alerts | ✅ PASS |

---

## Appendix A: File Inventory

### Backend Files Modified/Created
| File | Status | Description |
|------|--------|-------------|
| `backend/app/models/followup.py` | ✅ Created | Chat message model |
| `backend/app/models/__init__.py` | ✅ Modified | Import order fix + FollowUp export |
| `backend/app/models/user.py` | ✅ Modified | Added followups, is_available, current_load, is_verified |
| `backend/app/models/consultation.py` | ✅ Modified | Added followups relationship + doctor availability fields |
| `backend/app/routes/consultation.py` | ✅ Modified | +edit, +followup, +history, +doctors/preview, +doctors/stats, +doctors/recommend |
| `backend/app/services/consultation_service.py` | ✅ Modified | +edit_response, +add_followup (two-way), +get_doctors_for_preview, +get_doctor_public_stats, +get_recommended_doctor, +find_best_doctor (load balancing) |
| `backend/app/utils/symptom_utils.py` | ✅ Modified | +generate_acknowledgement, +generate_advice, +generate_suggested_tests, +generate_urgency |
| `backend/app/utils/seed.py` | ✅ Modified | Seed doctors with is_verified=True, is_available=True, current_load=0 |
| `backend/app/ml/symptom_model.py` | ✅ Modified | +predict_topk, +spell correction, +model caching |
| `backend/app/models/file_attachment.py` | ✅ Created | FileAttachment model for consultation uploads |
| `backend/app/routes/upload.py` | ✅ Created | Upload, list, serve, delete file endpoints |
| `backend/config.py` | ✅ Modified | Added MAX_CONTENT_LENGTH (5MB) |

### Frontend Files Modified/Created
| File | Status | Description |
|------|--------|-------------|
| `frontend/src/pages/DoctorDashboard.jsx` | ✅ Modified | 2-panel + inline chat + edit response + history + AI assist |
| `frontend/src/pages/PatientDashboard.jsx` | ✅ Modified | Chat modal + message doctor button + history + prediction table |
| `frontend/src/pages/SubmitSymptomsPage.jsx` | ✅ Modified | Doctor marketplace with availability, workload, recommendation |
| `frontend/src/pages/RegisterPage.jsx` | ✅ Modified | Split-screen layout with password strength, role cards |
| `frontend/src/pages/LoginPage.jsx` | ✅ Modified | Split-screen layout with trust badges, password toggle |
| `frontend/src/pages/AuthPages.css` | ✅ Created | Shared auth page styles |
| `frontend/src/components/NavBar.jsx` | ✅ Modified | Tailwind + active states + mobile hamburger menu |
| `frontend/src/components/Toast.jsx` | ✅ Created | Toast notification item component |
| `frontend/src/components/ToastProvider.jsx` | ✅ Created | Global toast context + useToast hook |
| `frontend/src/components/Skeleton.jsx` | ✅ Created | Skeleton loaders (text, card, table, stats, pills) |
| `frontend/src/components/EmptyState.jsx` | ✅ Created | Reusable empty state with icon + CTA |
| `frontend/src/components/AnimatedModal.jsx` | ✅ Created | Modal wrapper with enter/exit animations |
| `frontend/src/components/FileUploadZone.jsx` | ✅ Created | Drag-drop file upload with preview |
| `frontend/src/services/upload.js` | ✅ Created | File upload API service |
| `frontend/src/pages/LabTestsPage.jsx` | ✅ Modified | Grid layout with styled cards |
| `frontend/src/pages/MedicinesPage.jsx` | ✅ Modified | Grid layout with stock/prescription badges |
| `frontend/src/services/consultation.js` | ✅ Modified | +getDoctorsPreview, +getDoctorPublicStats, +getRecommendedDoctor |

---

## Appendix B: Seed Data

### Doctors (Auto-Created)
| Name | Specialization | Email | Verified | Available |
|------|---------------|-------|----------|-----------|
| Dr. Sarah Kimani | General Doctor | sarah@mediassist.local | ✅ | ✅ |
| Dr. James Ochieng | Endocrinologist | james@mediassist.local | ✅ | ✅ |
| Dr. Amina Hassan | Pulmonologist | amina@mediassist.local | ✅ | ✅ |
| Dr. Peter Mwangi | Cardiologist | peter@mediassist.local | ✅ | ✅ |
| Dr. Grace Wanjiku | Neurologist | grace@mediassist.local | ✅ | ✅ |
| Dr. David Otieno | Dermatologist | david@mediassist.local | ✅ | ✅ |

### Lab Tests (Auto-Created)
Complete Blood Count (CBC), Blood Glucose Fasting, Lipid Profile, Kidney Function Test, Liver Function Test, Thyroid Panel (TSH), Urine Analysis

### Medicines (Auto-Created)
Paracetamol 500mg, Amoxicillin 250mg, Ibuprofen 400mg, Omeprazole 20mg, Cetirizine 10mg, Metformin 500mg

---

*End of Documentation*
