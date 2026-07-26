CREATE TABLE `auth_tokens` (
  `id` VARCHAR(255) NOT NULL,
  `collection_name` VARCHAR(255) NOT NULL,
  `collection_id` VARCHAR(255) NOT NULL,
  `record_id` VARCHAR(255) NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `last_used_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`token_hash`)
);

CREATE TABLE `cache` (
  `key` VARCHAR(255) NOT NULL,
  `value` TEXT NOT NULL,
  `expiration` BIGINT NOT NULL,
  PRIMARY KEY (`key`)
);

CREATE TABLE `cache_locks` (
  `key` VARCHAR(255) NOT NULL,
  `owner` VARCHAR(255) NOT NULL,
  `expiration` BIGINT NOT NULL,
  PRIMARY KEY (`key`)
);

CREATE TABLE `email_templates` (
  `id` BIGINT NOT NULL,
  `collection_id` VARCHAR(255) NOT NULL,
  `action` VARCHAR(255) NOT NULL,
  `content` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`collection_id`, `action`)
);

CREATE TABLE `failed_jobs` (
  `id` BIGINT NOT NULL,
  `uuid` VARCHAR(255) NOT NULL,
  `connection` TEXT NOT NULL,
  `queue` TEXT NOT NULL,
  `payload` TEXT NOT NULL,
  `exception` TEXT NOT NULL,
  `failed_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`uuid`)
);

CREATE TABLE `job_batches` (
  `id` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `total_jobs` INTEGER NOT NULL,
  `pending_jobs` INTEGER NOT NULL,
  `failed_jobs` INTEGER NOT NULL,
  `failed_job_ids` TEXT NOT NULL,
  `options` TEXT,
  `cancelled_at` INTEGER,
  `created_at` INTEGER NOT NULL,
  `finished_at` INTEGER,
  PRIMARY KEY (`id`)
);

CREATE TABLE `jobs` (
  `id` BIGINT NOT NULL,
  `queue` VARCHAR(255) NOT NULL,
  `payload` TEXT NOT NULL,
  `attempts` INTEGER NOT NULL,
  `reserved_at` INTEGER,
  `available_at` INTEGER NOT NULL,
  `created_at` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_accounts` (
  `id` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(255) NOT NULL,
  `provider_user_id` VARCHAR(255) NOT NULL,
  `collection_id` VARCHAR(255) NOT NULL,
  `record_id` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`provider`, `provider_user_id`, `collection_id`)
);

CREATE TABLE `oauth_providers` (
  `id` BIGINT NOT NULL,
  `collection_id` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(255) NOT NULL,
  `enabled` TINYINT(1) NOT NULL,
  `client_id` VARCHAR(255) NOT NULL,
  `client_secret` TEXT NOT NULL,
  `redirect_uri` VARCHAR(255),
  `scopes` JSON,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`collection_id`, `provider`)
);

CREATE TABLE `otp_tokens` (
  `id` BIGINT NOT NULL,
  `collection_id` VARCHAR(255) NOT NULL,
  `record_id` VARCHAR(255) NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `action` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `used_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`token_hash`)
);

CREATE TABLE `schema_jobs` (
  `id` BIGINT NOT NULL,
  `collection_id` VARCHAR(255) NOT NULL,
  `operation` VARCHAR(255) NOT NULL,
  `table_name` VARCHAR(255) NOT NULL,
  `started_at` DATETIME NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `settings` (
  `id` BIGINT NOT NULL,
  `group` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `locked` TINYINT(1) NOT NULL,
  `payload` JSON NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`group`, `name`)
);

CREATE INDEX `idx_auth_tokens_collection_id_record_id_1` ON `auth_tokens` (`collection_id`, `record_id`);

CREATE INDEX `idx_cache_expiration_1` ON `cache` (`expiration`);

CREATE INDEX `idx_cache_locks_expiration_1` ON `cache_locks` (`expiration`);

CREATE INDEX `idx_jobs_queue_1` ON `jobs` (`queue`);

CREATE INDEX `idx_oauth_accounts_collection_id_record_id_1` ON `oauth_accounts` (`collection_id`, `record_id`);

CREATE INDEX `idx_otp_tokens_record_id_action_1` ON `otp_tokens` (`record_id`, `action`);

CREATE INDEX `idx_otp_tokens_collection_id_record_id_action_expires_at_2` ON `otp_tokens` (`collection_id`, `record_id`, `action`, `expires_at`);

CREATE INDEX `idx_otp_tokens_expires_at_used_at_3` ON `otp_tokens` (`expires_at`, `used_at`);

CREATE INDEX `idx_schema_jobs_collection_id_1` ON `schema_jobs` (`collection_id`);
