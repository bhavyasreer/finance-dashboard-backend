# 🚀 Finance Backend API

> A clean,secure, role-based backend system designed with real-world fintech principles, enabling secure financial data management and analytics through scalable APIs.

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
* **Database**: SQLite
* **ORM**: SQLAlchemy
* **Validation**: Pydantic
* **Authentication**: JWT (token-based)
* **Security**: Password hashing using bcrypt

---

## 🏗️ Architecture

```
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

```http
POST /auth/login
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs....",
  "token_type": "bearer",
  "message": "Login successful"
}
```

Use token in all protected requests:

```http
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

## 👥 Role-Based Access Control (RBAC)

| Role    | Permissions                   |
| ------- | ----------------------------- |
| Viewer  | Dashboard only                |
| Analyst | Records (read) + Dashboard    |
| Admin   | Full access (users + records) |

---

## 👤 User Management

### Features

* Create users (Admin only)
* Update user roles
* Deactivate users
* List users

---

### 🔍 Search & Filters

```http
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

```http
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

```http
GET /records?search=lunch
```

Search applies to:

* notes only

✔ Keeps behavior clean and predictable

---

## 📊 Dashboard / Analytics (Key Strength)

### APIs

* `/dashboard/summary`
* `/dashboard/category-breakdown`
* `/dashboard/monthly-trends`
* `/dashboard/recent`

---

### Features

* Aggregated financial insights
* Category-based analysis
* Time-based trends
* Recent activity

---

## 🛡️ Security

* Passwords hashed using bcrypt
* No password exposure in API responses
* JWT required for protected endpoints
* Role-based checks enforced

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

## 🌐 Live API & Documentation

* **Live API**: https://finance-dashboard-backend-g30n.onrender.com
* **Swagger Docs**: https://finance-dashboard-backend-g30n.onrender.com/docs

---

## 🧪 How to Test the API

### 1. Open API Documentation

Access the live Swagger UI:

https://finance-dashboard-backend-g30n.onrender.com/docs

This provides an interactive interface to explore and test all API endpoints.
### 2. Authenticate

Use the login endpoint to obtain a JWT token:

```http
POST /auth/login
```

Provide valid credentials for an existing user (e.g., bootstrap admin created at startup).

---

### 3. Authorize

1. Copy the `access_token` from the response
2. Click **Authorize** in Swagger
3. Enter:

```
Bearer <your_token>
```

---

### 4. Test Core Features

#### 👤 User Management (Admin)

* Create users
* Assign roles
* Activate/deactivate users

---

#### 🔄 Role-Based Access

* Login as created user
* Test role restrictions

Examples:

* Analyst → cannot create records (403)
* Viewer → dashboard-only access

---

#### 💰 Records

* Create records (Admin)
* Fetch records using filters & search

---

#### 📊 Dashboard

Test:

* `/dashboard/summary`
* `/dashboard/category-breakdown`
* `/dashboard/monthly-trends`
* `/dashboard/recent`

---

### ⚠️ Expected Behavior

* Invalid login → 401 Unauthorized
* Unauthorized access → 403 Forbidden
* Invalid input → 422 Validation Error
* Not found → 404

---

## ⚖️ Trade-offs & Assumptions

* SQLite used for simplicity
* No public signup (security-first design)
* Simple RBAC over complex permissions
* Search limited to text fields
* Focus on backend design over infrastructure

---

## 🚀 Future Improvements

* Multi-tenant support
* Fine-grained permissions
* Audit logging
* Export reports (CSV/PDF)
* Rate limiting

---

## 🎯 Final Notes

This project demonstrates:

* Strong backend architecture
* Secure authentication and RBAC
* Thoughtful API design
* Real-world fintech system modeling
* APIs optimized for frontend consumption

---

💬 *Built with a focus on clarity, security, and production-level backend practices.*
