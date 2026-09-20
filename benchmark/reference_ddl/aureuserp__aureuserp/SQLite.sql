CREATE TABLE "cache" (
  "key" VARCHAR(255) NOT NULL,
  "value" TEXT NOT NULL,
  "expiration" INTEGER NOT NULL,
  PRIMARY KEY ("key")
);

CREATE TABLE "cache_locks" (
  "key" VARCHAR(255) NOT NULL,
  "owner" VARCHAR(255) NOT NULL,
  "expiration" INTEGER NOT NULL,
  PRIMARY KEY ("key")
);

CREATE TABLE "failed_jobs" (
  "id" BIGINT NOT NULL,
  "uuid" VARCHAR(255) NOT NULL,
  "connection" TEXT NOT NULL,
  "queue" TEXT NOT NULL,
  "payload" TEXT NOT NULL,
  "exception" TEXT NOT NULL,
  "failed_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid")
);

CREATE TABLE "job_batches" (
  "id" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "total_jobs" INTEGER NOT NULL,
  "pending_jobs" INTEGER NOT NULL,
  "failed_jobs" INTEGER NOT NULL,
  "failed_job_ids" TEXT NOT NULL,
  "options" TEXT,
  "cancelled_at" INTEGER,
  "created_at" INTEGER NOT NULL,
  "finished_at" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "jobs" (
  "id" BIGINT NOT NULL,
  "queue" VARCHAR(255) NOT NULL,
  "payload" TEXT NOT NULL,
  "attempts" INTEGER NOT NULL,
  "reserved_at" INTEGER,
  "available_at" INTEGER NOT NULL,
  "created_at" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "notifications" (
  "id" CHAR(36) NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "notifiable_id" BIGINT NOT NULL,
  "notifiable_type" VARCHAR(255) NOT NULL,
  "data" TEXT NOT NULL,
  "read_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "password_reset_tokens" (
  "email" VARCHAR(255) NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("email")
);

CREATE TABLE "permissions" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "guard_name" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("name", "guard_name")
);

CREATE TABLE "personal_access_tokens" (
  "id" BIGINT NOT NULL,
  "tokenable_id" BIGINT NOT NULL,
  "tokenable_type" VARCHAR(255) NOT NULL,
  "name" TEXT NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "abilities" TEXT,
  "last_used_at" TIMESTAMP,
  "expires_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("token")
);

CREATE TABLE "roles" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "guard_name" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("name", "guard_name")
);

CREATE TABLE "sessions" (
  "id" VARCHAR(255) NOT NULL,
  "user_id" BIGINT,
  "ip_address" VARCHAR(255),
  "user_agent" TEXT,
  "payload" TEXT NOT NULL,
  "last_activity" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "settings" (
  "id" BIGINT NOT NULL,
  "group" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "locked" BOOLEAN NOT NULL,
  "payload" TEXT NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("group", "name")
);

CREATE TABLE "users" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "email_verified_at" TIMESTAMP,
  "language" VARCHAR(255),
  "is_active" BOOLEAN NOT NULL,
  "password" VARCHAR(255) NOT NULL,
  "resource_permission" VARCHAR(255) NOT NULL,
  "remember_token" VARCHAR(255),
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("email")
);

CREATE TABLE "website_pages" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "content" TEXT NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "is_published" BOOLEAN NOT NULL,
  "is_header_visible" BOOLEAN NOT NULL,
  "is_footer_visible" BOOLEAN NOT NULL,
  "published_at" TIMESTAMP,
  "meta_title" VARCHAR(255),
  "meta_keywords" VARCHAR(255),
  "meta_description" TEXT,
  "creator_id" BIGINT,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("slug"),
  FOREIGN KEY ("creator_id") REFERENCES "users" ("id")
);

CREATE TABLE "exports" (
  "id" BIGINT NOT NULL,
  "completed_at" TIMESTAMP,
  "file_disk" VARCHAR(255) NOT NULL,
  "file_name" VARCHAR(255),
  "exporter" VARCHAR(255) NOT NULL,
  "processed_rows" INTEGER NOT NULL,
  "total_rows" INTEGER NOT NULL,
  "successful_rows" INTEGER NOT NULL,
  "user_id" BIGINT NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "imports" (
  "id" BIGINT NOT NULL,
  "completed_at" TIMESTAMP,
  "file_name" VARCHAR(255) NOT NULL,
  "file_path" VARCHAR(255) NOT NULL,
  "importer" VARCHAR(255) NOT NULL,
  "processed_rows" INTEGER NOT NULL,
  "total_rows" INTEGER NOT NULL,
  "successful_rows" INTEGER NOT NULL,
  "user_id" BIGINT NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "model_has_permissions" (
  "permission_id" BIGINT NOT NULL,
  "model_type" VARCHAR(255) NOT NULL,
  "model_id" BIGINT NOT NULL,
  PRIMARY KEY ("permission_id", "model_id", "model_type"),
  FOREIGN KEY ("permission_id") REFERENCES "permissions" ("id")
);

CREATE TABLE "model_has_roles" (
  "role_id" BIGINT NOT NULL,
  "model_type" VARCHAR(255) NOT NULL,
  "model_id" BIGINT NOT NULL,
  PRIMARY KEY ("role_id", "model_id", "model_type"),
  FOREIGN KEY ("role_id") REFERENCES "roles" ("id")
);

CREATE TABLE "role_has_permissions" (
  "permission_id" BIGINT NOT NULL,
  "role_id" BIGINT NOT NULL,
  PRIMARY KEY ("permission_id", "role_id"),
  FOREIGN KEY ("permission_id") REFERENCES "permissions" ("id"),
  FOREIGN KEY ("role_id") REFERENCES "roles" ("id")
);

CREATE TABLE "failed_import_rows" (
  "id" BIGINT NOT NULL,
  "data" TEXT NOT NULL,
  "import_id" BIGINT NOT NULL,
  "validation_error" TEXT,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("import_id") REFERENCES "imports" ("id")
);

CREATE INDEX "idx_jobs_queue_1" ON "jobs" ("queue");

CREATE INDEX "idx_notifications_notifiable_id_notifiable_type_1" ON "notifications" ("notifiable_id", "notifiable_type");

CREATE INDEX "idx_personal_access_tokens_expires_at_1" ON "personal_access_tokens" ("expires_at");

CREATE INDEX "idx_personal_access_tokens_tokenable_id_tokenable_type_2" ON "personal_access_tokens" ("tokenable_id", "tokenable_type");

CREATE INDEX "idx_sessions_user_id_1" ON "sessions" ("user_id");

CREATE INDEX "idx_sessions_last_activity_2" ON "sessions" ("last_activity");

CREATE INDEX "idx_model_has_permissions_model_id_model_type_1" ON "model_has_permissions" ("model_id", "model_type");

CREATE INDEX "idx_model_has_roles_model_id_model_type_1" ON "model_has_roles" ("model_id", "model_type");
