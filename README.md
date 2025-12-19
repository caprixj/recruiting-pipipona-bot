# Telegram Recruiting Bot

A high-performance, asynchronous backend for automating the initial stages of candidate recruitment via Telegram. This phase focuses on the **Adizes Management Style Test** to identify candidate profiles (Producer, Administrator, Entrepreneur, Integrator).

## ℹ️ Purpose

To streamline the candidate screening process by capturing applicant data and evaluating their management style through an interactive, ranking-based assessment.

## ✨ Key Features

* **Automated Onboarding:** Structured collection of candidate name, phone number, and resume links with validation.
* **Interactive Adizes Test:** * Dynamic ranking UI (unique 1-4 assignment).
* Auto-advance logic upon question completion.
* Real-time scoring of **P, A, E, and I** dimensions.


* **Admin Reporting:** Secure `/export` command that generates an `.xlsx` report of all candidates and their test results.
* **Data Integrity:** PostgreSQL as the source of truth for all profiles and survey results using `JSONB` for flexible data storage.
* **Localization:** Built-in I18n support for multiple languages.

## 🛠 Tech Stack

* **Language:** Python 3.12


* **Frameworks:**
* `Aiogram 3` (Bot Logic)
* `FastAPI` (Lifecycle & Web Server)


* **Database & State:**
* `PostgreSQL` (Data & Persistence)
* `SQLAlchemy 2.0` (Async ORM)
* `Redis` (FSM & Caching)


* **Tools:**
* `Alembic` (Migrations)
* `OpenPyXL` (Excel Generation)
* `Pydantic` (Config)
* `Docker` (Containerization)