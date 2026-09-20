CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(320) NOT NULL,
  `password_hash` VARCHAR(500) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB;

CREATE TABLE `currencies` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` CHAR(3) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `symbol` VARCHAR(20) NULL,
  `decimal_places` TINYINT NOT NULL DEFAULT 2,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_currencies_code` (`code`)
) ENGINE=InnoDB;

CREATE TABLE `companies` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `default_currency_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `legal_name` VARCHAR(255) NULL,
  `registration_number` VARCHAR(100) NULL,
  `tax_identifier` VARCHAR(100) NULL,
  `locale` VARCHAR(20) NOT NULL DEFAULT 'en',
  `timezone` VARCHAR(64) NOT NULL DEFAULT 'UTC',
  `fiscal_year_start_month` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_companies_currency` FOREIGN KEY (`default_currency_id`) REFERENCES `currencies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `company_memberships` (
  `company_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `role_name` VARCHAR(100) NOT NULL,
  `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`company_id`, `user_id`),
  CONSTRAINT `fk_company_memberships_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_company_memberships_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `company_profiles` (
  `company_id` BIGINT NOT NULL,
  `logo_path` VARCHAR(1000) NULL,
  `website` VARCHAR(1000) NULL,
  `phone` VARCHAR(50) NULL,
  `email` VARCHAR(320) NULL,
  `profile_data` JSON NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`),
  CONSTRAINT `fk_company_profiles_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `company_addresses` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `address_type` VARCHAR(40) NOT NULL,
  `line_one` VARCHAR(255) NOT NULL,
  `line_two` VARCHAR(255) NULL,
  `city` VARCHAR(150) NULL,
  `region` VARCHAR(150) NULL,
  `postal_code` VARCHAR(40) NULL,
  `country_code` CHAR(2) NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_company_addresses_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `departments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `parent_id` BIGINT NULL,
  `code` VARCHAR(64) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_departments_company_code` (`company_id`, `code`),
  CONSTRAINT `fk_departments_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_departments_parent` FOREIGN KEY (`parent_id`) REFERENCES `departments`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `company_defaults` (
  `company_id` BIGINT NOT NULL,
  `default_values` JSON NOT NULL,
  `updated_by_user_id` BIGINT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`),
  CONSTRAINT `fk_company_defaults_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_company_defaults_user` FOREIGN KEY (`updated_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `document_defaults` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `document_type` VARCHAR(50) NOT NULL,
  `prefix` VARCHAR(30) NULL,
  `next_number` BIGINT NOT NULL DEFAULT 1,
  `default_terms` TEXT NULL,
  `default_notes` TEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_document_defaults_company_type` (`company_id`, `document_type`),
  CONSTRAINT `fk_document_defaults_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `contacts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `display_name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(320) NULL,
  `phone` VARCHAR(50) NULL,
  `billing_address` JSON NULL,
  `shipping_address` JSON NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_contacts_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `clients` (
  `contact_id` BIGINT NOT NULL,
  `credit_limit` DECIMAL(18,2) NULL,
  `payment_terms_days` INT NULL,
  PRIMARY KEY (`contact_id`),
  CONSTRAINT `fk_clients_contact` FOREIGN KEY (`contact_id`) REFERENCES `contacts`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `vendors` (
  `contact_id` BIGINT NOT NULL,
  `vendor_reference` VARCHAR(100) NULL,
  `payment_terms_days` INT NULL,
  PRIMARY KEY (`contact_id`),
  CONSTRAINT `fk_vendors_contact` FOREIGN KEY (`contact_id`) REFERENCES `contacts`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `accounts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `parent_account_id` BIGINT NULL,
  `code` VARCHAR(64) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `account_type` VARCHAR(50) NOT NULL,
  `normal_balance` VARCHAR(10) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_accounts_company_code` (`company_id`, `code`),
  CONSTRAINT `fk_accounts_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_accounts_parent` FOREIGN KEY (`parent_account_id`) REFERENCES `accounts`(`id`),
  CONSTRAINT `ck_accounts_balance` CHECK (`normal_balance` IN ('debit', 'credit'))
) ENGINE=InnoDB;

CREATE TABLE `bank_accounts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `ledger_account_id` BIGINT NOT NULL,
  `bank_name` VARCHAR(255) NOT NULL,
  `account_name` VARCHAR(255) NOT NULL,
  `account_number` VARCHAR(100) NOT NULL,
  `currency_id` BIGINT NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_bank_accounts_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_bank_accounts_ledger` FOREIGN KEY (`ledger_account_id`) REFERENCES `accounts`(`id`),
  CONSTRAINT `fk_bank_accounts_currency` FOREIGN KEY (`currency_id`) REFERENCES `currencies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `connected_accounts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `provider` VARCHAR(100) NOT NULL,
  `external_identifier` VARCHAR(255) NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `connection_data` JSON NULL,
  `last_synced_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_connected_accounts_provider` (`company_id`, `provider`, `external_identifier`),
  CONSTRAINT `fk_connected_accounts_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `connected_bank_accounts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `connected_account_id` BIGINT NOT NULL,
  `bank_account_id` BIGINT NOT NULL,
  `external_identifier` VARCHAR(255) NOT NULL,
  `last_balance` DECIMAL(18,2) NULL,
  `last_synced_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_connected_bank_external` (`connected_account_id`, `external_identifier`),
  CONSTRAINT `fk_connected_bank_connection` FOREIGN KEY (`connected_account_id`) REFERENCES `connected_accounts`(`id`),
  CONSTRAINT `fk_connected_bank_account` FOREIGN KEY (`bank_account_id`) REFERENCES `bank_accounts`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `offerings` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `unit_price` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `income_account_id` BIGINT NULL,
  `expense_account_id` BIGINT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_offerings_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_offerings_income_account` FOREIGN KEY (`income_account_id`) REFERENCES `accounts`(`id`),
  CONSTRAINT `fk_offerings_expense_account` FOREIGN KEY (`expense_account_id`) REFERENCES `accounts`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `accounting_periods` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `starts_on` DATE NOT NULL,
  `ends_on` DATE NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'open',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_accounting_period_company_dates` (`company_id`, `starts_on`, `ends_on`),
  CONSTRAINT `fk_accounting_periods_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `transactions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `period_id` BIGINT NULL,
  `transaction_number` VARCHAR(100) NOT NULL,
  `transaction_date` DATE NOT NULL,
  `description` TEXT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'draft',
  `created_by_user_id` BIGINT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `posted_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_transactions_company_number` (`company_id`, `transaction_number`),
  CONSTRAINT `fk_transactions_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_transactions_period` FOREIGN KEY (`period_id`) REFERENCES `accounting_periods`(`id`),
  CONSTRAINT `fk_transactions_creator` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `journal_entries` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `transaction_id` BIGINT NOT NULL,
  `ledger_account_id` BIGINT NOT NULL,
  `entry_date` DATE NOT NULL,
  `entry_type` VARCHAR(10) NOT NULL,
  `amount` DECIMAL(18,2) NOT NULL,
  `memo` VARCHAR(1000) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_journal_entries_transaction` FOREIGN KEY (`transaction_id`) REFERENCES `transactions`(`id`),
  CONSTRAINT `fk_journal_entries_account` FOREIGN KEY (`ledger_account_id`) REFERENCES `accounts`(`id`),
  CONSTRAINT `ck_journal_entry_type` CHECK (`entry_type` IN ('debit', 'credit')),
  CONSTRAINT `ck_journal_entry_amount` CHECK (`amount` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `invoices` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `client_id` BIGINT NOT NULL,
  `currency_id` BIGINT NOT NULL,
  `invoice_number` VARCHAR(100) NOT NULL,
  `issue_date` DATE NOT NULL,
  `due_date` DATE NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `subtotal_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `discount_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `tax_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `total_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `paid_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `outstanding_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `notes` TEXT NULL,
  `created_by_user_id` BIGINT NULL,
  `updated_by_user_id` BIGINT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_invoices_company_number` (`company_id`, `invoice_number`),
  CONSTRAINT `fk_invoices_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_invoices_client` FOREIGN KEY (`client_id`) REFERENCES `clients`(`contact_id`),
  CONSTRAINT `fk_invoices_currency` FOREIGN KEY (`currency_id`) REFERENCES `currencies`(`id`),
  CONSTRAINT `fk_invoices_creator` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_invoices_updater` FOREIGN KEY (`updated_by_user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `ck_invoice_amounts` CHECK (`total_amount` >= 0 AND `paid_amount` >= 0 AND `outstanding_amount` >= 0)
) ENGINE=InnoDB;

CREATE TABLE `bills` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `vendor_id` BIGINT NOT NULL,
  `currency_id` BIGINT NOT NULL,
  `bill_number` VARCHAR(100) NOT NULL,
  `issue_date` DATE NOT NULL,
  `due_date` DATE NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `total_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `paid_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `outstanding_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `notes` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_bills_company_number` (`company_id`, `bill_number`),
  CONSTRAINT `fk_bills_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_bills_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `vendors`(`contact_id`),
  CONSTRAINT `fk_bills_currency` FOREIGN KEY (`currency_id`) REFERENCES `currencies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `estimates` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `client_id` BIGINT NOT NULL,
  `currency_id` BIGINT NOT NULL,
  `estimate_number` VARCHAR(100) NOT NULL,
  `issue_date` DATE NOT NULL,
  `expires_on` DATE NULL,
  `status` VARCHAR(30) NOT NULL,
  `total_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `notes` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_estimates_company_number` (`company_id`, `estimate_number`),
  CONSTRAINT `fk_estimates_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_estimates_client` FOREIGN KEY (`client_id`) REFERENCES `clients`(`contact_id`),
  CONSTRAINT `fk_estimates_currency` FOREIGN KEY (`currency_id`) REFERENCES `currencies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `recurring_invoices` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `client_id` BIGINT NOT NULL,
  `currency_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `frequency` VARCHAR(30) NOT NULL,
  `interval_count` INT NOT NULL DEFAULT 1,
  `next_run_date` DATE NOT NULL,
  `ends_on` DATE NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'active',
  `total_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_recurring_invoices_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_recurring_invoices_client` FOREIGN KEY (`client_id`) REFERENCES `clients`(`contact_id`),
  CONSTRAINT `fk_recurring_invoices_currency` FOREIGN KEY (`currency_id`) REFERENCES `currencies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `document_line_items` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `document_type` VARCHAR(30) NOT NULL,
  `document_id` BIGINT NOT NULL,
  `line_number` INT NOT NULL,
  `offering_id` BIGINT NULL,
  `description` VARCHAR(1000) NOT NULL,
  `quantity` DECIMAL(18,4) NOT NULL,
  `unit_price` DECIMAL(18,2) NOT NULL,
  `discount_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `tax_amount` DECIMAL(18,2) NOT NULL DEFAULT 0,
  `line_total` DECIMAL(18,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_document_line_number` (`document_type`, `document_id`, `line_number`),
  CONSTRAINT `fk_document_lines_offering` FOREIGN KEY (`offering_id`) REFERENCES `offerings`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `adjustments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `adjustment_type` VARCHAR(30) NOT NULL,
  `calculation_type` VARCHAR(30) NOT NULL,
  `rate` DECIMAL(18,6) NULL,
  `fixed_amount` DECIMAL(18,2) NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_adjustments_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `document_adjustments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `adjustment_id` BIGINT NOT NULL,
  `document_type` VARCHAR(30) NOT NULL,
  `document_id` BIGINT NOT NULL,
  `amount` DECIMAL(18,2) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_document_adjustments_definition` FOREIGN KEY (`adjustment_id`) REFERENCES `adjustments`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `document_links` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `source_type` VARCHAR(30) NOT NULL,
  `source_id` BIGINT NOT NULL,
  `target_type` VARCHAR(30) NOT NULL,
  `target_id` BIGINT NOT NULL,
  `link_type` VARCHAR(50) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_document_links` (`source_type`, `source_id`, `target_type`, `target_id`, `link_type`)
) ENGINE=InnoDB;

CREATE TABLE `payments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `contact_id` BIGINT NOT NULL,
  `bank_account_id` BIGINT NULL,
  `currency_id` BIGINT NOT NULL,
  `payment_date` DATE NOT NULL,
  `amount` DECIMAL(18,2) NOT NULL,
  `direction` VARCHAR(20) NOT NULL,
  `reference` VARCHAR(255) NULL,
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_payments_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_payments_contact` FOREIGN KEY (`contact_id`) REFERENCES `contacts`(`id`),
  CONSTRAINT `fk_payments_bank` FOREIGN KEY (`bank_account_id`) REFERENCES `bank_accounts`(`id`),
  CONSTRAINT `fk_payments_currency` FOREIGN KEY (`currency_id`) REFERENCES `currencies`(`id`),
  CONSTRAINT `ck_payments_direction` CHECK (`direction` IN ('incoming', 'outgoing'))
) ENGINE=InnoDB;

CREATE TABLE `payment_applications` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `payment_id` BIGINT NOT NULL,
  `document_type` VARCHAR(30) NOT NULL,
  `document_id` BIGINT NOT NULL,
  `applied_amount` DECIMAL(18,2) NOT NULL,
  `applied_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_payment_application` (`payment_id`, `document_type`, `document_id`),
  CONSTRAINT `fk_payment_applications_payment` FOREIGN KEY (`payment_id`) REFERENCES `payments`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `budgets` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `starts_on` DATE NOT NULL,
  `ends_on` DATE NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'draft',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_budgets_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `budget_allocations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `budget_id` BIGINT NOT NULL,
  `account_id` BIGINT NOT NULL,
  `period_start` DATE NOT NULL,
  `period_end` DATE NOT NULL,
  `allocated_amount` DECIMAL(18,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_budget_allocation_period` (`budget_id`, `account_id`, `period_start`),
  CONSTRAINT `fk_budget_allocations_budget` FOREIGN KEY (`budget_id`) REFERENCES `budgets`(`id`),
  CONSTRAINT `fk_budget_allocations_account` FOREIGN KEY (`account_id`) REFERENCES `accounts`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `import_jobs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `import_type` VARCHAR(50) NOT NULL,
  `source_file` VARCHAR(1000) NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `total_rows` INT NOT NULL DEFAULT 0,
  `processed_rows` INT NOT NULL DEFAULT 0,
  `failed_rows` INT NOT NULL DEFAULT 0,
  `started_at` DATETIME NULL,
  `completed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_import_jobs_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `failed_import_rows` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `import_job_id` BIGINT NOT NULL,
  `row_number` INT NOT NULL,
  `row_data` JSON NULL,
  `error_message` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_failed_import_rows_job` FOREIGN KEY (`import_job_id`) REFERENCES `import_jobs`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `export_jobs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `export_type` VARCHAR(50) NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `output_file` VARCHAR(1000) NULL,
  `started_at` DATETIME NULL,
  `completed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_export_jobs_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `notifications` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `company_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `notification_type` VARCHAR(50) NOT NULL,
  `content` JSON NOT NULL,
  `read_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_notifications_company` FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

CREATE INDEX `idx_journal_ledger_date_type` ON `journal_entries`(`ledger_account_id`, `entry_date`, `entry_type`);
CREATE INDEX `idx_invoices_client_status` ON `invoices`(`client_id`, `status`, `outstanding_amount`);
CREATE INDEX `idx_invoices_client_aging` ON `invoices`(`client_id`, `due_date`, `status`);
CREATE INDEX `idx_accounts_company_type` ON `accounts`(`company_id`, `account_type`, `code`);
CREATE INDEX `idx_transactions_company_date` ON `transactions`(`company_id`, `transaction_date`, `status`);
CREATE INDEX `idx_contacts_company_name` ON `contacts`(`company_id`, `display_name`);
CREATE INDEX `idx_bills_vendor_due` ON `bills`(`vendor_id`, `status`, `due_date`);
CREATE INDEX `idx_payments_contact_date` ON `payments`(`contact_id`, `payment_date`);
CREATE INDEX `idx_budget_allocations_account` ON `budget_allocations`(`account_id`, `period_start`, `period_end`);
CREATE INDEX `idx_import_jobs_status` ON `import_jobs`(`company_id`, `status`, `created_at`);
CREATE INDEX `idx_notifications_unread` ON `notifications`(`user_id`, `read_at`, `created_at`);
