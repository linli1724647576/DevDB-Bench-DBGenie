CREATE TABLE "vendor" (
  "id" INTEGER NOT NULL,
  "registered" TIMESTAMP NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "comment" VARCHAR(255),
  "empty_spool_weight" DOUBLE PRECISION,
  "external_id" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "filament" (
  "id" INTEGER NOT NULL,
  "registered" TIMESTAMP NOT NULL,
  "name" VARCHAR(255),
  "vendor_id" INTEGER,
  "material" VARCHAR(255),
  "price" DOUBLE PRECISION,
  "density" DOUBLE PRECISION NOT NULL,
  "diameter" DOUBLE PRECISION NOT NULL,
  "weight" DOUBLE PRECISION,
  "spool_weight" DOUBLE PRECISION,
  "article_number" VARCHAR(255),
  "comment" VARCHAR(255),
  "settings_extruder_temp" INTEGER,
  "settings_bed_temp" INTEGER,
  "color_hex" VARCHAR(255),
  "multi_color_hexes" VARCHAR(255),
  "multi_color_direction" VARCHAR(255),
  "external_id" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "spool" (
  "id" INTEGER NOT NULL,
  "registered" TIMESTAMP NOT NULL,
  "first_used" TIMESTAMP,
  "last_used" TIMESTAMP,
  "filament_id" INTEGER NOT NULL,
  "used_weight" DOUBLE PRECISION NOT NULL,
  "location" VARCHAR(255),
  "lot_nr" VARCHAR(255),
  "comment" VARCHAR(255),
  "archived" BOOLEAN,
  "price" DOUBLE PRECISION,
  "initial_weight" DOUBLE PRECISION,
  "spool_weight" DOUBLE PRECISION,
  PRIMARY KEY ("id")
);

CREATE TABLE "setting" (
  "key" VARCHAR(255) NOT NULL,
  "value" TEXT NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  PRIMARY KEY ("key")
);

CREATE TABLE "vendor_field" (
  "vendor_id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("vendor_id", "key")
);

CREATE TABLE "filament_field" (
  "filament_id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("filament_id", "key")
);

CREATE TABLE "spool_field" (
  "spool_id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("spool_id", "key")
);

CREATE INDEX "idx_vendor_id_1" ON "vendor" ("id");

CREATE INDEX "idx_filament_id_1" ON "filament" ("id");

CREATE INDEX "idx_spool_id_1" ON "spool" ("id");

CREATE INDEX "idx_setting_key_1" ON "setting" ("key");

CREATE INDEX "idx_vendor_field_key_1" ON "vendor_field" ("key");

CREATE INDEX "idx_vendor_field_vendor_id_2" ON "vendor_field" ("vendor_id");

CREATE INDEX "idx_filament_field_filament_id_1" ON "filament_field" ("filament_id");

CREATE INDEX "idx_filament_field_key_2" ON "filament_field" ("key");

CREATE INDEX "idx_spool_field_key_1" ON "spool_field" ("key");

CREATE INDEX "idx_spool_field_spool_id_2" ON "spool_field" ("spool_id");

ALTER TABLE "filament" ADD CONSTRAINT "fk_filament_vendor_id_1" FOREIGN KEY ("vendor_id") REFERENCES "vendor" ("id");

ALTER TABLE "spool" ADD CONSTRAINT "fk_spool_filament_id_1" FOREIGN KEY ("filament_id") REFERENCES "filament" ("id");

ALTER TABLE "vendor_field" ADD CONSTRAINT "fk_vendor_field_vendor_id_1" FOREIGN KEY ("vendor_id") REFERENCES "vendor" ("id");

ALTER TABLE "filament_field" ADD CONSTRAINT "fk_filament_field_filament_id_1" FOREIGN KEY ("filament_id") REFERENCES "filament" ("id");

ALTER TABLE "spool_field" ADD CONSTRAINT "fk_spool_field_spool_id_1" FOREIGN KEY ("spool_id") REFERENCES "spool" ("id");
