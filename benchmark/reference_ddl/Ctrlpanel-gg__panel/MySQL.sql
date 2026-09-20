CREATE TABLE `activity_log` (
  `id` BIGINT NOT NULL,
  `log_name` VARCHAR(255),
  `description` TEXT NOT NULL,
  `subject_type` VARCHAR(255),
  `subject_id` CHAR(36),
  `causer_type` VARCHAR(255),
  `causer_id` CHAR(36),
  `properties` TEXT,
  `event` VARCHAR(255),
  `batch_uuid` CHAR(36),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `application_apis` (
  `token` VARCHAR(255) NOT NULL,
  `memo` VARCHAR(255),
  `last_used` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`token`),
  UNIQUE (`token`)
);

CREATE TABLE `coupons` (
  `id` BIGINT NOT NULL,
  `code` VARCHAR(255) NOT NULL,
  `type` ENUM('amount','percentage') NOT NULL,
  `value` DECIMAL(18, 2) NOT NULL,
  `uses` INTEGER NOT NULL,
  `max_uses` INTEGER NOT NULL,
  `expires_at` DATETIME,
  `min_product_price` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`code`)
);

CREATE TABLE `discord_users` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `username` VARCHAR(255) NOT NULL,
  `avatar` VARCHAR(255),
  `discriminator` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255),
  `verified` TINYINT(1),
  `public_flags` INTEGER,
  `flags` INTEGER,
  `locale` VARCHAR(255),
  `mfa_enabled` TINYINT(1),
  `premium_type` INTEGER,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `egg_product` (
  `egg_id` BIGINT NOT NULL,
  `product_id` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME
);

CREATE TABLE `eggs` (
  `id` BIGINT NOT NULL,
  `nest_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `docker_image` VARCHAR(255) NOT NULL,
  `startup` TEXT NOT NULL,
  `environment` JSON NOT NULL,
  `disabled` TINYINT(1) NOT NULL,
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

CREATE TABLE `invoices` (
  `id` BIGINT NOT NULL,
  `invoice_name` VARCHAR(255) NOT NULL,
  `invoice_user` VARCHAR(255) NOT NULL,
  `payment_id` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
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

CREATE TABLE `locations` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
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

CREATE TABLE `nests` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `disabled` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `node_product` (
  `node_id` BIGINT NOT NULL,
  `product_id` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME
);

CREATE TABLE `nodes` (
  `id` BIGINT NOT NULL,
  `location_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `disabled` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
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

CREATE TABLE `partner_discounts` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `partner_discount` INTEGER NOT NULL,
  `registered_user_discount` INTEGER NOT NULL,
  `referral_system_commission` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `password_resets` (
  `email` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` DATETIME
);

CREATE TABLE `payments` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `payment_id` VARCHAR(255),
  `type` VARCHAR(255),
  `status` VARCHAR(255),
  `amount` VARCHAR(255),
  `price` DECIMAL(18, 2),
  `currency_code` VARCHAR(255) NOT NULL,
  `tax_value` DECIMAL(18, 2),
  `tax_percent` FLOAT,
  `total_price` DECIMAL(18, 2),
  `payment_method` VARCHAR(255) NOT NULL,
  `shop_item_product_id` VARCHAR(255),
  `coupon_code` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `permissions` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `guard_name` VARCHAR(255) NOT NULL,
  `readable_name` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`name`, `guard_name`)
);

CREATE TABLE `products` (
  `id` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255),
  `description` VARCHAR(255),
  `price` BIGINT NOT NULL,
  `memory` INTEGER NOT NULL,
  `cpu` INTEGER NOT NULL,
  `swap` INTEGER NOT NULL,
  `disk` INTEGER NOT NULL,
  `io` INTEGER NOT NULL,
  `databases` INTEGER NOT NULL,
  `backups` INTEGER NOT NULL,
  `allocations` INTEGER NOT NULL,
  `disabled` TINYINT(1) NOT NULL,
  `minimum_credits` BIGINT,
  `minimum_credits_old` BIGINT,
  `oom_killer` TINYINT(1) NOT NULL,
  `billing_period` VARCHAR(255) NOT NULL,
  `serverlimit` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
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
  `color` VARCHAR(255),
  `power` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`name`, `guard_name`)
);

CREATE TABLE `servers` (
  `id` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `suspended` DATETIME,
  `identifier` VARCHAR(255),
  `pterodactyl_id` INTEGER,
  `user_id` BIGINT NOT NULL,
  `product_id` VARCHAR(255) NOT NULL,
  `status` VARCHAR(255) NOT NULL,
  `suspension_warning_sent_at` DATETIME,
  `last_billed` DATETIME,
  `canceled` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `settings` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `payload` JSON,
  `group` VARCHAR(255) NOT NULL,
  `locked` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`group`, `name`)
);

CREATE TABLE `shop_products` (
  `id` VARCHAR(255) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `price` DECIMAL(18, 2) NOT NULL,
  `quantity` INTEGER NOT NULL,
  `description` VARCHAR(255) NOT NULL,
  `currency_code` VARCHAR(255) NOT NULL,
  `disabled` TINYINT(1) NOT NULL,
  `display` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_blacklists` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `status` VARCHAR(255) NOT NULL,
  `reason` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_categories` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_comments` (
  `id` INTEGER NOT NULL,
  `ticket_id` INTEGER NOT NULL,
  `user_id` INTEGER NOT NULL,
  `ticketcomment` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `tickets` (
  `id` INTEGER NOT NULL,
  `user_id` INTEGER NOT NULL,
  `ticketcategory_id` INTEGER NOT NULL,
  `ticket_id` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `priority` VARCHAR(255) NOT NULL,
  `message` TEXT NOT NULL,
  `status` VARCHAR(255) NOT NULL,
  `server` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`ticket_id`)
);

CREATE TABLE `user_coupons` (
  `user_id` BIGINT NOT NULL,
  `coupon_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME
);

CREATE TABLE `user_referrals` (
  `referral_id` BIGINT,
  `registered_user_id` BIGINT,
  `created_at` DATETIME,
  `updated_at` DATETIME
);

CREATE TABLE `user_voucher` (
  `user_id` BIGINT NOT NULL,
  `voucher_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME
);

CREATE TABLE `users` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `credits` DECIMAL(18, 2) NOT NULL,
  `server_limit` INTEGER NOT NULL,
  `pterodactyl_id` VARCHAR(255),
  `avatar` TEXT,
  `email` VARCHAR(255) NOT NULL,
  `email_verified_at` DATETIME,
  `password` VARCHAR(255) NOT NULL,
  `remember_token` VARCHAR(255),
  `ip` VARCHAR(255),
  `last_seen` DATETIME,
  `discord_verified_at` DATETIME,
  `suspended` TINYINT(1) NOT NULL,
  `referral_code` VARCHAR(255),
  `email_verified_reward` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`email`)
);

CREATE TABLE `useful_links` (
  `id` BIGINT NOT NULL,
  `icon` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `link` VARCHAR(255),
  `description` TEXT NOT NULL,
  `position` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `vouchers` (
  `id` BIGINT NOT NULL,
  `code` VARCHAR(255) NOT NULL,
  `memo` VARCHAR(255),
  `credits` FLOAT NOT NULL,
  `uses` INTEGER NOT NULL,
  `expires_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`code`)
);

CREATE INDEX `idx_activity_log_log_name_1` ON `activity_log` (`log_name`);

CREATE INDEX `idx_activity_log_subject_type_subject_id_2` ON `activity_log` (`subject_type`, `subject_id`);

CREATE INDEX `idx_activity_log_causer_type_causer_id_3` ON `activity_log` (`causer_type`, `causer_id`);

CREATE INDEX `idx_jobs_queue_1` ON `jobs` (`queue`);

CREATE INDEX `idx_model_has_permissions_model_id_model_type_1` ON `model_has_permissions` (`model_id`, `model_type`);

CREATE INDEX `idx_model_has_roles_model_id_model_type_1` ON `model_has_roles` (`model_id`, `model_type`);

CREATE INDEX `idx_notifications_notifiable_type_notifiable_id_1` ON `notifications` (`notifiable_type`, `notifiable_id`);

CREATE INDEX `idx_password_resets_email_1` ON `password_resets` (`email`);

CREATE INDEX `idx_servers_status_1` ON `servers` (`status`);

CREATE INDEX `idx_settings_group_1` ON `settings` (`group`);

ALTER TABLE `egg_product` ADD CONSTRAINT `fk_egg_product_egg_id_1` FOREIGN KEY (`egg_id`) REFERENCES `eggs` (`id`);

ALTER TABLE `egg_product` ADD CONSTRAINT `fk_egg_product_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `eggs` ADD CONSTRAINT `fk_eggs_nest_id_1` FOREIGN KEY (`nest_id`) REFERENCES `nests` (`id`);

ALTER TABLE `model_has_permissions` ADD CONSTRAINT `fk_model_has_permissions_permission_id_1` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`);

ALTER TABLE `model_has_roles` ADD CONSTRAINT `fk_model_has_roles_role_id_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);

ALTER TABLE `node_product` ADD CONSTRAINT `fk_node_product_node_id_1` FOREIGN KEY (`node_id`) REFERENCES `nodes` (`id`);

ALTER TABLE `node_product` ADD CONSTRAINT `fk_node_product_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `nodes` ADD CONSTRAINT `fk_nodes_location_id_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`);

ALTER TABLE `payments` ADD CONSTRAINT `fk_payments_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `role_has_permissions` ADD CONSTRAINT `fk_role_has_permissions_permission_id_1` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`);

ALTER TABLE `role_has_permissions` ADD CONSTRAINT `fk_role_has_permissions_role_id_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);

ALTER TABLE `servers` ADD CONSTRAINT `fk_servers_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `servers` ADD CONSTRAINT `fk_servers_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `ticket_blacklists` ADD CONSTRAINT `fk_ticket_blacklists_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_coupons` ADD CONSTRAINT `fk_user_coupons_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_coupons` ADD CONSTRAINT `fk_user_coupons_coupon_id_2` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`id`);

ALTER TABLE `user_referrals` ADD CONSTRAINT `fk_user_referrals_referral_id_1` FOREIGN KEY (`referral_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_referrals` ADD CONSTRAINT `fk_user_referrals_registered_user_id_2` FOREIGN KEY (`registered_user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_voucher` ADD CONSTRAINT `fk_user_voucher_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_voucher` ADD CONSTRAINT `fk_user_voucher_voucher_id_2` FOREIGN KEY (`voucher_id`) REFERENCES `vouchers` (`id`);
