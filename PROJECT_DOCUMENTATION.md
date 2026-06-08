# MediAssist AI — Complete Project Documentation

> **Last Updated:** 27 May 2026
> **Status:** Production-Ready MVP with Real-Time Chat, AI Predictions, Load-Balanced Doctor Assignment, File Uploads, M-Pesa Payment Integration, Appointment Scheduling, and Complete UI/UX Polish

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
13. [M-Pesa Payment Integration](#13-mpesa-payment-integration)
14. [Trust & Credibility](#14-trust--credibility)
15. [Pages & Screens](#15-pages--screens)
16. [Known Limitations & Suggestions](#16-known-limitations--suggestions)
17. [Testing Results](#17-testing-results)

---

## 1. Project Overview

**MediAssist AI** is a full-stack healthcare web application that connects patients with doctors through an AI-assisted clinical workflow. Patients submit symptoms, receive AI-powered condition predictions, and get structured medical responses from verified doctors. The system includes real-time two-way messaging, lab test booking, medicine ordering, doctor marketplace with load balancing, M-Pesa payment integration, appointment scheduling, and comprehensive analytics.

### Core Value Proposition
- **For Patients:** Quick AI symptom analysis + transparent doctor selection + direct access to verified doctors + structured medical advice + M-Pesa payments + appointment booking
- **For Doctors:** Organized patient queue with severity prioritization + AI-assisted response generation + real-time chat + workload analytics
- **For Platform:** Scalable specialization-based routing with load balancing + clean audit trails + trust-building features + revenue analytics

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
| Payment API | Safaricom Daraja M-Pesa API |
| CORS | flask-cors |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 (Vite) |
| Styling | Tailwind CSS v4 |
| Routing | react-router-dom |
| HTTP Client | Axios |
| Icons | Lucide React |

### DevOps
| Component | Technology |
|-----------|------------|
| Build Tool | Vite |
| Proxy | Vite dev server proxies `/api` → `localhost:5000` |
| Package Manager | npm (frontend), pip (backend) |
| Tunnel | ngrok (for M-Pesa callbacks) |

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
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Book Lab Tests │    │  Order Medicines │    │  Pay via M-Pesa │
│  (if advised)   │    │  (if prescribed) │    │  (KSh 1 demo)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Book Appointment│
                                               │  (with doctor)   │
                                               └─────────────────┘
```

**Detailed Steps:**
1. **Register/Login** → Patient creates account (name, email, password, role="patient")
2. **Submit Symptoms** → Types symptoms in natural language (e.g., "headache, fever, body aches")
3. **AI Analysis** → Hybrid clinical engine predicts top 3 conditions with confidence scores
4. **Doctor Selection** → Patient sees ALL verified doctors with availability, workload, and specialization. Can override the AI-recommended doctor.
5. **Consultation Created** → System assigns priority (LOW/MEDIUM/HIGH) based on symptom severity keywords. Doctor load is incremented.
6. **Wait for Response** → Patient sees consultation in dashboard with "pending" status
7. **Doctor Responds** → Patient receives structured response (Acknowledgement, Advice, Tests, Urgency)
8. **Two-Way Chat** → Patient can message doctor for follow-up questions (until case resolved)
9. **Book Labs/Order Meds** → Patient can browse and book lab tests or order medicines separately
10. **Pay via M-Pesa** → Patient pays for services using Safaricom M-Pesa STK Push (demo mode: always KSh 1)
11. **Book Appointment** → Patient can book appointments with doctors

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
│   │   ├── payment.py           # Payment records with M-Pesa
│   │   ├── review.py            # Doctor reviews
│   │   └── patient_profile.py   # Extended patient data
│   ├── routes/
│   │   ├── auth.py              # Login/register
│   │   ├── consultation.py      # CRUD + chat + history + doctor preview/stats/recommend
│   │   ├── doctor.py            # Doctor-only routes
│   │   ├── patient.py           # Patient-only routes
│   │   ├── symptoms.py          # AI prediction endpoint
│   │   ├── payment.py           # M-Pesa payment endpoints
│   │   ├── appointment.py       # Appointment booking
│   │   ├── review.py            # Doctor reviews
│   │   └── upload.py            # File uploads
│   ├── services/
│   │   ├── consultation_service.py  # Business logic (load balancing, history, stats)
│   │   ├── auth_service.py          # Auth helpers
│   │   ├── prediction_service.py    # ML wrapper
│   │   ├── payment_service.py       # Payment processing
│   │   ├── mpesa_service.py         # M-Pesa Daraja API integration
│   │   └── order_service.py         # Order processing
│   ├── utils/
│   │   ├── symptom_utils.py     # Normalization + AI insights + response generation
│   │   ├── time_format.py       # Human-readable timestamps
│   │   ├── decorators.py        # Role-required decorator
│   │   └── seed.py              # Seed data (doctors, lab tests, medicines)
│   └── ml/
│       ├── symptom_model.py     # Model loader/predictor (top-k + spell correction)
│       ├── clinical/engine.py   # Hybrid Clinical Prediction Engine
│       ├── train_model.py       # Training script (generic dataset)
│       ├── train_tropical_model.py # Training script (tropical diseases)
│       ├── generate_tropical_dataset.py # Synthetic dataset generator
│       └── artifacts/           # Saved models + valid symptoms
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
│   ├── NavBar.jsx               # Top navigation (role-aware)
│   ├── PaymentModal.jsx         # M-Pesa payment modal with STK Push
│   ├── Toast.jsx                # Toast notification item
│   ├── ToastProvider.jsx        # Global toast context
│   ├── Skeleton.jsx             # Skeleton loaders
│   ├── EmptyState.jsx           # Reusable empty state
│   ├── AnimatedModal.jsx        # Modal with animations
│   └── FileUploadZone.jsx       # Drag-drop file upload
├── pages/
│   ├── LoginPage.jsx            # Patient/doctor login
│   ├── RegisterPage.jsx         # Registration with specialization
│   ├── PatientDashboard.jsx     # Patient dashboard + chat modal + history
│   ├── DoctorDashboard.jsx      # 2-panel clinical interface + inline chat + edit response
│   ├── SubmitSymptomsPage.jsx   # Symptom input + doctor selection marketplace
│   ├── LabTestsPage.jsx         # Lab test catalog + booking + payment
│   ├── MedicinesPage.jsx        # Medicine catalog + ordering + payment
│   ├── AppointmentsPage.jsx     # Appointment booking + payment
│   └── AdminDashboard.jsx       # Admin analytics + doctor management + payments
└── services/
    ├── api.js                   # Axios instance with JWT
    ├── auth.js                  # Auth API calls
    ├── consultation.js          # Consultation API calls
    ├── payment.js               # Payment API calls
    ├── appointment.js           # Appointment API calls
    └── review.js                # Review API calls
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
| `/patient/appointments` | Patient | AppointmentsPage |
| `/doctor/dashboard` | Doctor | DoctorDashboard |
| `/admin/dashboard` | Admin | AdminDashboard |

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
       │
       ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ appointments│       │   payments  │       │   reviews   │
│             │       │  (M-Pesa)   │       │             │
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

#### `payments` (M-Pesa Integration)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | FK → users | |
| appointment_id | FK → appointments | Nullable |
| order_id | FK → orders | Nullable |
| amount | Numeric(10,2) | Actual charged amount (KSh 1 in demo) |
| displayed_amount | Numeric(10,2) | Original price shown to user |
| payment_method | String(32) | M-Pesa / Card / Cash |
| transaction_reference | String(128) | M-Pesa CheckoutRequestID |
| merchant_request_id | String(128) | M-Pesa MerchantRequestID |
| status | String(32) | pending / processing / success / failed / cancelled |
| phone_number | String(16) | Normalized 254XXXXXXXXX |
| mpesa_receipt_number | String(64) | M-Pesa receipt |
| failure_reason | String(255) | Error description |
| paid_at | DateTime | Success timestamp |
| created_at | DateTime | |
| updated_at | DateTime | |

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
| item_type | String(32) | lab_test / medicine |
| item_id | Integer | |
| total_amount | Numeric(10,2) | |
| payment_status | String(32) | pending / paid |
| created_at | DateTime | |

#### `appointments`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| patient_id | FK → users | |
| doctor_id | FK → users | |
| appointment_date | Date | |
| appointment_time | String(16) | |
| status | String(32) | scheduled / completed / cancelled |
| notes | Text | |
| created_at | DateTime | |

#### `reviews`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| patient_id | FK → users | |
| doctor_id | FK → users | |
| rating | Integer | 1-5 stars |
| comment | Text | |
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

### 7.7 Payment Routes (M-Pesa)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/payments/create` | JWT | Create a payment record |
| POST | `/api/payments/<id>/stk-push` | JWT | Initiate M-Pesa STK Push |
| GET | `/api/payments/<id>/status` | JWT | Poll payment status |
| POST | `/api/payments/<id>/complete` | JWT | Legacy simulation complete |
| GET | `/api/payments/my-payments` | JWT | Get user's payment history |
| POST | `/api/payments/mpesa/callback` | — | M-Pesa Daraja callback endpoint |

### 7.8 Appointment Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/appointments/doctor/<id>/available-slots` | JWT | Get available time slots |
| POST | `/api/appointments/book` | JWT + patient | Book an appointment |
| GET | `/api/appointments/patient` | JWT + patient | Patient's appointments |
| GET | `/api/appointments/doctor` | JWT + doctor | Doctor's appointments |
| POST | `/api/appointments/<id>/cancel` | JWT | Cancel an appointment |

### 7.9 Review Routes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/reviews/create` | JWT + patient | Create a review |
| GET | `/api/reviews/doctor/<id>` | JWT | Get doctor's reviews |
| GET | `/api/reviews/doctor/<id>/summary` | JWT | Get doctor's review summary |

### 7.10 Admin Routes
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
| GET | `/api/admin/payments` | JWT + admin | Payment analytics |
| GET | `/api/admin/reviews` | JWT + admin | Review analytics |

---

## 8. AI/ML System

### 8.1 Hybrid Clinical Prediction Engine

The symptom checker uses a **hybrid architecture** combining rule-based clinical scoring with machine learning:

```
User Input → Advanced Normalization → Symptom Extraction →
    → Rule-Based Weighted Scoring (PRIMARY) →
    → ML Fallback (supporting) →
    → Confidence Calibration →
    → Red Flag Detection →
    → Top-3 Ranking + Clinical Insights → API Response
```

### 8.2 Disease Knowledge Base (15 Diseases)

| Disease | Severity | Category |
|---------|----------|----------|
| Malaria | HIGH | infectious |
| Typhoid | HIGH | infectious |
| Dengue | HIGH | infectious |
| Pneumonia | HIGH | respiratory |
| Flu | MEDIUM | respiratory |
| COVID-19 | MEDIUM | respiratory |
| Gastroenteritis | MEDIUM | gastrointestinal |
| Food Poisoning | MEDIUM | gastrointestinal |
| Tuberculosis | HIGH | infectious |
| Asthma | MEDIUM | respiratory |
| UTI | MEDIUM | urinary |
| Chickenpox | LOW | infectious |
| Common Cold | LOW | respiratory |
| Meningitis | HIGH | neurological |
| Diabetes Warning | MEDIUM | endocrine |

### 8.3 Symptom Weighting System

Each disease has symptoms weighted 1-5:
- **5** = Critical/pathognomonic (defining symptom)
- **4** = Core symptom
- **3** = Common symptom
- **2** = Supporting symptom
- **1** = Rare symptom

### 8.4 Prediction Flow

```
Patient inputs: "fever, headache, joint pain"
        │
        ▼
┌─────────────────┐
│ Text Parsing    │ → Split by commas/spaces, normalize
│ + Aliases       │ → Handle misspellings, Swahili, slang
│ + Fuzzy Match   │ → difflib.get_close_matches (65% cutoff)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Symptom Vector  │ → Canonical symptoms extracted
│ Extraction      │ → Multi-word phrases, trigrams, bigrams
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Rule-Based      │ → Weighted symptom scoring per disease
│ Scoring         │ → raw_score = matched_weight / denominator
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Confidence      │ → Calibrate based on symptom count,
│ Calibration     │ → red flags, missing core symptoms
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ ML Fallback     │ → RandomForest (if clinical < 0.50)
│ (Optional)      │ → Dynamic blending weights
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Top 3 Results   │ → Malaria (82%), Typhoid (45%), Flu (30%)
└─────────────────┘
```

### 8.5 ML Model Details

#### Tropical Disease Model (NEW)
- **Algorithm:** Random Forest Classifier (scikit-learn)
- **Training Data:** 1,800 synthetic cases → 15 tropical diseases
- **Features:** 65 canonical symptoms
- **Accuracy:** 99.78% (on 450 test cases)
- **Output:** Top 3 predicted conditions with confidence scores
- **File:** `symptom_model_tropical.joblib`

#### Generic Model (Legacy)
- **Algorithm:** Random Forest Classifier
- **Training Data:** 4,920 cases → 41 diseases (Kaggle dataset)
- **Features:** 132 symptoms
- **Accuracy:** 97.6%
- **File:** `symptom_model.joblib`

### 8.6 Dynamic Blending Weights

When ML fallback activates (clinical confidence < 0.50):

| Clinical Confidence | Clinical Weight | ML Weight |
|---------------------|-----------------|-----------|
| < 0.10 | 40% | 60% |
| < 0.20 | 60% | 40% |
| < 0.35 | 75% | 25% |
| ≥ 0.35 | 85% | 15% |

### 8.7 Model Training
- Tropical training script: `backend/app/ml/train_tropical_model.py`
- Generic training script: `backend/app/ml/train_model.py`
- Tropical model: `backend/app/ml/artifacts/symptom_model_tropical.joblib`
- Generic model: `backend/app/ml/artifacts/symptom_model.joblib`
- Valid symptoms: `backend/app/ml/artifacts/valid_symptoms_tropical.json`

---

## 9. Symptom Normalization

### 9.1 Problem
Patients type symptoms in inconsistent ways:
- `paininthejoint` → should be `Joint Pain`
- `stomachache` → should be `Abdominal Pain`
- `feverish` → should be `Fever`
- `homa kali` → should be `High Fever` (Swahili)

### 9.2 Solution
Comprehensive alias mapping with 200+ entries:

```python
_SYMPTOM_ALIASES = {
    # Misspellings
    "vomitting": "vomiting",
    "diarhea": "diarrhea",
    # Slang
    "puking": "vomiting",
    "throwing up": "vomiting",
    # Swahili
    "homa kali": "high fever",
    "tumbo kuumwa": "abdominal pain",
    "kuchoka sana": "fatigue",
    "shingo ngumu": "stiff neck",
    # ... 200+ more
}
```

### 9.3 Normalization Process
1. Extract multi-word phrases first (longest match wins)
2. Split by commas/semicolons/newlines
3. Strip whitespace, lowercase
4. Check alias dictionary (trigram → bigram → unigram)
5. Fuzzy match against canonical symptoms (65% cutoff)
6. Remove stop words
7. Deduplicate
8. Return canonical symptom list

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

## 13. M-Pesa Payment Integration

### 13.1 Architecture

```
Patient clicks Pay
        │
        ▼
┌─────────────────┐
│ Create Payment  │ → Record created with displayed_amount
│ Record          │ → amount = KSh 1 (demo mode)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Enter Phone     │ → Normalize to 254XXXXXXXXX
│ Number          │ → Validate Kenyan format
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Initiate STK    │ → POST to Safaricom Daraja API
│ Push            │ → Consumer Key + Secret → OAuth token
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Patient Receives│ → M-Pesa popup on phone
│ STK Push        │ → Enter PIN 0000 (sandbox)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Safaricom Sends │ → POST to /api/payments/mpesa/callback
│ Callback        │ → Verify + update transaction
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Frontend Polls  │ → GET /api/payments/<id>/status
│ Status          │ → Every 5 seconds
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Show Receipt    │ → Transaction ID, M-Pesa receipt,
│                 │ → Item, Amount, Timestamp, Status
└─────────────────┘
```

### 13.2 Demo Safety Mode

| Setting | Value | Purpose |
|---------|-------|---------|
| `DEMO_PAYMENT_MODE` | `true` | Always charge KSh 1 |
| Displayed price | Real price (e.g., KSh 1200) | UI shows actual cost |
| STK Push amount | KSh 1 | Safaricom only charges 1 |
| Database `amount` | 1.00 | Actual transaction |
| Database `displayed_amount` | 1200.00 | For analytics/receipts |

### 13.3 Phone Number Normalization

| Input | Output |
|-------|--------|
| `0712345678` | `254712345678` |
| `+254712345678` | `254712345678` |
| `254712345678` | `254712345678` |

### 13.4 Payment Status Tracking

| Status | Description |
|--------|-------------|
| `pending` | Payment record created, not yet initiated |
| `processing` | STK Push sent, waiting for user PIN |
| `success` | Callback received, payment confirmed |
| `failed` | STK Push failed or user declined |
| `cancelled` | User cancelled or timed out |

### 13.5 Environment Variables

```env
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=https://your-ngrok-url/api/payments/mpesa/callback
MPESA_ENV=sandbox
DEMO_PAYMENT_MODE=true
MPESA_DEFAULT_PHONE=254795058994
```

### 13.6 Admin Revenue Analytics

Admin dashboard shows:
- Total revenue (using `displayed_amount` for realistic reporting)
- Completed/failed/pending transaction counts
- Payment method breakdown
- Revenue by payment method

---

## 14. Trust & Credibility

### 14.1 Implemented Trust Features
| Feature | Implementation |
|---------|---------------|
| **AI Disclaimer** | "AI-assisted predictions. Not a final medical diagnosis." — shown on both dashboards |
| **Doctor Verification Badge** | Blue "Verified" badge next to doctor name (only `is_verified=True`) |
| **Doctor Availability** | Green/gray dot showing online/offline status |
| **Doctor Workload** | Current patient load visible to patients |
| **Doctor Specialization** | Always displayed with doctor name |
| **Timestamp with Timezone** | Full localized timestamp |
| **Structured Responses** | Doctor responses have 4 mandatory fields, not free text |
| **Confidence Scores** | AI predictions show % confidence with color coding |
| **Severity System** | Color-coded badges (Green/Yellow/Red) with clinical meaning |
| **M-Pesa Security** | Encrypted transaction indicators, secure payment modal |
| **Payment Receipts** | Professional receipt with transaction ID, M-Pesa receipt number |

### 14.2 Severity Color Coding
| Severity | Color | Meaning | Action |
|----------|-------|---------|--------|
| LOW | Green 🟢 | Mild symptoms | Self-care suggested |
| MEDIUM | Yellow 🟡 | Needs attention | Visit within 24-48 hours |
| HIGH | Red 🔴 | Serious condition | Immediate care required |

Applied to: badges, card border tints, background tints, urgency boxes

---

## 15. Pages & Screens

### 15.1 Login Page (`/login`)
- Gradient background with radial accents
- Centered card with medical cross icon
- Email + Password inputs with focus animations
- "Remember me" checkbox + "Forgot password" link
- Loading spinner on submit
- Auto-redirects by role after login

### 15.2 Register Page (`/register`)
- Centered card layout
- Fields: Full Name, Email, Password, Role (dropdown)
- If Role = Doctor: shows Specialization dropdown (11 options)
- Styled error/success alert boxes
- "Already have an account?" link

### 15.3 Patient Dashboard (`/patient/dashboard`)
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

### 15.4 Doctor Dashboard (`/doctor/dashboard`)
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

### 15.5 Submit Symptoms Page (`/patient/submit-symptoms`)
- Header with description
- Symptom textarea with placeholder
- Common symptom chips (English + Swahili)
- Analyze button with loading spinner
- **Results section:**
  - Primary prediction with confidence circle
  - Top 3 predictions with visual ranking bars
  - Cleaned symptoms understood
  - Urgency guidance
  - AI Clinical Insight panel
  - Recommended diagnostic tests
- **Doctor Selection section (Marketplace):**
  - AI-recommended doctor highlighted
  - Grid of ALL verified doctor cards with avatar, name, specialization, availability dot, workload
  - Click to select (checkmark appears)
  - Selected doctor banner
  - "Consult Doctor" button + "Go to Dashboard" button

### 15.6 Payment Modal
- M-Pesa branded header with Safaricom green
- Amount card showing real price
- Phone number input with validation
- Security indicator (encrypted transaction)
- "Pay" button with M-Pesa branding
- Processing states: STK sent → Waiting → Success/Failed
- Success: Professional receipt with transaction details
- Failure: Retry button + error message

### 15.7 Lab Tests Page (`/patient/lab-tests`)
- Header + description
- Grid of test cards (2 columns on desktop)
- Each card: Test name, description, price badge, "Book" button
- After booking: Payment modal appears
- Loading spinner while fetching
- Empty state if no tests

### 15.8 Medicines Page (`/patient/medicines`)
- Header + description
- Grid of medicine cards (2 columns on desktop)
- Each card: Medicine name, manufacturer, price badge, prescription required badge, stock level, "Order" button
- After ordering: Payment modal appears
- Out-of-stock items: grayed out, disabled button
- Loading spinner while fetching

### 15.9 Appointments Page (`/patient/appointments`)
- Header + description
- Doctor selection dropdown
- Date picker
- Available time slots grid
- Book button
- After booking: Payment modal appears
- List of existing appointments with status badges

### 15.10 Admin Dashboard (`/admin/dashboard`)
- **Analytics cards:** Total Users, Doctors, Patients, Revenue, Consultations, Appointments
- **Doctor Management table:** Verify/unverify, toggle availability
- **Consultation Overview:** All consultations with priority badges
- **Payment Analytics:** Revenue breakdown, completed/failed/pending counts, method breakdown
- **Review Analytics:** Average rating, top doctors, recent reviews

---

## 16. Known Limitations & Suggestions

### 16.1 Current Limitations

| # | Limitation | Impact |
|---|-----------|--------|
| 1 | ~~No admin dashboard~~ | ✅ Implemented |
| 2 | ~~No doctor availability status toggle~~ | ✅ Implemented |
| 3 | ~~No appointment scheduling~~ | ✅ Implemented |
| 4 | ~~No payment integration~~ | ✅ Implemented — M-Pesa STK Push |
| 5 | ~~No push notifications~~ | ✅ Implemented — toast notification system |
| 6 | ~~No file uploads~~ | ✅ Implemented |
| 7 | ~~No doctor ratings/reviews~~ | ✅ Implemented |
| 8 | **JWT key is short (28 bytes)** | Security warning — should be 32+ bytes |
| 9 | **No email/SMS notifications** | No external notification system |
| 10 | **SQLite for production** | Won't scale beyond a few concurrent users |
| 11 | **M-Pesa sandbox only** | Real payments require production credentials |
| 12 | **ngrok required for callbacks** | Callbacks need public URL |

### 16.2 Future Enhancements

#### Suggestion 1: Production M-Pesa
- Upgrade from sandbox to production Daraja API
- Apply for Paybill/Till number
- Remove `DEMO_PAYMENT_MODE` flag
- Charge actual prices

#### Suggestion 2: WebSocket-Based Real-Time
- Replace polling with Socket.IO
- Instant chat messages
- Push notifications for new consultations
- Doctor "typing" indicators

#### Suggestion 3: Video Consultations
- Integrate WebRTC for video calls
- Scheduled video appointments
- Screen sharing for lab results

#### Suggestion 4: Mobile App
- React Native or Flutter app
- Push notifications
- Offline symptom checker

#### Suggestion 5: Multi-Language Support
- Full Swahili UI
- Voice input for symptoms
- Localized medical terminology

---

## 17. Testing Results

### 17.1 Backend Tests (Manual)
| Test | Result |
|------|--------|
| App loads without errors | ✅ PASS |
| All database tables exist | ✅ PASS |
| Seed doctors created | ✅ PASS |
| Lab tests seeded | ✅ PASS |
| Medicines seeded | ✅ PASS |
| Symptom normalization works | ✅ PASS |
| AI insight generation works | ✅ PASS |
| Doctor assignment by specialization | ✅ PASS |
| Load balancing (least busy doctor) | ✅ PASS |
| Priority assignment | ✅ PASS |
| Consultation creation | ✅ PASS |
| Structured doctor response | ✅ PASS |
| Two-way followup messages | ✅ PASS |
| History timeline generation | ✅ PASS |
| Doctor stats calculation | ✅ PASS |
| File upload endpoints | ✅ PASS |
| M-Pesa STK Push initiation | ✅ PASS |
| M-Pesa callback handling | ✅ PASS |
| Payment status polling | ✅ PASS |
| Appointment booking | ✅ PASS |
| Review creation | ✅ PASS |

### 17.2 ML Model Tests
| Test | Result |
|------|--------|
| Tropical model training | ✅ PASS (99.78% accuracy) |
| Generic model loading | ✅ PASS (97.6% accuracy) |
| Clinical engine predictions | ✅ PASS |
| ML fallback activation | ✅ PASS |
| Dynamic blending | ✅ PASS |
| Swahili symptom handling | ✅ PASS |
| Red flag detection | ✅ PASS |
| Confidence calibration | ✅ PASS |

### 17.3 Frontend Tests (Build)
| Test | Result |
|------|--------|
| Production build succeeds | ✅ PASS |
| No compilation errors | ✅ PASS |
| CSS bundle optimized | ✅ PASS |
| JS bundle optimized | ✅ PASS |
| Toast notification system | ✅ PASS |
| Skeleton loaders | ✅ PASS |
| Empty state components | ✅ PASS |
| Payment modal UI | ✅ PASS |
| Mobile responsive | ✅ PASS |

### 17.4 Integration Tests (End-to-End)
| Test | Result |
|------|--------|
| Patient registers → logs in → submits symptoms → gets predictions | ✅ PASS |
| Patient sees doctor marketplace | ✅ PASS |
| Patient selects doctor → creates consultation | ✅ PASS |
| Doctor logs in → sees consultation in queue | ✅ PASS |
| Doctor submits structured response | ✅ PASS |
| Patient sees response in dashboard | ✅ PASS |
| Patient sends chat message | ✅ PASS |
| Doctor sees chat message | ✅ PASS |
| Patient books lab test → pays via M-Pesa | ✅ PASS |
| Patient orders medicine → pays via M-Pesa | ✅ PASS |
| Patient books appointment → pays via M-Pesa | ✅ PASS |
| Admin views payment analytics | ✅ PASS |
| Patient leaves doctor review | ✅ PASS |

---

## Appendix A: File Inventory

### New Backend Files (M-Pesa + ML)
| File | Description |
|------|-------------|
| `backend/app/services/mpesa_service.py` | M-Pesa Daraja API integration (STK Push, callback, query) |
| `backend/app/services/payment_service.py` | Payment business logic with demo safety |
| `backend/app/ml/clinical/engine.py` | Hybrid Clinical Prediction Engine |
| `backend/app/ml/generate_tropical_dataset.py` | Synthetic tropical disease dataset generator |
| `backend/app/ml/train_tropical_model.py` | Tropical disease RandomForest trainer |
| `backend/app/ml/artifacts/symptom_model_tropical.joblib` | Trained tropical model (99.78% accuracy) |
| `backend/app/ml/artifacts/valid_symptoms_tropical.json` | 65 canonical symptom names |
| `backend/app/ml/datasets/Training_Tropical.csv` | 1,800 training samples |
| `backend/app/ml/datasets/Testing_Tropical.csv` | 450 test samples |

### New Frontend Files
| File | Description |
|------|-------------|
| `frontend/src/components/PaymentModal.jsx` | M-Pesa payment modal with STK Push flow |
| `frontend/src/services/payment.js` | Payment API service |
| `frontend/src/services/appointment.js` | Appointment API service |
| `frontend/src/services/review.js` | Review API service |
| `frontend/src/pages/AdminDashboard.jsx` | Admin analytics dashboard |
| `frontend/src/pages/AppointmentsPage.jsx` | Appointment booking page |

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
