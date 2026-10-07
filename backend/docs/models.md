# Data Model

Generated from the SQLAlchemy models with [paracelsus](https://github.com/tedivm/paracelsus). Regenerate with:

```bash
uv run paracelsus inject docs/models.md app.core.database:Base --import-module "app.models:*"
```

<!-- BEGIN_SQLALCHEMY_DOCS -->
```mermaid
erDiagram
  applications {
    UUID id PK
    UUID project_id FK "indexed"
    VARCHAR(100) branch
    VARCHAR(64) container_id "nullable"
    DATETIME created_at
    TEXT description
    INTEGER desired_replicas
    VARCHAR(255) dockerfile_path
    VARCHAR(255) domain UK "indexed"
    JSON env_vars
    VARCHAR(500) git_url
    VARCHAR(255) image_tag "nullable"
    DATETIME last_deployed_at "nullable"
    VARCHAR(255) name
    INTEGER port
    VARCHAR(100) slug
    ENUM status
    DATETIME updated_at "nullable"
  }

  deployments {
    UUID id PK
    UUID application_id FK "indexed"
    VARCHAR(40) commit_hash "nullable"
    DATETIME completed_at "nullable"
    INTEGER log_size "nullable"
    VARCHAR(255) log_uri "nullable"
    DATETIME started_at
    ENUM status
  }

  organization_members {
    UUID organization_id PK,FK
    INTEGER user_id PK,FK
    DATETIME joined_at
    ENUM role
  }

  organizations {
    UUID id PK
    INTEGER owner_id FK "indexed"
    DATETIME created_at
    VARCHAR(255) name UK "indexed"
    VARCHAR(100) slug UK "indexed"
    DATETIME updated_at "nullable"
  }

  passkeys {
    UUID id PK
    INTEGER user_id FK "indexed"
    DATETIME created_at
    BLOB credential_id UK "indexed"
    DATETIME last_used_at "nullable"
    VARCHAR(255) name
    BLOB public_key
    INTEGER sign_count
    JSON transports
  }

  projects {
    UUID id PK
    UUID organization_id FK "indexed"
    DATETIME created_at
    TEXT description "nullable"
    VARCHAR(255) name
    VARCHAR(100) slug
    ENUM status
    DATETIME updated_at "nullable"
  }

  users {
    INTEGER id PK
    DATETIME created_at
    VARCHAR(255) email UK "indexed"
    VARCHAR(255) full_name
    BOOLEAN is_active
    DATETIME last_login "nullable"
    VARCHAR(128) password
    ENUM role
    DATETIME updated_at "nullable"
    VARCHAR(255) username UK "indexed"
  }

  projects ||--o{ applications : project_id
  applications ||--o{ deployments : application_id
  users ||--o| organization_members : user_id
  organizations ||--o| organization_members : organization_id
  users ||--o{ organizations : owner_id
  users ||--o{ passkeys : user_id
  organizations ||--o{ projects : organization_id

```
<!-- END_SQLALCHEMY_DOCS -->
