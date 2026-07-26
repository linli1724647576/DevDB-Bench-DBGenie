CREATE TABLE `activities` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `epics` (
  `id` BIGINT NOT NULL,
  `project_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `starts_at` DATE NOT NULL,
  `ends_at` DATE NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  `parent_id` BIGINT,
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
  PRIMARY KEY (`id`)
);

CREATE TABLE `jobs` (
  `id` BIGINT NOT NULL,
  `queue` VARCHAR(255) NOT NULL,
  `payload` TEXT NOT NULL,
  `attempts` SMALLINT NOT NULL,
  `reserved_at` INTEGER,
  `available_at` INTEGER NOT NULL,
  `created_at` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `media` (
  `id` BIGINT NOT NULL,
  `model_type` VARCHAR(255) NOT NULL,
  `model_id` BIGINT NOT NULL,
  `uuid` VARCHAR(36),
  `collection_name` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `mime_type` VARCHAR(255),
  `disk` VARCHAR(255) NOT NULL,
  `conversions_disk` VARCHAR(255),
  `size` BIGINT NOT NULL,
  `manipulations` TEXT NOT NULL,
  `custom_properties` TEXT NOT NULL,
  `generated_conversions` TEXT NOT NULL,
  `responsive_images` TEXT NOT NULL,
  `order_column` INTEGER,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `migrations` (
  `id` INTEGER NOT NULL,
  `migration` VARCHAR(255) NOT NULL,
  `batch` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `model_has_permissions` (
  `permission_id` BIGINT NOT NULL,
  `model_type` VARCHAR(255) NOT NULL,
  `model_id` BIGINT NOT NULL,
  PRIMARY KEY (`permission_id`, `model_id`, `model_type`)
);

CREATE TABLE `model_has_roles` (
  `role_id` BIGINT NOT NULL,
  `model_type` VARCHAR(255) NOT NULL,
  `model_id` BIGINT NOT NULL,
  PRIMARY KEY (`role_id`, `model_id`, `model_type`)
);

CREATE TABLE `notifications` (
  `id` VARCHAR(36) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `notifiable_type` VARCHAR(255) NOT NULL,
  `notifiable_id` BIGINT NOT NULL,
  `data` TEXT NOT NULL,
  `read_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `password_resets` (
  `email` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` DATETIME
);

CREATE TABLE `pending_user_emails` (
  `id` BIGINT NOT NULL,
  `user_type` VARCHAR(255) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `permissions` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `guard_name` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `personal_access_tokens` (
  `id` BIGINT NOT NULL,
  `tokenable_type` VARCHAR(255) NOT NULL,
  `tokenable_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `token` VARCHAR(64) NOT NULL,
  `abilities` TEXT,
  `last_used_at` DATETIME,
  `expires_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `project_favorites` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `project_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `project_statuses` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `color` VARCHAR(255) NOT NULL,
  `is_default` TINYINT(1) NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `project_users` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `project_id` BIGINT NOT NULL,
  `role` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `projects` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `owner_id` BIGINT NOT NULL,
  `status_id` BIGINT NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `ticket_prefix` VARCHAR(255) NOT NULL,
  `status_type` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `role_has_permissions` (
  `permission_id` BIGINT NOT NULL,
  `role_id` BIGINT NOT NULL,
  PRIMARY KEY (`permission_id`, `role_id`)
);

CREATE TABLE `roles` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `guard_name` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `settings` (
  `id` BIGINT NOT NULL,
  `group` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `locked` TINYINT(1) NOT NULL,
  `payload` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `socialite_users` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `provider` VARCHAR(255) NOT NULL,
  `provider_id` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_activities` (
  `id` BIGINT NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `old_status_id` BIGINT NOT NULL,
  `new_status_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_comments` (
  `id` BIGINT NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `content` TEXT NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_hours` (
  `id` BIGINT NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `value` DOUBLE(8,2) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `comment` TEXT,
  `activity_id` BIGINT,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_priorities` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `color` VARCHAR(255) NOT NULL,
  `is_default` TINYINT(1) NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_relations` (
  `id` BIGINT NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `relation_id` BIGINT NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `sort` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_statuses` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `color` VARCHAR(255) NOT NULL,
  `is_default` TINYINT(1) NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `order` INTEGER NOT NULL,
  `project_id` BIGINT,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_subscribers` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_types` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `icon` VARCHAR(255) NOT NULL,
  `color` VARCHAR(255) NOT NULL,
  `is_default` TINYINT(1) NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `tickets` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `content` TEXT NOT NULL,
  `owner_id` BIGINT NOT NULL,
  `responsible_id` BIGINT,
  `status_id` BIGINT NOT NULL,
  `project_id` BIGINT NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `code` VARCHAR(255) NOT NULL,
  `type_id` BIGINT NOT NULL,
  `order` INTEGER NOT NULL,
  `priority_id` BIGINT NOT NULL,
  `estimation` DOUBLE(8,2),
  `epic_id` BIGINT,
  PRIMARY KEY (`id`)
);

CREATE TABLE `time_sheet_cells` (
  `id` BIGINT NOT NULL,
  `time_sheet_id` BIGINT NOT NULL,
  `value` DOUBLE(8,2) NOT NULL,
  `is_trip` TINYINT(1) NOT NULL,
  `comment` TEXT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `date` DATE NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `time_sheets` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `project_id` BIGINT,
  `task` TEXT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `users` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `email_verified_at` DATETIME,
  `password` VARCHAR(255),
  `two_factor_secret` TEXT,
  `two_factor_recovery_codes` TEXT,
  `two_factor_confirmed_at` DATETIME,
  `remember_token` VARCHAR(100),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  `creation_token` VARCHAR(36),
  PRIMARY KEY (`id`)
);

CREATE INDEX `idx_password_resets_email_1` ON `password_resets` (`email`);

ALTER TABLE `epics` ADD CONSTRAINT `fk_epics_parent_id_1` FOREIGN KEY (`parent_id`) REFERENCES `epics` (`id`);

ALTER TABLE `model_has_permissions` ADD CONSTRAINT `fk_model_has_permissions_permission_id_1` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`);

ALTER TABLE `model_has_roles` ADD CONSTRAINT `fk_model_has_roles_role_id_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);

ALTER TABLE `project_favorites` ADD CONSTRAINT `fk_project_favorites_project_id_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`);

ALTER TABLE `project_users` ADD CONSTRAINT `fk_project_users_project_id_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`);

ALTER TABLE `projects` ADD CONSTRAINT `fk_projects_owner_id_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`);

ALTER TABLE `role_has_permissions` ADD CONSTRAINT `fk_role_has_permissions_permission_id_1` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`);

ALTER TABLE `ticket_activities` ADD CONSTRAINT `fk_ticket_activities_new_status_id_1` FOREIGN KEY (`new_status_id`) REFERENCES `ticket_statuses` (`id`);

ALTER TABLE `ticket_comments` ADD CONSTRAINT `fk_ticket_comments_ticket_id_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`);

ALTER TABLE `ticket_hours` ADD CONSTRAINT `fk_ticket_hours_activity_id_1` FOREIGN KEY (`activity_id`) REFERENCES `activities` (`id`);

ALTER TABLE `ticket_relations` ADD CONSTRAINT `fk_ticket_relations_relation_id_1` FOREIGN KEY (`relation_id`) REFERENCES `tickets` (`id`);

ALTER TABLE `ticket_statuses` ADD CONSTRAINT `fk_ticket_statuses_project_id_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`);

ALTER TABLE `ticket_subscribers` ADD CONSTRAINT `fk_ticket_subscribers_ticket_id_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`);

ALTER TABLE `tickets` ADD CONSTRAINT `fk_tickets_epic_id_1` FOREIGN KEY (`epic_id`) REFERENCES `epics` (`id`);

ALTER TABLE `time_sheet_cells` ADD CONSTRAINT `fk_time_sheet_cells_time_sheet_id_1` FOREIGN KEY (`time_sheet_id`) REFERENCES `time_sheets` (`id`);

ALTER TABLE `time_sheets` ADD CONSTRAINT `fk_time_sheets_project_id_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`);
