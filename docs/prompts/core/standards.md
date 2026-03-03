Here is the refined `standards.md` incorporating your adjustments:

# 🧹 TelegramRecruitingBot: Architecture & Code Standards

## 1. Python, Stack & Syntax Standards

* **Version:** Strictly **Python 3.12**.
* **Dependency Manager:** **Poetry** (with `poetry.lock` committed).
* **Asynchrony:** Strictly **Async/Await**. Blocking I/O is forbidden in Services and Repositories.
* **Type Hinting:**
* *Required:* Strict static typing for all arguments, returns, and class attributes.
* *Tooling:* Code must pass **Mypy** (strict mode).
* *Syntax:* Use modern Union syntax (`int | None`), `ParamSpec`/`TypeVar` for decorators, and `collections.abc` generics (`Sequence`, `Iterable`).


* **Linting & Formatting:**
* **Ruff:** Handles imports (isort) and linting.
* **Black:** Handles formatting.
* *Rule:* CI/CD relies on `ruff check` and `black --check`.



## 2. Naming & File Conventions

* **Consistency:** Align naming across layers.
* *Example:* `Employee` (Model) -> `EmployeeRepository` -> `EmployeeService`.


* **Entity Renaming (Crucial):**
* **Rule:** The user entity is strictly named **`Employee`**.
* *Forbidden:* `User` (to avoid shadowing `aiogram.types.User`).


* **Interface Naming:**
* **Rule:** Abstract Base Classes (Interfaces) must start with **`I`**.
* *Required:* `ISurveyStrategy`, `IRepository`.


* **File Naming (Explicit Suffixes):**
* **Rule:** File names must explicitly state their architectural role. **Generic names are strictly forbidden.**
* *Required:* `employee_service.py`, `session_repository.py`, `adizes_strategy.py`.
* *Forbidden:* `employee.py` (Ambiguous), `repo.py`, `logic.py`, `utils.py`.


* **Data File Naming:**
* **Rule:** Configuration/Survey files must be named comprehensively to distinguish variants.
* *Required:* `adizes_v1.yaml`, `adizes_short_form.yaml`, `vacancy_backend_senior.yaml`.
* *Forbidden:* `adizes.yaml` (Too vague), `test.json`.


* **Classes:**
* **Repositories:** Full words required. `SessionRepository`, `EmployeeRepository`.
* **Services:** `SurveyService`, `I18nService`.
* **Strategies:** `AdizesStrategy`, `VacancyStrategy`.



## 3. Core Architectural Patterns

* **Structure:** **Service-Repository Pattern** with **Strategy Pattern** for survey logic.
* **Root:** `src/` (Source Root).
* **Layers:**
* `src/configs`: Configuration & Constants.
* `src/core`: Interfaces (`ISurveyStrategy`) & Exceptions.
* `src/database`: Infrastructure (Engine, Redis).
* `src/models`: SQLAlchemy Declarative Models.
* `src/repositories`: Data Access Logic (CRUD).
* `src/strategies`: Encapsulated Algorithms (e.g., Scoring, Next-Question Logic).
* `src/services`: Business Logic (Orchestrators).
* `src/bot`: Presentation Layer (Aiogram).


* **Service Layer Responsibility:**
* **Rule:** Orchestrates Repositories and Strategies. Pure business logic.
* **One Service, One File:** `SurveyService` lives in `survey_service.py`.
* *Forbidden:* Standalone "script" functions, loose logic in `__init__.py`.



## 4. UI Integrity & State Management (New)

* **Anti-Time Travel (Message Locking):**
* **Rule:** Any handler that modifies survey state **must** be decorated with `@require_message_lock`.
* **Goal:** Prevent "Zombie Buttons" (interacting with old questions).


* **Ghost Busting:**
* **Rule:** The FSM is the source of truth for *active* interactions. The DB is the source of truth for *history*.
* **Protocol:** On collision (start new test while active), strictly enforce a choice: "Resume" or "Restart".


* **The "Invisible Broom":**
* **Rule:** Never leave a ReplyKeyboard (e.g., Phone Request) stuck on screen. Use ephemeral "cleaning" messages to remove them.



## 5. Data Access (Async SQLAlchemy)

* **Driver:** `asyncpg` (PostgreSQL).
* **Notation:** **SQLAlchemy 2.0+ Declarative** (`Mapped[...]`, `mapped_column`).
* **Repositories:**
* **Dumb Storage:** No business logic. Just `SELECT`, `INSERT`, `UPDATE`.
* **Return Types:** Return Domain Models (`Employee`) or Python scalars.



## 6. Error Handling & Exceptions

* **Exceptions > Flags:**
* *Forbidden:* Returning `False` or `None` to signal failure.
* *Required:* Raise custom exceptions defined in `src/core/exceptions.py`.


* **Example Flow:**
* *Bad:* Service returns `None` on error.
* *Good:* Service raises `SurveySessionNotFoundError`. Bot Layer catches it and displays a localized alert.



## 7. Documentation (The "Junie" Protocol)

* **Standard:** **Google Python Style**.
* **Requirement:** Every Class, Method, and Function must have a docstring.
* **Format:**
* Summary line.
* `Args:` (Name, Type, Description).
* `Attributes:` (For Classes - Name, Type, Description).
* `Returns:` (Type, Description).
* `Raises:` (Exception Type, Condition).



## 8. Git Flow & Version Control

* **Branching:**
* `main`: Production ready.
* `dev`: Development branch.


* **Artifacts:**
* **Always commit:** `poetry.lock`.
* **Never commit:** `.env`, `__pycache__`, `.venv`.