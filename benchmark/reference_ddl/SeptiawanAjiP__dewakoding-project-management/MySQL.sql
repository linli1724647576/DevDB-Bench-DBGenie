CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(320) NOT NULL,
  `password_hash` VARCHAR(500) NULL,
  `google_identifier` VARCHAR(255) NULL,
  `avatar_url` VARCHAR(1000) NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `last_login_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_google_identifier` (`google_identifier`)
) ENGINE=InnoDB;

CREATE TABLE `personal_settings` (
  `user_id` BIGINT NOT NULL,
  `theme` VARCHAR(30) NULL,
  `locale` VARCHAR(20) NULL,
  `timezone` VARCHAR(64) NULL,
  `notification_preferences` JSON NULL,
  `board_preferences` JSON NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_personal_settings_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `projects` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `owner_user_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `color` VARCHAR(30) NULL,
  `icon` VARCHAR(100) NULL,
  `is_pinned` BOOLEAN NOT NULL DEFAULT FALSE,
  `timeline_start` DATE NULL,
  `timeline_end` DATE NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_projects_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `project_members` (
  `project_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `member_role` VARCHAR(50) NOT NULL DEFAULT 'member',
  `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`project_id`, `user_id`),
  CONSTRAINT `fk_project_members_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `fk_project_members_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `external_access_credentials` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `client_name` VARCHAR(255) NOT NULL,
  `credential_identifier` VARCHAR(255) NOT NULL,
  `secret_hash` VARCHAR(500) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `expires_at` DATETIME NULL,
  `last_used_at` DATETIME NULL,
  `use_count` BIGINT NOT NULL DEFAULT 0,
  `revoked_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_external_credential_identifier` (`credential_identifier`),
  CONSTRAINT `fk_external_credentials_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `external_access_events` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `credential_id` BIGINT NOT NULL,
  `event_type` VARCHAR(50) NOT NULL,
  `request_context` JSON NULL,
  `occurred_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_external_access_events_credential` FOREIGN KEY (`credential_id`) REFERENCES `external_access_credentials`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `ticket_statuses` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `color` VARCHAR(30) NULL,
  `sequence_number` INT NOT NULL DEFAULT 0,
  `is_completion_status` BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ticket_status_project_name` (`project_id`, `name`),
  CONSTRAINT `fk_ticket_status_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `ticket_priorities` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `color` VARCHAR(30) NULL,
  `weight` INT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ticket_priorities_name` (`name`)
) ENGINE=InnoDB;

CREATE TABLE `epics` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `color` VARCHAR(30) NULL,
  `start_date` DATE NULL,
  `target_date` DATE NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_epics_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `tickets` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `status_id` BIGINT NOT NULL,
  `priority_id` BIGINT NULL,
  `epic_id` BIGINT NULL,
  `created_by_user_id` BIGINT NOT NULL,
  `title` VARCHAR(500) NOT NULL,
  `description` TEXT NULL,
  `board_position` DECIMAL(18,6) NOT NULL DEFAULT 0,
  `progress_percent` TINYINT NOT NULL DEFAULT 0,
  `start_date` DATE NULL,
  `target_date` DATE NULL,
  `completed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_tickets_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `fk_tickets_status` FOREIGN KEY (`status_id`) REFERENCES `ticket_statuses`(`id`),
  CONSTRAINT `fk_tickets_priority` FOREIGN KEY (`priority_id`) REFERENCES `ticket_priorities`(`id`),
  CONSTRAINT `fk_tickets_epic` FOREIGN KEY (`epic_id`) REFERENCES `epics`(`id`),
  CONSTRAINT `fk_tickets_creator` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `ck_ticket_progress` CHECK (`progress_percent` BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE `ticket_assignees` (
  `ticket_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `assigned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ticket_id`, `user_id`),
  CONSTRAINT `fk_ticket_assignees_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets`(`id`),
  CONSTRAINT `fk_ticket_assignees_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `notifications` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `notification_type` VARCHAR(50) NOT NULL,
  `title` VARCHAR(500) NULL,
  `context_data` JSON NOT NULL,
  `read_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE INDEX `idx_users_google_login` ON `users`(`google_identifier`, `is_active`);
CREATE INDEX `idx_project_members_project` ON `project_members`(`project_id`, `user_id`);
CREATE INDEX `idx_external_credentials_verify` ON `external_access_credentials`(`credential_identifier`, `is_active`, `expires_at`);
CREATE INDEX `idx_external_access_events` ON `external_access_events`(`credential_id`, `occurred_at`);
CREATE INDEX `idx_statuses_board_sequence` ON `ticket_statuses`(`project_id`, `sequence_number`);
CREATE INDEX `idx_tickets_board` ON `tickets`(`project_id`, `status_id`, `board_position`);
CREATE INDEX `idx_tickets_timeline` ON `tickets`(`project_id`, `target_date`);
CREATE INDEX `idx_ticket_assignees_user` ON `ticket_assignees`(`user_id`, `ticket_id`);
CREATE INDEX `idx_notifications_unread` ON `notifications`(`user_id`, `read_at`, `created_at`);
