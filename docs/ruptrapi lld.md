# API Change Impact Analyzer – Detailed Data Model (V0)

> Goal: Define **clean, future-proof base models** so V0–V2 development is not blocked by poor schema decisions. This document is intentionally detailed and opinionated.

---

## 0. Core Design Assumptions (LOCK THESE)

1. **Multi-tenancy first (but lightweight)**
   - Every business entity is scoped by `organization_id`
   - Even in V0 (no auth), this prevents future refactors

2. **Relational-first design**
   - PostgreSQL as primary DB
   - Strong foreign keys
   - Explicit relationships

3. **Auth-light V0, auth-ready V1**
   - Users exist in schema
   - Auth logic is optional initially

4. **Immutability where it matters**
   - API specs are immutable
   - Analysis results are append-only

5. **Soft-delete & audit ready (NEW)**
   - All entities support soft deletion via `is_deleted`
   - All entities track `created_by` and `updated_by` (FK → user.id)

---

## 0.1 Cross-Cutting Audit & Deletion Fields (APPLIES TO ALL TABLES)

Every table defined below implicitly includes the following fields unless stated otherwise:

```
is_deleted (BOOLEAN DEFAULT FALSE)
created_by (UUID, FK → user.id)
updated_by (UUID, FK → user.id)
```

Rules:
- **Soft delete only**: rows are never physically deleted in V0+
- `is_deleted = TRUE` rows are excluded by default in queries
- `created_by` is set at insert time
- `updated_by` is set on every update

This avoids future schema rewrites for audit, compliance, or restore workflows.

---

## 1. Base / Cross-Cutting Models

### 1.1 Organization

Represents a tenant.

```
organization
------------
id (UUID, PK)
name (VARCHAR, NOT NULL)
slug (VARCHAR, UNIQUE, NOT NULL)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

Notes:
- `slug` used for URLs / headers later
- One org can have many users, services, consumers

---

### 1.2 User (Minimal, Auth-Ready)

```
user
----
id (UUID, PK)
organization_id (UUID, FK → organization.id)
email (VARCHAR, UNIQUE)
name (VARCHAR)
role (ENUM: ADMIN, MEMBER)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

Notes:
- No password fields in V0
- Can be extended with OAuth later

---

## 2. API Producer Side Models

### 2.1 Service (API Producer)

Represents a service that **owns** APIs.

```
service
-------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
name (VARCHAR, NOT NULL)
description (TEXT)
base_path (VARCHAR)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

Examples:
- order-service
- payment-service

---

### 2.2 API Spec Version

Stores versioned OpenAPI contracts.

```
api_spec_version
----------------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
service_id (UUID, FK → service.id)
version_label (VARCHAR, NOT NULL)
raw_spec (JSONB, NOT NULL)
spec_hash (VARCHAR, NOT NULL)
created_at (TIMESTAMP)
```

Constraints:
- UNIQUE(service_id, spec_hash)

Notes:
- Immutable once stored
- `spec_hash` prevents duplicate uploads

---

## 3. Consumer Side Models

### 3.1 Consumer

Represents a downstream dependency.

```
consumer
--------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
name (VARCHAR, NOT NULL)
description (TEXT)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

Examples:
- frontend-app
- analytics-service

---

### 3.2 Consumer Dependency

Defines which APIs a consumer depends on.

```
consumer_dependency
-------------------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
consumer_id (UUID, FK → consumer.id)
service_id (UUID, FK → service.id)
http_method (VARCHAR, NOT NULL)
path (VARCHAR, NOT NULL)
created_at (TIMESTAMP)
```

Constraints:
- UNIQUE(consumer_id, service_id, http_method, path)

---

## 4. Change & Impact Models (Core Intelligence)

### 4.1 API Change

Represents a detected change between two specs.

```
api_change
----------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
service_id (UUID, FK → service.id)
old_spec_id (UUID, FK → api_spec_version.id)
new_spec_id (UUID, FK → api_spec_version.id)
change_type (ENUM: BREAKING, NON_BREAKING)
severity (ENUM: HIGH, MEDIUM, LOW)
http_method (VARCHAR)
path (VARCHAR)
description (TEXT)
created_at (TIMESTAMP)
```

Notes:
- Derived data (can be recomputed)
- Stored for audit/history

---

### 4.2 Impact

Maps changes to affected consumers.

```
impact
------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
api_change_id (UUID, FK → api_change.id)
consumer_id (UUID, FK → consumer.id)
risk_level (ENUM: HIGH, MEDIUM, LOW)
created_at (TIMESTAMP)
```

---

## 5. Analysis Run (Important for History & CI)

### 5.1 Analysis Run

Represents a single comparison execution.

```
analysis_run
------------
id (UUID, PK)
organization_id (UUID, FK → organization.id)
service_id (UUID, FK → service.id)
old_spec_id (UUID, FK → api_spec_version.id)
new_spec_id (UUID, FK → api_spec_version.id)
status (ENUM: SUCCESS, FAILED)
started_at (TIMESTAMP)
completed_at (TIMESTAMP)
```

Notes:
- Allows CI/CD traceability
- Groups changes + impacts

---

## 6. Relationships Summary (Mental Map)

- organization → users
- organization → services → api_spec_versions
- organization → consumers → consumer_dependencies
- api_spec_versions → api_changes
- api_changes → impacts
- analysis_run → api_changes → impacts

---

## 7. What We Intentionally EXCLUDED in V0

- Hard deletes (soft delete is supported)
- Role-based permissions per entity
- Row-level security policies
- Runtime traffic ingestion
- Full audit trails beyond created/updated by

All can be added **without schema refactor**.

---

## 8. SQLAlchemy Mapping Guidance

- Use UUID primary keys
- Use `relationship()` only where needed
- Avoid bidirectional explosion
- Index:
  - organization_id
  - service_id
  - consumer_id

---

## 9. This Is the "No-Regret" Schema

If you:
- Open-source this
- Add auth
- Add CI integrations
- Add AI summaries

This schema **will not block you**.

---

## 10. Next Correct Steps (Order Matters)

1. Translate this into SQLAlchemy models
2. Add Alembic migrations
3. Define API request/response schemas
4. Implement diff engine

---

> Principle: *Bad schemas kill good ideas. This one won’t.*

