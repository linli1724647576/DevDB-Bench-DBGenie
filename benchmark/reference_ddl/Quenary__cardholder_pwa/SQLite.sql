CREATE TABLE "user_roles" (
  "code" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("code")
);

CREATE TABLE "settings" (
  "key" VARCHAR(255) NOT NULL,
  "value" VARCHAR(255) NOT NULL,
  "value_type" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("key")
);

CREATE TABLE "users" (
  "id" INTEGER NOT NULL,
  "username" VARCHAR(255) NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "hashed_password" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "role_code" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("email"),
  UNIQUE ("username"),
  FOREIGN KEY ("role_code") REFERENCES "user_roles" ("code")
);

CREATE TABLE "cards" (
  "id" INTEGER NOT NULL,
  "code" VARCHAR(255) NOT NULL,
  "code_type" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "color" VARCHAR(255),
  "user_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "is_favorite" BOOLEAN NOT NULL,
  "used_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "password_recovery_codes" (
  "id" INTEGER NOT NULL,
  "code" VARCHAR(255) NOT NULL,
  "user_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "expires_at" TIMESTAMP NOT NULL,
  "revoked" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("code"),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "refresh_tokens" (
  "id" INTEGER NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "user_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "expires_at" TIMESTAMP NOT NULL,
  "revoked" BOOLEAN NOT NULL,
  "user_agent" VARCHAR(255),
  "ip_address" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("token"),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE UNIQUE INDEX "uidx_users_email_1" ON "users" ("email");

CREATE INDEX "idx_users_id_2" ON "users" ("id");

CREATE UNIQUE INDEX "uidx_users_username_3" ON "users" ("username");

CREATE INDEX "idx_cards_id_1" ON "cards" ("id");

CREATE UNIQUE INDEX "uidx_password_recovery_codes_code_1" ON "password_recovery_codes" ("code");

CREATE INDEX "idx_password_recovery_codes_id_2" ON "password_recovery_codes" ("id");

CREATE INDEX "idx_refresh_tokens_id_1" ON "refresh_tokens" ("id");

CREATE UNIQUE INDEX "uidx_refresh_tokens_token_2" ON "refresh_tokens" ("token");
