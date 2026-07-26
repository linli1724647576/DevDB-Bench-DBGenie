CREATE TABLE `agent_conversation_messages` (
  `id` VARCHAR(255) NOT NULL,
  `conversation_id` VARCHAR(255) NOT NULL,
  `user_id` INTEGER,
  `agent` VARCHAR(255) NOT NULL,
  `role` VARCHAR(255) NOT NULL,
  `content` TEXT NOT NULL,
  `attachments` TEXT NOT NULL,
  `tool_calls` TEXT NOT NULL,
  `tool_results` TEXT NOT NULL,
  `usage` TEXT NOT NULL,
  `meta` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `agent_conversations` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` INTEGER,
  `title` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
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
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `queue` VARCHAR(255) NOT NULL,
  `payload` TEXT NOT NULL,
  `attempts` SMALLINT NOT NULL,
  `reserved_at` INTEGER UNSIGNED,
  `available_at` INTEGER UNSIGNED NOT NULL,
  `created_at` INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_access_tokens` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` BIGINT UNSIGNED,
  `client_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(255),
  `scopes` TEXT,
  `revoked` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `expires_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_auth_codes` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `client_id` BIGINT UNSIGNED NOT NULL,
  `scopes` TEXT,
  `revoked` TINYINT(1) NOT NULL,
  `expires_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_clients` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `user_id` BIGINT UNSIGNED,
  `name` VARCHAR(255) NOT NULL,
  `secret` VARCHAR(255),
  `provider` VARCHAR(255),
  `redirect` TEXT NOT NULL,
  `personal_access_client` TINYINT(1) NOT NULL,
  `password_client` TINYINT(1) NOT NULL,
  `revoked` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_personal_access_clients` (
  `id` BIGINT AUTO_INCREMENT NOT NULL,
  `client_id` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_refresh_tokens` (
  `id` VARCHAR(255) NOT NULL,
  `access_token_id` VARCHAR(255) NOT NULL,
  `revoked` TINYINT(1) NOT NULL,
  `expires_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `personal_access_tokens` (
  `id` BIGINT NOT NULL,
  `tokenable_type` VARCHAR(255) NOT NULL,
  `tokenable_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `abilities` TEXT,
  `last_used_at` DATETIME,
  `expires_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`token`)
);

CREATE TABLE `sessions` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` INTEGER,
  `ip_address` VARCHAR(255),
  `user_agent` TEXT,
  `payload` TEXT NOT NULL,
  `last_activity` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE INDEX `idx_agent_conversation_messages_conversation_id_1` ON `agent_conversation_messages` (`conversation_id`);

CREATE INDEX `idx_agent_conversation_messages_conversation_id_use_41620c42` ON `agent_conversation_messages` (`conversation_id`, `user_id`, `updated_at`);

CREATE INDEX `idx_agent_conversation_messages_user_id_3` ON `agent_conversation_messages` (`user_id`);

CREATE INDEX `idx_agent_conversations_user_id_updated_at_1` ON `agent_conversations` (`user_id`, `updated_at`);

CREATE INDEX `idx_jobs_queue_1` ON `jobs` (`queue`);

CREATE INDEX `idx_oauth_access_tokens_user_id_1` ON `oauth_access_tokens` (`user_id`);

CREATE INDEX `idx_oauth_auth_codes_user_id_1` ON `oauth_auth_codes` (`user_id`);

CREATE INDEX `idx_oauth_clients_user_id_1` ON `oauth_clients` (`user_id`);

CREATE INDEX `idx_oauth_refresh_tokens_access_token_id_1` ON `oauth_refresh_tokens` (`access_token_id`);

CREATE INDEX `idx_personal_access_tokens_tokenable_type_tokenable_id_1` ON `personal_access_tokens` (`tokenable_type`, `tokenable_id`);

CREATE INDEX `idx_sessions_last_activity_1` ON `sessions` (`last_activity`);
