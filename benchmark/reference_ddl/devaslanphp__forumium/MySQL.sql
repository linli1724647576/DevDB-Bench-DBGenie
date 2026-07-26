CREATE TABLE `configurations` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `is_enabled` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `discussion_visits` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `discussion_id` BIGINT NOT NULL,
  `meta` TEXT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `discussions` (
  `id` BIGINT NOT NULL,
  `is_public` TINYINT(1) NOT NULL,
  `is_locked` TINYINT(1) NOT NULL,
  `visits` BIGINT NOT NULL,
  `unique_visits` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `notifications` (
  `id` CHAR(36) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `notifiable_type` VARCHAR(255) NOT NULL,
  `notifiable_id` BIGINT NOT NULL,
  `data` TEXT NOT NULL,
  `read_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `points` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `source_type` VARCHAR(255) NOT NULL,
  `source_id` BIGINT NOT NULL,
  `value` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `replies` (
  `is_best` TINYINT(1) NOT NULL
);

CREATE TABLE `tags` (
  `description` TEXT NOT NULL
);

CREATE TABLE `users` (
  `id` BIGINT NOT NULL,
  `bio` TEXT,
  `is_email_visible` TINYINT(1) NOT NULL,
  `picture` VARCHAR(255),
  `total_points` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE INDEX `idx_discussion_visits_user_id_1` ON `discussion_visits` (`user_id`);

CREATE INDEX `idx_discussion_visits_discussion_id_2` ON `discussion_visits` (`discussion_id`);

CREATE INDEX `idx_notifications_notifiable_type_notifiable_id_1` ON `notifications` (`notifiable_type`, `notifiable_id`);

CREATE INDEX `idx_points_user_id_1` ON `points` (`user_id`);

CREATE INDEX `idx_points_source_type_source_id_2` ON `points` (`source_type`, `source_id`);

ALTER TABLE `discussion_visits` ADD CONSTRAINT `fk_discussion_visits_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `discussion_visits` ADD CONSTRAINT `fk_discussion_visits_discussion_id_2` FOREIGN KEY (`discussion_id`) REFERENCES `discussions` (`id`);

ALTER TABLE `points` ADD CONSTRAINT `fk_points_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
