CREATE TABLE "administrator" (
  "adminId" INTEGER NOT NULL,
  "fullname" VARCHAR(100),
  "password" VARCHAR(100) NOT NULL,
  "email" VARCHAR(30) NOT NULL,
  "phone" VARCHAR(25),
  PRIMARY KEY ("adminId"),
  UNIQUE ("email")
);

CREATE TABLE "booking" (
  "id" INTEGER NOT NULL,
  "cid" INTEGER NOT NULL,
  "status" VARCHAR(100),
  "notes" VARCHAR(500),
  PRIMARY KEY ("id")
);

CREATE TABLE "customer" (
  "cid" INTEGER NOT NULL,
  "fullname" VARCHAR(100) NOT NULL,
  "email" VARCHAR(50) NOT NULL,
  "password" VARCHAR(150) NOT NULL,
  "phone" VARCHAR(25) NOT NULL,
  "isadmin" INTEGER NOT NULL,
  PRIMARY KEY ("cid")
);

CREATE TABLE "pricing" (
  "pricing_id" INTEGER NOT NULL,
  "booking_id" INTEGER NOT NULL,
  "nights" INTEGER NOT NULL,
  "total_price" DOUBLE PRECISION NOT NULL,
  "booked_date" DATE NOT NULL,
  PRIMARY KEY ("pricing_id")
);

CREATE TABLE "reservation" (
  "id" INTEGER NOT NULL,
  "start" VARCHAR(30) NOT NULL,
  "end" VARCHAR(30) NOT NULL,
  "type" VARCHAR(100) NOT NULL,
  "requirement" VARCHAR(100),
  "adults" INTEGER NOT NULL,
  "children" INTEGER,
  "requests" VARCHAR(500),
  "timestamp" TIMESTAMP NOT NULL,
  "hash" VARCHAR(100),
  PRIMARY KEY ("id")
);

ALTER TABLE "booking" ADD CONSTRAINT "fk_booking_cid_1" FOREIGN KEY ("cid") REFERENCES "customer" ("cid");

ALTER TABLE "pricing" ADD CONSTRAINT "fk_pricing_booking_id_1" FOREIGN KEY ("booking_id") REFERENCES "booking" ("id");

ALTER TABLE "reservation" ADD CONSTRAINT "fk_reservation_id_1" FOREIGN KEY ("id") REFERENCES "booking" ("id");

CREATE INDEX "idx_customer_email" ON "customer" ("email");
CREATE INDEX "idx_booking_customer" ON "booking" ("cid", "id");
CREATE INDEX "idx_booking_status" ON "booking" ("status");
CREATE INDEX "idx_pricing_booking" ON "pricing" ("booking_id");
