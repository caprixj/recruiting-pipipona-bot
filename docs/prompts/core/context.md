### Project Context & Business Logic

**1. Motivation & Goal**

* **Problem:** Traditional candidate screening is slow, manual, and inconsistent. Recruiters lack a standardized, automated way to assess a candidate's management style before the first interview.
* **Solution:** An automated Telegram Bot that administers the **Adizes Management Style (PAEI)** test, collects candidate profiles, and provides instant scoring and categorization.
* **Vision:** A modular "Survey Engine" starting with Adizes (MVP) but capable of expanding to Technical Vacancy tests and other assessments in Phase 2.

**2. Functional Scope (MVP)**

* **Form Factor:** Telegram Bot (Aiogram 3.x).
* **Core Feature:** **The Adizes Test (PAEI)**.
* **Mechanic:** 20 Questions with 4 options each.
* **Ranking Logic:** Dynamic UI where users rank options 1-4 (Unique selection enforcement).
* **Scoring Strategy:** Encapsulated logic (Strategy Pattern) calculating P, A, E, I dimensions.
* **Anti-Bias:** Randomized mapping via YAML to prevent Primacy Effect bias.


* **Session Integrity & UI Security:**
* **Anti-Time Travel:** Strict **Message ID Locking** (`@require_message_lock`) prevents users from interacting with old questions ("zombie buttons").
* **Ghost Busting:** Automated detection of abandoned sessions vs. active collisions, forcing users to resolving conflicts ("Resume" vs "Restart").
* **UI Hygiene:** "Invisible Broom" pattern ensures strictly one active keyboard, removing stuck "Share Contact" buttons.


* **User Profile:** Structured data collection: Full Name, Phone Number (Validation), and Resume Link.
* **Data Strategy:**
* **Persistence:** PostgreSQL with `JSONB` columns for survey answers. This allows schema flexibility for future test types without altering table structure.
* **Localization:** Content is strictly separated from logic using YAML-based I18n (RU/EN).



**3. Team & Roles**

* **Anton (Product Owner & Lead Dev):** Requirements definition, core implementation, and business logic validation.
* **Gemini (System Architect):** Architecture enforcement, boilerplate generation, refactoring, and ensuring strict adherence to `standards.md`.

**4. Development Workflow**

* **Git Strategy:** Strict **Git Flow**.
* `main`: Production-ready.
* `dev`: Integration & Task-specific branch.


* **Database Workflow (Dev Phase):**
* **Strategy:** "Squash/Nuke". We prefer re-initializing the schema/volume during early dev to keep migrations clean, though Alembic is configured for production upgrades.


* **Tech Constraints:**
* **Language:** Python 3.12.
* **Tooling:** Poetry (Dependencies), Docker (Containerization).
* **Architecture:** Service-Repository Pattern with **Strategy Pattern** for Survey Logic.