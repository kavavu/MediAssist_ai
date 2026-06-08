# MediAssist AI — Project Summary for Final Submission

**Student Name:** Ryan Kavavu  
**Project Title:** MediAssist AI — An AI-Assisted Healthcare Platform with M-Pesa Integration  
**Submission Date:** 27 May 2026  

---

## 1. Project Title & Tagline

**MediAssist AI**  
*"AI-Powered Healthcare for Everyone, Everywhere"*

---

## 2. Problem Statement

In Kenya and many developing countries, accessing quality healthcare is a significant challenge:

- **Long wait times** at hospitals and clinics (often 4-8 hours)
- **Shortage of doctors** — Kenya has only 1 doctor per 16,000 people (WHO recommends 1:1,000)
- **High cost** of consultations, lab tests, and medicines
- **Limited access** in rural areas — patients travel long distances
- **No early triage** — patients with mild symptoms crowd hospitals
- **Cash-only payments** — no digital payment integration for healthcare
- **Language barriers** — medical systems only in English, excluding Swahili speakers

**MediAssist AI solves these problems** by providing an AI-powered symptom checker, connecting patients with verified doctors online, enabling digital M-Pesa payments, and supporting both English and Swahili.

---

## 3. Project Objectives

### Primary Objectives
1. **Build an AI symptom checker** that predicts diseases from natural language symptoms with high accuracy
2. **Connect patients with doctors** through a digital platform with load balancing
3. **Enable M-Pesa payments** for consultations, lab tests, medicines, and appointments
4. **Support Swahili** symptom input for Kenyan patients
5. **Provide structured medical responses** from doctors with AI assistance

### Secondary Objectives
6. Implement real-time two-way chat between patients and doctors
7. Build an admin dashboard for platform analytics and doctor management
8. Add appointment scheduling with time slots
9. Enable file uploads for medical documents and images
10. Implement doctor verification and review system

---

## 4. Key Features Implemented

### 4.1 AI Symptom Checker (Hybrid Engine)
- **Rule-based weighted scoring** for 15 tropical diseases (Malaria, Typhoid, Dengue, etc.)
- **Machine Learning fallback** — RandomForest trained on 1,800 synthetic cases (99.78% accuracy)
- **Dynamic blending** — ML contributes more when clinical engine is uncertain
- **Swahili support** — 20+ Swahili symptom aliases ("homa kali", "tumbo kuumwa")
- **Red flag detection** — Emergency symptoms trigger urgent warnings
- **Top-3 predictions** with confidence scores and match quality

### 4.2 Doctor Marketplace
- **Verified doctor profiles** with specialization, availability, workload
- **AI-recommended doctor** based on predicted condition
- **Patient override** — patient can choose any verified doctor
- **Load balancing** — system assigns to least busy matching doctor
- **Priority system** — HIGH/MEDIUM/LOW based on symptom severity

### 4.3 M-Pesa Payment Integration
- **Safaricom Daraja API** — real STK Push to patient's phone
- **Demo safety mode** — always charges KSh 1 regardless of displayed price
- **Phone normalization** — handles 07XX, 254XXX, +254XXX formats
- **Callback handling** — verifies and updates transaction records
- **Status polling** — frontend checks every 5 seconds
- **Professional receipts** — transaction ID, M-Pesa receipt, timestamp
- **Admin revenue analytics** — using displayed amounts for realistic reporting

### 4.4 Real-Time Chat
- **Two-way messaging** between patients and doctors
- **Auto-refresh** every 5 seconds
- **Message bubbles** with role-based styling
- **Security validation** — only consultation participants can chat

### 4.5 Appointment Scheduling
- **Time slot generation** — 09:00 AM to 03:00 PM
- **Conflict detection** — prevents double-booking
- **Payment integration** — pay after booking
- **Status tracking** — scheduled / completed / cancelled

### 4.6 Admin Dashboard
- **Platform analytics** — users, doctors, patients, revenue, consultations
- **Doctor management** — verify/unverify, toggle availability
- **Payment analytics** — completed/failed/pending, revenue breakdown
- **Review analytics** — average ratings, top doctors

---

## 5. Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Flask (Python 3.13) | Web server |
| Database | SQLite + SQLAlchemy | Data persistence |
| Authentication | JWT (flask-jwt-extended) | Secure login |
| ML Model | scikit-learn RandomForest | Disease prediction |
| Payment API | Safaricom Daraja M-Pesa API | Mobile payments |
| File Uploads | Flask (multipart) | Medical documents |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18 + Vite | UI library |
| Styling | Tailwind CSS v4 | Styling |
| Icons | Lucide React | Icon system |
| HTTP Client | Axios | API calls |
| Build Tool | Vite | Bundling |

### DevOps & Tools
| Component | Technology | Purpose |
|-----------|------------|---------|
| Tunnel | ngrok | Public callback URL |
| Version Control | Git | Source control |
| Package Manager | npm (frontend), pip (backend) | Dependencies |

---

## 6. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React 18 + Tailwind CSS + Vite                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Patient │ │ Doctor  │ │  Admin  │ │ Payment │          │
│  │ Dashboard│ │Dashboard│ │Dashboard│ │  Modal  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP /api
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  Flask + SQLAlchemy + JWT                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  Auth   │ │Symptom  │ │Consult. │ │ Payment │          │
│  │ Routes  │ │ Routes  │ │ Routes  │ │ Routes  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Clinical │ │   ML    │ │ M-Pesa  │ │  Admin  │          │
│  │ Engine  │ │Fallback │ │ Service │ │ Service │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌─────────┐  ┌─────────┐  ┌─────────┐
      │ SQLite  │  │Safaricom│  │  ngrok  │
      │   DB    │  │ Daraja  │  │ (tunnel)│
      └─────────┘  └─────────┘  └─────────┘
```

---

## 7. AI/ML System Details

### 7.1 Hybrid Prediction Engine

**Primary: Rule-Based Clinical Scoring**
- 15 tropical diseases with weighted symptoms (1-5 scale)
- Symptom normalization with 200+ aliases (English + Swahili)
- Implicit symptom mappings (e.g., "vomiting" implies "nausea")
- Core symptom bonuses (+10% if >50% core matched, +15% if all core matched)
- Confidence calibration with penalties for few symptoms, missing core symptoms

**Fallback: RandomForest ML Model**
- Trained on 1,800 synthetic cases for 15 diseases
- 65 canonical symptoms as binary features
- 99.78% test accuracy
- Activates when clinical confidence < 0.50

**Dynamic Blending**
| Clinical Confidence | Clinical Weight | ML Weight |
|---------------------|-----------------|-----------|
| < 0.10 | 40% | 60% |
| < 0.20 | 60% | 40% |
| < 0.35 | 75% | 25% |
| ≥ 0.35 | 85% | 15% |

### 7.2 Example Predictions

| Input | Top Prediction | Confidence | Match Quality |
|-------|---------------|------------|---------------|
| "fever, chills, sweating, headache, body ache" | Malaria | 92% | High |
| "high fever, abdominal pain, headache, loss of appetite" | Typhoid | 91% | High |
| "high fever, severe headache, pain behind eyes, muscle pain, rash" | Dengue | 92% | High |
| "weakness, dizziness, fatigue" | Gastroenteritis | 21% | Low |
| "burning urination, frequent urination, pelvic pain" | UTI | 58% | Moderate |

---

## 8. M-Pesa Payment Integration

### 8.1 Payment Flow
```
1. Patient clicks "Pay" on medicine/lab/appointment
2. Payment modal opens with M-Pesa branding
3. Patient enters phone number (auto-normalized)
4. Backend creates payment record (amount = KSh 1 in demo)
5. Backend initiates STK Push via Safaricom Daraja API
6. Patient receives M-Pesa popup on phone
7. Patient enters PIN (0000 in sandbox)
8. Safaricom sends callback to backend
9. Backend updates payment status to "success"
10. Frontend polls status and shows receipt
```

### 8.2 Demo Safety
- **Displayed price:** Real price (e.g., KSh 1200 for medicine)
- **Actual charge:** Always KSh 1 (safe for demos)
- **Database:** Stores both `amount` (1.00) and `displayed_amount` (1200.00)
- **Analytics:** Uses `displayed_amount` for realistic revenue reporting

### 8.3 Environment Variables
```
MPESA_CONSUMER_KEY=zw3l8Y7e4zvLkmPbyMzKeqfxcTiwsvKN
MPESA_CONSUMER_SECRET=mDbREBlZZcB1KO98
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=https://kinship-childish-maximize.ngrok-free.dev/api/payments/mpesa/callback
MPESA_ENV=sandbox
DEMO_PAYMENT_MODE=true
MPESA_DEFAULT_PHONE=254795058994
```

---

## 9. Database Schema

### Core Tables
- **users** — patients, doctors, admins (with verification, availability, load)
- **consultations** — symptom submissions, AI predictions, doctor responses
- **followups** — chat messages between patients and doctors
- **payments** — M-Pesa transactions with status tracking
- **appointments** — scheduled doctor appointments
- **orders** — lab test and medicine orders
- **reviews** — patient ratings and comments for doctors
- **lab_tests** — catalog of available lab tests
- **medicines** — catalog of available medicines
- **file_attachments** — uploaded medical documents

---

## 10. Testing Results

### Backend Tests
| Test | Result |
|------|--------|
| App loads without errors | ✅ PASS |
| All database tables exist | ✅ PASS |
| Seed data created | ✅ PASS |
| Symptom normalization | ✅ PASS |
| AI predictions (clinical engine) | ✅ PASS |
| ML fallback activation | ✅ PASS |
| Doctor assignment + load balancing | ✅ PASS |
| Priority assignment | ✅ PASS |
| Two-way chat | ✅ PASS |
| M-Pesa STK Push | ✅ PASS |
| Payment callback handling | ✅ PASS |
| Appointment booking | ✅ PASS |
| File uploads | ✅ PASS |

### ML Model Tests
| Test | Result |
|------|--------|
| Tropical model accuracy | ✅ 99.78% |
| Generic model accuracy | ✅ 97.6% |
| Swahili symptom handling | ✅ PASS |
| Red flag detection | ✅ PASS |
| Dynamic blending | ✅ PASS |

### Frontend Tests
| Test | Result |
|------|--------|
| Production build | ✅ PASS |
| Payment modal UI | ✅ PASS |
| Mobile responsive | ✅ PASS |
| Toast notifications | ✅ PASS |

---

## 11. Challenges Faced & Solutions

### Challenge 1: ML Model Disease Mismatch
**Problem:** The original ML model was trained on 41 generic diseases, but the clinical engine only knew 15 tropical diseases. The ML fallback couldn't contribute meaningful predictions.

**Solution:** Generated a synthetic dataset of 1,800 cases for exactly 15 tropical diseases, retrained the RandomForest, and implemented dynamic blending weights.

### Challenge 2: M-Pesa Callback URL
**Problem:** Safaricom needs a public HTTPS URL to send callbacks, but the backend runs on localhost.

**Solution:** Used ngrok to create a public tunnel (`https://kinship-childish-maximize.ngrok-free.dev`) that forwards to `localhost:5000`.

### Challenge 3: Demo Safety
**Problem:** During live demos, we can't charge real prices (KSh 1200) to lecturer phones.

**Solution:** Implemented `DEMO_PAYMENT_MODE` flag that always sends KSh 1 to Safaricom while displaying real prices in the UI. Stored both `amount` and `displayed_amount` in the database.

### Challenge 4: Phone Number Formats
**Problem:** Users enter phone numbers in various formats (0712..., 254712..., +254712...).

**Solution:** Automatic normalization function that converts all formats to `254XXXXXXXXX` before STK Push.

### Challenge 5: Swahili Symptom Input
**Problem:** Many Kenyan patients describe symptoms in Swahili.

**Solution:** Added 20+ Swahili symptom aliases to the normalization engine ("homa kali" → "high fever", "tumbo kuumwa" → "abdominal pain").

---

## 12. Future Enhancements

1. **Production M-Pesa** — Upgrade from sandbox to production with real Paybill
2. **WebSocket Chat** — Replace polling with Socket.IO for instant messaging
3. **Video Consultations** — Integrate WebRTC for video appointments
4. **Mobile App** — Build React Native app for Android/iOS
5. **Full Swahili UI** — Translate entire interface to Swahili
6. **PostgreSQL** — Replace SQLite for production scalability
7. **Push Notifications** — Add Firebase Cloud Messaging
8. **Insurance Integration** — Connect with NHIF and private insurers

---

## 13. Conclusion

MediAssist AI demonstrates a complete healthcare platform that:

- ✅ **Predicts diseases** from natural language symptoms using a hybrid AI engine
- ✅ **Connects patients with doctors** through a digital marketplace with load balancing
- ✅ **Enables M-Pesa payments** for all services with demo-safe KSh 1 charging
- ✅ **Supports Swahili** symptom input for Kenyan patients
- ✅ **Provides structured medical responses** with AI assistance
- ✅ **Includes real-time chat**, appointment scheduling, file uploads, and admin analytics

The project successfully combines **machine learning**, **mobile payments**, **real-time communication**, and **healthcare workflows** into a single integrated platform suitable for the Kenyan market.

---

## 14. References

1. Safaricom Daraja API Documentation — https://developer.safaricom.co.ke/
2. scikit-learn RandomForest Classifier — https://scikit-learn.org/
3. Flask Web Framework — https://flask.palletsprojects.com/
4. React Documentation — https://react.dev/
5. Tailwind CSS — https://tailwindcss.com/
6. World Health Organization — Doctor-to-Patient Ratio Guidelines
7. Kenya Ministry of Health — Digital Health Strategy 2023-2027

---

*Submitted by: Ryan Kavavu*  
*Date: 27 May 2026*
