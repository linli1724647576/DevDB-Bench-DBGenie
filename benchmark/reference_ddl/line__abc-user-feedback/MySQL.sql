CREATE TABLE `ai_integrations` (
  `id` INTEGER NOT NULL,
  `project_id` INTEGER NOT NULL,
  `provider` VARCHAR(255) NOT NULL,
  `api_key` VARCHAR(255) NOT NULL,
  `endpoint_url` VARCHAR(255),
  `system_prompt` TEXT NOT NULL,
  `token_threshold` INTEGER,
  `notification_threshold` FLOAT,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`project_id`)
);

CREATE TABLE `ai_field_templates` (
  `id` INTEGER NOT NULL,
  `project_id` INTEGER NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `prompt` TEXT NOT NULL,
  `model` VARCHAR(255),
  `temperature` FLOAT NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ai_usages` (
  `id` INTEGER NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `deleted_at` DATETIME,
  `year` INTEGER NOT NULL,
  `month` INTEGER NOT NULL,
  `day` INTEGER NOT NULL,
  `category` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(255) NOT NULL,
  `used_tokens` INTEGER NOT NULL,
  `project_id` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ai_issue_templates` (
  `id` INTEGER NOT NULL,
  `channel_id` INTEGER NOT NULL,
  `target_field_keys` JSON NOT NULL,
  `prompt` TEXT NOT NULL,
  `is_enabled` TINYINT(1) NOT NULL,
  `model` VARCHAR(255),
  `temperature` FLOAT NOT NULL,
  `data_reference_amount` INTEGER NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `categories` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `project_id` INTEGER NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`project_id`, `name`)
);

CREATE INDEX `idx_ai_integrations_project_active` ON `ai_integrations` (`project_id`, `deleted_at`);

CREATE INDEX `idx_ai_field_templates_project_active` ON `ai_field_templates` (`project_id`, `deleted_at`);

CREATE UNIQUE INDEX `uidx_ai_usages_daily` ON `ai_usages` (`project_id`, `provider`, `category`, `year`, `month`, `day`);

CREATE INDEX `idx_ai_usages_project_month_activity_provider` ON `ai_usages` (`project_id`, `year`, `month`, `category`, `provider`);

CREATE INDEX `idx_ai_issue_templates_channel_active` ON `ai_issue_templates` (`channel_id`, `is_enabled`, `deleted_at`);

CREATE INDEX `idx_categories_project_created` ON `categories` (`project_id`, `created_at`);
