CREATE TABLE "rotation_records" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "success" BOOLEAN NOT NULL,
  "error_message" TEXT,
  "featured_collections" TEXT NOT NULL,
  "group_contributions" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "collection_usage" (
  "id" INTEGER NOT NULL,
  "collection_name" VARCHAR(255) NOT NULL,
  "last_rotation_id" INTEGER,
  "last_rotated_at" TIMESTAMP,
  "times_used" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("collection_name")
);

CREATE TABLE "pending_simulations" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "selected_collections" TEXT NOT NULL,
  "rotation_snapshot" TEXT,
  "applied" BOOLEAN NOT NULL,
  "applied_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "trakt_missing_items" (
  "id" INTEGER NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "trakt_id" INTEGER,
  "slug" VARCHAR(255),
  "imdb_id" VARCHAR(255),
  "tmdb_id" INTEGER,
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "letterboxd_missing_items" (
  "id" INTEGER NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "slug" VARCHAR(255) NOT NULL,
  "letterboxd_url" VARCHAR(255),
  "tmdb_id" INTEGER,
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "mdblist_missing_items" (
  "id" INTEGER NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "imdb_id" VARCHAR(255),
  "tmdb_id" INTEGER,
  "trakt_id" INTEGER,
  "mdblist_id" VARCHAR(255),
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "tmdb_missing_items" (
  "id" INTEGER NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "tmdb_id" INTEGER,
  "media_type" VARCHAR(255),
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "anilist_missing_items" (
  "id" INTEGER NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "media_format" VARCHAR(255),
  "anilist_id" INTEGER,
  "mal_id" INTEGER,
  "tmdb_id" INTEGER,
  "imdb_id" VARCHAR(255),
  "tvdb_id" INTEGER,
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "mal_missing_items" (
  "id" INTEGER NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "media_type" VARCHAR(255),
  "mal_id" INTEGER,
  "anilist_id" INTEGER,
  "tmdb_id" INTEGER,
  "imdb_id" VARCHAR(255),
  "tvdb_id" INTEGER,
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "import_missing_items" (
  "id" INTEGER NOT NULL,
  "import_name" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "plex_collection" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "type" VARCHAR(255) NOT NULL,
  "imdb_id" VARCHAR(255),
  "tmdb_id" INTEGER,
  "tvdb_id" INTEGER,
  "parent_title" VARCHAR(255),
  "season_number" INTEGER,
  "episode_number" INTEGER,
  "first_seen" TIMESTAMP NOT NULL,
  "last_seen" TIMESTAMP NOT NULL,
  "times_seen" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "collection_analytics" (
  "id" INTEGER NOT NULL,
  "collection_name" VARCHAR(255) NOT NULL,
  "plex_library" VARCHAR(255) NOT NULL,
  "rating_key" INTEGER,
  "media_type" VARCHAR(255),
  "total_plays" INTEGER NOT NULL,
  "total_duration_seconds" INTEGER,
  "unique_users" INTEGER,
  "rotation_id" INTEGER,
  "collected_at" TIMESTAMP NOT NULL,
  "extra_data" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "pinned_collections" (
  "id" INTEGER NOT NULL,
  "collection_name" VARCHAR(255) NOT NULL,
  "library_name" VARCHAR(255) NOT NULL,
  "display_order" INTEGER NOT NULL,
  "pinned_at" TIMESTAMP NOT NULL,
  "visibility_home" BOOLEAN NOT NULL,
  "visibility_shared" BOOLEAN NOT NULL,
  "visibility_recommended" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("collection_name")
);

CREATE TABLE "source_sync_records" (
  "id" INTEGER NOT NULL,
  "integration_type" VARCHAR(255) NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "source_url" VARCHAR(255) NOT NULL,
  "sync_status" VARCHAR(255) NOT NULL,
  "last_sync_time" TIMESTAMP,
  "items_total" INTEGER NOT NULL,
  "items_matched" INTEGER NOT NULL,
  "error_message" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "users" (
  "id" INTEGER NOT NULL,
  "plex_id" INTEGER,
  "plex_username" VARCHAR(255),
  "plex_email" VARCHAR(255),
  "plex_thumb" VARCHAR(255),
  "role" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "password_hash" VARCHAR(255),
  "created_at" TIMESTAMP NOT NULL,
  "last_login_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("plex_id")
);

CREATE TABLE "collection_display_order" (
  "id" INTEGER NOT NULL,
  "collection_name" VARCHAR(255) NOT NULL,
  "display_order" INTEGER NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("collection_name")
);

CREATE TABLE "seerr_auto_requests" (
  "id" INTEGER NOT NULL,
  "tmdb_id" INTEGER NOT NULL,
  "media_type" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "year" INTEGER,
  "integration_type" VARCHAR(255) NOT NULL,
  "source_name" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "error_message" VARCHAR(255),
  "requested_at" TIMESTAMP NOT NULL,
  "downloaded_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_rotation_records_id_1" ON "rotation_records" ("id");

CREATE INDEX "idx_rotation_records_created_at_2" ON "rotation_records" ("created_at");

CREATE INDEX "idx_collection_usage_id_1" ON "collection_usage" ("id");

CREATE INDEX "idx_collection_usage_collection_name_2" ON "collection_usage" ("collection_name");

CREATE INDEX "idx_pending_simulations_id_1" ON "pending_simulations" ("id");

CREATE INDEX "idx_pending_simulations_created_at_2" ON "pending_simulations" ("created_at");

CREATE INDEX "idx_collection_analytics_id_1" ON "collection_analytics" ("id");

CREATE INDEX "idx_collection_analytics_collection_name_2" ON "collection_analytics" ("collection_name");

CREATE INDEX "idx_collection_analytics_media_type_3" ON "collection_analytics" ("media_type");

CREATE INDEX "idx_collection_analytics_rotation_id_4" ON "collection_analytics" ("rotation_id");

CREATE INDEX "idx_collection_analytics_collected_at_5" ON "collection_analytics" ("collected_at");

CREATE INDEX "idx_pinned_collections_id_1" ON "pinned_collections" ("id");

CREATE INDEX "idx_pinned_collections_collection_name_2" ON "pinned_collections" ("collection_name");

CREATE INDEX "idx_pinned_collections_display_order_3" ON "pinned_collections" ("display_order");

CREATE INDEX "idx_source_sync_records_id_1" ON "source_sync_records" ("id");

CREATE INDEX "idx_source_sync_records_integration_type_2" ON "source_sync_records" ("integration_type");

CREATE INDEX "idx_source_sync_records_source_name_3" ON "source_sync_records" ("source_name");

CREATE INDEX "idx_users_plex_id_1" ON "users" ("plex_id");

CREATE INDEX "idx_collection_display_order_id_1" ON "collection_display_order" ("id");

CREATE INDEX "idx_collection_display_order_collection_name_2" ON "collection_display_order" ("collection_name");

CREATE INDEX "idx_collection_display_order_display_order_3" ON "collection_display_order" ("display_order");

CREATE INDEX "idx_seerr_auto_requests_tmdb_id_1" ON "seerr_auto_requests" ("tmdb_id");
