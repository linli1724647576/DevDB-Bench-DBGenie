CREATE TABLE "accounts_profile" (
  "id" INTEGER NOT NULL,
  "next_report_date" TIMESTAMP,
  "user_id" INTEGER NOT NULL,
  "ping_log_limit" INTEGER NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "check_limit" INTEGER NOT NULL,
  "last_sms_date" TIMESTAMP,
  "sms_limit" INTEGER NOT NULL,
  "sms_sent" INTEGER NOT NULL,
  "sort" VARCHAR(255) NOT NULL,
  "nag_period" BIGINT NOT NULL,
  "next_nag_date" TIMESTAMP,
  "deletion_notice_date" TIMESTAMP,
  "last_active_date" TIMESTAMP,
  "call_limit" INTEGER NOT NULL,
  "calls_sent" INTEGER NOT NULL,
  "last_call_date" TIMESTAMP,
  "reports" VARCHAR(255) NOT NULL,
  "tz" VARCHAR(255) NOT NULL,
  "theme" VARCHAR(255),
  "totp" VARCHAR(255),
  "totp_created" TIMESTAMP,
  "deletion_scheduled_date" TIMESTAMP,
  "over_limit_date" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id")
);

CREATE TABLE "accounts_member" (
  "id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "project_id" INTEGER NOT NULL,
  "transfer_request_date" TIMESTAMP,
  "role" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id", "project_id")
);

CREATE TABLE "accounts_project" (
  "id" INTEGER NOT NULL,
  "code" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "api_key" VARCHAR(255) NOT NULL,
  "api_key_readonly" VARCHAR(255) NOT NULL,
  "owner_id" INTEGER NOT NULL,
  "badge_key" VARCHAR(255) NOT NULL,
  "ping_key" VARCHAR(255),
  "show_slugs" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("code"),
  UNIQUE ("badge_key"),
  UNIQUE ("ping_key")
);

CREATE TABLE "accounts_credential" (
  "id" INTEGER NOT NULL,
  "code" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "data" BYTEA NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("code")
);

CREATE TABLE "api_check" (
  "id" INTEGER NOT NULL,
  "code" UUID NOT NULL,
  "last_ping" TIMESTAMP,
  "user_id" INTEGER,
  "alert_after" TIMESTAMP,
  "status" VARCHAR(255) NOT NULL,
  "timeout" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "grace" BIGINT NOT NULL,
  "tags" VARCHAR(255) NOT NULL,
  "n_pings" INTEGER NOT NULL,
  "kind" VARCHAR(255) NOT NULL,
  "schedule" VARCHAR(255) NOT NULL,
  "tz" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "api_ping" (
  "id" INTEGER NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "remote_addr" VARCHAR(255),
  "method" VARCHAR(255) NOT NULL,
  "ua" VARCHAR(255) NOT NULL,
  "owner_id" INTEGER NOT NULL,
  "scheme" VARCHAR(255) NOT NULL,
  "n" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "api_channel" (
  "id" INTEGER NOT NULL,
  "code" UUID NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "kind" VARCHAR(255) NOT NULL,
  "value" TEXT NOT NULL,
  "email_verified" BOOLEAN NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "api_notification" (
  "id" INTEGER NOT NULL,
  "check_status" VARCHAR(255) NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "channel_id" INTEGER NOT NULL,
  "owner_id" INTEGER NOT NULL,
  "error" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "payments_subscription" (
  "id" INTEGER NOT NULL,
  "customer_id" VARCHAR(255) NOT NULL,
  "payment_method_token" VARCHAR(255) NOT NULL,
  "subscription_id" VARCHAR(255) NOT NULL,
  "user_id" INTEGER NOT NULL,
  "plan_id" VARCHAR(255) NOT NULL,
  "address_id" VARCHAR(255) NOT NULL,
  "send_invoices" BOOLEAN NOT NULL,
  "plan_name" VARCHAR(255) NOT NULL,
  "invoice_email" VARCHAR(255) NOT NULL,
  "next_billing_date" DATE,
  "renew_notice_date" DATE,
  "setup_date" DATE,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id")
);

CREATE TABLE "logs_record" (
  "id" INTEGER NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "level" INTEGER NOT NULL,
  "message" TEXT NOT NULL,
  "traceback" TEXT NOT NULL,
  "host" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_accounts_project_api_key_1" ON "accounts_project" ("api_key");

CREATE INDEX "idx_accounts_project_api_key_readonly_2" ON "accounts_project" ("api_key_readonly");

CREATE INDEX "idx_api_check_code_1" ON "api_check" ("code");

ALTER TABLE "accounts_member" ADD CONSTRAINT "fk_accounts_member_project_id_1" FOREIGN KEY ("project_id") REFERENCES "accounts_project" ("id");

ALTER TABLE "api_ping" ADD CONSTRAINT "fk_api_ping_owner_id_1" FOREIGN KEY ("owner_id") REFERENCES "api_check" ("id");

ALTER TABLE "api_notification" ADD CONSTRAINT "fk_api_notification_channel_id_1" FOREIGN KEY ("channel_id") REFERENCES "api_channel" ("id");

ALTER TABLE "api_notification" ADD CONSTRAINT "fk_api_notification_owner_id_2" FOREIGN KEY ("owner_id") REFERENCES "api_check" ("id");
