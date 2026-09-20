CREATE TABLE `roles` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `permissions` JSON,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`name`)
);

CREATE TABLE `users` (
  `id` BIGINT NOT NULL,
  `first_name` VARCHAR(255),
  `last_name` VARCHAR(255),
  `email` VARCHAR(255) NOT NULL,
  `role_id` BIGINT,
  `email_verified_at` DATETIME,
  `password` VARCHAR(255) NOT NULL,
  `tfa_secret` TEXT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`email`)
);

CREATE TABLE `password_reset_tokens` (
  `email` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  PRIMARY KEY (`email`)
);

CREATE TABLE `settings` (
  `id` BIGINT NOT NULL,
  `key` VARCHAR(255) NOT NULL,
  `value` TEXT,
  `type` VARCHAR(255) NOT NULL,
  `encrypted` TINYINT(1) NOT NULL,
  `settingable_id` INTEGER,
  `settingable_type` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`key`, `settingable_id`, `settingable_type`)
);

CREATE TABLE `extensions` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `extension` VARCHAR(255) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `enabled` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `categories` (
  `id` BIGINT NOT NULL,
  `slug` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `parent_id` BIGINT,
  `full_slug` TEXT,
  `sort` INTEGER,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`slug`)
);

CREATE TABLE `products` (
  `id` BIGINT NOT NULL,
  `category_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `image` VARCHAR(255),
  `slug` VARCHAR(255),
  `description` TEXT,
  `stock` INTEGER,
  `per_user_limit` INTEGER,
  `sort` INTEGER,
  `allow_quantity` ENUM('disabled','separated','combined') NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `currencies` (
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `prefix` VARCHAR(255),
  `suffix` VARCHAR(255),
  `format` ENUM('1.000,00','1,000.00','1 000,00','1 000.00') NOT NULL,
  PRIMARY KEY (`code`)
);

CREATE TABLE `plans` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255),
  `priceable_id` INTEGER NOT NULL,
  `priceable_type` VARCHAR(255) NOT NULL,
  `type` ENUM('free','one-time','recurring') NOT NULL,
  `billing_period` INTEGER,
  `billing_unit` ENUM('hour','day','week','month','year'),
  `sort` INTEGER,
  PRIMARY KEY (`id`)
);

CREATE TABLE `prices` (
  `id` BIGINT NOT NULL,
  `price` DECIMAL(18, 2),
  `setup_fee` DECIMAL(18, 2),
  `currency_code` VARCHAR(255) NOT NULL,
  `plan_id` BIGINT,
  PRIMARY KEY (`id`)
);

CREATE TABLE `audit_logs` (
  `id` BIGINT NOT NULL,
  `action` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255),
  `user_id` BIGINT,
  `changes` JSON,
  `created_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `config_options` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `env_variable` VARCHAR(255),
  `type` VARCHAR(255),
  `sort` INTEGER,
  `hidden` TINYINT(1) NOT NULL,
  `parent_id` BIGINT,
  `description` TEXT,
  `upgradable` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `config_option_products` (
  `id` BIGINT NOT NULL,
  `config_option_id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `tax_rates` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `rate` DECIMAL(18, 2) NOT NULL,
  `country` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`country`)
);

CREATE TABLE `coupons` (
  `id` BIGINT NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `applies_to` VARCHAR(255) NOT NULL,
  `recurring` INTEGER,
  `code` VARCHAR(255) NOT NULL,
  `value` DECIMAL(18, 2),
  `max_uses` INTEGER,
  `max_uses_per_user` INTEGER,
  `starts_at` DATETIME,
  `expires_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `orders` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `currency_code` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `services` (
  `id` BIGINT NOT NULL,
  `status` VARCHAR(255) NOT NULL,
  `order_id` BIGINT,
  `product_id` BIGINT,
  `user_id` BIGINT NOT NULL,
  `currency_code` VARCHAR(255) NOT NULL,
  `quantity` INTEGER NOT NULL,
  `price` DECIMAL(18, 2) NOT NULL,
  `plan_id` BIGINT,
  `coupon_id` BIGINT,
  `expires_at` DATETIME,
  `subscription_id` VARCHAR(255),
  `billing_agreement_id` BIGINT,
  `label` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `service_configs` (
  `id` BIGINT NOT NULL,
  `configurable_id` INTEGER NOT NULL,
  `configurable_type` VARCHAR(255) NOT NULL,
  `config_option_id` BIGINT NOT NULL,
  `config_value_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `invoices` (
  `id` BIGINT NOT NULL,
  `number` VARCHAR(255),
  `status` VARCHAR(255) NOT NULL,
  `due_at` DATE,
  `currency_code` VARCHAR(255) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`number`)
);

CREATE TABLE `invoice_items` (
  `id` BIGINT NOT NULL,
  `invoice_id` BIGINT NOT NULL,
  `price` DECIMAL(18, 2) NOT NULL,
  `quantity` INTEGER NOT NULL,
  `description` VARCHAR(255),
  `reference_id` INTEGER,
  `reference_type` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `invoice_transactions` (
  `id` BIGINT NOT NULL,
  `invoice_id` BIGINT NOT NULL,
  `gateway_id` BIGINT,
  `amount` DECIMAL(18, 2) NOT NULL,
  `fee` DECIMAL(18, 2),
  `transaction_id` VARCHAR(255),
  `status` VARCHAR(255) NOT NULL,
  `is_credit_transaction` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `coupon_products` (
  `id` BIGINT NOT NULL,
  `coupon_id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `tickets` (
  `id` BIGINT NOT NULL,
  `subject` VARCHAR(255) NOT NULL,
  `status` VARCHAR(255) NOT NULL,
  `priority` VARCHAR(255) NOT NULL,
  `department` VARCHAR(255),
  `user_id` BIGINT NOT NULL,
  `assigned_to` BIGINT,
  `service_id` BIGINT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_messages` (
  `id` BIGINT NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `message` TEXT NOT NULL,
  `ticket_mail_log_id` BIGINT,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `notification_templates` (
  `id` BIGINT NOT NULL,
  `key` VARCHAR(255) NOT NULL,
  `subject` VARCHAR(255) NOT NULL,
  `enabled` TINYINT(1) NOT NULL,
  `body` TEXT NOT NULL,
  `mail_enabled` ENUM('force','choice_on','choice_off','never') NOT NULL,
  `in_app_enabled` ENUM('force','choice_on','choice_off','never') NOT NULL,
  `in_app_title` VARCHAR(255),
  `in_app_body` TEXT,
  `in_app_url` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`key`)
);

CREATE TABLE `email_logs` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT,
  `subject` VARCHAR(255) NOT NULL,
  `to` VARCHAR(255) NOT NULL,
  `sent_at` DATETIME,
  `status` VARCHAR(255) NOT NULL,
  `error` TEXT,
  `created_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_access_tokens` (
  `id` VARCHAR(255) NOT NULL,
  `user_id` BIGINT,
  `client_id` CHAR(36) NOT NULL,
  `name` VARCHAR(255),
  `scopes` TEXT,
  `revoked` TINYINT(1) NOT NULL,
  `expires_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `oauth_clients` (
  `id` CHAR(36) NOT NULL,
  `user_id` BIGINT,
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

CREATE TABLE `service_cancellations` (
  `id` BIGINT NOT NULL,
  `service_id` BIGINT NOT NULL,
  `reason` VARCHAR(255),
  `type` ENUM('immediate','end_of_period') NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `service_upgrades` (
  `id` BIGINT NOT NULL,
  `service_id` BIGINT NOT NULL,
  `plan_id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  `invoice_id` BIGINT,
  `status` VARCHAR(255) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `product_upgrades` (
  `id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  `upgrade_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `credits` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `currency_code` VARCHAR(255) NOT NULL,
  `amount` DECIMAL(18, 2) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `debug_logs` (
  `id` BIGINT NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `context` JSON NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `api_keys` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `permissions` JSON,
  `token` VARCHAR(255) NOT NULL,
  `user_id` BIGINT,
  `enabled` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`token`)
);

CREATE TABLE `ticket_message_attachments` (
  `id` BIGINT NOT NULL,
  `filename` VARCHAR(255) NOT NULL,
  `path` VARCHAR(255) NOT NULL,
  `ticket_message_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ticket_mail_logs` (
  `id` BIGINT NOT NULL,
  `message_id` VARCHAR(255) NOT NULL,
  `subject` VARCHAR(255) NOT NULL,
  `from` VARCHAR(255) NOT NULL,
  `to` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `status` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `invoice_snapshots` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255),
  `properties` JSON,
  `tax_name` VARCHAR(255),
  `tax_rate` DECIMAL(18, 2),
  `tax_country` VARCHAR(255),
  `bill_to` TEXT,
  `invoice_id` BIGINT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `cron_stats` (
  `id` BIGINT NOT NULL,
  `key` VARCHAR(255) NOT NULL,
  `value` INTEGER NOT NULL,
  `date` DATE NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `carts` (
  `id` BIGINT NOT NULL,
  `ulid` VARCHAR(255) NOT NULL,
  `user_id` BIGINT,
  `coupon_id` BIGINT,
  `currency_code` VARCHAR(255) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`ulid`)
);

CREATE TABLE `cart_items` (
  `id` BIGINT NOT NULL,
  `cart_id` BIGINT NOT NULL,
  `product_id` BIGINT,
  `plan_id` BIGINT,
  `config_options` JSON,
  `checkout_config` JSON,
  `quantity` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `billing_agreements` (
  `id` BIGINT NOT NULL,
  `ulid` VARCHAR(255) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `gateway_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `type` VARCHAR(255),
  `expiry` DATE,
  `external_reference` VARCHAR(255) NOT NULL,
  `deleted_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`ulid`),
  UNIQUE (`external_reference`)
);

CREATE TABLE `user_sessions` (
  `id` BIGINT NOT NULL,
  `ulid` VARCHAR(255) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `ip_address` VARCHAR(255),
  `user_agent` VARCHAR(255),
  `last_activity` DATETIME NOT NULL,
  `expires_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`ulid`)
);

CREATE TABLE `user_authentication_logs` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `ip_address` VARCHAR(255) NOT NULL,
  `last_used_at` DATETIME NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `notification_preferences` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `notification_template_id` BIGINT NOT NULL,
  `mail_enabled` TINYINT(1) NOT NULL,
  `in_app_enabled` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `notification_subscriptions` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `endpoint` VARCHAR(255) NOT NULL,
  `p256dh_key` TEXT NOT NULL,
  `auth_key` TEXT NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`endpoint`)
);

CREATE TABLE `notifications` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `url` VARCHAR(255),
  `read_at` DATETIME,
  `show_in_app` TINYINT(1) NOT NULL,
  `show_as_push` TINYINT(1) NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `ext_affiliates` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `code` VARCHAR(255) NOT NULL,
  `enabled` TINYINT(1) NOT NULL,
  `reward` INTEGER,
  `discount` INTEGER,
  `visitors` INTEGER NOT NULL,
  `signups` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`),
  UNIQUE (`code`)
);

CREATE TABLE `ext_affiliate_orders` (
  `id` BIGINT NOT NULL,
  `affiliate_id` BIGINT NOT NULL,
  `order_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`order_id`)
);

CREATE INDEX `idx_users_role_id_1` ON `users` (`role_id`);

CREATE INDEX `idx_oauth_access_tokens_user_id_1` ON `oauth_access_tokens` (`user_id`);

CREATE INDEX `idx_oauth_clients_user_id_1` ON `oauth_clients` (`user_id`);

CREATE INDEX `idx_cron_stats_date_1` ON `cron_stats` (`date`);

CREATE INDEX `idx_user_sessions_ulid_1` ON `user_sessions` (`ulid`);

CREATE INDEX `idx_user_authentication_logs_user_id_ip_address_1` ON `user_authentication_logs` (`user_id`, `ip_address`);

CREATE INDEX `idx_categories_parent` ON `categories` (`parent_id`);
CREATE INDEX `idx_products_category` ON `products` (`category_id`);
CREATE INDEX `idx_products_slug` ON `products` (`slug`);
CREATE INDEX `idx_plans_priceable` ON `plans` (`priceable_type`, `priceable_id`);
CREATE INDEX `idx_prices_plan_currency` ON `prices` (`plan_id`, `currency_code`);
CREATE INDEX `idx_auditlogs_user_created` ON `audit_logs` (`user_id`, `created_at`);
CREATE INDEX `idx_configoptions_parent` ON `config_options` (`parent_id`);
CREATE INDEX `idx_configproducts_product` ON `config_option_products` (`product_id`, `config_option_id`);
CREATE INDEX `idx_taxrates_country` ON `tax_rates` (`country`);
CREATE INDEX `idx_coupons_code_expiry` ON `coupons` (`code`, `expires_at`);
CREATE INDEX `idx_orders_user_created` ON `orders` (`user_id`, `created_at`);
CREATE INDEX `idx_services_user_status` ON `services` (`user_id`, `status`);
CREATE INDEX `idx_services_expiry_status` ON `services` (`expires_at`, `status`);
CREATE INDEX `idx_services_product` ON `services` (`product_id`);
CREATE INDEX `idx_serviceconfigs_option` ON `service_configs` (`config_option_id`);
CREATE INDEX `idx_invoices_user_status` ON `invoices` (`user_id`, `status`);
CREATE INDEX `idx_invoices_due_status` ON `invoices` (`due_at`, `status`);
CREATE INDEX `idx_invoiceitems_invoice` ON `invoice_items` (`invoice_id`);
CREATE INDEX `idx_transactions_invoice_status` ON `invoice_transactions` (`invoice_id`, `status`);
CREATE INDEX `idx_couponproducts_product` ON `coupon_products` (`product_id`, `coupon_id`);
CREATE INDEX `idx_tickets_user_status` ON `tickets` (`user_id`, `status`);
CREATE INDEX `idx_tickets_assigned_status` ON `tickets` (`assigned_to`, `status`);
CREATE INDEX `idx_tickets_service` ON `tickets` (`service_id`);
CREATE INDEX `idx_ticketmessages_ticket_created` ON `ticket_messages` (`ticket_id`, `created_at`);
CREATE INDEX `idx_emaillogs_user_status` ON `email_logs` (`user_id`, `status`);
CREATE INDEX `idx_oauth_tokens_client_revoked` ON `oauth_access_tokens` (`client_id`, `revoked`);
CREATE INDEX `idx_servicecancellations_service` ON `service_cancellations` (`service_id`);
CREATE INDEX `idx_serviceupgrades_service_status` ON `service_upgrades` (`service_id`, `status`);
CREATE INDEX `idx_productupgrades_product` ON `product_upgrades` (`product_id`);
CREATE INDEX `idx_credits_user_currency` ON `credits` (`user_id`, `currency_code`);
CREATE INDEX `idx_apikeys_user_enabled` ON `api_keys` (`user_id`, `enabled`);
CREATE INDEX `idx_attachments_message` ON `ticket_message_attachments` (`ticket_message_id`);
CREATE INDEX `idx_maillogs_message_status` ON `ticket_mail_logs` (`message_id`, `status`);
CREATE INDEX `idx_invoicesnapshots_invoice` ON `invoice_snapshots` (`invoice_id`);
CREATE INDEX `idx_cronstats_key_date` ON `cron_stats` (`key`, `date`);
CREATE INDEX `idx_carts_user_created` ON `carts` (`user_id`, `created_at`);
CREATE INDEX `idx_cartitems_cart` ON `cart_items` (`cart_id`);
CREATE INDEX `idx_billingagreements_user` ON `billing_agreements` (`user_id`);
CREATE INDEX `idx_usersessions_user_expiry` ON `user_sessions` (`user_id`, `expires_at`);
CREATE INDEX `idx_notificationpreferences_user` ON `notification_preferences` (`user_id`, `notification_template_id`);
CREATE INDEX `idx_pushsubscriptions_user` ON `notification_subscriptions` (`user_id`);
CREATE INDEX `idx_notifications_user_unread` ON `notifications` (`user_id`, `read_at`);
CREATE INDEX `idx_affiliates_user` ON `ext_affiliates` (`user_id`);
CREATE INDEX `idx_affiliateorders_affiliate` ON `ext_affiliate_orders` (`affiliate_id`);

ALTER TABLE `categories` ADD CONSTRAINT `fk_categories_parent_id_1` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`);

ALTER TABLE `products` ADD CONSTRAINT `fk_products_category_id_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`);

ALTER TABLE `prices` ADD CONSTRAINT `fk_prices_plan_id_1` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`);

ALTER TABLE `audit_logs` ADD CONSTRAINT `fk_audit_logs_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `config_options` ADD CONSTRAINT `fk_config_options_parent_id_1` FOREIGN KEY (`parent_id`) REFERENCES `config_options` (`id`);

ALTER TABLE `config_option_products` ADD CONSTRAINT `fk_config_option_products_config_option_id_1` FOREIGN KEY (`config_option_id`) REFERENCES `config_options` (`id`);

ALTER TABLE `config_option_products` ADD CONSTRAINT `fk_config_option_products_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `orders` ADD CONSTRAINT `fk_orders_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `services` ADD CONSTRAINT `fk_services_order_id_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`);

ALTER TABLE `services` ADD CONSTRAINT `fk_services_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `services` ADD CONSTRAINT `fk_services_user_id_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `services` ADD CONSTRAINT `fk_services_plan_id_4` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`);

ALTER TABLE `services` ADD CONSTRAINT `fk_services_coupon_id_5` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`id`);

ALTER TABLE `services` ADD CONSTRAINT `fk_services_billing_agreement_id_6` FOREIGN KEY (`billing_agreement_id`) REFERENCES `billing_agreements` (`id`);

ALTER TABLE `service_configs` ADD CONSTRAINT `fk_service_configs_config_option_id_1` FOREIGN KEY (`config_option_id`) REFERENCES `config_options` (`id`);

ALTER TABLE `service_configs` ADD CONSTRAINT `fk_service_configs_config_value_id_2` FOREIGN KEY (`config_value_id`) REFERENCES `config_options` (`id`);

ALTER TABLE `invoices` ADD CONSTRAINT `fk_invoices_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `invoice_items` ADD CONSTRAINT `fk_invoice_items_invoice_id_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`);

ALTER TABLE `invoice_transactions` ADD CONSTRAINT `fk_invoice_transactions_invoice_id_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`);

ALTER TABLE `invoice_transactions` ADD CONSTRAINT `fk_invoice_transactions_gateway_id_2` FOREIGN KEY (`gateway_id`) REFERENCES `extensions` (`id`);

ALTER TABLE `coupon_products` ADD CONSTRAINT `fk_coupon_products_coupon_id_1` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`id`);

ALTER TABLE `coupon_products` ADD CONSTRAINT `fk_coupon_products_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `tickets` ADD CONSTRAINT `fk_tickets_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `tickets` ADD CONSTRAINT `fk_tickets_assigned_to_2` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`);

ALTER TABLE `tickets` ADD CONSTRAINT `fk_tickets_service_id_3` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`);

ALTER TABLE `ticket_messages` ADD CONSTRAINT `fk_ticket_messages_ticket_id_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`);

ALTER TABLE `ticket_messages` ADD CONSTRAINT `fk_ticket_messages_user_id_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `ticket_messages` ADD CONSTRAINT `fk_ticket_messages_ticket_mail_log_id_3` FOREIGN KEY (`ticket_mail_log_id`) REFERENCES `ticket_mail_logs` (`id`);

ALTER TABLE `email_logs` ADD CONSTRAINT `fk_email_logs_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `service_cancellations` ADD CONSTRAINT `fk_service_cancellations_service_id_1` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`);

ALTER TABLE `service_upgrades` ADD CONSTRAINT `fk_service_upgrades_service_id_1` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`);

ALTER TABLE `service_upgrades` ADD CONSTRAINT `fk_service_upgrades_plan_id_2` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`);

ALTER TABLE `service_upgrades` ADD CONSTRAINT `fk_service_upgrades_product_id_3` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `service_upgrades` ADD CONSTRAINT `fk_service_upgrades_invoice_id_4` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`);

ALTER TABLE `product_upgrades` ADD CONSTRAINT `fk_product_upgrades_product_id_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `product_upgrades` ADD CONSTRAINT `fk_product_upgrades_upgrade_id_2` FOREIGN KEY (`upgrade_id`) REFERENCES `products` (`id`);

ALTER TABLE `credits` ADD CONSTRAINT `fk_credits_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `api_keys` ADD CONSTRAINT `fk_api_keys_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `ticket_message_attachments` ADD CONSTRAINT `fk_ticket_message_attachments_ticket_message_id_1` FOREIGN KEY (`ticket_message_id`) REFERENCES `ticket_messages` (`id`);

ALTER TABLE `invoice_snapshots` ADD CONSTRAINT `fk_invoice_snapshots_invoice_id_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`);

ALTER TABLE `carts` ADD CONSTRAINT `fk_carts_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `carts` ADD CONSTRAINT `fk_carts_coupon_id_2` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`id`);

ALTER TABLE `cart_items` ADD CONSTRAINT `fk_cart_items_cart_id_1` FOREIGN KEY (`cart_id`) REFERENCES `carts` (`id`);

ALTER TABLE `cart_items` ADD CONSTRAINT `fk_cart_items_product_id_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `cart_items` ADD CONSTRAINT `fk_cart_items_plan_id_3` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`);

ALTER TABLE `billing_agreements` ADD CONSTRAINT `fk_billing_agreements_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `billing_agreements` ADD CONSTRAINT `fk_billing_agreements_gateway_id_2` FOREIGN KEY (`gateway_id`) REFERENCES `extensions` (`id`);

ALTER TABLE `user_sessions` ADD CONSTRAINT `fk_user_sessions_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_authentication_logs` ADD CONSTRAINT `fk_user_authentication_logs_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `notification_preferences` ADD CONSTRAINT `fk_notification_preferences_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `notification_preferences` ADD CONSTRAINT `fk_notification_preferences_notification_template_id_2` FOREIGN KEY (`notification_template_id`) REFERENCES `notification_templates` (`id`);

ALTER TABLE `notification_subscriptions` ADD CONSTRAINT `fk_notification_subscriptions_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `notifications` ADD CONSTRAINT `fk_notifications_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `ext_affiliates` ADD CONSTRAINT `fk_ext_affiliates_user_id_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `ext_affiliate_orders` ADD CONSTRAINT `fk_ext_affiliate_orders_affiliate_id_1` FOREIGN KEY (`affiliate_id`) REFERENCES `ext_affiliates` (`id`);

ALTER TABLE `ext_affiliate_orders` ADD CONSTRAINT `fk_ext_affiliate_orders_order_id_2` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`);
