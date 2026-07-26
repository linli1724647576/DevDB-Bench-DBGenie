CREATE TABLE "actions" (
  "id" BIGINT NOT NULL,
  "action_type" VARCHAR(255) NOT NULL,
  "action_option" VARCHAR(255),
  "target_type" VARCHAR(255),
  "target_id" INTEGER,
  "user_type" VARCHAR(255),
  "user_id" INTEGER,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "authorizations" (
  "id" BIGINT NOT NULL,
  "provider" VARCHAR(255) NOT NULL,
  "uid" VARCHAR(255) NOT NULL,
  "user_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "comments" (
  "id" BIGINT NOT NULL,
  "body" TEXT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "commentable_type" VARCHAR(255),
  "commentable_id" INTEGER,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "counters" (
  "id" BIGINT NOT NULL,
  "countable_type" VARCHAR(255),
  "countable_id" BIGINT,
  "key" VARCHAR(255) NOT NULL,
  "value" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("countable_type", "countable_id", "key")
);

CREATE TABLE "devices" (
  "id" BIGINT NOT NULL,
  "platform" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "last_actived_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "exception_tracks" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255),
  "body" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "locations" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "users_count" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "nodes" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "summary" VARCHAR(255),
  "sort" INTEGER NOT NULL,
  "topics_count" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "notes" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "body" TEXT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "word_count" INTEGER NOT NULL,
  "changes_count" INTEGER NOT NULL,
  "publish" BOOLEAN,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "notifications" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "actor_id" INTEGER,
  "notify_type" VARCHAR(255) NOT NULL,
  "target_type" VARCHAR(255),
  "target_id" INTEGER,
  "second_target_type" VARCHAR(255),
  "second_target_id" INTEGER,
  "third_target_type" VARCHAR(255),
  "third_target_id" INTEGER,
  "read_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "oauth_access_grants" (
  "id" BIGINT NOT NULL,
  "resource_owner_id" INTEGER NOT NULL,
  "application_id" INTEGER NOT NULL,
  "token" VARCHAR(255) NOT NULL,
  "expires_in" BIGINT,
  "redirect_uri" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "revoked_at" TIMESTAMP,
  "scopes" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("token")
);

CREATE TABLE "oauth_access_tokens" (
  "id" BIGINT NOT NULL,
  "resource_owner_id" INTEGER,
  "application_id" INTEGER,
  "token" VARCHAR(255) NOT NULL,
  "refresh_token" VARCHAR(255),
  "expires_in" BIGINT,
  "revoked_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "scopes" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("refresh_token"),
  UNIQUE ("token")
);

CREATE TABLE "oauth_applications" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "uid" VARCHAR(255) NOT NULL,
  "secret" VARCHAR(255) NOT NULL,
  "redirect_uri" TEXT NOT NULL,
  "scopes" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  "owner_id" INTEGER,
  "owner_type" VARCHAR(255),
  "level" INTEGER NOT NULL,
  "confidential" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uid")
);

CREATE TABLE "page_versions" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "version" INTEGER NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "desc" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "photos" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER,
  "image" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "profiles" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "contacts" JSONB NOT NULL,
  "rewards" JSONB NOT NULL,
  "preferences" JSONB NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id")
);

CREATE TABLE "replies" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "topic_id" INTEGER NOT NULL,
  "body" TEXT NOT NULL,
  "state" INTEGER NOT NULL,
  "likes_count" INTEGER,
  "mentioned_user_ids" JSONB,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  "action" VARCHAR(255),
  "target_type" VARCHAR(255),
  "target_id" VARCHAR(255),
  "reply_to_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "search_documents" (
  "id" BIGINT NOT NULL,
  "searchable_type" VARCHAR(255) NOT NULL,
  "searchable_id" INTEGER NOT NULL,
  "tokens" TSVECTOR,
  "content" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("searchable_type", "searchable_id")
);

CREATE TABLE "settings" (
  "id" BIGINT NOT NULL,
  "var" VARCHAR(255) NOT NULL,
  "value" TEXT,
  "thing_id" INTEGER,
  "thing_type" VARCHAR(255),
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("thing_type", "thing_id", "var")
);

CREATE TABLE "team_users" (
  "id" BIGINT NOT NULL,
  "team_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "role" INTEGER,
  "status" INTEGER,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "topics" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "node_id" INTEGER NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "body" TEXT NOT NULL,
  "last_reply_id" INTEGER,
  "last_reply_user_id" INTEGER,
  "last_reply_user_login" VARCHAR(255),
  "who_deleted" VARCHAR(255),
  "last_active_mark" INTEGER,
  "lock_node" BOOLEAN,
  "suggested_at" TIMESTAMP,
  "grade" INTEGER,
  "replied_at" TIMESTAMP,
  "replies_count" INTEGER NOT NULL,
  "likes_count" INTEGER,
  "mentioned_user_ids" JSONB,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  "closed_at" TIMESTAMP,
  "team_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "user_ssos" (
  "id" BIGINT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "uid" VARCHAR(255) NOT NULL,
  "username" VARCHAR(255),
  "email" VARCHAR(255),
  "name" VARCHAR(255),
  "avatar_url" VARCHAR(255),
  "last_payload" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uid")
);

CREATE TABLE "users" (
  "id" BIGINT NOT NULL,
  "login" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255),
  "email" VARCHAR(255) NOT NULL,
  "email_md5" VARCHAR(255) NOT NULL,
  "email_public" BOOLEAN NOT NULL,
  "location" VARCHAR(255),
  "location_id" INTEGER,
  "bio" VARCHAR(255),
  "website" VARCHAR(255),
  "company" VARCHAR(255),
  "github" VARCHAR(255),
  "twitter" VARCHAR(255),
  "avatar" VARCHAR(255),
  "state" INTEGER NOT NULL,
  "tagline" VARCHAR(255),
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  "encrypted_password" VARCHAR(255) NOT NULL,
  "reset_password_token" VARCHAR(255),
  "reset_password_sent_at" TIMESTAMP,
  "remember_created_at" TIMESTAMP,
  "sign_in_count" INTEGER NOT NULL,
  "current_sign_in_at" TIMESTAMP,
  "last_sign_in_at" TIMESTAMP,
  "current_sign_in_ip" VARCHAR(255),
  "last_sign_in_ip" VARCHAR(255),
  "password_salt" VARCHAR(255) NOT NULL,
  "persistence_token" VARCHAR(255) NOT NULL,
  "single_access_token" VARCHAR(255) NOT NULL,
  "perishable_token" VARCHAR(255) NOT NULL,
  "topics_count" INTEGER NOT NULL,
  "replies_count" INTEGER NOT NULL,
  "type" VARCHAR(255),
  "failed_attempts" INTEGER NOT NULL,
  "unlock_token" VARCHAR(255),
  "locked_at" TIMESTAMP,
  "team_users_count" INTEGER,
  "followers_count" INTEGER,
  "following_count" INTEGER,
  "confirmation_token" VARCHAR(255),
  "confirmed_at" TIMESTAMP,
  "confirmation_sent_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("confirmation_token"),
  UNIQUE ("email"),
  UNIQUE ("login"),
  UNIQUE ("unlock_token")
);

CREATE INDEX "idx_actions_target_type_target_id_action_type_1" ON "actions" ("target_type", "target_id", "action_type");

CREATE INDEX "idx_actions_user_type_user_id_action_type_2" ON "actions" ("user_type", "user_id", "action_type");

CREATE INDEX "idx_authorizations_provider_uid_1" ON "authorizations" ("provider", "uid");

CREATE INDEX "idx_comments_commentable_id_1" ON "comments" ("commentable_id");

CREATE INDEX "idx_comments_commentable_type_2" ON "comments" ("commentable_type");

CREATE INDEX "idx_comments_user_id_3" ON "comments" ("user_id");

CREATE UNIQUE INDEX "uidx_counters_countable_type_countable_id_key_1" ON "counters" ("countable_type", "countable_id", "key");

CREATE INDEX "idx_counters_countable_type_countable_id_2" ON "counters" ("countable_type", "countable_id");

CREATE INDEX "idx_counters_countable_type_key_value_3" ON "counters" ("countable_type", "key", "value");

CREATE INDEX "idx_devices_user_id_1" ON "devices" ("user_id");

CREATE INDEX "idx_locations_name_1" ON "locations" ("name");

CREATE INDEX "idx_nodes_sort_1" ON "nodes" ("sort");

CREATE INDEX "idx_notes_user_id_1" ON "notes" ("user_id");

CREATE INDEX "idx_notifications_user_id_1" ON "notifications" ("user_id");

CREATE UNIQUE INDEX "uidx_oauth_access_grants_token_1" ON "oauth_access_grants" ("token");

CREATE UNIQUE INDEX "uidx_oauth_access_tokens_refresh_token_1" ON "oauth_access_tokens" ("refresh_token");

CREATE INDEX "idx_oauth_access_tokens_resource_owner_id_2" ON "oauth_access_tokens" ("resource_owner_id");

CREATE UNIQUE INDEX "uidx_oauth_access_tokens_token_3" ON "oauth_access_tokens" ("token");

CREATE INDEX "idx_oauth_applications_owner_id_owner_type_1" ON "oauth_applications" ("owner_id", "owner_type");

CREATE UNIQUE INDEX "uidx_oauth_applications_uid_2" ON "oauth_applications" ("uid");

CREATE INDEX "idx_page_versions_page_id_1" ON "page_versions" ("page_id");

CREATE INDEX "idx_photos_user_id_1" ON "photos" ("user_id");

CREATE UNIQUE INDEX "uidx_profiles_user_id_1" ON "profiles" ("user_id");

CREATE INDEX "idx_replies_deleted_at_1" ON "replies" ("deleted_at");

CREATE INDEX "idx_replies_topic_id_2" ON "replies" ("topic_id");

CREATE INDEX "idx_replies_user_id_3" ON "replies" ("user_id");

CREATE UNIQUE INDEX "uidx_search_documents_searchable_type_searchable_id_1" ON "search_documents" ("searchable_type", "searchable_id");

CREATE INDEX "idx_search_documents_tokens_2" ON "search_documents" USING GIN ("tokens");

CREATE UNIQUE INDEX "uidx_settings_thing_type_thing_id_var_1" ON "settings" ("thing_type", "thing_id", "var");

CREATE INDEX "idx_team_users_team_id_1" ON "team_users" ("team_id");

CREATE INDEX "idx_team_users_user_id_2" ON "team_users" ("user_id");

CREATE INDEX "idx_topics_deleted_at_1" ON "topics" ("deleted_at");

CREATE INDEX "idx_topics_grade_2" ON "topics" ("grade");

CREATE INDEX "idx_topics_last_active_mark_3" ON "topics" ("last_active_mark");

CREATE INDEX "idx_topics_last_reply_id_4" ON "topics" ("last_reply_id");

CREATE INDEX "idx_topics_likes_count_5" ON "topics" ("likes_count");

CREATE INDEX "idx_topics_node_id_deleted_at_6" ON "topics" ("node_id", "deleted_at");

CREATE INDEX "idx_topics_suggested_at_7" ON "topics" ("suggested_at");

CREATE INDEX "idx_topics_team_id_8" ON "topics" ("team_id");

CREATE INDEX "idx_topics_user_id_9" ON "topics" ("user_id");

CREATE UNIQUE INDEX "uidx_user_ssos_uid_1" ON "user_ssos" ("uid");

CREATE UNIQUE INDEX "uidx_users_confirmation_token_1" ON "users" ("confirmation_token");

CREATE UNIQUE INDEX "uidx_users_email_2" ON "users" ("email");

CREATE INDEX "idx_users_location_3" ON "users" ("location");

CREATE UNIQUE INDEX "uidx_users_login_4" ON "users" ("login");

CREATE UNIQUE INDEX "uidx_users_unlock_token_5" ON "users" ("unlock_token");

CREATE INDEX "idx_users_lower((login)::text)varchar_pattern_ops_6" ON "users" (lower(("login")::text) varchar_pattern_ops);

CREATE INDEX "idx_users_lower((name)::text)varchar_pattern_ops_7" ON "users" (lower(("name")::text) varchar_pattern_ops);
