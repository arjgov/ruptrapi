# API Change Impact Analyzer (Internal Developer Tool)

## 1. One‑Line Summary
A backend developer tool that analyzes changes between versions of API contracts (OpenAPI specs), detects breaking changes, maps impacted consumers, and generates actionable impact reports before deployment.

---

## 2. Problem Statement (Why This Exists)
In microservice-based systems, APIs evolve frequently. Teams often lack visibility into which downstream services will break when an API contract changes. This leads to production incidents, delayed releases, and manual coordination overhead.

This project solves that by providing an automated way to:
- Compare API versions
- Identify breaking vs non-breaking changes
- Determine which consumers are affected
- Surface risk *before* deployment

This tool is **developer-facing**, not customer-facing, and is designed to be used locally, in CI pipelines, or as an internal platform service.

---

## 3. Target Users
- Backend engineers working with microservices
- Platform / infra engineers
- Teams maintaining shared APIs

---

## 4. Core Concepts

### 4.1 API Specification
- OpenAPI (Swagger) YAML or JSON
- Versioned and immutable once stored

### 4.2 Consumer
- A simulated downstream service that depends on specific API endpoints
- Defined via configuration (not real production services)

### 4.3 Change
- A difference detected between two API versions

### 4.4 Impact
- The effect of a change on one or more consumers

---

## 5. Core Features (MUST HAVE)

### 5.1 API Spec Ingestion
**Description**:
- Accept OpenAPI specs (YAML / JSON)
- Validate schema correctness
- Store versions immutably

**Key Behaviors**:
- Upload spec via REST API
- Assign version identifiers (e.g., v1, v2)
- Reject invalid OpenAPI files

---

### 5.2 Change Detection Engine (Core Logic)
**Purpose**: Identify differences between two API versions

**Breaking Changes (High Severity)**:
- Endpoint removed
- HTTP method removed
- Required request field removed
- Response field removed
- Field type changed
- Enum value removed

**Non‑Breaking Changes (Lower Severity)**:
- New endpoint added
- Optional field added
- New enum value added

**Output**:
- Structured JSON diff
- Categorized by severity (HIGH / MEDIUM / LOW)

---

### 5.3 Consumer Mapping
**Description**:
- Maintain a mapping of consumers to API endpoints they depend on

**Example**:
```
frontend-app → GET /orders/{id}
reporting-service → POST /reports
```

**Notes**:
- Consumers are simulated (no real company data)
- Stored as config or DB records

---

### 5.4 Impact Analysis Engine
**Purpose**:
- Combine detected changes with consumer mappings

**Responsibilities**:
- Identify which consumers are affected
- Assign risk level per consumer

**Example Output**:
```
Change: Response field 'status' removed from GET /orders/{id}
Impacted Consumers: frontend-app, analytics-service
Risk: HIGH
```

---

### 5.5 Impact Report Generation
**Formats**:
- JSON (machine‑readable)
- Markdown / plain text (human‑readable)

**Use Cases**:
- Manual review
- CI/CD checks
- Documentation

---

## 6. Optional / Phase‑2 Features (NICE TO HAVE)

### 6.1 Risk Scoring
- Compute overall API change risk based on:
  - Number of breaking changes
  - Number of impacted consumers
  - Severity of changes

### 6.2 Version History & Timeline
- Track historical API changes
- Show when breaking changes were introduced

### 6.3 CI/CD Integration (Simulated)
- Single endpoint that can be called from pipelines
- Fails build on HIGH risk changes

---

## 7. What This Project Intentionally Does NOT Include
- Authentication / authorization
- User accounts
- UI-heavy dashboards
- Kubernetes or complex infra
- Real Confluence / GitHub integrations

This is intentional to keep the project focused and credible.

---

## 8. Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Pydantic

### Parsing & Validation
- OpenAPI parsing libraries or custom parser
- YAML / JSON handling

### Storage
- PostgreSQL (preferred) or SQLite
- Stores:
  - API specs
  - Versions
  - Consumer mappings
  - Analysis results

### Business Logic
- Pure Python diff engine
- Clear separation between:
  - Parsing
  - Diffing
  - Impact analysis

### Testing
- Pytest
- Focus on correctness of diff detection

### Packaging (Optional)
- Docker (simple, single container)

---

## 9. High‑Level Architecture

- REST API Layer (FastAPI)
- Spec Ingestion Module
- Diff Engine
- Impact Analysis Module
- Reporting Module
- Persistence Layer

All components are modular and independently testable.

---

## 10. System Design Talking Points (Interview‑Ready)

- Definition of breaking vs non‑breaking changes
- Schema evolution strategies
- False positives vs false negatives
- Performance of diff computation
- Versioning and immutability
- Extensibility to GraphQL / Async APIs
- CI/CD integration patterns

---

## 11. Resume‑Ready Description (Final Form)

"Designed and built an internal developer tool to analyze API contract changes, detect breaking changes, and identify impacted consumers in microservice‑based systems using Python and FastAPI."

---

## 12. Build Plan (Realistic)

**Week 1**
- Spec ingestion
- Version storage
- Basic diff detection

**Week 2**
- Breaking change rules
- Consumer mapping
- Impact analysis

**Week 3 (Optional)**
- Reporting polish
- Tests
- Documentation

---

## 13. Core Design Principle

> Build something a real engineering team would trust, not a demo that looks impressive.

