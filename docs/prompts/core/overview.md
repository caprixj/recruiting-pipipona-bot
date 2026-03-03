# TelegramRecruitingBot_v1 (MVP)

**Description:** An asynchronous Telegram bot designed to automate candidate screening via the Adizes Management Style (PAEI) test. It handles candidate profiling, ranking-based surveys, and immediate scoring, serving as a modular "Survey Engine" for recruitment.

### Tech Stack

* **Core:** Python 3.12, **Poetry** (Dependency Management), **Docker** (Containerization).
* **Bot Framework:** **Aiogram 3.x** (Async, Type-safe).
* **Database:**
* **PostgreSQL:** Primary storage using **JSONB** for flexible survey answers.
* **Redis:** Configured for infrastructure/caching (currently using `MemoryStorage` for FSM in MVP).


* **ORM:** **SQLAlchemy 2.0** (Async, Declarative) + **Alembic** (Migrations).
* **Configuration:** **pydantic-settings** (Type-safe `.env` parsing).
* **Quality Control:** **Ruff** (Linting/Imports), **Black** (Formatting), **Mypy** (Strict Static Typing).

### Architecture & Folder Structure

* **Root:** `src/` (Source Root).
* **Pattern:** **Service-Repository** with **Strategy Pattern** for survey logic.

**Directory Tree:**

* `data/`: **Configuration & Content**.
* `locales/`: YAML translation files (e.g., `ru/ui.yaml`, `ru/surveys/`).
* `surveys/`: YAML logic mapping (e.g., `adizes_v1.yaml`).


* `src/configs`: **Configuration**.
* `env_settings.py`: Pydantic settings loading `.env`.
* `logging.py`: Log formatters.


* `src/core`: **Kernel**.
* `exceptions.py`: Custom domain exceptions (e.g., `SurveySessionNotFoundError`).
* `interfaces/`: Abstract Base Classes (e.g., `ISurveyStrategy`).


* `src/models`: **Entities**.
* Pure SQLAlchemy declarative models (`Employee`, `SurveySession`).
* *Rule:* No business logic here, only schema definitions.


* `src/database`: **Infrastructure**.
* `session_manager.py`: Postgres engine & session factory.
* `redis_manager.py`: Redis connection factory.


* `src/repositories`: **Data Access Layer**.
* CRUD operations (`EmployeeRepository`, `SurveyRepository`).
* *Rule:* Returns Domain Models, not raw cursors.


* `src/strategies`: **Survey Logic**.
* `adizes.py`: Implementation of the Adizes PAEI logic.


* `src/services`: **Business Logic**.
* `survey_service.py`: Orchestrator for session flow (Start, Next, Finish).
* `employee_service.py`: Candidate management.
* `i18n_service.py`: Localization logic.


* `src/bot`: **Presentation Layer** (The UI).
* `handlers/`: Aiogram Routers (`onboarding`, `testing`).
* `keyboards/`: Generators for Ranking Keyboards.
* `middlewares/`: I18n middleware.
* `utils/decorators.py`: **UI Integrity** (Message ID Locking).



### Design Standards

1. **Error Handling:**
* **Forbidden:** Returning `False` or `None` to signal failure.
* **Required:** Raise custom exceptions defined in `src/core/exceptions.py`.
* *Example:* If a session is active, raise `SurveySessionError`. The Bot Layer catches this and provides a localized error message.


2. **Dependency Injection:**
* **Services:** Receive Repositories via manual constructor injection or strictly typed dependency injection.
* **Handlers:** Receive Services via Aiogram's DI mechanism.


3. **Data Strategy:**
* **Logic:** Encapsulated in Strategy classes (`src/strategies/adizes.py`).
* **Structure:** Defined in YAML (`data/surveys/adizes_v1.yaml`).
* **Persistence:** `JSONB` for survey answers to allow flexible schema evolution.


4. **UI Integrity (New):**
* **Message Locking:** Handlers modifying survey state must use `@require_message_lock` to prevent "Time Travel" bugs (interacting with old messages).
* **Ghost Busting:** Strict FSM state management to detect and handle abandoned sessions/collisions.