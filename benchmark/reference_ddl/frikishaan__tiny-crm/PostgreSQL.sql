CREATE TABLE "accounts" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "phone" VARCHAR(255),
  "email" VARCHAR(255),
  "address" TEXT,
  "total_sales" DOUBLE PRECISION,
  "primary_contact_id" BIGINT,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "contacts" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "phone" VARCHAR(255),
  "account_id" BIGINT,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "leads" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "customer_id" BIGINT,
  "source" INTEGER,
  "estimated_revenue" DECIMAL(18, 2),
  "description" TEXT,
  "status" INTEGER NOT NULL,
  "disqualification_reason" INTEGER,
  "disqualification_description" TEXT,
  "date_disqualified" TIMESTAMP,
  "date_qualified" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "deals" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "customer_id" BIGINT,
  "lead_id" BIGINT,
  "estimated_revenue" DECIMAL(18, 2),
  "actual_revenue" DECIMAL(18, 2),
  "description" TEXT,
  "status" INTEGER NOT NULL,
  "date_won" TIMESTAMP,
  "date_lost" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "deal_products" (
  "id" BIGINT NOT NULL,
  "product_id" BIGINT NOT NULL,
  "deal_id" BIGINT NOT NULL,
  "quantity" INTEGER NOT NULL,
  "price_per_unit" DECIMAL(18, 2) NOT NULL,
  "total_amount" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "products" (
  "id" BIGINT NOT NULL,
  "product_id" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "type" INTEGER NOT NULL,
  "price" DECIMAL(18, 2) NOT NULL,
  "is_available" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("product_id")
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

CREATE TABLE "password_resets" (
  "email" VARCHAR(255) NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("email")
);

CREATE TABLE "personal_access_tokens" (
  "id" BIGINT NOT NULL,
  "tokenable_type" VARCHAR(255) NOT NULL,
  "tokenable_id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "abilities" TEXT,
  "last_used_at" TIMESTAMP,
  "expires_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("token")
);

CREATE INDEX "idx_leads_status_customer_id_1" ON "leads" ("status", "customer_id");

CREATE INDEX "idx_deals_status_customer_id_lead_id_1" ON "deals" ("status", "customer_id", "lead_id");

CREATE INDEX "idx_products_product_id_name_1" ON "products" ("product_id", "name");

CREATE INDEX "idx_jobs_queue_1" ON "jobs" ("queue");

CREATE INDEX "idx_personal_access_tokens_tokenable_type_tokenable_id_1" ON "personal_access_tokens" ("tokenable_type", "tokenable_id");

ALTER TABLE "accounts" ADD CONSTRAINT "fk_accounts_primary_contact_id_1" FOREIGN KEY ("primary_contact_id") REFERENCES "contacts" ("id");

ALTER TABLE "contacts" ADD CONSTRAINT "fk_contacts_account_id_1" FOREIGN KEY ("account_id") REFERENCES "accounts" ("id");

ALTER TABLE "leads" ADD CONSTRAINT "fk_leads_customer_id_1" FOREIGN KEY ("customer_id") REFERENCES "accounts" ("id");

ALTER TABLE "deals" ADD CONSTRAINT "fk_deals_customer_id_1" FOREIGN KEY ("customer_id") REFERENCES "accounts" ("id");

ALTER TABLE "deals" ADD CONSTRAINT "fk_deals_lead_id_2" FOREIGN KEY ("lead_id") REFERENCES "leads" ("id");

ALTER TABLE "deal_products" ADD CONSTRAINT "fk_deal_products_product_id_1" FOREIGN KEY ("product_id") REFERENCES "products" ("id");

ALTER TABLE "deal_products" ADD CONSTRAINT "fk_deal_products_deal_id_2" FOREIGN KEY ("deal_id") REFERENCES "deals" ("id");
