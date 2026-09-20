CREATE TABLE `roles` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_name` (`name`)
) ENGINE=InnoDB;

CREATE TABLE `policies` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  `resource` VARCHAR(150) NOT NULL,
  `action` VARCHAR(100) NOT NULL,
  `conditions` JSON NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_policies_resource_action` (`resource`, `action`)
) ENGINE=InnoDB;

CREATE TABLE `role_policies` (
  `role_id` BIGINT NOT NULL,
  `policy_id` BIGINT NOT NULL,
  PRIMARY KEY (`role_id`, `policy_id`),
  CONSTRAINT `fk_role_policies_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`),
  CONSTRAINT `fk_role_policies_policy` FOREIGN KEY (`policy_id`) REFERENCES `policies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `schools` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `country` VARCHAR(100) NULL,
  `city` VARCHAR(100) NULL,
  `metadata` JSON NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(320) NOT NULL,
  `password_hash` VARCHAR(500) NULL,
  `facebook_identifier` VARCHAR(255) NULL,
  `invited_by_user_id` BIGINT NULL,
  `school_id` BIGINT NULL,
  `first_name` VARCHAR(150) NULL,
  `last_name` VARCHAR(150) NULL,
  `account_status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `activated_at` DATETIME NULL,
  `last_login_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_facebook` (`facebook_identifier`),
  CONSTRAINT `fk_users_inviter` FOREIGN KEY (`invited_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_users_school` FOREIGN KEY (`school_id`) REFERENCES `schools`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `user_profiles` (
  `user_id` BIGINT NOT NULL,
  `display_name` VARCHAR(255) NULL,
  `bio` TEXT NULL,
  `avatar_url` VARCHAR(1000) NULL,
  `birth_date` DATE NULL,
  `education_level` VARCHAR(100) NULL,
  `profile_data` JSON NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_user_profiles_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `social_logins` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `provider` VARCHAR(50) NOT NULL,
  `provider_identifier` VARCHAR(255) NOT NULL,
  `profile_data` JSON NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_social_login_provider` (`provider`, `provider_identifier`),
  CONSTRAINT `fk_social_logins_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `invitations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `inviter_user_id` BIGINT NOT NULL,
  `invitee_email` VARCHAR(320) NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `expires_at` DATETIME NULL,
  `accepted_by_user_id` BIGINT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_invitations_token` (`token_hash`),
  CONSTRAINT `fk_invitations_inviter` FOREIGN KEY (`inviter_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_invitations_accepted_user` FOREIGN KEY (`accepted_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `password_reset_tokens` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `token_hash` VARCHAR(255) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `used_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_password_reset_token` (`token_hash`),
  CONSTRAINT `fk_password_reset_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `user_roles` (
  `user_id` BIGINT NOT NULL,
  `role_id` BIGINT NOT NULL,
  `assigned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`, `role_id`),
  CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `api_clients` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  `secret_hash` VARCHAR(500) NOT NULL,
  `role_id` BIGINT NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `last_used_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_api_clients_name` (`name`),
  CONSTRAINT `fk_api_clients_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `courses` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(500) NOT NULL,
  `description` TEXT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'draft',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `course_enrollments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `course_id` BIGINT NOT NULL,
  `progress_percent` TINYINT NOT NULL DEFAULT 0,
  `status` VARCHAR(30) NOT NULL DEFAULT 'enrolled',
  `enrolled_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `completed_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_course_enrollment` (`user_id`, `course_id`),
  CONSTRAINT `fk_enrollments_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_enrollments_course` FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`),
  CONSTRAINT `ck_enrollment_progress` CHECK (`progress_percent` BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE `course_feedback` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `course_id` BIGINT NOT NULL,
  `rating` TINYINT NOT NULL,
  `feedback` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_course_feedback` (`user_id`, `course_id`),
  CONSTRAINT `fk_course_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_course_feedback_course` FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`),
  CONSTRAINT `ck_course_rating` CHECK (`rating` BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE `comments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `course_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `parent_comment_id` BIGINT NULL,
  `content` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_comments_course` FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`),
  CONSTRAINT `fk_comments_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_comments_parent` FOREIGN KEY (`parent_comment_id`) REFERENCES `comments`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `comment_reactions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `comment_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `reaction_type` VARCHAR(30) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_comment_reaction` (`comment_id`, `user_id`, `reaction_type`),
  CONSTRAINT `fk_comment_reactions_comment` FOREIGN KEY (`comment_id`) REFERENCES `comments`(`id`),
  CONSTRAINT `fk_comment_reactions_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `communication_templates` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  `channel` VARCHAR(30) NOT NULL,
  `subject_template` TEXT NULL,
  `body_template` LONGTEXT NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_templates_name` (`name`)
) ENGINE=InnoDB;

CREATE TABLE `notifications` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `notification_type` VARCHAR(50) NOT NULL,
  `structured_content` JSON NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `delivered_at` DATETIME NULL,
  `read_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `badges` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `event_name` VARCHAR(150) NOT NULL,
  `sequence_number` INT NOT NULL,
  `icon_url` VARCHAR(1000) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_badges_event_sequence` (`event_name`, `sequence_number`)
) ENGINE=InnoDB;

CREATE TABLE `achievements` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `badge_id` BIGINT NOT NULL,
  `event_name` VARCHAR(150) NOT NULL,
  `test_identifier` VARCHAR(255) NULL,
  `course_id` BIGINT NULL,
  `social_platform` VARCHAR(80) NULL,
  `progress` DECIMAL(8,4) NOT NULL DEFAULT 0,
  `status` VARCHAR(30) NOT NULL DEFAULT 'in_progress',
  `metadata` JSON NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `earned_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_achievements_user_badge` (`user_id`, `badge_id`),
  CONSTRAINT `fk_achievements_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_achievements_badge` FOREIGN KEY (`badge_id`) REFERENCES `badges`(`id`),
  CONSTRAINT `fk_achievements_course` FOREIGN KEY (`course_id`) REFERENCES `courses`(`id`),
  CONSTRAINT `ck_achievement_progress` CHECK (`progress` >= 0)
) ENGINE=InnoDB;

CREATE INDEX `idx_users_email_facebook` ON `users`(`email`, `facebook_identifier`);
CREATE INDEX `idx_users_invited_by` ON `users`(`invited_by_user_id`);
CREATE INDEX `idx_api_clients_credentials` ON `api_clients`(`name`, `secret_hash`, `role_id`);
CREATE INDEX `idx_notifications_unread` ON `notifications`(`user_id`, `notification_type`, `is_active`, `read_at`);
CREATE INDEX `idx_badges_event_sequence` ON `badges`(`event_name`, `sequence_number`);
CREATE INDEX `idx_achievements_user_event` ON `achievements`(`user_id`, `event_name`, `test_identifier`);
CREATE INDEX `idx_achievements_course_share` ON `achievements`(`user_id`, `course_id`, `social_platform`);
CREATE INDEX `idx_achievements_user_status` ON `achievements`(`user_id`, `status`, `badge_id`);
CREATE INDEX `idx_achievements_badge` ON `achievements`(`badge_id`, `status`);
CREATE INDEX `idx_achievements_event` ON `achievements`(`event_name`, `status`);
