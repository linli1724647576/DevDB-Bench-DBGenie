CREATE TABLE "account" (
  "id" TEXT NOT NULL,
  "account_id" TEXT NOT NULL,
  "provider_id" TEXT NOT NULL,
  "user_id" UUID NOT NULL,
  "access_token" TEXT,
  "refresh_token" TEXT,
  "id_token" TEXT,
  "access_token_expires_at" TIMESTAMP,
  "refresh_token_expires_at" TIMESTAMP,
  "scope" TEXT,
  "password" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "app_data" (
  "id" UUID NOT NULL,
  "app" TEXT NOT NULL,
  "user_id" UUID NOT NULL,
  "data" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "categories" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "color" TEXT NOT NULL,
  "llm_prompt" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "currencies" (
  "id" UUID NOT NULL,
  "user_id" UUID,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "fields" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "llm_prompt" TEXT,
  "options" JSONB,
  "created_at" TIMESTAMP NOT NULL,
  "is_visible_in_list" BOOLEAN NOT NULL,
  "is_visible_in_analysis" BOOLEAN NOT NULL,
  "is_required" BOOLEAN NOT NULL,
  "is_extra" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "files" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "filename" TEXT NOT NULL,
  "path" TEXT NOT NULL,
  "mimetype" TEXT NOT NULL,
  "metadata" JSONB,
  "is_reviewed" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "cached_parse_result" JSONB,
  "is_splitted" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "progress" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "type" TEXT NOT NULL,
  "data" JSONB,
  "current" INTEGER NOT NULL,
  "total" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "projects" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "color" TEXT NOT NULL,
  "llm_prompt" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "sessions" (
  "id" UUID NOT NULL,
  "token" TEXT NOT NULL,
  "expires_at" TIMESTAMP NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "ip_address" TEXT,
  "user_agent" TEXT,
  "user_id" UUID NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "settings" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "value" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "transactions" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "name" TEXT,
  "description" TEXT,
  "merchant" TEXT,
  "total" INTEGER,
  "currency_code" TEXT,
  "converted_total" INTEGER,
  "converted_currency_code" TEXT,
  "type" TEXT,
  "note" TEXT,
  "files" JSONB NOT NULL,
  "extra" JSONB,
  "category_code" TEXT,
  "project_code" TEXT,
  "issued_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "text" TEXT,
  "items" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "users" (
  "id" UUID NOT NULL,
  "email" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "avatar" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "membership_plan" TEXT,
  "membership_expires_at" TIMESTAMP,
  "is_email_verified" BOOLEAN NOT NULL,
  "image" TEXT,
  "storage_limit" INTEGER,
  "business_address" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "verification" (
  "id" UUID NOT NULL,
  "identifier" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  "expires_at" TIMESTAMP NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "uidx_app_data_user_id_app_1" ON "app_data" ("user_id", "app");

CREATE UNIQUE INDEX "uidx_categories_user_id_code_1" ON "categories" ("user_id", "code");

CREATE UNIQUE INDEX "uidx_currencies_user_id_code_1" ON "currencies" ("user_id", "code");

CREATE UNIQUE INDEX "uidx_fields_user_id_code_1" ON "fields" ("user_id", "code");

CREATE INDEX "idx_progress_user_id_1" ON "progress" ("user_id");

CREATE UNIQUE INDEX "uidx_projects_user_id_code_1" ON "projects" ("user_id", "code");

CREATE UNIQUE INDEX "uidx_sessions_token_1" ON "sessions" ("token");

CREATE UNIQUE INDEX "uidx_settings_user_id_code_1" ON "settings" ("user_id", "code");

CREATE INDEX "idx_transactions_user_id_1" ON "transactions" ("user_id");

CREATE INDEX "idx_transactions_project_code_2" ON "transactions" ("project_code");

CREATE INDEX "idx_transactions_category_code_3" ON "transactions" ("category_code");

CREATE INDEX "idx_transactions_issued_at_4" ON "transactions" ("issued_at");

CREATE INDEX "idx_transactions_name_5" ON "transactions" ("name");

CREATE INDEX "idx_transactions_merchant_6" ON "transactions" ("merchant");

CREATE INDEX "idx_transactions_total_7" ON "transactions" ("total");

CREATE UNIQUE INDEX "uidx_users_email_1" ON "users" ("email");

ALTER TABLE "account" ADD CONSTRAINT "fk_account_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "app_data" ADD CONSTRAINT "fk_app_data_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "categories" ADD CONSTRAINT "fk_categories_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "currencies" ADD CONSTRAINT "fk_currencies_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "fields" ADD CONSTRAINT "fk_fields_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "files" ADD CONSTRAINT "fk_files_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "progress" ADD CONSTRAINT "fk_progress_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "projects" ADD CONSTRAINT "fk_projects_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "sessions" ADD CONSTRAINT "fk_sessions_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "settings" ADD CONSTRAINT "fk_settings_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "transactions" ADD CONSTRAINT "fk_transactions_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "transactions" ADD CONSTRAINT "fk_transactions_category_code_user_id_2" FOREIGN KEY ("category_code", "user_id") REFERENCES "categories" ("code", "user_id");

ALTER TABLE "transactions" ADD CONSTRAINT "fk_transactions_project_code_user_id_3" FOREIGN KEY ("project_code", "user_id") REFERENCES "projects" ("code", "user_id");
