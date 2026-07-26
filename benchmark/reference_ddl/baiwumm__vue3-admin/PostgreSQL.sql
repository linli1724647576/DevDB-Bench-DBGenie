CREATE TABLE "organizations" (
  "id" BIGSERIAL PRIMARY KEY,
  "parent_id" BIGINT REFERENCES "organizations"("id"),
  "code" VARCHAR(64) NOT NULL UNIQUE,
  "name" VARCHAR(255) NOT NULL,
  "sort_order" INTEGER NOT NULL DEFAULT 0,
  "status" VARCHAR(30) NOT NULL DEFAULT 'active',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "roles" (
  "id" BIGSERIAL PRIMARY KEY,
  "name" VARCHAR(150) NOT NULL,
  "code" VARCHAR(100) NOT NULL UNIQUE,
  "description" TEXT,
  "status" VARCHAR(30) NOT NULL DEFAULT 'active',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "menus" (
  "id" BIGSERIAL PRIMARY KEY,
  "parent_id" BIGINT REFERENCES "menus"("id"),
  "name" VARCHAR(150) NOT NULL,
  "route_path" VARCHAR(500),
  "component" VARCHAR(500),
  "permission_code" VARCHAR(150),
  "menu_type" VARCHAR(30) NOT NULL DEFAULT 'menu',
  "icon" VARCHAR(150),
  "metadata" JSONB,
  "action_label" VARCHAR(255),
  "sort_order" INTEGER NOT NULL DEFAULT 0,
  "is_visible" BOOLEAN NOT NULL DEFAULT TRUE,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "posts" (
  "id" BIGSERIAL PRIMARY KEY,
  "organization_id" BIGINT NOT NULL REFERENCES "organizations"("id"),
  "parent_id" BIGINT REFERENCES "posts"("id"),
  "code" VARCHAR(64) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "sort_order" INTEGER NOT NULL DEFAULT 0,
  "status" VARCHAR(30) NOT NULL DEFAULT 'active',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE ("organization_id", "code")
);

CREATE TABLE "users" (
  "id" BIGSERIAL PRIMARY KEY,
  "account" VARCHAR(150) NOT NULL UNIQUE,
  "password_hash" VARCHAR(500) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "email" VARCHAR(320),
  "phone" VARCHAR(50),
  "avatar_url" TEXT,
  "gender" VARCHAR(20),
  "status" VARCHAR(30) NOT NULL DEFAULT 'active',
  "sort_order" INTEGER NOT NULL DEFAULT 0,
  "tags" JSONB,
  "country" VARCHAR(100),
  "region" VARCHAR(100),
  "city" VARCHAR(100),
  "organization_id" BIGINT REFERENCES "organizations"("id"),
  "primary_post_id" BIGINT REFERENCES "posts"("id"),
  "session_token" VARCHAR(500),
  "login_count" INTEGER NOT NULL DEFAULT 0,
  "last_login_ip" VARCHAR(64),
  "last_login_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "user_role_assignments" (
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "role_id" BIGINT NOT NULL REFERENCES "roles"("id"),
  "assigned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "role_id")
);

CREATE TABLE "user_post_assignments" (
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "post_id" BIGINT NOT NULL REFERENCES "posts"("id"),
  "is_primary" BOOLEAN NOT NULL DEFAULT FALSE,
  "assigned_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "post_id")
);

CREATE TABLE "role_menu_permissions" (
  "role_id" BIGINT NOT NULL REFERENCES "roles"("id"),
  "menu_id" BIGINT NOT NULL REFERENCES "menus"("id"),
  "granted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("role_id", "menu_id")
);

CREATE TABLE "notifications" (
  "id" BIGSERIAL PRIMARY KEY,
  "title" VARCHAR(500) NOT NULL,
  "content" TEXT NOT NULL,
  "publication_status" VARCHAR(30) NOT NULL DEFAULT 'draft',
  "published_at" TIMESTAMPTZ,
  "expires_at" TIMESTAMPTZ,
  "created_by_user_id" BIGINT REFERENCES "users"("id"),
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "notification_recipients" (
  "notification_id" BIGINT NOT NULL REFERENCES "notifications"("id"),
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "delivered_at" TIMESTAMPTZ,
  "read_at" TIMESTAMPTZ,
  PRIMARY KEY ("notification_id", "user_id")
);

CREATE TABLE "audit_logs" (
  "id" BIGSERIAL PRIMARY KEY,
  "user_id" BIGINT REFERENCES "users"("id"),
  "action_type" VARCHAR(100) NOT NULL,
  "request_method" VARCHAR(20),
  "request_path" TEXT,
  "request_parameters" JSONB,
  "client_environment" JSONB,
  "ip_address" VARCHAR(64),
  "country" VARCHAR(100),
  "region" VARCHAR(100),
  "city" VARCHAR(100),
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "i18n_entries" (
  "id" BIGSERIAL PRIMARY KEY,
  "parent_id" BIGINT REFERENCES "i18n_entries"("id"),
  "label_key" VARCHAR(255) NOT NULL UNIQUE,
  "default_label" VARCHAR(500),
  "sort_order" INTEGER NOT NULL DEFAULT 0,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "i18n_translations" (
  "entry_id" BIGINT NOT NULL REFERENCES "i18n_entries"("id"),
  "locale" VARCHAR(20) NOT NULL,
  "translated_label" TEXT NOT NULL,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("entry_id", "locale"),
  CHECK ("locale" IN ('zh-CN', 'zh-TW', 'en', 'ja'))
);

CREATE INDEX "idx_users_login" ON "users" ("account", "status");
CREATE INDEX "idx_users_filter" ON "users" ("status", "account", "organization_id", "primary_post_id");
CREATE INDEX "idx_roles_filter" ON "roles" ("name", "code", "created_at");
CREATE INDEX "idx_menus_parent_sort" ON "menus" ("parent_id", "sort_order");
CREATE INDEX "idx_organizations_parent_sort" ON "organizations" ("parent_id", "sort_order");
CREATE INDEX "idx_posts_organization" ON "posts" ("organization_id", "parent_id", "sort_order");
CREATE INDEX "idx_role_permissions_role" ON "role_menu_permissions" ("role_id", "menu_id");
CREATE INDEX "idx_notification_filter" ON "notifications" ("publication_status", "published_at", "title");
CREATE INDEX "idx_notification_recipient_read" ON "notification_recipients" ("user_id", "read_at", "notification_id");
CREATE INDEX "idx_audit_logs_filter" ON "audit_logs" ("user_id", "action_type", "created_at");
CREATE INDEX "idx_i18n_parent" ON "i18n_entries" ("parent_id", "sort_order");
