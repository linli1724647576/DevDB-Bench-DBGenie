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

CREATE TABLE `language_lines` (
  `id` INTEGER NOT NULL,
  `group` VARCHAR(255) NOT NULL,
  `key` VARCHAR(255) NOT NULL,
  `text` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `notifications` (
  `id` CHAR(36) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `notifiable_id` BIGINT NOT NULL,
  `notifiable_type` VARCHAR(255) NOT NULL,
  `data` TEXT NOT NULL,
  `read_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_clients` (
  `secret` VARCHAR(255),
  `provider` VARCHAR(255)
);

CREATE TABLE `reports` (
  `id` INTEGER NOT NULL,
  `tid` INTEGER NOT NULL,
  `uploader` INTEGER NOT NULL,
  `reporter` INTEGER NOT NULL,
  `reason` TEXT NOT NULL,
  `status` INTEGER NOT NULL,
  `report_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `scopes` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`name`)
);

CREATE TABLE `textures` (
  `likes` INTEGER NOT NULL
);

CREATE TABLE `users` (
  `nickname` VARCHAR(255),
  `ip` VARCHAR(255),
  `locale` VARCHAR(255),
  `is_dark_mode` TINYINT(1) NOT NULL
);

CREATE UNIQUE INDEX `uidx_reports_reporter_texture` ON `reports` (`reporter`, `tid`);

CREATE INDEX `idx_reports_reporter_recent` ON `reports` (`reporter`, `report_at`, `id`);

CREATE INDEX `idx_reports_status_recent` ON `reports` (`status`, `report_at`, `id`);

CREATE INDEX `idx_reports_texture` ON `reports` (`tid`);

CREATE FULLTEXT INDEX `ftidx_reports_reason` ON `reports` (`reason`);
