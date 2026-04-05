# 🚀 Finance Backend API

> A clean, role-based backend system designed with real-world fintech principles, enabling secure financial data management and analytics through scalable APIs.

---

## 🧠 Overview

This project simulates a **real-world fintech backend system** where users interact with financial data based on their roles.

The system focuses on:

* Secure authentication and access control
* Clean API design and usability
* Analytical insights beyond basic CRUD
* Maintainable and scalable architecture
* Serving structured data efficiently to frontend dashboards

---

## ⚙️ Tech Stack

* **Backend Framework**: FastAPI
* **Language**: Python
* **Database**: SQLite (local); PostgreSQL on Render via `DATABASE_URL` when deployed
* **ORM**: SQLAlchemy
* **Validation**: Pydantic
* **Authentication**: JWT (token-based)
* **Security**: Password hashing using bcrypt

---

## 🏗️ Architecture

```text id="arcg7p"
app/
├── routes/      → API endpoints
├── services/    → business logic
├── models/      → database models
├── schemas/     → request/response validation
├── db/          → database setup
├── core/        → authentication & security
```

✔ Clear separation of concerns
✔ Scalable and maintainable design

---

## 🧠 Design Decisions

* JWT authentication for **stateless and scalable APIs**
* Admin-controlled user creation ensures **data integrity and security**
* RBAC implemented via **dependency-based checks**
* Clean separation between:

  * Search (flexible)
  * Filters (structured)
  * ID-based actions (precise)
* Dashboard APIs designed for **minimal frontend processing**
* Avoided over-engineering to keep system **simple and predictable**

---

## 🔐 Authentication & Authorization

### 🔑 JWT Authentication

```http id="7rqz8g"
POST /auth/login
```

Response:

```json id="y7k0d9"
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "message": "Login successful"
}
```

Use token in all requests:

```http id="eq6kkz"
Authorization: Bearer <token>
```

---

## 🔐 Authentication Flow

1. System starts → bootstrap admin is created (if none exists)
2. Admin logs in
3. Admin creates users
4. Users log in using credentials
5. Backend enforces access using JWT + roles

---

## 🔑 Bootstrap Admin

A default admin is created on startup if none exists.

```env id="x1a1tn"
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=admin123456
```

Ensures system accessibility for initial setup.

---

## 👥 Role-Based Access Control (RBAC)

| Role    | Permissions                   |
| ------- | ----------------------------- |
| Viewer  | Dashboard only                |
| Analyst | Records (read) + Dashboard    |
| Admin   | Full access (users + records) |

---

## 🧠 Access Model

* No public signup
* Users are created by admin only
* Ensures secure and controlled system usage

---

## 🔐 User Onboarding

For simplicity, users are created by the admin with predefined credentials, which are then shared with the respective users for login.

This approach aligns with controlled access models used in internal systems.

In real-world applications, onboarding is typically handled more securely via:

* Invite-based email systems
* Temporary passwords with forced reset
* Secure password setup links

These enhancements were intentionally not implemented to keep the system focused and aligned with assignment scope.

---

## 👤 User Management

### Features

* Create users (Admin only)
* Update user roles
* Deactivate users
* List users

---

### 🔍 Search & Filters

```http id="2p7diz"
GET /users?search=john
```

Search applies to:

* name
* email

Filters:

* role
* is_active

---

### ❗ Design Choice

```http id="s5vf2x"
PATCH /users/{id}
DELETE /users/{id}
```

✔ ID-based operations ensure clarity and prevent ambiguity

---

## 💰 Financial Records System

### CRUD Operations

* Create (Admin)
* Read (Admin, Analyst)
* Update (Admin)
* Soft delete (Admin)

---

### 🔍 Filtering

* category
* type (income/expense)
* date range

---

### 🔎 Search

```http id="3hrj3w"
GET /records?search=lunch
```

Search applies to:

* notes ONLY

---

### ❗ Design Decision

* Category removed from search
* Used strictly as a filter

✔ Keeps behavior clean and predictable

---

## 📊 Dashboard / Analytics (Key Strength 🔥)

### APIs:

* `/dashboard/summary`
* `/dashboard/category-breakdown`
* `/dashboard/monthly-trends`
* `/dashboard/recent`

---

### Features:

* Aggregated financial insights
* Category-based analysis
* Time-based trends
* Recent activity

---

## 📈 Adaptive Trends

* ≤ 31 days → daily aggregation
* > 31 days → monthly aggregation

✔ Provides meaningful and context-aware insights

---

## 🛡️ Security

* Passwords hashed using bcrypt
* No password exposure in API responses
* JWT required for protected endpoints
* Role-based checks enforced across APIs

---

## 📡 API Design

### RESTful Structure

* `/records` → list
* `/records/{id}` → single resource

---

### Clean Separation

| Feature | Purpose               |
| ------- | --------------------- |
| Search  | Flexible querying     |
| Filters | Structured conditions |
| ID      | Updates/deletes       |

---

## 🧪 How to Test

### Step 1: Run Server

```bash id="rd9hqi"
uvicorn app.main:app --reload
```

---

### Step 2: Open Swagger

```id="8y93qf"
http://127.0.0.1:8000/docs
```

---

### Step 3: Login (Admin)

```id="6mg3qg"
email: admin@gmail.com
password: admin123456
```

---

### Step 4: Authorize

Click **Authorize** and paste:

```id="ux24k4"
Bearer <token>
```

---

### Step 5: Test Flow

1. Create user (analyst)
2. Login as analyst
3. Access records and dashboard
4. Try creating record → ❌ 403 Forbidden

---

## 🧾 Example Response

```json id="1px3nx"
{
  "total_income": 100000,
  "total_expense": 50000,
  "net_balance": 50000
}
```

---

## 🧪 Edge Cases Handled

* Invalid login → 401 Unauthorized
* Unauthorized access → 403 Forbidden
* Non-existent resources → 404 Not Found
* Invalid input → structured validation errors
* Empty results → meaningful responses

---

## 🏦 Real-World Relevance

* Admin-controlled access reflects internal financial systems
* RBAC ensures controlled handling of sensitive data
* Soft delete supports audit and recovery scenarios
* Dashboard APIs simulate real analytics systems
* JWT aligns with modern API security practices

---

## ⚡ Performance Considerations

* Aggregations handled at database level
* Pagination limits response size
* Filters reduce unnecessary data processing
* Lightweight DB ensures fast local execution

---

## 🧩 Additional Features

* Pagination
* Filtering
* Search
* Soft delete
* Structured error handling
* Swagger documentation with proper tags

---

## ⚙️ Environment Variables

```env id="6cjlwm"
JWT_SECRET_KEY=your_secret_key
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=admin123456
DATABASE_URL=sqlite:///./finance.db
```

---

## ⚖️ Trade-offs & Assumptions

* SQLite used for simplicity and ease of setup
* No public signup (security-first design)
* Simple RBAC over complex permission systems
* Search limited to text fields for clarity
* Focus on backend design rather than infrastructure

---

## 🚀 Future Improvements

* Multi-tenant architecture
* Fine-grained permissions
* Audit logging
* Export reports (CSV/PDF)
* Rate limiting

---

## 🎯 Final Notes

This project demonstrates:

* Strong backend architecture
* Secure authentication and RBAC
* Thoughtful API design decisions
* Real-world fintech system modeling
* APIs optimized for frontend consumption

---

💬 *Built with a focus on clarity, security, and production-level backend practices.*
