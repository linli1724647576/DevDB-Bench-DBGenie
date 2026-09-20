CREATE TABLE "users" (
  "id" BIGSERIAL PRIMARY KEY,
  "authentication_identity" VARCHAR(255) NOT NULL UNIQUE,
  "email" VARCHAR(320),
  "first_name" VARCHAR(150),
  "last_name" VARCHAR(150),
  "locale" VARCHAR(20) NOT NULL DEFAULT 'en',
  "timezone" VARCHAR(64) NOT NULL DEFAULT 'UTC',
  "is_first_connection" BOOLEAN NOT NULL DEFAULT TRUE,
  "is_administrator" BOOLEAN NOT NULL DEFAULT FALSE,
  "is_device_account" BOOLEAN NOT NULL DEFAULT FALSE,
  "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
  "last_activity_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "teams" (
  "id" BIGSERIAL PRIMARY KEY,
  "team_identifier" VARCHAR(255) NOT NULL UNIQUE,
  "display_name" VARCHAR(255),
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "documents" (
  "id" BIGSERIAL PRIMARY KEY,
  "creator_user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "parent_document_id" BIGINT REFERENCES "documents"("id"),
  "source_document_id" BIGINT REFERENCES "documents"("id"),
  "title" TEXT NOT NULL,
  "normalized_title" TEXT NOT NULL,
  "excerpt" TEXT,
  "stable_path" TEXT NOT NULL UNIQUE,
  "visibility" VARCHAR(30) NOT NULL DEFAULT 'private',
  "is_deleted" BOOLEAN NOT NULL DEFAULT FALSE,
  "deleted_at" TIMESTAMPTZ,
  "descendant_deletion_impacted_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (char_length("title") > 0),
  CHECK ("visibility" IN ('private', 'restricted', 'public'))
);

CREATE TABLE "document_attachments" (
  "id" BIGSERIAL PRIMARY KEY,
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "file_name" TEXT NOT NULL,
  "content_type" VARCHAR(255),
  "storage_key" TEXT NOT NULL,
  "size_bytes" BIGINT,
  "metadata" JSONB,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK ("size_bytes" IS NULL OR "size_bytes" >= 0)
);

CREATE TABLE "document_permissions" (
  "id" BIGSERIAL PRIMARY KEY,
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "grantee_user_id" BIGINT REFERENCES "users"("id"),
  "grantee_team_id" BIGINT REFERENCES "teams"("id"),
  "role" VARCHAR(40) NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (("grantee_user_id" IS NOT NULL)::INTEGER + ("grantee_team_id" IS NOT NULL)::INTEGER = 1),
  UNIQUE ("document_id", "grantee_user_id"),
  UNIQUE ("document_id", "grantee_team_id")
);

CREATE TABLE "document_invitations" (
  "id" BIGSERIAL PRIMARY KEY,
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "invited_by_user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "invitee_email" VARCHAR(320) NOT NULL,
  "intended_role" VARCHAR(40) NOT NULL,
  "status" VARCHAR(30) NOT NULL DEFAULT 'pending',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "responded_at" TIMESTAMPTZ
);

CREATE TABLE "document_access_requests" (
  "id" BIGSERIAL PRIMARY KEY,
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "requesting_user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "requested_role" VARCHAR(40),
  "status" VARCHAR(30) NOT NULL DEFAULT 'pending',
  "request_details" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE ("document_id", "requesting_user_id", "status")
);

CREATE TABLE "document_favorites" (
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "marked_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "document_id")
);

CREATE TABLE "hidden_documents" (
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "hidden_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "document_id")
);

CREATE TABLE "opened_document_traces" (
  "id" BIGSERIAL PRIMARY KEY,
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "opened_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "trace_state" VARCHAR(30) NOT NULL DEFAULT 'visible',
  UNIQUE ("user_id", "document_id")
);

CREATE TABLE "discussion_threads" (
  "id" BIGSERIAL PRIMARY KEY,
  "document_id" BIGINT NOT NULL REFERENCES "documents"("id"),
  "created_by_user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "is_resolved" BOOLEAN NOT NULL DEFAULT FALSE,
  "resolved_by_user_id" BIGINT REFERENCES "users"("id"),
  "resolved_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "comments" (
  "id" BIGSERIAL PRIMARY KEY,
  "thread_id" BIGINT NOT NULL REFERENCES "discussion_threads"("id"),
  "author_user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "parent_comment_id" BIGINT REFERENCES "comments"("id"),
  "structured_content" JSONB NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "emoji_reactions" (
  "id" BIGSERIAL PRIMARY KEY,
  "comment_id" BIGINT NOT NULL REFERENCES "comments"("id"),
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "emoji_value" VARCHAR(64) NOT NULL,
  "reacted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE ("comment_id", "user_id", "emoji_value")
);

CREATE TABLE "reconciliation_workflows" (
  "id" BIGSERIAL PRIMARY KEY,
  "csv_source_reference" TEXT NOT NULL,
  "confirmation_details" JSONB,
  "status" VARCHAR(30) NOT NULL,
  "started_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completed_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "reconciliation_accounts" (
  "workflow_id" BIGINT NOT NULL REFERENCES "reconciliation_workflows"("id"),
  "user_id" BIGINT NOT NULL REFERENCES "users"("id"),
  "participant_role" VARCHAR(40) NOT NULL,
  "confirmed_at" TIMESTAMPTZ,
  PRIMARY KEY ("workflow_id", "user_id")
);

CREATE TABLE "reconciliation_logs" (
  "id" BIGSERIAL PRIMARY KEY,
  "workflow_id" BIGINT NOT NULL REFERENCES "reconciliation_workflows"("id"),
  "log_level" VARCHAR(20) NOT NULL,
  "message" TEXT NOT NULL,
  "logged_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX "idx_documents_normalized_title" ON "documents" ("normalized_title");
CREATE INDEX "idx_documents_creator" ON "documents" ("creator_user_id", "updated_at");
CREATE INDEX "idx_documents_parent" ON "documents" ("parent_document_id");
CREATE INDEX "idx_documents_indexing_changes" ON "documents" ("updated_at", "deleted_at");
CREATE INDEX "idx_documents_visibility" ON "documents" ("visibility", "is_deleted");
CREATE INDEX "idx_permissions_document_user" ON "document_permissions" ("document_id", "grantee_user_id");
CREATE INDEX "idx_permissions_document_team" ON "document_permissions" ("document_id", "grantee_team_id");
CREATE INDEX "idx_favorites_user" ON "document_favorites" ("user_id", "marked_at");
CREATE INDEX "idx_hidden_user" ON "hidden_documents" ("user_id", "hidden_at");
CREATE INDEX "idx_opened_public_lookup" ON "opened_document_traces" ("user_id", "document_id");
CREATE INDEX "idx_threads_document" ON "discussion_threads" ("document_id", "created_at");
CREATE INDEX "idx_comments_thread" ON "comments" ("thread_id", "created_at");
CREATE INDEX "idx_reactions_comment" ON "emoji_reactions" ("comment_id");
CREATE INDEX "idx_reconciliation_status" ON "reconciliation_workflows" ("status", "created_at");
