CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(150) NOT NULL,
  `email` VARCHAR(320) NOT NULL,
  `display_name` VARCHAR(255) NULL,
  `is_reviewer` BOOLEAN NOT NULL DEFAULT FALSE,
  `status` VARCHAR(30) NOT NULL DEFAULT 'active',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB;

CREATE TABLE `teams` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `slug` VARCHAR(180) NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_teams_slug` (`slug`)
) ENGINE=InnoDB;

CREATE TABLE `team_members` (
  `team_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `role` VARCHAR(50) NOT NULL,
  `joined_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`team_id`, `user_id`),
  CONSTRAINT `fk_team_members_team` FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`),
  CONSTRAINT `fk_team_members_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `addons` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `public_identifier` VARCHAR(255) NOT NULL,
  `default_locale` VARCHAR(20) NOT NULL DEFAULT 'en-US',
  `status` VARCHAR(30) NOT NULL,
  `average_rating` DECIMAL(4,2) NOT NULL DEFAULT 0,
  `rating_count` BIGINT NOT NULL DEFAULT 0,
  `download_count` BIGINT NOT NULL DEFAULT 0,
  `update_count` BIGINT NOT NULL DEFAULT 0,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_addons_public_identifier` (`public_identifier`)
) ENGINE=InnoDB;

CREATE TABLE `addon_owners` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `user_id` BIGINT NULL,
  `team_id` BIGINT NULL,
  `is_current` BOOLEAN NOT NULL DEFAULT TRUE,
  `effective_from` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `effective_to` DATETIME(6) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_addon_owners_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`),
  CONSTRAINT `fk_addon_owners_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_addon_owners_team` FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`),
  CONSTRAINT `ck_addon_owner_subject` CHECK ((`user_id` IS NOT NULL) + (`team_id` IS NOT NULL) = 1)
) ENGINE=InnoDB;

CREATE TABLE `addon_texts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `locale` VARCHAR(20) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `summary` TEXT NULL,
  `description` LONGTEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_addon_texts_locale` (`addon_id`, `locale`),
  CONSTRAINT `fk_addon_texts_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `addon_icons` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `file_path` VARCHAR(1000) NOT NULL,
  `mime_type` VARCHAR(100) NULL,
  `width` INT NULL,
  `height` INT NULL,
  `is_primary` BOOLEAN NOT NULL DEFAULT FALSE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_addon_icons_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `addon_support` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `support_email` VARCHAR(320) NULL,
  `support_url` VARCHAR(1000) NULL,
  `support_text` TEXT NULL,
  `is_current` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_addon_support_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `categories` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `slug` VARCHAR(180) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categories_slug` (`slug`)
) ENGINE=InnoDB;

CREATE TABLE `tags` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `slug` VARCHAR(180) NOT NULL,
  `label` VARCHAR(255) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_tags_slug` (`slug`),
  UNIQUE KEY `uq_tags_label` (`label`)
) ENGINE=InnoDB;

CREATE TABLE `addon_categories` (
  `addon_id` BIGINT NOT NULL,
  `category_id` BIGINT NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`addon_id`, `category_id`),
  CONSTRAINT `fk_addon_categories_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`),
  CONSTRAINT `fk_addon_categories_category` FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `addon_tags` (
  `addon_id` BIGINT NOT NULL,
  `tag_id` BIGINT NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`addon_id`, `tag_id`),
  CONSTRAINT `fk_addon_tags_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`),
  CONSTRAINT `fk_addon_tags_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `screenshots` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `file_path` VARCHAR(1000) NOT NULL,
  `caption` VARCHAR(500) NULL,
  `position` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_screenshots_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `compatibility_rules` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `application` VARCHAR(100) NOT NULL,
  `platform` VARCHAR(100) NULL,
  `minimum_version` VARCHAR(50) NULL,
  `maximum_version` VARCHAR(50) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_compatibility_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `licenses` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `slug` VARCHAR(180) NOT NULL,
  `license_text` LONGTEXT NULL,
  `is_custom` BOOLEAN NOT NULL DEFAULT FALSE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_licenses_slug` (`slug`)
) ENGINE=InnoDB;

CREATE TABLE `addon_versions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `license_id` BIGINT NULL,
  `version_string` VARCHAR(100) NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `released_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_addon_versions` (`addon_id`, `version_string`),
  CONSTRAINT `fk_addon_versions_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`),
  CONSTRAINT `fk_addon_versions_license` FOREIGN KEY (`license_id`) REFERENCES `licenses`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `addon_files` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `version_id` BIGINT NOT NULL,
  `file_path` VARCHAR(1000) NOT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `file_hash` VARCHAR(255) NULL,
  `size_bytes` BIGINT NULL,
  `platform` VARCHAR(100) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_addon_files_version` FOREIGN KEY (`version_id`) REFERENCES `addon_versions`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `file_review_metadata` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `version_id` BIGINT NOT NULL,
  `metadata_type` VARCHAR(100) NOT NULL,
  `metadata_json` JSON NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_file_review_metadata_version` FOREIGN KEY (`version_id`) REFERENCES `addon_versions`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `file_signing_results` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_file_id` BIGINT NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `result_json` JSON NULL,
  `occurred_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_signing_file` FOREIGN KEY (`addon_file_id`) REFERENCES `addon_files`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `file_validation_results` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_file_id` BIGINT NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `result_json` JSON NULL,
  `occurred_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_validation_file` FOREIGN KEY (`addon_file_id`) REFERENCES `addon_files`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `security_findings` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_file_id` BIGINT NOT NULL,
  `source_system` VARCHAR(100) NOT NULL,
  `severity` VARCHAR(30) NOT NULL,
  `finding_code` VARCHAR(100) NULL,
  `description` TEXT NULL,
  `finding_json` JSON NULL,
  `occurred_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_security_findings_file` FOREIGN KEY (`addon_file_id`) REFERENCES `addon_files`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `ratings` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `addon_id` BIGINT NOT NULL,
  `version_id` BIGINT NULL,
  `rating_value` TINYINT NOT NULL,
  `title` VARCHAR(255) NULL,
  `written_feedback` TEXT NULL,
  `is_current` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ratings_author_version` (`user_id`, `addon_id`, `version_id`),
  CONSTRAINT `fk_ratings_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_ratings_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`),
  CONSTRAINT `fk_ratings_version` FOREIGN KEY (`version_id`) REFERENCES `addon_versions`(`id`),
  CONSTRAINT `ck_ratings_value` CHECK (`rating_value` BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE `rating_replies` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `rating_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `body` TEXT NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_rating_replies_rating` FOREIGN KEY (`rating_id`) REFERENCES `ratings`(`id`),
  CONSTRAINT `fk_rating_replies_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `moderation_reports` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `reported_by_user_id` BIGINT NULL,
  `target_type` VARCHAR(60) NOT NULL,
  `target_id` BIGINT NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'open',
  `report_text` TEXT NOT NULL,
  `external_reference` VARCHAR(255) NULL,
  `moderation_result` JSON NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_moderation_reports_user` FOREIGN KEY (`reported_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `collections` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `owner_user_id` BIGINT NOT NULL,
  `slug` VARCHAR(180) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `is_public` BOOLEAN NOT NULL DEFAULT FALSE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_collections_owner_slug` (`owner_user_id`, `slug`),
  CONSTRAINT `fk_collections_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `collection_items` (
  `collection_id` BIGINT NOT NULL,
  `addon_id` BIGINT NOT NULL,
  `position` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`collection_id`, `addon_id`),
  CONSTRAINT `fk_collection_items_collection` FOREIGN KEY (`collection_id`) REFERENCES `collections`(`id`),
  CONSTRAINT `fk_collection_items_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `featured_collections` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `collection_id` BIGINT NOT NULL,
  `placement_type` VARCHAR(50) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `position` INT NOT NULL DEFAULT 0,
  `starts_at` DATETIME(6) NULL,
  `ends_at` DATETIME(6) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_featured_collections_collection` FOREIGN KEY (`collection_id`) REFERENCES `collections`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `homepage_heroes` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `section_type` VARCHAR(50) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `target_type` VARCHAR(50) NULL,
  `target_id` BIGINT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `position` INT NOT NULL DEFAULT 0,
  `starts_at` DATETIME(6) NULL,
  `ends_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `review_queue_items` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `reviewer_user_id` BIGINT NULL,
  `addon_id` BIGINT NOT NULL,
  `version_id` BIGINT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `priority` INT NOT NULL DEFAULT 0,
  `assigned_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_review_queue_reviewer` FOREIGN KEY (`reviewer_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_review_queue_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`),
  CONSTRAINT `fk_review_queue_version` FOREIGN KEY (`version_id`) REFERENCES `addon_versions`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `review_alerts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `reviewer_user_id` BIGINT NOT NULL,
  `addon_id` BIGINT NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'active',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_review_alerts_reviewer_addon` (`reviewer_user_id`, `addon_id`),
  CONSTRAINT `fk_review_alerts_reviewer` FOREIGN KEY (`reviewer_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_review_alerts_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `reviewer_notes` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `author_user_id` BIGINT NOT NULL,
  `target_type` VARCHAR(60) NOT NULL,
  `target_id` BIGINT NOT NULL,
  `body` TEXT NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_reviewer_notes_author` FOREIGN KEY (`author_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `canned_responses` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_by_user_id` BIGINT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_canned_responses_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `approval_summaries` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `version_id` BIGINT NOT NULL,
  `reviewer_user_id` BIGINT NOT NULL,
  `decision` VARCHAR(30) NOT NULL,
  `summary_text` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_approval_summaries_version` FOREIGN KEY (`version_id`) REFERENCES `addon_versions`(`id`),
  CONSTRAINT `fk_approval_summaries_reviewer` FOREIGN KEY (`reviewer_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `reviewer_score_history` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `reviewer_user_id` BIGINT NOT NULL,
  `target_type` VARCHAR(60) NULL,
  `target_id` BIGINT NULL,
  `score_delta` INT NOT NULL,
  `reason` VARCHAR(500) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_reviewer_scores_user` FOREIGN KEY (`reviewer_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `attention_flags` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `target_type` VARCHAR(60) NOT NULL,
  `target_id` BIGINT NOT NULL,
  `flag_type` VARCHAR(60) NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'open',
  `created_by_user_id` BIGINT NOT NULL,
  `resolved_by_user_id` BIGINT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `resolved_at` DATETIME(6) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_attention_flags_creator` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_attention_flags_resolver` FOREIGN KEY (`resolved_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `system_settings` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `setting_key` VARCHAR(255) NOT NULL,
  `setting_value` JSON NOT NULL,
  `updated_by_user_id` BIGINT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_system_settings_key` (`setting_key`),
  CONSTRAINT `fk_system_settings_user` FOREIGN KEY (`updated_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `blocked_identifiers` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `identifier` VARCHAR(255) NOT NULL,
  `block_type` VARCHAR(40) NOT NULL,
  `reason` VARCHAR(500) NULL,
  `created_by_user_id` BIGINT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_blocked_identifiers` (`identifier`, `block_type`),
  CONSTRAINT `fk_blocked_identifiers_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `api_credentials` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `access_key` VARCHAR(255) NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'active',
  `last_used_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_api_credentials_key` (`access_key`),
  CONSTRAINT `fk_api_credentials_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `email_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NULL,
  `recipient_email` VARCHAR(320) NOT NULL,
  `subject` VARCHAR(500) NULL,
  `status` VARCHAR(30) NOT NULL,
  `sent_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_email_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `activity_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NULL,
  `event_type` VARCHAR(100) NOT NULL,
  `severity` VARCHAR(20) NULL,
  `target_type` VARCHAR(60) NULL,
  `target_id` BIGINT NULL,
  `message` TEXT NULL,
  `context_json` JSON NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_activity_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `addon_daily_metrics` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `addon_id` BIGINT NOT NULL,
  `metric_date` DATE NOT NULL,
  `download_count` BIGINT NOT NULL DEFAULT 0,
  `update_count` BIGINT NOT NULL DEFAULT 0,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_addon_daily_metrics` (`addon_id`, `metric_date`),
  CONSTRAINT `fk_addon_daily_metrics_addon` FOREIGN KEY (`addon_id`) REFERENCES `addons`(`id`)
) ENGINE=InnoDB;

CREATE INDEX `idx_tags_active_label` ON `tags`(`is_active`, `label`);
CREATE INDEX `idx_homepage_heroes_active` ON `homepage_heroes`(`section_type`, `is_active`, `position`);
CREATE INDEX `idx_ratings_addon_current` ON `ratings`(`addon_id`, `is_current`, `created_at`);
CREATE INDEX `idx_ratings_version` ON `ratings`(`version_id`, `created_at`);
CREATE INDEX `idx_review_alerts_addon` ON `review_alerts`(`addon_id`, `status`);
CREATE INDEX `idx_addon_versions_status` ON `addon_versions`(`addon_id`, `status`, `released_at`);
CREATE INDEX `idx_addon_files_version` ON `addon_files`(`version_id`);
CREATE INDEX `idx_security_findings_file` ON `security_findings`(`addon_file_id`, `severity`);
CREATE INDEX `idx_review_queue_status` ON `review_queue_items`(`status`, `priority`, `created_at`);
CREATE INDEX `idx_moderation_reports_status` ON `moderation_reports`(`status`, `created_at`);
CREATE INDEX `idx_addon_daily_metrics_date` ON `addon_daily_metrics`(`metric_date`, `addon_id`);
CREATE INDEX `idx_activity_logs_target` ON `activity_logs`(`target_type`, `target_id`, `created_at`);
