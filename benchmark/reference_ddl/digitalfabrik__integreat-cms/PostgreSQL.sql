CREATE TABLE "cms_user" (
  "id" BIGINT NOT NULL,
  "password" VARCHAR(255) NOT NULL,
  "last_login" TIMESTAMP,
  "username" VARCHAR(255) NOT NULL,
  "first_name" VARCHAR(255) NOT NULL,
  "last_name" VARCHAR(255) NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "date_joined" TIMESTAMP NOT NULL,
  "chat_last_visited" TIMESTAMP NOT NULL,
  "expert_mode" BOOLEAN NOT NULL,
  "organization_id" BIGINT,
  "totp_key" VARCHAR(255),
  "passwordless_authentication_enabled" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("username"),
  UNIQUE ("email")
);

CREATE TABLE "cms_directory" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "parent_id" BIGINT,
  "region_id" BIGINT,
  "is_hidden" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_event" (
  "id" BIGINT NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "archived" BOOLEAN NOT NULL,
  "start" TIMESTAMP NOT NULL,
  "end" TIMESTAMP NOT NULL,
  "icon_id" BIGINT,
  "location_id" BIGINT,
  "recurrence_rule_id" BIGINT,
  "region_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_feedback" (
  "id" BIGINT NOT NULL,
  "rating" BOOLEAN,
  "comment" TEXT NOT NULL,
  "is_technical" BOOLEAN NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "language_id" BIGINT NOT NULL,
  "read_by_id" BIGINT,
  "region_id" BIGINT NOT NULL,
  "archived" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_imprintpage" (
  "id" BIGINT NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "region_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_language" (
  "id" BIGINT NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "bcp47_tag" VARCHAR(255) NOT NULL,
  "native_name" VARCHAR(255) NOT NULL,
  "english_name" VARCHAR(255) NOT NULL,
  "text_direction" VARCHAR(255) NOT NULL,
  "primary_country_code" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("slug"),
  UNIQUE ("bcp47_tag")
);

CREATE TABLE "cms_mediafile" (
  "id" BIGINT NOT NULL,
  "file" VARCHAR(255) NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "alt_text" VARCHAR(255),
  "uploaded_date" TIMESTAMP NOT NULL,
  "parent_directory_id" BIGINT,
  "region_id" BIGINT,
  "is_hidden" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_offertemplate" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "supported_by_app_in_content" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("slug")
);

CREATE TABLE "cms_organization" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  "icon_id" BIGINT NOT NULL,
  "region_id" BIGINT NOT NULL,
  "website" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("slug")
);

CREATE TABLE "cms_page" (
  "id" BIGINT NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "explicitly_archived" BOOLEAN NOT NULL,
  "lft" INTEGER NOT NULL,
  "rgt" INTEGER NOT NULL,
  "tree_id" INTEGER NOT NULL,
  "depth" INTEGER NOT NULL,
  "icon_id" BIGINT,
  "mirrored_page_id" BIGINT,
  "organization_id" BIGINT,
  "parent_id" BIGINT,
  "region_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_poi" (
  "id" BIGINT NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "address" VARCHAR(255) NOT NULL,
  "postcode" VARCHAR(255) NOT NULL,
  "city" VARCHAR(255) NOT NULL,
  "country" VARCHAR(255) NOT NULL,
  "latitude" DOUBLE PRECISION,
  "longitude" DOUBLE PRECISION,
  "archived" BOOLEAN NOT NULL,
  "email" VARCHAR(255),
  "phone_number" VARCHAR(255),
  "website" VARCHAR(255),
  "opening_hours" JSONB NOT NULL,
  "icon_id" BIGINT,
  "category_id" BIGINT NOT NULL,
  "organization_id" BIGINT,
  "region_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_recurrencerule" (
  "id" BIGINT NOT NULL,
  "frequency" VARCHAR(255) NOT NULL,
  "interval" INTEGER NOT NULL,
  "weekdays_for_weekly" JSONB,
  "weekday_for_monthly" INTEGER,
  "recurrence_end_date" DATE,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_role" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "staff_role" BOOLEAN NOT NULL,
  "group_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_region" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "administrative_division" VARCHAR(255) NOT NULL,
  "events_enabled" BOOLEAN NOT NULL,
  "push_notifications_enabled" BOOLEAN NOT NULL,
  "latitude" DOUBLE PRECISION,
  "longitude" DOUBLE PRECISION,
  "created_date" TIMESTAMP NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  "page_permissions_enabled" BOOLEAN NOT NULL,
  "chat_enabled" BOOLEAN NOT NULL,
  "external_news_enabled" BOOLEAN NOT NULL,
  "timezone" VARCHAR(255) NOT NULL,
  "locations_enabled" BOOLEAN NOT NULL,
  "seo_enabled" BOOLEAN NOT NULL,
  "machine_translate_events" INTEGER NOT NULL,
  "machine_translate_pages" INTEGER NOT NULL,
  "machine_translate_pois" INTEGER NOT NULL,
  "term_explanations_enabled" BOOLEAN NOT NULL,
  "machine_translate_pushnotifications" INTEGER NOT NULL,
  "icon_id" BIGINT,
  PRIMARY KEY ("id"),
  UNIQUE ("slug")
);

CREATE TABLE "cms_pushnotification" (
  "id" BIGINT NOT NULL,
  "channel" VARCHAR(255) NOT NULL,
  "sent_date" TIMESTAMP,
  "created_date" TIMESTAMP NOT NULL,
  "mode" VARCHAR(255) NOT NULL,
  "scheduled_send_date" TIMESTAMP,
  "do_not_translate_title" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_poitranslation" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "content" TEXT,
  "version" INTEGER NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  "automatic_translation" BOOLEAN NOT NULL,
  "creator_id" BIGINT,
  "language_id" BIGINT NOT NULL,
  "poi_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("poi_id", "language_id", "version")
);

CREATE TABLE "cms_pagetranslation" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "content" TEXT,
  "version" INTEGER NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  "automatic_translation" BOOLEAN NOT NULL,
  "creator_id" BIGINT,
  "language_id" BIGINT NOT NULL,
  "page_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("page_id", "language_id", "version")
);

CREATE TABLE "cms_imprintpagetranslation" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "content" TEXT,
  "version" INTEGER NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  "automatic_translation" BOOLEAN NOT NULL,
  "creator_id" BIGINT,
  "language_id" BIGINT NOT NULL,
  "page_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("page_id", "language_id", "version")
);

CREATE TABLE "cms_eventtranslation" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "content" TEXT,
  "version" INTEGER NOT NULL,
  "last_updated" TIMESTAMP NOT NULL,
  "automatic_translation" BOOLEAN NOT NULL,
  "creator_id" BIGINT,
  "event_id" BIGINT NOT NULL,
  "language_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("event_id", "language_id", "version")
);

CREATE TABLE "cms_chatmessage" (
  "id" BIGINT NOT NULL,
  "text" TEXT NOT NULL,
  "sent_datetime" TIMESTAMP NOT NULL,
  "sender_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_fidokey" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "key_id" BYTEA NOT NULL,
  "public_key" BYTEA NOT NULL,
  "sign_count" INTEGER NOT NULL,
  "last_usage" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "user_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id", "name")
);

CREATE TABLE "cms_pushnotificationtranslation" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "text" TEXT,
  "last_updated" TIMESTAMP NOT NULL,
  "automatic_translation" BOOLEAN NOT NULL,
  "language_id" BIGINT NOT NULL,
  "push_notification_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("push_notification_id", "language_id")
);

CREATE TABLE "cms_languagetreenode" (
  "id" BIGINT NOT NULL,
  "lft" INTEGER NOT NULL,
  "rgt" INTEGER NOT NULL,
  "tree_id" INTEGER NOT NULL,
  "depth" INTEGER NOT NULL,
  "visible" BOOLEAN NOT NULL,
  "active" BOOLEAN NOT NULL,
  "language_id" BIGINT NOT NULL,
  "parent_id" BIGINT,
  "region_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("language_id", "region_id")
);

CREATE TABLE "cms_poicategory" (
  "id" BIGINT NOT NULL,
  "color" VARCHAR(255),
  "icon" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_poicategorytranslation" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "category_id" BIGINT NOT NULL,
  "language_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_searchresultfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  "search_query" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_poifeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  "poi_translation_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_pagefeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  "page_translation_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_offerfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  "offer_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_eventfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  "event_translation_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_eventlistfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_imprintpagefeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_mapfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_offerlistfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_regionfeedback" (
  "feedback_ptr_id" BIGINT NOT NULL,
  PRIMARY KEY ("feedback_ptr_id")
);

CREATE TABLE "cms_userchat" (
  "id" BIGINT NOT NULL,
  "created_timestamp" TIMESTAMP NOT NULL,
  "last_message_timestamp" TIMESTAMP NOT NULL,
  "total_words_generated" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "cms_contact" (
  "id" BIGINT NOT NULL,
  "phone_number" VARCHAR(255),
  "mobile_phone_number" VARCHAR(255),
  "opening_hours" JSONB,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_cms_page_lft_1" ON "cms_page" ("lft");

CREATE INDEX "idx_cms_page_rgt_2" ON "cms_page" ("rgt");

CREATE INDEX "idx_cms_page_tree_id_3" ON "cms_page" ("tree_id");

CREATE INDEX "idx_cms_page_depth_4" ON "cms_page" ("depth");

CREATE INDEX "idx_cms_languagetreenode_lft_1" ON "cms_languagetreenode" ("lft");

CREATE INDEX "idx_cms_languagetreenode_rgt_2" ON "cms_languagetreenode" ("rgt");

CREATE INDEX "idx_cms_languagetreenode_tree_id_3" ON "cms_languagetreenode" ("tree_id");

CREATE INDEX "idx_cms_languagetreenode_depth_4" ON "cms_languagetreenode" ("depth");

CREATE INDEX "idx_cms_user_organization" ON "cms_user" ("organization_id");
CREATE INDEX "idx_cms_directory_region_parent" ON "cms_directory" ("region_id", "parent_id");
CREATE INDEX "idx_cms_event_region_start" ON "cms_event" ("region_id", "start");
CREATE INDEX "idx_cms_event_region_archived" ON "cms_event" ("region_id", "archived");
CREATE INDEX "idx_cms_feedback_region_created" ON "cms_feedback" ("region_id", "created_date");
CREATE INDEX "idx_cms_feedback_review" ON "cms_feedback" ("archived", "read_by_id");
CREATE INDEX "idx_cms_imprintpage_region" ON "cms_imprintpage" ("region_id");
CREATE INDEX "idx_cms_mediafile_region" ON "cms_mediafile" ("region_id");
CREATE INDEX "idx_cms_mediafile_directory" ON "cms_mediafile" ("parent_directory_id");
CREATE INDEX "idx_cms_organization_region" ON "cms_organization" ("region_id");
CREATE INDEX "idx_cms_page_region_archived" ON "cms_page" ("region_id", "explicitly_archived");
CREATE INDEX "idx_cms_page_parent" ON "cms_page" ("parent_id");
CREATE INDEX "idx_cms_page_organization" ON "cms_page" ("organization_id");
CREATE INDEX "idx_cms_poi_region_archived" ON "cms_poi" ("region_id", "archived");
CREATE INDEX "idx_cms_poi_category" ON "cms_poi" ("category_id");
CREATE INDEX "idx_cms_poi_organization" ON "cms_poi" ("organization_id");
CREATE INDEX "idx_cms_poitranslation_lookup" ON "cms_poitranslation" ("poi_id", "language_id", "status");
CREATE INDEX "idx_cms_pagetranslation_lookup" ON "cms_pagetranslation" ("page_id", "language_id", "status");
CREATE INDEX "idx_cms_imprinttranslation_lookup" ON "cms_imprintpagetranslation" ("page_id", "language_id", "status");
CREATE INDEX "idx_cms_eventtranslation_lookup" ON "cms_eventtranslation" ("event_id", "language_id", "status");
CREATE INDEX "idx_cms_pushnotification_schedule" ON "cms_pushnotification" ("scheduled_send_date", "sent_date");
CREATE INDEX "idx_cms_pushtranslation_language" ON "cms_pushnotificationtranslation" ("language_id", "push_notification_id");
CREATE INDEX "idx_cms_languagetree_region_active" ON "cms_languagetreenode" ("region_id", "active", "visible");
CREATE INDEX "idx_cms_languagetree_parent" ON "cms_languagetreenode" ("parent_id");
CREATE INDEX "idx_cms_poicategorytranslation_language" ON "cms_poicategorytranslation" ("language_id", "category_id");
CREATE INDEX "idx_cms_chatmessage_sender_created" ON "cms_chatmessage" ("sender_id", "sent_datetime");
CREATE INDEX "idx_cms_fidokey_user" ON "cms_fidokey" ("user_id");
CREATE INDEX "idx_cms_poifeedback_translation" ON "cms_poifeedback" ("poi_translation_id");
CREATE INDEX "idx_cms_pagefeedback_translation" ON "cms_pagefeedback" ("page_translation_id");
CREATE INDEX "idx_cms_eventfeedback_translation" ON "cms_eventfeedback" ("event_translation_id");
CREATE INDEX "idx_cms_region_slug" ON "cms_region" ("slug");

ALTER TABLE "cms_user" ADD CONSTRAINT "fk_cms_user_organization_id_1" FOREIGN KEY ("organization_id") REFERENCES "cms_organization" ("id");

ALTER TABLE "cms_directory" ADD CONSTRAINT "fk_cms_directory_parent_id_1" FOREIGN KEY ("parent_id") REFERENCES "cms_directory" ("id");

ALTER TABLE "cms_directory" ADD CONSTRAINT "fk_cms_directory_region_id_2" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_event" ADD CONSTRAINT "fk_cms_event_icon_id_1" FOREIGN KEY ("icon_id") REFERENCES "cms_mediafile" ("id");

ALTER TABLE "cms_event" ADD CONSTRAINT "fk_cms_event_location_id_2" FOREIGN KEY ("location_id") REFERENCES "cms_poi" ("id");

ALTER TABLE "cms_event" ADD CONSTRAINT "fk_cms_event_recurrence_rule_id_3" FOREIGN KEY ("recurrence_rule_id") REFERENCES "cms_recurrencerule" ("id");

ALTER TABLE "cms_event" ADD CONSTRAINT "fk_cms_event_region_id_4" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_feedback" ADD CONSTRAINT "fk_cms_feedback_language_id_1" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_feedback" ADD CONSTRAINT "fk_cms_feedback_read_by_id_2" FOREIGN KEY ("read_by_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_feedback" ADD CONSTRAINT "fk_cms_feedback_region_id_3" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_imprintpage" ADD CONSTRAINT "fk_cms_imprintpage_region_id_1" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_mediafile" ADD CONSTRAINT "fk_cms_mediafile_parent_directory_id_1" FOREIGN KEY ("parent_directory_id") REFERENCES "cms_directory" ("id");

ALTER TABLE "cms_mediafile" ADD CONSTRAINT "fk_cms_mediafile_region_id_2" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_organization" ADD CONSTRAINT "fk_cms_organization_icon_id_1" FOREIGN KEY ("icon_id") REFERENCES "cms_mediafile" ("id");

ALTER TABLE "cms_organization" ADD CONSTRAINT "fk_cms_organization_region_id_2" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_page" ADD CONSTRAINT "fk_cms_page_icon_id_1" FOREIGN KEY ("icon_id") REFERENCES "cms_mediafile" ("id");

ALTER TABLE "cms_page" ADD CONSTRAINT "fk_cms_page_mirrored_page_id_2" FOREIGN KEY ("mirrored_page_id") REFERENCES "cms_page" ("id");

ALTER TABLE "cms_page" ADD CONSTRAINT "fk_cms_page_organization_id_3" FOREIGN KEY ("organization_id") REFERENCES "cms_organization" ("id");

ALTER TABLE "cms_page" ADD CONSTRAINT "fk_cms_page_parent_id_4" FOREIGN KEY ("parent_id") REFERENCES "cms_page" ("id");

ALTER TABLE "cms_page" ADD CONSTRAINT "fk_cms_page_region_id_5" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_poi" ADD CONSTRAINT "fk_cms_poi_icon_id_1" FOREIGN KEY ("icon_id") REFERENCES "cms_mediafile" ("id");

ALTER TABLE "cms_poi" ADD CONSTRAINT "fk_cms_poi_category_id_2" FOREIGN KEY ("category_id") REFERENCES "cms_poicategory" ("id");

ALTER TABLE "cms_poi" ADD CONSTRAINT "fk_cms_poi_organization_id_3" FOREIGN KEY ("organization_id") REFERENCES "cms_organization" ("id");

ALTER TABLE "cms_poi" ADD CONSTRAINT "fk_cms_poi_region_id_4" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_region" ADD CONSTRAINT "fk_cms_region_icon_id_1" FOREIGN KEY ("icon_id") REFERENCES "cms_mediafile" ("id");

ALTER TABLE "cms_poitranslation" ADD CONSTRAINT "fk_cms_poitranslation_creator_id_1" FOREIGN KEY ("creator_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_poitranslation" ADD CONSTRAINT "fk_cms_poitranslation_language_id_2" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_poitranslation" ADD CONSTRAINT "fk_cms_poitranslation_poi_id_3" FOREIGN KEY ("poi_id") REFERENCES "cms_poi" ("id");

ALTER TABLE "cms_pagetranslation" ADD CONSTRAINT "fk_cms_pagetranslation_creator_id_1" FOREIGN KEY ("creator_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_pagetranslation" ADD CONSTRAINT "fk_cms_pagetranslation_language_id_2" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_pagetranslation" ADD CONSTRAINT "fk_cms_pagetranslation_page_id_3" FOREIGN KEY ("page_id") REFERENCES "cms_page" ("id");

ALTER TABLE "cms_imprintpagetranslation" ADD CONSTRAINT "fk_cms_imprintpagetranslation_creator_id_1" FOREIGN KEY ("creator_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_imprintpagetranslation" ADD CONSTRAINT "fk_cms_imprintpagetranslation_language_id_2" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_imprintpagetranslation" ADD CONSTRAINT "fk_cms_imprintpagetranslation_page_id_3" FOREIGN KEY ("page_id") REFERENCES "cms_imprintpage" ("id");

ALTER TABLE "cms_eventtranslation" ADD CONSTRAINT "fk_cms_eventtranslation_creator_id_1" FOREIGN KEY ("creator_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_eventtranslation" ADD CONSTRAINT "fk_cms_eventtranslation_event_id_2" FOREIGN KEY ("event_id") REFERENCES "cms_event" ("id");

ALTER TABLE "cms_eventtranslation" ADD CONSTRAINT "fk_cms_eventtranslation_language_id_3" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_chatmessage" ADD CONSTRAINT "fk_cms_chatmessage_sender_id_1" FOREIGN KEY ("sender_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_fidokey" ADD CONSTRAINT "fk_cms_fidokey_user_id_1" FOREIGN KEY ("user_id") REFERENCES "cms_user" ("id");

ALTER TABLE "cms_pushnotificationtranslation" ADD CONSTRAINT "fk_cms_pushnotificationtranslation_language_id_1" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_pushnotificationtranslation" ADD CONSTRAINT "fk_cms_pushnotificationtranslation_push_notification_id_2" FOREIGN KEY ("push_notification_id") REFERENCES "cms_pushnotification" ("id");

ALTER TABLE "cms_languagetreenode" ADD CONSTRAINT "fk_cms_languagetreenode_language_id_1" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_languagetreenode" ADD CONSTRAINT "fk_cms_languagetreenode_parent_id_2" FOREIGN KEY ("parent_id") REFERENCES "cms_languagetreenode" ("id");

ALTER TABLE "cms_languagetreenode" ADD CONSTRAINT "fk_cms_languagetreenode_region_id_3" FOREIGN KEY ("region_id") REFERENCES "cms_region" ("id");

ALTER TABLE "cms_poicategorytranslation" ADD CONSTRAINT "fk_cms_poicategorytranslation_category_id_1" FOREIGN KEY ("category_id") REFERENCES "cms_poicategory" ("id");

ALTER TABLE "cms_poicategorytranslation" ADD CONSTRAINT "fk_cms_poicategorytranslation_language_id_2" FOREIGN KEY ("language_id") REFERENCES "cms_language" ("id");

ALTER TABLE "cms_searchresultfeedback" ADD CONSTRAINT "fk_cms_searchresultfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_poifeedback" ADD CONSTRAINT "fk_cms_poifeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_poifeedback" ADD CONSTRAINT "fk_cms_poifeedback_poi_translation_id_2" FOREIGN KEY ("poi_translation_id") REFERENCES "cms_poitranslation" ("id");

ALTER TABLE "cms_pagefeedback" ADD CONSTRAINT "fk_cms_pagefeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_pagefeedback" ADD CONSTRAINT "fk_cms_pagefeedback_page_translation_id_2" FOREIGN KEY ("page_translation_id") REFERENCES "cms_pagetranslation" ("id");

ALTER TABLE "cms_offerfeedback" ADD CONSTRAINT "fk_cms_offerfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_offerfeedback" ADD CONSTRAINT "fk_cms_offerfeedback_offer_id_2" FOREIGN KEY ("offer_id") REFERENCES "cms_offertemplate" ("id");

ALTER TABLE "cms_eventfeedback" ADD CONSTRAINT "fk_cms_eventfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_eventfeedback" ADD CONSTRAINT "fk_cms_eventfeedback_event_translation_id_2" FOREIGN KEY ("event_translation_id") REFERENCES "cms_eventtranslation" ("id");

ALTER TABLE "cms_eventlistfeedback" ADD CONSTRAINT "fk_cms_eventlistfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_imprintpagefeedback" ADD CONSTRAINT "fk_cms_imprintpagefeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_mapfeedback" ADD CONSTRAINT "fk_cms_mapfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_offerlistfeedback" ADD CONSTRAINT "fk_cms_offerlistfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");

ALTER TABLE "cms_regionfeedback" ADD CONSTRAINT "fk_cms_regionfeedback_feedback_ptr_id_1" FOREIGN KEY ("feedback_ptr_id") REFERENCES "cms_feedback" ("id");
