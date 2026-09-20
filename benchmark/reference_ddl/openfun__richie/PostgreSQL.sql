CREATE TABLE "richie_blog_post" (
  "id" INTEGER NOT NULL,
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_blog_post_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "variant" VARCHAR(255),
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_category" (
  "id" INTEGER NOT NULL,
  "color" VARCHAR(255),
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_category_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "variant" VARCHAR(255),
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_course" (
  "id" INTEGER NOT NULL,
  "code" VARCHAR(255),
  "duration" VARCHAR(255),
  "effort" VARCHAR(255),
  "is_listed" BOOLEAN NOT NULL,
  "is_self_paced" BOOLEAN NOT NULL,
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_course_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "variant" VARCHAR(255),
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_course_run" (
  "id" INTEGER NOT NULL,
  "direct_course_id" INTEGER NOT NULL,
  "draft_course_run_id" INTEGER,
  "resource_link" VARCHAR(255),
  "start" TIMESTAMP,
  "end" TIMESTAMP,
  "enrollment_start" TIMESTAMP,
  "enrollment_end" TIMESTAMP,
  "languages" VARCHAR(255) NOT NULL,
  "sync_mode" VARCHAR(255) NOT NULL,
  "enrollment_count" INTEGER NOT NULL,
  "catalog_visibility" VARCHAR(255) NOT NULL,
  "price" DECIMAL(18, 2),
  "price_currency" VARCHAR(255) NOT NULL,
  "discounted_price" DECIMAL(18, 2),
  "discount" VARCHAR(255),
  "offer" VARCHAR(255),
  "certificate_price" DECIMAL(18, 2),
  "certificate_discounted_price" DECIMAL(18, 2),
  "certificate_discount" VARCHAR(255),
  "certificate_offer" VARCHAR(255),
  "display_mode" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_course_run_translation" (
  "id" INTEGER NOT NULL,
  "language_code" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255),
  "master_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("language_code", "master_id")
);

CREATE TABLE "richie_licence" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "content" TEXT NOT NULL,
  "logo_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_licence_translation" (
  "id" INTEGER NOT NULL,
  "language_code" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "content" TEXT NOT NULL,
  "master_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("language_code", "master_id")
);

CREATE TABLE "richie_licence_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "description" TEXT NOT NULL,
  "licence_id" INTEGER NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_menuentry" (
  "id" INTEGER NOT NULL,
  "allow_submenu" BOOLEAN NOT NULL,
  "menu_color" VARCHAR(255) NOT NULL,
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_organization" (
  "id" INTEGER NOT NULL,
  "code" VARCHAR(255),
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_organization_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "variant" VARCHAR(255),
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_organizations_by_category_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "variant" VARCHAR(255),
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_page_role" (
  "id" INTEGER NOT NULL,
  "role" VARCHAR(255) NOT NULL,
  "page_id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL,
  "folder_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("page_id", "role")
);

CREATE TABLE "richie_person" (
  "id" INTEGER NOT NULL,
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_person_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  "bio" TEXT,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "richie_program" (
  "id" INTEGER NOT NULL,
  "duration" VARCHAR(255),
  "effort" VARCHAR(255),
  "price" DECIMAL(18, 2),
  "extended_object_id" INTEGER NOT NULL,
  "public_extension_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "richie_program_plugin" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "page_id" INTEGER NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "section_section" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "title" VARCHAR(255),
  "template" VARCHAR(255) NOT NULL,
  "attributes" JSONB NOT NULL,
  "grid_columns" VARCHAR(255) NOT NULL,
  "grid_gutter" BOOLEAN NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "simple_text_ckeditor_simpletext" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "body" TEXT NOT NULL,
  "variant" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "slider_slider" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "slider_slideitem" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "content" TEXT NOT NULL,
  "link_url" VARCHAR(255),
  "link_open_blank" BOOLEAN NOT NULL,
  "image_id" INTEGER,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "glimpse_glimpse" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "title" VARCHAR(255),
  "variant" VARCHAR(255),
  "content" TEXT NOT NULL,
  "link_url" VARCHAR(255),
  "image_id" INTEGER,
  "link_page_id" INTEGER,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "html_sitemap_htmlsitemappage" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "max_depth" INTEGER,
  "in_navigation" BOOLEAN NOT NULL,
  "include_root_page" BOOLEAN NOT NULL,
  "root_page_id" INTEGER,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "large_banner_largebanner" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "logo_alt_text" VARCHAR(255) NOT NULL,
  "background_image_id" INTEGER,
  "logo_id" INTEGER,
  "template" VARCHAR(255) NOT NULL,
  "content" TEXT NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "lti_consumer_lticonsumer" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "lti_provider_id" VARCHAR(255),
  "oauth_consumer_key" VARCHAR(255),
  "shared_secret" VARCHAR(255),
  "is_automatic_resizing" BOOLEAN,
  "inline_ratio" DOUBLE PRECISION,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "nesteditem_nesteditem" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "content" TEXT NOT NULL,
  "variant" VARCHAR(255),
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE TABLE "plain_text_plaintext" (
  "cmsplugin_ptr_id" INTEGER NOT NULL,
  "body" TEXT NOT NULL,
  PRIMARY KEY ("cmsplugin_ptr_id")
);

CREATE INDEX "idx_richie_course_code_1" ON "richie_course" ("code");

CREATE INDEX "idx_richie_organization_code_1" ON "richie_organization" ("code");

ALTER TABLE "richie_blog_post" ADD CONSTRAINT "fk_richie_blog_post_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_blog_post" ("id");

ALTER TABLE "richie_category" ADD CONSTRAINT "fk_richie_category_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_category" ("id");

ALTER TABLE "richie_course" ADD CONSTRAINT "fk_richie_course_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_course" ("id");

ALTER TABLE "richie_course_run" ADD CONSTRAINT "fk_richie_course_run_direct_course_id_1" FOREIGN KEY ("direct_course_id") REFERENCES "richie_course" ("id");

ALTER TABLE "richie_course_run" ADD CONSTRAINT "fk_richie_course_run_draft_course_run_id_2" FOREIGN KEY ("draft_course_run_id") REFERENCES "richie_course_run" ("id");

ALTER TABLE "richie_course_run_translation" ADD CONSTRAINT "fk_richie_course_run_translation_master_id_1" FOREIGN KEY ("master_id") REFERENCES "richie_course_run" ("id");

ALTER TABLE "richie_licence_translation" ADD CONSTRAINT "fk_richie_licence_translation_master_id_1" FOREIGN KEY ("master_id") REFERENCES "richie_licence" ("id");

ALTER TABLE "richie_licence_plugin" ADD CONSTRAINT "fk_richie_licence_plugin_licence_id_1" FOREIGN KEY ("licence_id") REFERENCES "richie_licence" ("id");

ALTER TABLE "richie_menuentry" ADD CONSTRAINT "fk_richie_menuentry_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_menuentry" ("id");

ALTER TABLE "richie_organization" ADD CONSTRAINT "fk_richie_organization_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_organization" ("id");

ALTER TABLE "richie_person" ADD CONSTRAINT "fk_richie_person_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_person" ("id");

ALTER TABLE "richie_program" ADD CONSTRAINT "fk_richie_program_public_extension_id_1" FOREIGN KEY ("public_extension_id") REFERENCES "richie_program" ("id");
