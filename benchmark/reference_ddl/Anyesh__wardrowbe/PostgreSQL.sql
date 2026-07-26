CREATE TABLE "item_images" (
  "id" UUID NOT NULL,
  "item_id" UUID NOT NULL,
  "image_path" VARCHAR(255) NOT NULL,
  "thumbnail_path" VARCHAR(255),
  "medium_path" VARCHAR(255),
  "position" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "item_pair_scores" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "item1_id" UUID NOT NULL,
  "item2_id" UUID NOT NULL,
  "compatibility_score" DECIMAL(18, 2) NOT NULL,
  "times_paired" INTEGER NOT NULL,
  "times_accepted" INTEGER NOT NULL,
  "times_rejected" INTEGER NOT NULL,
  "total_rating_sum" INTEGER NOT NULL,
  "rating_count" INTEGER NOT NULL,
  "occasion_performance" JSONB NOT NULL,
  "weather_performance" JSONB NOT NULL,
  "wear_bonus" DECIMAL(18, 2),
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id", "item1_id", "item2_id")
);

CREATE TABLE "outfit_performances" (
  "outfit_id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "performance_score" DECIMAL(18, 2) NOT NULL,
  "acceptance_score" DECIMAL(18, 2),
  "rating_score" DECIMAL(18, 2),
  "wear_score" DECIMAL(18, 2),
  "occasion" VARCHAR(255) NOT NULL,
  "weather_temp" INTEGER,
  "weather_condition" VARCHAR(255),
  "item_composition" JSONB NOT NULL,
  "color_composition" JSONB NOT NULL,
  "was_modified" BOOLEAN NOT NULL,
  "modification_notes" TEXT,
  "computed_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("outfit_id")
);

CREATE TABLE "style_insights" (
  "id" UUID NOT NULL,
  "user_id" UUID NOT NULL,
  "category" VARCHAR(255) NOT NULL,
  "insight_type" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "confidence" DECIMAL(18, 2) NOT NULL,
  "supporting_data" JSONB NOT NULL,
  "is_acknowledged" BOOLEAN NOT NULL,
  "acknowledged_at" TIMESTAMP,
  "expires_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "user_learning_profiles" (
  "user_id" UUID NOT NULL,
  "learned_color_scores" JSONB NOT NULL,
  "learned_style_scores" JSONB NOT NULL,
  "learned_occasion_patterns" JSONB NOT NULL,
  "learned_weather_preferences" JSONB NOT NULL,
  "learned_temporal_patterns" JSONB NOT NULL,
  "overall_acceptance_rate" DECIMAL(18, 2),
  "average_overall_rating" DECIMAL(18, 2),
  "average_comfort_rating" DECIMAL(18, 2),
  "average_style_rating" DECIMAL(18, 2),
  "feedback_count" INTEGER NOT NULL,
  "outfits_rated" INTEGER NOT NULL,
  "last_computed_at" TIMESTAMP,
  "model_version" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("user_id")
);

CREATE TABLE "wash_history" (
  "id" UUID NOT NULL,
  "item_id" UUID NOT NULL,
  "washed_at" DATE NOT NULL,
  "method" VARCHAR(255),
  "notes" TEXT,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_item_images_item_id_1" ON "item_images" ("item_id");

CREATE INDEX "idx_item_pair_scores_user_id_1" ON "item_pair_scores" ("user_id");

CREATE INDEX "idx_item_pair_scores_item1_id_2" ON "item_pair_scores" ("item1_id");

CREATE INDEX "idx_item_pair_scores_item2_id_3" ON "item_pair_scores" ("item2_id");

CREATE INDEX "idx_item_pair_scores_user_id_compatibility_score_4" ON "item_pair_scores" ("user_id", "compatibility_score");

CREATE INDEX "idx_outfit_performances_user_id_1" ON "outfit_performances" ("user_id");

CREATE INDEX "idx_outfit_performances_user_id_occasion_2" ON "outfit_performances" ("user_id", "occasion");

CREATE INDEX "idx_style_insights_user_id_1" ON "style_insights" ("user_id");

CREATE INDEX "idx_style_insights_user_id_is_acknowledged_expires_at_2" ON "style_insights" ("user_id", "is_acknowledged", "expires_at");

CREATE INDEX "idx_wash_history_item_id_washed_at_1" ON "wash_history" ("item_id", "washed_at");
