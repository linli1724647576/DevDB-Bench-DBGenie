CREATE TABLE "building_schema_versions" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "building_schema_id" UUID NOT NULL,
  "number" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "patch" JSONB,
  "reverse_patch" JSONB,
  PRIMARY KEY ("id")
);

CREATE TABLE "building_schemas" (
  "id" UUID NOT NULL,
  "design_session_id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "schema" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "git_sha" TEXT,
  "initial_schema_snapshot" JSONB,
  "schema_file_path" TEXT,
  PRIMARY KEY ("id"),
  UNIQUE ("design_session_id")
);

CREATE TABLE "checkpoint_blobs" (
  "id" UUID NOT NULL,
  "thread_id" TEXT NOT NULL,
  "checkpoint_ns" TEXT NOT NULL,
  "channel" TEXT NOT NULL,
  "version" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "blob" BYTEA,
  "organization_id" UUID NOT NULL,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("thread_id", "checkpoint_ns", "channel", "version", "organization_id")
);

CREATE TABLE "checkpoint_writes" (
  "id" UUID NOT NULL,
  "thread_id" TEXT NOT NULL,
  "checkpoint_ns" TEXT NOT NULL,
  "checkpoint_id" TEXT NOT NULL,
  "task_id" TEXT NOT NULL,
  "idx" INTEGER NOT NULL,
  "channel" TEXT NOT NULL,
  "type" TEXT,
  "blob" BYTEA NOT NULL,
  "organization_id" UUID NOT NULL,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx", "organization_id")
);

CREATE TABLE "checkpoints" (
  "id" UUID NOT NULL,
  "thread_id" TEXT NOT NULL,
  "checkpoint_ns" TEXT NOT NULL,
  "checkpoint_id" TEXT NOT NULL,
  "parent_checkpoint_id" TEXT,
  "checkpoint" JSONB NOT NULL,
  "metadata" JSONB NOT NULL,
  "organization_id" UUID NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("thread_id", "checkpoint_ns", "checkpoint_id", "organization_id")
);

CREATE TABLE "design_sessions" (
  "id" UUID NOT NULL,
  "project_id" UUID,
  "organization_id" UUID NOT NULL,
  "created_by_user_id" UUID NOT NULL,
  "parent_design_session_id" UUID,
  "name" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "github_repositories" (
  "id" UUID NOT NULL,
  "name" TEXT NOT NULL,
  "owner" TEXT NOT NULL,
  "github_installation_identifier" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "github_repository_identifier" INTEGER NOT NULL,
  "organization_id" UUID NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("github_repository_identifier", "organization_id")
);

CREATE TABLE "invitations" (
  "id" UUID NOT NULL,
  "email" TEXT NOT NULL,
  "invite_by_user_id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "invited_at" TIMESTAMP,
  "token" UUID NOT NULL,
  "expired_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("token")
);

CREATE TABLE "organization_members" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "joined_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id", "organization_id")
);

CREATE TABLE "organizations" (
  "id" UUID NOT NULL,
  "name" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "project_repository_mappings" (
  "id" UUID NOT NULL,
  "project_id" UUID NOT NULL,
  "repository_id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "organization_id" UUID NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "projects" (
  "id" UUID NOT NULL,
  "name" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "organization_id" UUID NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "public_share_settings" (
  "design_session_id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("design_session_id")
);

CREATE TABLE "schema_file_paths" (
  "id" UUID NOT NULL,
  "path" TEXT NOT NULL,
  "project_id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "format" TEXT NOT NULL,
  "organization_id" UUID NOT NULL,
  PRIMARY KEY ("id"),
  CHECK ("format" IN ('schemarb', 'postgres', 'prisma', 'tbls'))
);

CREATE TABLE "users" (
  "id" UUID NOT NULL,
  "name" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "avatar_url" TEXT,
  PRIMARY KEY ("id"),
  UNIQUE ("email")
);

ALTER TABLE "building_schema_versions" ADD CONSTRAINT "fk_building_schema_versions_building_schema_id_1" FOREIGN KEY ("building_schema_id") REFERENCES "building_schemas" ("id");

ALTER TABLE "building_schema_versions" ADD CONSTRAINT "fk_building_schema_versions_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "building_schemas" ADD CONSTRAINT "fk_building_schemas_design_session_id_1" FOREIGN KEY ("design_session_id") REFERENCES "design_sessions" ("id");

ALTER TABLE "building_schemas" ADD CONSTRAINT "fk_building_schemas_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "checkpoint_blobs" ADD CONSTRAINT "fk_checkpoint_blobs_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "checkpoint_writes" ADD CONSTRAINT "fk_checkpoint_writes_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "checkpoints" ADD CONSTRAINT "fk_checkpoints_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "design_sessions" ADD CONSTRAINT "fk_design_sessions_created_by_user_id_1" FOREIGN KEY ("created_by_user_id") REFERENCES "users" ("id");

ALTER TABLE "design_sessions" ADD CONSTRAINT "fk_design_sessions_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "design_sessions" ADD CONSTRAINT "fk_design_sessions_parent_design_session_id_3" FOREIGN KEY ("parent_design_session_id") REFERENCES "design_sessions" ("id");

ALTER TABLE "design_sessions" ADD CONSTRAINT "fk_design_sessions_project_id_4" FOREIGN KEY ("project_id") REFERENCES "projects" ("id");

ALTER TABLE "github_repositories" ADD CONSTRAINT "fk_github_repositories_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "invitations" ADD CONSTRAINT "fk_invitations_invite_by_user_id_1" FOREIGN KEY ("invite_by_user_id") REFERENCES "users" ("id");

ALTER TABLE "invitations" ADD CONSTRAINT "fk_invitations_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "organization_members" ADD CONSTRAINT "fk_organization_members_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "organization_members" ADD CONSTRAINT "fk_organization_members_user_id_2" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "project_repository_mappings" ADD CONSTRAINT "fk_project_repository_mappings_project_id_1" FOREIGN KEY ("project_id") REFERENCES "projects" ("id");

ALTER TABLE "project_repository_mappings" ADD CONSTRAINT "fk_project_repository_mappings_repository_id_2" FOREIGN KEY ("repository_id") REFERENCES "github_repositories" ("id");

ALTER TABLE "project_repository_mappings" ADD CONSTRAINT "fk_project_repository_mappings_organization_id_3" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "projects" ADD CONSTRAINT "fk_projects_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

ALTER TABLE "public_share_settings" ADD CONSTRAINT "fk_public_share_settings_design_session_id_1" FOREIGN KEY ("design_session_id") REFERENCES "design_sessions" ("id");

ALTER TABLE "schema_file_paths" ADD CONSTRAINT "fk_schema_file_paths_project_id_1" FOREIGN KEY ("project_id") REFERENCES "projects" ("id");

ALTER TABLE "schema_file_paths" ADD CONSTRAINT "fk_schema_file_paths_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "organizations" ("id");

CREATE INDEX "idx_building_schema_versions_schema_number" ON "building_schema_versions" ("building_schema_id", "number");
CREATE INDEX "idx_organization_members_org_user" ON "organization_members" ("organization_id", "user_id");
CREATE INDEX "idx_design_sessions_project" ON "design_sessions" ("project_id");
CREATE INDEX "idx_project_repository_mappings_project_repository" ON "project_repository_mappings" ("project_id", "repository_id");
CREATE INDEX "idx_schema_file_paths_project" ON "schema_file_paths" ("project_id");
CREATE INDEX "idx_projects_organization" ON "projects" ("organization_id");
CREATE INDEX "idx_github_repositories_org_installation" ON "github_repositories" ("organization_id", "github_installation_identifier");
