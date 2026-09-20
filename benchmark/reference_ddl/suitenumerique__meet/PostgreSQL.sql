CREATE TABLE "meet_resource" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "meet_user" (
  "id" UUID NOT NULL,
  "password" VARCHAR(255) NOT NULL,
  "last_login" TIMESTAMP,
  "is_superuser" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "sub" VARCHAR(255),
  "email" VARCHAR(255),
  "admin_email" VARCHAR(255),
  "full_name" VARCHAR(255),
  "short_name" VARCHAR(255),
  "language" VARCHAR(255) NOT NULL,
  "timezone" VARCHAR(255) NOT NULL,
  "is_device" BOOLEAN NOT NULL,
  "is_staff" BOOLEAN NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("sub"),
  UNIQUE ("admin_email")
);

CREATE TABLE "meet_room" (
  "resource_id" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255),
  "access_level" VARCHAR(255) NOT NULL,
  "configuration" JSONB NOT NULL,
  "pin_code" VARCHAR(255),
  PRIMARY KEY ("resource_id"),
  UNIQUE ("slug"),
  UNIQUE ("pin_code")
);

CREATE TABLE "meet_resource_access" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "resource_id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "role" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id", "resource_id")
);

CREATE TABLE "meet_recording" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "worker_id" VARCHAR(255),
  "room_id" UUID NOT NULL,
  "mode" VARCHAR(255) NOT NULL,
  "options" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "meet_recording_access" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "user_id" UUID,
  "team" VARCHAR(255) NOT NULL,
  "role" VARCHAR(255) NOT NULL,
  "recording_id" UUID NOT NULL,
  PRIMARY KEY ("id"),
  CHECK ((user_id IS NOT NULL AND team = '') OR (user_id IS NULL AND team != ''))
);

CREATE TABLE "meet_application" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "client_id" VARCHAR(255) NOT NULL,
  "client_secret" VARCHAR(255) NOT NULL,
  "scopes" JSONB NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("client_id")
);

CREATE TABLE "meet_application_domain" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "domain" VARCHAR(255) NOT NULL,
  "application_id" UUID NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("application_id", "domain")
);

CREATE TABLE "file" (
  "id" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "deleted_at" TIMESTAMP,
  "hard_deleted_at" TIMESTAMP,
  "filename" VARCHAR(255) NOT NULL,
  "upload_state" VARCHAR(255) NOT NULL,
  "mimetype" VARCHAR(255),
  "size" BIGINT,
  "description" TEXT,
  "malware_detection_info" JSONB,
  "creator_id" UUID,
  PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "uidx_meet_recording_room_id_1" ON "meet_recording" ("room_id");

CREATE UNIQUE INDEX "uidx_meet_recording_access_user_id_recording_id_1" ON "meet_recording_access" ("user_id", "recording_id");

CREATE UNIQUE INDEX "uidx_meet_recording_access_team_recording_id_2" ON "meet_recording_access" ("team", "recording_id");

CREATE INDEX "idx_file_creator_id_type_created_at_1" ON "file" ("creator_id", "type", "created_at");

ALTER TABLE "meet_room" ADD CONSTRAINT "fk_meet_room_resource_id_1" FOREIGN KEY ("resource_id") REFERENCES "meet_resource" ("id");

ALTER TABLE "meet_resource_access" ADD CONSTRAINT "fk_meet_resource_access_resource_id_1" FOREIGN KEY ("resource_id") REFERENCES "meet_resource" ("id");

ALTER TABLE "meet_resource_access" ADD CONSTRAINT "fk_meet_resource_access_user_id_2" FOREIGN KEY ("user_id") REFERENCES "meet_user" ("id");

ALTER TABLE "meet_recording" ADD CONSTRAINT "fk_meet_recording_room_id_1" FOREIGN KEY ("room_id") REFERENCES "meet_room" ("resource_id");

ALTER TABLE "meet_recording_access" ADD CONSTRAINT "fk_meet_recording_access_user_id_1" FOREIGN KEY ("user_id") REFERENCES "meet_user" ("id");

ALTER TABLE "meet_recording_access" ADD CONSTRAINT "fk_meet_recording_access_recording_id_2" FOREIGN KEY ("recording_id") REFERENCES "meet_recording" ("id");

ALTER TABLE "meet_application_domain" ADD CONSTRAINT "fk_meet_application_domain_application_id_1" FOREIGN KEY ("application_id") REFERENCES "meet_application" ("id");

ALTER TABLE "file" ADD CONSTRAINT "fk_file_creator_id_1" FOREIGN KEY ("creator_id") REFERENCES "meet_user" ("id");
