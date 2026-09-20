CREATE TABLE "Media" (
  "id" INTEGER NOT NULL,
  "creation_date" TIMESTAMP NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "extension" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "Page" (
  "id" INTEGER NOT NULL,
  "uuid" CHAR(36) NOT NULL,
  "creation_date" TIMESTAMP NOT NULL,
  "publication_date" TIMESTAMP,
  "publication_end_date" TIMESTAMP,
  "last_modification_date" TIMESTAMP NOT NULL,
  "status" INTEGER NOT NULL,
  "template" VARCHAR(255),
  "delegate_to" VARCHAR(255),
  "freeze_date" TIMESTAMP,
  "redirect_to_url" VARCHAR(255),
  "lft" INTEGER NOT NULL,
  "rght" INTEGER NOT NULL,
  "tree_id" INTEGER NOT NULL,
  "level" INTEGER NOT NULL,
  "author_id" INTEGER NOT NULL,
  "parent_id" INTEGER,
  "redirect_to_id" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("parent_id") REFERENCES "Page" ("id"),
  FOREIGN KEY ("redirect_to_id") REFERENCES "Page" ("id")
);

CREATE TABLE "Content" (
  "id" INTEGER NOT NULL,
  "language" VARCHAR(255) NOT NULL,
  "body" TEXT NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "creation_date" TIMESTAMP NOT NULL,
  "page_id" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("page_id") REFERENCES "Page" ("id")
);

CREATE TABLE "PageAlias" (
  "id" INTEGER NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "page_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("url"),
  FOREIGN KEY ("page_id") REFERENCES "Page" ("id")
);

CREATE TABLE "Page_sites" (
  "id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "site_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("page_id", "site_id"),
  FOREIGN KEY ("page_id") REFERENCES "Page" ("id")
);

CREATE INDEX "idx_Page_lft_1" ON "Page" ("lft");

CREATE INDEX "idx_Page_rght_2" ON "Page" ("rght");

CREATE INDEX "idx_Page_tree_id_3" ON "Page" ("tree_id");

CREATE INDEX "idx_Page_level_4" ON "Page" ("level");

CREATE INDEX "idx_Content_type_1" ON "Content" ("type");
