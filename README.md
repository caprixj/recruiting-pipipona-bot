# Telegram Recruiting Bot (MVP)

An asynchronous recruiting automation tool designed to streamline candidate screening. This system administers the *
*Adizes Management Style (PAEI)** assessment, enforcing strict session integrity and structured data collection via a
modular "Survey Engine" architecture.

## ℹ️ Core Functionality

* **Domain:** Automated candidate screening and PAEI profiling (Producer, Administrator, Entrepreneur, Integrator).
* **Architecture:** Layered Service-Repository pattern with Hexagonal influences, ensuring separation between the UI (
  Aiogram), Business Logic (Services), and Persistence (PostgreSQL).

## ✨ Key Features

### 👤 Candidate Onboarding

* **Structured Profiling:** Guided finite state machine (FSM) flow for collecting Name, Phone (validated), and Resume
  links.
* **Idempotency:** logic ensures `Employee` entities are updated rather than duplicated during re-onboarding.
* **UI Hygiene:** Enforces a single active keyboard state to prevent interface clutter.

### 📊 Adizes Assessment Engine

* **Ranking Logic:** Implements the 1-to-4 strict ranking system (no ties allowed).
* **State Integrity & Concurrency:**
* **Message Locking:** Decorator-based guard prevents race conditions and interactions with outdated UI elements ("
  anti-time travel").
* **Collision Handling:** Detects interrupted or abandoned sessions, offering context-aware options to Resume or
  Restart.
* **Scoring:** Immediate calculation of PAEI classification upon completion.

### 🛡 Admin & Infrastructure

* **Data Export:** `/export` command generates timestamped `.xlsx` reports via OpenPyXL.
* **Schema Flexibility:** Utilizes PostgreSQL `JSONB` for survey answers, allowing survey structures to evolve without
  strict schema migrations.

## 🛠 Tech Stack

* **Runtime:** Python 3.12
* **Framework:** Aiogram 3.x (Async)
* **Persistence:**
* **Database:** PostgreSQL (Asyncpg)
* **ORM:** SQLAlchemy 2.0 (Declarative) + Alembic
* **State Storage:** MemoryStorage (MVP configuration)
* **Distribution:** Docker / Docker Compose