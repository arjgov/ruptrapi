# API Change Impact Analyzer – Low Level Design (LLD)

> Goal: Design the system once in a clean, extensible way so the MVP is simple, but future features (multi-tenant, CI integration, AI summaries) are not blocked.

---

## 1. Design Principles

1. **Multi-tenancy first (but lightweight)**
   - Every entity is scoped by `organization_id`
   - No auth in MVP, but the data model supports it

2. **Clear separation of concerns**
   - Spec storage ≠ diff logic ≠ impact analysis ≠ reporting

3. **Backend-first, frontend as a thin client**
   - Frontend only calls APIs
   - All logic stays server-side

4. **Extensible, not over-engineered**
   - Single service for MVP
   - Internally modular (can split into services later)

---

## 2. High-Level Architecture

Single backend service (FastAPI) with internal modules:

- API Layer (REST)
- Domain Models
- Spec Management Module
- Change Detection Engine
- Impact Analysis Engine
- Reporting Module
- Persistence Layer

Frontend (Next.js) is optional and talks only to REST APIs.

---

## 3. Core Entities & Data Models

All entities include:
- `id` (UUID)
- `organization_id` (UUID)
- `created_at`
- `updated_at`

### 3.1 Organization

Represents a tenant.

```
Organization
-----------
id
name
slug
created_at
```

Notes:
- In MVP, organization can be created implicitly
- Later used for auth, RBAC, billing

---

### 3.2 Service (API Producer)

Represents a service that exposes APIs.

```
Service
-------
id
organization_id
name
base_url (optional)
description
```

Examples:
- order-service
- payment-service

---

### 3.3 API Spec Version

Stores versioned OpenAPI specs per service.

```
ApiSpecVersion
--------------
id
organization_id
service_id
version_label (v1, v2, 2024-01-15)
raw_spec (JSON)
hash
```

Notes:
- Specs are immutable once stored
- `hash` helps avoid duplicate uploads

---

### 3.4 Consumer

Represents a downstream dependency.

```
Consumer
--------
id
organization_id
name
description
```

Examples:
- frontend-app
- reporting-service

---

### 3.5 Consumer Dependency

Maps consumers to endpoints they use.

```
ConsumerDependency
------------------
id
organization_id
consumer_id
service_id
http_method
path
```

Notes:
- Simple static mapping
- Can be expanded later to support patterns

---

### 3.6 Change

Represents a detected change between API versions.

```
ApiChange
---------
id
organization_id
service_id
old_spec_id
new_spec_id
change_type (BREAKING | NON_BREAKING)
severity (HIGH | MEDIUM | LOW)
http_method
path
description
```

---

### 3.7 Impact

Represents how a change affects consumers.

```
Impact
------
id
organization_id
change_id
consumer_id
risk_level (HIGH | MEDIUM | LOW)
```

---

## 4. Core Services / Modules (Code-Level)

### 4.1 Organization Context

- Inject `organization_id` into every request
- For MVP, can be passed as header or query param

---

### 4.2 Spec Management Service

Responsibilities:
- Validate OpenAPI specs
- Store versions
- Fetch versions for comparison

Functions:
- `upload_spec()`
- `get_spec_versions()`
- `get_spec_by_version()`

---

### 4.3 Change Detection Engine

Pure domain logic.

Responsibilities:
- Compare two OpenAPI specs
- Detect breaking vs non-breaking changes

Design:
- Stateless
- Input: old_spec, new_spec
- Output: list of `ApiChange`

Rules Engine:
- Endpoint removed → BREAKING
- Method removed → BREAKING
- Required field removed → BREAKING
- Field type changed → BREAKING
- Optional field added → NON_BREAKING

---

### 4.4 Impact Analysis Engine

Responsibilities:
- Map changes to consumer dependencies
- Compute risk

Logic:
- For each `ApiChange`, find matching `ConsumerDependency`
- Create `Impact` records

---

### 4.5 Reporting Module

Responsibilities:
- Aggregate changes + impacts
- Generate outputs

Outputs:
- JSON report
- Markdown report (optional)

---

## 5. API Endpoints (MVP)

### Organization
- `POST /organizations`

### Services
- `POST /services`
- `GET /services`

### API Specs
- `POST /services/{service_id}/specs`
- `GET /services/{service_id}/specs`

### Consumers
- `POST /consumers`
- `GET /consumers`

### Consumer Dependencies
- `POST /dependencies`

### Analysis
- `POST /analyze`

Input:
- service_id
- old_version
- new_version

Output:
- changes
- impacted consumers
- risk summary

---

## 6. Frontend Mapping (Optional MVP)

Frontend pages:
- Organization setup (optional)
- Service & spec upload
- Consumer & dependency config
- Analyze & view report

Frontend has **no business logic**.

---

## 7. What This Design Enables Later (Without Refactor)

- Auth & RBAC (organization_id already exists)
- CI/CD integration
- AI-generated summaries
- Webhooks
- Multi-service impact analysis
- GraphQL support

---

## 8. What We Intentionally Avoided

- Microservices split
- Event-driven architecture
- Heavy auth flows
- Distributed databases

Those can be added later if needed.

---

## 9. MVP Implementation Order

1. Data models
2. Spec ingestion
3. Diff engine
4. Impact analysis
5. Analyze endpoint
6. Minimal frontend

---

## 10. Mental Model (Remember This)

> This is a **platform-style backend** with clean domain boundaries.
> MVP is small, but the design is future-proof.

