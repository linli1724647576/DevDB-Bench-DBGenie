CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(320) NOT NULL,
  `password_hash` VARCHAR(500) NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB;

CREATE TABLE `roles` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `permissions` JSON NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_name` (`name`)
) ENGINE=InnoDB;

CREATE TABLE `user_roles` (
  `user_id` BIGINT NOT NULL,
  `role_id` BIGINT NOT NULL,
  `assigned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`, `role_id`),
  CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `customers` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(320) NULL,
  `phone` VARCHAR(50) NULL,
  `address` TEXT NULL,
  `contact_info` JSON NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `vendors` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(320) NULL,
  `phone` VARCHAR(50) NULL,
  `address` TEXT NULL,
  `contact_info` JSON NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `projects` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `customer_id` BIGINT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `status` VARCHAR(40) NOT NULL DEFAULT 'active',
  `start_date` DATE NULL,
  `end_date` DATE NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_projects_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `bank_accounts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `customer_id` BIGINT NULL,
  `vendor_id` BIGINT NULL,
  `account_name` VARCHAR(255) NOT NULL,
  `bank_name` VARCHAR(255) NOT NULL,
  `account_number` VARCHAR(100) NOT NULL,
  `iban` VARCHAR(100) NULL,
  `swift_code` VARCHAR(50) NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_bank_accounts_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`),
  CONSTRAINT `fk_bank_accounts_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `vendors`(`id`),
  CONSTRAINT `ck_bank_account_partner` CHECK ((`customer_id` IS NOT NULL) + (`vendor_id` IS NOT NULL) = 1)
) ENGINE=InnoDB;

CREATE TABLE `payments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `customer_id` BIGINT NULL,
  `vendor_id` BIGINT NULL,
  `project_id` BIGINT NULL,
  `bank_account_id` BIGINT NULL,
  `created_by_user_id` BIGINT NULL,
  `business_context` VARCHAR(100) NULL,
  `amount` DECIMAL(18,2) NOT NULL,
  `payment_date` DATE NOT NULL,
  `paid_at` DATETIME NULL,
  `direction` VARCHAR(20) NOT NULL,
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_payments_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`),
  CONSTRAINT `fk_payments_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `vendors`(`id`),
  CONSTRAINT `fk_payments_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `fk_payments_bank_account` FOREIGN KEY (`bank_account_id`) REFERENCES `bank_accounts`(`id`),
  CONSTRAINT `fk_payments_creator` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `ck_payments_partner` CHECK ((`customer_id` IS NOT NULL) + (`vendor_id` IS NOT NULL) = 1),
  CONSTRAINT `ck_payments_direction` CHECK (`direction` IN ('incoming', 'outgoing')),
  CONSTRAINT `ck_payments_amount` CHECK (`amount` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `invoices` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `creator_user_id` BIGINT NOT NULL,
  `invoice_number` VARCHAR(100) NOT NULL,
  `issue_date` DATE NOT NULL,
  `due_date` DATE NULL,
  `paid_date` DATE NULL,
  `subtotal_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `discount_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `total_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `notes` TEXT NULL,
  `status` VARCHAR(40) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_invoices_number` (`invoice_number`),
  CONSTRAINT `fk_invoices_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `fk_invoices_creator` FOREIGN KEY (`creator_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `ck_invoice_amounts` CHECK (`subtotal_amount` >= 0 AND `discount_amount` >= 0 AND `total_amount` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `invoice_items` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `invoice_id` BIGINT NOT NULL,
  `line_number` INT NOT NULL,
  `description` VARCHAR(1000) NOT NULL,
  `quantity` DECIMAL(18,4) NOT NULL,
  `unit_price` DECIMAL(18,2) NOT NULL,
  `line_total` DECIMAL(18,2) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_invoice_items_line` (`invoice_id`, `line_number`),
  CONSTRAINT `fk_invoice_items_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`),
  CONSTRAINT `ck_invoice_item_values` CHECK (`quantity` > 0 AND `unit_price` >= 0 AND `line_total` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `issues` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `owner_user_id` BIGINT NULL,
  `title` VARCHAR(500) NOT NULL,
  `description` TEXT NULL,
  `status` VARCHAR(40) NOT NULL DEFAULT 'open',
  `priority` VARCHAR(30) NULL,
  `progress_percent` TINYINT NOT NULL DEFAULT 0,
  `position` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_issues_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `fk_issues_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `ck_issues_progress` CHECK (`progress_percent` BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE `tasks` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `project_id` BIGINT NOT NULL,
  `issue_id` BIGINT NULL,
  `owner_user_id` BIGINT NULL,
  `title` VARCHAR(500) NOT NULL,
  `description` TEXT NULL,
  `status` VARCHAR(40) NOT NULL DEFAULT 'open',
  `priority` VARCHAR(30) NULL,
  `progress_percent` TINYINT NOT NULL DEFAULT 0,
  `position` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_tasks_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `fk_tasks_issue` FOREIGN KEY (`issue_id`) REFERENCES `issues`(`id`),
  CONSTRAINT `fk_tasks_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `ck_tasks_progress` CHECK (`progress_percent` BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE `calendar_events` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `project_id` BIGINT NULL,
  `title` VARCHAR(500) NOT NULL,
  `description` TEXT NULL,
  `starts_at` DATETIME NOT NULL,
  `ends_at` DATETIME NULL,
  `location` VARCHAR(500) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_calendar_events_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_calendar_events_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `comments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `author_user_id` BIGINT NOT NULL,
  `project_id` BIGINT NULL,
  `subject_type` VARCHAR(60) NOT NULL,
  `subject_id` BIGINT NOT NULL,
  `content` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_comments_author` FOREIGN KEY (`author_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_comments_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `file_attachments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `uploaded_by_user_id` BIGINT NOT NULL,
  `project_id` BIGINT NULL,
  `subject_type` VARCHAR(60) NOT NULL,
  `subject_id` BIGINT NOT NULL,
  `file_name` VARCHAR(500) NOT NULL,
  `file_path` VARCHAR(1000) NOT NULL,
  `size_bytes` BIGINT NULL,
  `mime_type` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_file_attachments_user` FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_file_attachments_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
  CONSTRAINT `ck_file_size` CHECK (`size_bytes` IS NULL OR `size_bytes` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `activity_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `actor_user_id` BIGINT NULL,
  `project_id` BIGINT NULL,
  `subject_type` VARCHAR(60) NOT NULL,
  `subject_id` BIGINT NOT NULL,
  `action_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `old_values` JSON NULL,
  `new_values` JSON NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_activity_logs_actor` FOREIGN KEY (`actor_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_activity_logs_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`)
) ENGINE=InnoDB;

CREATE INDEX `idx_customers_active_name` ON `customers`(`is_active`, `name`);
CREATE INDEX `idx_vendors_active_name` ON `vendors`(`is_active`, `name`);
CREATE INDEX `idx_payments_customer_recent` ON `payments`(`customer_id`, `payment_date`, `paid_at`);
CREATE INDEX `idx_payments_vendor_recent` ON `payments`(`vendor_id`, `payment_date`, `paid_at`);
CREATE INDEX `idx_payments_daily_report` ON `payments`(`payment_date`, `direction`, `amount`);
CREATE INDEX `idx_payments_project` ON `payments`(`project_id`, `payment_date`);
CREATE INDEX `idx_invoices_project_status` ON `invoices`(`project_id`, `status`, `issue_date`);
CREATE INDEX `idx_invoice_items_invoice` ON `invoice_items`(`invoice_id`, `line_number`);
CREATE INDEX `idx_issues_project_status` ON `issues`(`project_id`, `status`, `position`);
CREATE INDEX `idx_tasks_project_status` ON `tasks`(`project_id`, `status`, `position`);
CREATE INDEX `idx_calendar_user_time` ON `calendar_events`(`user_id`, `starts_at`);
CREATE INDEX `idx_comments_subject` ON `comments`(`subject_type`, `subject_id`, `created_at`);
CREATE INDEX `idx_files_subject` ON `file_attachments`(`subject_type`, `subject_id`, `created_at`);
CREATE INDEX `idx_activity_subject` ON `activity_logs`(`subject_type`, `subject_id`, `created_at`);
