CREATE TABLE "user" (
  "id" INTEGER NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "password" VARCHAR(255) NOT NULL,
  "totp_uri" VARCHAR(255),
  "is_admin" INTEGER,
  "dashboard_visible_rows" VARCHAR(255),
  "dashboard_extended_rows" VARCHAR(255),
  "dashboard_order_rows" VARCHAR(255),
  "jellyfin_access_token" VARCHAR(255),
  "jellyfin_user_id" VARCHAR(255),
  "jellyfin_server_url" VARCHAR(255),
  "jellyfin_sync_enabled" INTEGER,
  "privacy_level" INTEGER,
  "date_format_id" INTEGER,
  "trakt_user_name" VARCHAR(255),
  "plex_webhook_uuid" VARCHAR(255),
  "jellyfin_webhook_uuid" VARCHAR(255),
  "emby_webhook_uuid" VARCHAR(255),
  "kodi_webhook_uuid" VARCHAR(255),
  "trakt_client_id" VARCHAR(255),
  "plex_client_id" VARCHAR(255),
  "plex_client_temporary_code" VARCHAR(255),
  "plex_access_token" VARCHAR(255),
  "plex_account_id" VARCHAR(255),
  "plex_server_url" VARCHAR(255),
  "jellyfin_scrobble_views" INTEGER,
  "emby_scrobble_views" INTEGER,
  "kodi_scrobble_views" INTEGER,
  "plex_scrobble_views" INTEGER,
  "plex_scrobble_ratings" INTEGER,
  "radarr_feed_uuid" VARCHAR(255),
  "watchlist_automatic_removal_enabled" INTEGER,
  "country" VARCHAR(255),
  "display_character_names" INTEGER,
  "locations_enabled" INTEGER,
  "core_account_changes_disabled" INTEGER,
  "display_tmdb_rating" INTEGER,
  "display_imdb_rating" INTEGER,
  "mastodon_enabled" INTEGER,
  "mastodon_username" VARCHAR(255),
  "mastodon_access_token" VARCHAR(255),
  "mastodon_post_visibility" VARCHAR(255),
  "mastodon_post_automatic" INTEGER,
  "created_at" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("email"),
  UNIQUE ("name")
);

CREATE TABLE "user_auth_token" (
  "id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "device_name" VARCHAR(255) NOT NULL,
  "user_agent" TEXT NOT NULL,
  "expiration_date" VARCHAR(255) NOT NULL,
  "created_at" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("user_id") REFERENCES "user" ("id")
);

CREATE TABLE "location" (
  "id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "is_cinema" INTEGER,
  "created_at" VARCHAR(255) NOT NULL,
  "updated_at" VARCHAR(255),
  PRIMARY KEY ("id"),
  FOREIGN KEY ("user_id") REFERENCES "user" ("id")
);

CREATE TABLE "movie_user_watch_dates" (
  "movie_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "watched_at" VARCHAR(255) NOT NULL,
  "plays" INTEGER,
  "comment" TEXT,
  "position" INTEGER NOT NULL,
  "location_id" INTEGER,
  FOREIGN KEY ("user_id") REFERENCES "user" ("id"),
  FOREIGN KEY ("location_id") REFERENCES "location" ("id")
);

CREATE TABLE "country" (
  "iso_3166_1" VARCHAR(255) NOT NULL,
  "english_name" VARCHAR(255) NOT NULL,
  "created_at" VARCHAR(255) NOT NULL,
  "updated_at" VARCHAR(255),
  PRIMARY KEY ("iso_3166_1")
);

CREATE TABLE "movie_production_countries" (
  "movie_id" VARCHAR(255) NOT NULL,
  "iso_3166_1" VARCHAR(255) NOT NULL,
  "position" INTEGER NOT NULL,
  "created_at" VARCHAR(255) NOT NULL,
  FOREIGN KEY ("iso_3166_1") REFERENCES "country" ("iso_3166_1")
);

CREATE INDEX "idx_country_english_name" ON "country" ("english_name");
CREATE INDEX "idx_user_created_at" ON "user" ("created_at");
CREATE INDEX "idx_user_privacy_name" ON "user" ("privacy_level", "name");
CREATE INDEX "idx_movie_watch_movie_user" ON "movie_user_watch_dates" ("movie_id", "user_id");
CREATE INDEX "idx_user_auth_token_token" ON "user_auth_token" ("token");
