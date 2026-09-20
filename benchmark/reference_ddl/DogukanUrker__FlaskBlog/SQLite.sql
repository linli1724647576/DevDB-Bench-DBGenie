CREATE TABLE "posts" (
  "id" INTEGER NOT NULL,
  "title" TEXT NOT NULL,
  "tags" TEXT NOT NULL,
  "content" TEXT NOT NULL,
  "banner" BLOB NOT NULL,
  "author" TEXT NOT NULL,
  "views" INTEGER,
  "time_stamp" INTEGER,
  "last_edit_time_stamp" INTEGER,
  "category" TEXT NOT NULL,
  "url_id" TEXT NOT NULL,
  "abstract" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "users" (
  "user_id" INTEGER NOT NULL,
  "username" TEXT NOT NULL,
  "email" TEXT NOT NULL,
  "password" TEXT NOT NULL,
  "profile_picture" TEXT,
  "role" TEXT,
  "points" INTEGER,
  "time_stamp" INTEGER,
  "is_verified" TEXT,
  PRIMARY KEY ("user_id"),
  UNIQUE ("username"),
  UNIQUE ("email")
);

CREATE TABLE "comments" (
  "id" INTEGER NOT NULL,
  "post_id" INTEGER,
  "comment" TEXT,
  "username" TEXT,
  "time_stamp" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("post_id") REFERENCES "posts" ("id")
);

CREATE INDEX "idx_posts_author_time_stamp" ON "posts" ("author", "time_stamp" DESC);
CREATE INDEX "idx_posts_time_stamp" ON "posts" ("time_stamp" DESC);
CREATE INDEX "idx_comments_post_time_stamp" ON "comments" ("post_id", "time_stamp" DESC);
CREATE INDEX "idx_comments_username_time_stamp" ON "comments" ("username", "time_stamp" DESC);
