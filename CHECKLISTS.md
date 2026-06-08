# MediAssist AI — Final Validation Checklists

> Use these checklists before your demo, before submitting, and during your defense preparation.

---

## 1. Production Readiness Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | `.env` file has strong SECRET_KEY (32+ random chars) | ☐ |
| 2 | `.env` file has strong JWT_SECRET_KEY (32+ random chars) | ☐ |
| 3 | `APP_ENV=production` is set for production | ☐ |
| 4 | CORS_ORIGINS is set to your frontend domain (not `*`) | ☐ |
| 5 | Database is PostgreSQL (not SQLite) in production | ☐ |
| 6 | File uploads directory is outside web root | ☐ |
| 7 | HTTPS is enabled (not HTTP) | ☐ |
| 8 | Debug mode is OFF | ☐ |
| 9 | Logging is configured and writing to files | ☐ |
| 10 | Database migrations are up to date | ☐ |

---

## 2. Security Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | Role escalation prevented (only "patient" from registration) | ☐ |
| 2 | Password strength enforced (8+ chars, letter + number) | ☐ |
| 3 | Email format validated | ☐ |
| 4 | Input length limits on all text fields | ☐ |
| 5 | JWT tokens expire after 1 hour | ☐ |
| 6 | All protected routes have `@jwt_required()` | ☐ |
| 7 | Role-restricted routes have `@role_required()` | ☐ |
| 8 | File uploads restricted to images and PDFs | ☐ |
| 9 | File size limited to 5MB | ☐ |
| 10 | No stack traces leaked to frontend | ☐ |
| 11 | CORS restricted to known origins | ☐ |
| 12 | M-Pesa callback returns 200 even on errors | ☐ |
| 13 | Payment completion endpoint restricted to admin | ☐ |
| 14 | SQL injection prevented (ORM used everywhere) | ☐ |
| 15 | No hardcoded secrets in code | ☐ |

---

## 3. Testing Checklist

### Backend Tests

| # | Test | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Register with valid data | 201 Created | ☐ |
| 2 | Register with duplicate email | 400 Error | ☐ |
| 3 | Register with weak password | 400 Error | ☐ |
| 4 | Register with invalid email | 400 Error | ☐ |
| 5 | Login with correct credentials | 200 + token | ☐ |
| 6 | Login with wrong password | 401 Unauthorized | ☐ |
| 7 | Access protected route without token | 401 Unauthorized | ☐ |
| 8 | Access doctor route as patient | 403 Forbidden | ☐ |
| 9 | Submit symptoms | Returns predictions | ☐ |
| 10 | Create consultation | 201 + assigned doctor | ☐ |
| 11 | Doctor responds to consultation | 200 + status=responded | ☐ |
| 12 | Send follow-up message | Message saved + socket emitted | ☐ |
| 13 | Book appointment | 201 + slot reserved | ☐ |
| 14 | Cancel appointment | Status=cancelled | ☐ |
| 15 | Create payment | 201 + payment record | ☐ |
| 16 | M-Pesa callback | Payment status updated | ☐ |
| 17 | Upload file | 201 + file metadata | ☐ |
| 18 | Upload invalid file type | 400 Error | ☐ |
| 19 | Upload oversized file | 400 Error | ☐ |
| 20 | Leave review | 201 + review saved | ☐ |
| 21 | Admin views dashboard | Stats returned | ☐ |
| 22 | Admin verifies doctor | Doctor is_verified=true | ☐ |

### Frontend Tests

| # | Test | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Load login page | Form renders | ☐ |
| 2 | Login as patient | Redirect to patient dashboard | ☐ |
| 3 | Login as doctor | Redirect to doctor dashboard | ☐ |
| 4 | Login as admin | Redirect to admin dashboard | ☐ |
| 5 | Submit symptoms | AI results display | ☐ |
| 6 | Create consultation | Success toast, consultation appears | ☐ |
| 7 | Doctor views consultations | List loads | ☐ |
| 8 | Doctor uses AI draft | Fields populated | ☐ |
| 9 | Doctor submits response | Status updates | ☐ |
| 10 | Open chat | Messages load | ☐ |
| 11 | Send chat message | Message appears instantly | ☐ |
| 12 | Book appointment | Calendar shows, booking succeeds | ☐ |
| 13 | Make payment | STK push initiated | ☐ |
| 14 | Upload file | File appears in list | ☐ |
| 15 | View history | Timeline renders | ☐ |
| 16 | Logout | Redirect to login, token cleared | ☐ |
| 17 | Refresh page while logged in | Still logged in | ☐ |
| 18 | Mobile responsive | Layout adapts | ☐ |

---

## 4. Demo Checklist

### Before Demo

| # | Task | Status |
|---|------|--------|
| 1 | Both servers running | ☐ |
| 2 | Test accounts created (patient, doctor, admin) | ☐ |
| 3 | At least one consultation created | ☐ |
| 4 | At least one appointment booked | ☐ |
| 5 | Browser console has no errors | ☐ |
| 6 | Network tab shows 200s (not 500s) | ☐ |
| 7 | Test on the machine you'll present from | ☐ |

### During Demo (Suggested Flow)

| # | Step | Time |
|---|------|------|
| 1 | Introduce the project (30 sec) | |
| 2 | Show patient registration/login (1 min) | |
| 3 | Submit symptoms → show AI prediction (2 min) | |
| 4 | Explain the AI pipeline (1 min) | |
| 5 | Create consultation → doctor assignment (1 min) | |
| 6 | Switch to doctor → view consultation (1 min) | |
| 7 | Use AI draft → submit response (1 min) | |
| 8 | Show real-time chat (1 min) | |
| 9 | Show appointment booking (1 min) | |
| 10 | Show M-Pesa payment flow (1 min) | |
| 11 | Show admin dashboard (1 min) | |
| 12 | Q&A (remaining time) | |

**Total: ~11 minutes + Q&A**

---

## 5. Viva (Defense) Checklist

### Be Ready to Explain

| Topic | Key Points |
|-------|-----------|
| **Why this project?** | Telemedicine gap in Africa, tropical diseases, accessibility |
| **Why Flask?** | Lightweight, Python ecosystem, easy to learn |
| **Why React?** | Component-based, fast, modern, good ecosystem |
| **Why SQLite?** | Simple for students, easy to migrate to PostgreSQL |
| **AI Pipeline** | Rule engine first → ML fallback → blending |
| **RandomForest** | Ensemble of decision trees, voting system, handles missing data |
| **Doctor Matching** | Specialization + availability + load balancing |
| **Real-time Chat** | WebSockets (Socket.IO), room-based, JWT auth |
| **M-Pesa Integration** | Daraja API, STK push, callback handling |
| **Security** | JWT, password hashing, role protection, input validation |
| **Challenges Faced** | Be honest: training data, Swahili normalization, callback testing |
| **Future Improvements** | More diseases, video calls, SMS notifications, mobile app |

### Common Questions & Answers

**Q: "How accurate is your AI?"**
A: "It's a screening tool, not a diagnostic tool. We cap confidence at 92% and always recommend seeing a doctor. The rule engine is based on clinical guidelines for tropical diseases."

**Q: "Did you collect real patient data?"**
A: "No, we used publicly available symptom-disease datasets and clinical literature. For a real deployment, we'd need ethical approval and data privacy compliance."

**Q: "What if the ML model is wrong?"**
A: "The rule engine is the primary predictor. The ML is a fallback when confidence is low. We also show the top 3 predictions, not just one. And we always include a medical disclaimer."

**Q: "How do you handle data privacy?"**
A: "Passwords are hashed with scrypt. JWT tokens expire after 1 hour. API endpoints are protected. File uploads are validated. In production, we'd also encrypt PII at rest."

**Q: "Can this scale?"**
A: "Yes. SQLite can be swapped for PostgreSQL. The app uses SQLAlchemy ORM so the database change is one line. For WebSockets, we'd add Redis for multi-server support."

---

## 6. Performance Checklist

| # | Check | Target | Status |
|---|-------|--------|--------|
| 1 | Page load time | < 3 seconds | ☐ |
| 2 | API response time (most endpoints) | < 500ms | ☐ |
| 3 | AI prediction time | < 2 seconds | ☐ |
| 4 | Chat message delivery | < 500ms | ☐ |
| 5 | Dashboard data load | < 2 seconds | ☐ |
| 6 | File upload (5MB) | < 10 seconds | ☐ |
| 7 | No memory leaks on long sessions | Stable | ☐ |
| 8 | Database queries use indexes | EXPLAIN shows index usage | ☐ |

---

## 7. API Consistency Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | All success responses use `{"success": true, ...}` | ☐ |
| 2 | All error responses use `{"error": "message"}` | ☐ |
| 3 | All protected routes return 401 for missing token | ☐ |
| 4 | All role-restricted routes return 403 for wrong role | ☐ |
| 5 | All 404s return JSON (not HTML) | ☐ |
| 6 | All 500s return generic message (no stack trace) | ☐ |
| 7 | Status codes are consistent (200=OK, 201=Created, 400=Bad Request, etc.) | ☐ |
| 8 | Date fields use ISO 8601 format | ☐ |
| 9 | IDs are integers | ☐ |
| 10 | Booleans are true/false (not strings) | ☐ |

---

## Final Sign-Off

**Before submitting your project, verify:**

- [ ] All checklists above are complete
- [ ] You can demo the full flow without errors
- [ ] You can explain every major component
- [ ] Your code has comments explaining the "why"
- [ ] Your README is updated
- [ ] Your `.env` does NOT contain real secrets (use `.env.example`)
- [ ] You've tested on a clean machine (or virtual environment)
- [ ] You have a backup of your database

**You've got this! 🎓**
