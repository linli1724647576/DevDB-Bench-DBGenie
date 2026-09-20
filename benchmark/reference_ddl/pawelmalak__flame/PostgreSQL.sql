CREATE TABLE "apps" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "icon" VARCHAR(255) NOT NULL,
  "isPinned" INTEGER,
  "isPublic" INTEGER,
  "description" VARCHAR(255) NOT NULL,
  "orderId" INTEGER,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "bookmarks" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "categoryId" INTEGER NOT NULL,
  "icon" VARCHAR(255),
  "isPublic" INTEGER,
  "orderId" INTEGER,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "categories" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "isPinned" INTEGER,
  "isPublic" INTEGER,
  "orderId" INTEGER,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "weather" (
  "id" INTEGER NOT NULL,
  "externalLastUpdate" VARCHAR(255),
  "tempC" DOUBLE PRECISION,
  "tempF" DOUBLE PRECISION,
  "isDay" INTEGER,
  "cloud" INTEGER,
  "conditionText" TEXT,
  "conditionCode" INTEGER,
  "humidity" INTEGER,
  "windK" DOUBLE PRECISION,
  "windM" DOUBLE PRECISION,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_categories_orderId" ON "categories" ("orderId");
CREATE INDEX "idx_bookmarks_category_order" ON "bookmarks" ("categoryId", "orderId");
CREATE INDEX "idx_apps_pinned_order" ON "apps" ("isPinned", "orderId");
CREATE INDEX "idx_weather_external_update" ON "weather" ("externalLastUpdate" DESC);
