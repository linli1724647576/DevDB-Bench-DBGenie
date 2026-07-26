CREATE TABLE "Supplier" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "active" BOOLEAN NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("slug")
);

CREATE TABLE "Tax" (
  "id" INTEGER NOT NULL,
  "rate" DOUBLE PRECISION NOT NULL,
  "description" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "Voucher" (
  "id" INTEGER NOT NULL,
  "number" VARCHAR(255) NOT NULL,
  "creation_date" TIMESTAMP NOT NULL,
  "start_date" DATE,
  "effective_from" DOUBLE PRECISION NOT NULL,
  "end_date" DATE,
  "kind_of" INTEGER NOT NULL,
  "value" DOUBLE PRECISION NOT NULL,
  "active" BOOLEAN NOT NULL,
  "used_amount" INTEGER NOT NULL,
  "last_used_date" TIMESTAMP,
  "limit" INTEGER,
  "creator_id" INTEGER,
  "group_id" INTEGER,
  "tax_id" INTEGER,
  "sums_up" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("number")
);

CREATE TABLE "VoucherGroup" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "creation_date" TIMESTAMP NOT NULL,
  "position" INTEGER NOT NULL,
  "creator_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "VoucherOptions" (
  "id" INTEGER NOT NULL,
  "number_prefix" VARCHAR(255) NOT NULL,
  "number_suffix" VARCHAR(255) NOT NULL,
  "number_length" INTEGER,
  "number_letters" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

ALTER TABLE "Voucher" ADD CONSTRAINT "fk_Voucher_group_id_1" FOREIGN KEY ("group_id") REFERENCES "VoucherGroup" ("id");

ALTER TABLE "Voucher" ADD CONSTRAINT "fk_Voucher_tax_id_2" FOREIGN KEY ("tax_id") REFERENCES "Tax" ("id");

CREATE INDEX "idx_Supplier_active" ON "Supplier" ("active");
CREATE INDEX "idx_Voucher_active_usage" ON "Voucher" ("active", "used_amount", "limit");
