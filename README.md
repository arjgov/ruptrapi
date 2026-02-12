# RuptrAPI - Dependency Intelligence for Modern Teams

**Stop Breaking Your Consumers. Know Before You Deploy.**

RuptrAPI is the single source of truth for your API dependencies. It automatically detects breaking changes in your OpenAPI specifications and instantly identifies which consumers (frontend apps, microservices, partners) will be impacted.

Designed for fast-moving startups and engineering teams where "move fast and break things" shouldn't mean breaking production.

---

## 🚀 Why Ruptr?

In modern microservices architectures, it's hard to know who consumes your API and how.
- **Frontend Developer:** "Why did the API stop working? The field `userId` is missing!"
- **Backend Developer:** "I deprecated that field last week, didn't you check the changelog?"
- **Product Manager:** "Why is the mobile app crashing in production?"

**RuptrAPI solves this by:**
1.  **Centralizing API Specs:** Upload your OpenAPI/Swagger files (v2, v3).
2.  **Automated diffing:** Detects breaking changes (e.g., field removals, type changes) and non-breaking improvements.
3.  **Dependency Mapping:** Know exactly which service consumes which endpoint.
4.  **Impact Analysis:** When a breaking change is detected, RuptrAPI tells you *exactly* who is affected.

## ✨ Key Features

-   **Smart Diff Engine:** Understands OpenAPI semantics (not just text diffs). Detects:
    -   Parameter removals/changes.
    -   Response schema modifications.
    -   Type changes (e.g., `string` -> `integer`).
-   **Impact Graph:** Maps Services (`Provider`) to Consumers (`Client`).
-   **Risk Scoring:** Categorizes changes by Severity (HIGH, MEDIUM, LOW) and Risk (BREAKING, NON-BREAKING).
-   **Team Collaboration:** Organized by Organizations and Services.

---

## 🛠 Tech Stack

-   **Backend:** Python 3.12+, FastAPI, SQLAlchemy (Async), Pydantic.
-   **Database:** PostgreSQL.
-   **Migrations:** Alembic.
-   **Analysis:** Custom Diff Engine with semantic understanding of OpenAPI.

---

## ⚡️ Getting Started

### Prerequisites

-   Python 3.12+
-   PostgreSQL
-   (Optional) Conda/Virtualenv

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/ruptrapi.git
cd ruptrapi/backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in `backend/` or set environment variables:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/ruptrapi
SECRET_KEY=your_secret_key
```

### 3. Database Migration

```bash
alembic upgrade head
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

Server will start at `http://localhost:8000`.
API Docs available at `http://localhost:8000/docs`.

---

## 📖 Usage Workflow

1.  **Create Organization:** Setup your team workspace.
2.  **Register Services:** Define your APIs (e.g., `Payment Service`).
3.  **Register Consumers:** Define who calls your APIs (e.g., `Web Frontend`, `Mobile App`).
4.  **Map Dependencies:** Tell RuptrAPI what endpoints consumers use.
    -   *Example:* `Web Frontend` uses `GET /users/{id}`.
5.  **Upload Specs:** Push your `openapi.yaml` (v1).
6.  **Evolve:**
    -   Make changes to your API.
    -   Upload new spec (v2).
    -   **Trigger Analysis:** RuptrAPI computes the diff and generates an **Impact Report**.

---

## 🔮 Future Roadmap

-   **Frontend Dashboard:** Visual impact graph (Coming Soon).
-   **CI/CD Integration:** Block PRs if high-risk breaking changes are detected without consumer sign-off.
-   **Notifications:** Slack/Email alerts for impact.
-   **Automatic Dependency Discovery:** Parse consumer codebases to auto-populate dependencies.

---

Built with ❤️ for better Engineering Culture.
