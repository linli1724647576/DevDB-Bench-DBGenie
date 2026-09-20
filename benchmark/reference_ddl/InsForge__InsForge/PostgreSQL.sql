CREATE TABLE "channels" (
  "id" UUID NOT NULL,
  "pattern" TEXT NOT NULL,
  "description" TEXT,
  "webhook_urls" TEXT[],
  "enabled" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("pattern")
);

CREATE TABLE "checkout_sessions" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "mode" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "payment_status" TEXT,
  "subject_type" TEXT,
  "subject_id" TEXT,
  "customer_email" TEXT,
  "line_items" JSONB NOT NULL,
  "success_url" TEXT NOT NULL,
  "cancel_url" TEXT NOT NULL,
  "idempotency_key" TEXT,
  "metadata" JSONB NOT NULL,
  "stripe_checkout_session_id" TEXT,
  "stripe_customer_id" TEXT,
  "stripe_payment_intent_id" TEXT,
  "stripe_subscription_id" TEXT,
  "url" TEXT,
  "last_error" TEXT,
  "raw" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_checkout_session_id")
);

CREATE TABLE "config" (
  "id" UUID NOT NULL,
  "retention_days" INTEGER,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "customer_portal_sessions" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "subject_type" TEXT NOT NULL,
  "subject_id" TEXT NOT NULL,
  "stripe_customer_id" TEXT,
  "return_url" TEXT,
  "configuration_id" TEXT,
  "url" TEXT,
  "last_error" TEXT,
  "raw" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "customers" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_customer_id" TEXT NOT NULL,
  "email" TEXT,
  "name" TEXT,
  "phone" TEXT,
  "deleted" BOOLEAN NOT NULL,
  "metadata" JSONB NOT NULL,
  "raw" JSONB NOT NULL,
  "stripe_created_at" TIMESTAMP,
  "synced_at" TIMESTAMP NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_customer_id")
);

CREATE TABLE "job_logs" (
  "id" UUID NOT NULL,
  "job_id" UUID,
  "executed_at" TIMESTAMP,
  "status_code" INTEGER,
  "success" BOOLEAN,
  "duration_ms" BIGINT,
  "message" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "jobs" (
  "id" UUID NOT NULL,
  "name" TEXT NOT NULL,
  "cron_schedule" TEXT NOT NULL,
  "function_url" TEXT NOT NULL,
  "http_method" TEXT NOT NULL,
  "encrypted_headers" TEXT,
  "headers" JSONB,
  "body" JSONB,
  "is_active" BOOLEAN NOT NULL,
  "cron_job_id" BIGINT,
  "last_executed_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "messages" (
  "id" UUID NOT NULL,
  "event_name" TEXT NOT NULL,
  "channel_id" UUID,
  "channel_name" TEXT NOT NULL,
  "payload" JSONB NOT NULL,
  "sender_type" TEXT NOT NULL,
  "sender_id" UUID,
  "ws_audience_count" INTEGER NOT NULL,
  "wh_audience_count" INTEGER NOT NULL,
  "wh_delivered_count" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "payment_history" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "subject_type" TEXT,
  "subject_id" TEXT,
  "stripe_customer_id" TEXT,
  "customer_email_snapshot" TEXT,
  "stripe_checkout_session_id" TEXT,
  "stripe_payment_intent_id" TEXT,
  "stripe_invoice_id" TEXT,
  "stripe_charge_id" TEXT,
  "stripe_refund_id" TEXT,
  "stripe_subscription_id" TEXT,
  "stripe_product_id" TEXT,
  "stripe_price_id" TEXT,
  "amount" BIGINT,
  "amount_refunded" BIGINT,
  "currency" TEXT,
  "description" TEXT,
  "paid_at" TIMESTAMP,
  "failed_at" TIMESTAMP,
  "refunded_at" TIMESTAMP,
  "stripe_created_at" TIMESTAMP,
  "raw" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "prices" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_price_id" TEXT NOT NULL,
  "stripe_product_id" TEXT,
  "active" BOOLEAN NOT NULL,
  "currency" TEXT NOT NULL,
  "unit_amount" BIGINT,
  "unit_amount_decimal" TEXT,
  "type" TEXT NOT NULL,
  "lookup_key" TEXT,
  "billing_scheme" TEXT,
  "tax_behavior" TEXT,
  "recurring_interval" TEXT,
  "recurring_interval_count" INTEGER,
  "metadata" JSONB NOT NULL,
  "raw" JSONB NOT NULL,
  "synced_at" TIMESTAMP NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_price_id")
);

CREATE TABLE "products" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_product_id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "active" BOOLEAN NOT NULL,
  "default_price_id" TEXT,
  "metadata" JSONB NOT NULL,
  "raw" JSONB NOT NULL,
  "synced_at" TIMESTAMP NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_product_id")
);

CREATE TABLE "services" (
  "id" UUID NOT NULL,
  "project_id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "image_url" TEXT NOT NULL,
  "port" INTEGER NOT NULL,
  "cpu" TEXT NOT NULL,
  "memory" INTEGER NOT NULL,
  "env_vars_encrypted" TEXT,
  "region" TEXT NOT NULL,
  "fly_app_id" TEXT,
  "fly_machine_id" TEXT,
  "status" TEXT NOT NULL,
  "endpoint_url" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("project_id", "name")
);

CREATE TABLE "stripe_connections" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_account_id" TEXT,
  "stripe_account_email" TEXT,
  "account_livemode" BOOLEAN,
  "status" TEXT NOT NULL,
  "webhook_endpoint_id" TEXT,
  "webhook_endpoint_url" TEXT,
  "webhook_configured_at" TIMESTAMP,
  "last_synced_at" TIMESTAMP,
  "last_sync_status" TEXT,
  "last_sync_error" TEXT,
  "last_sync_counts" JSONB NOT NULL,
  "raw" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment")
);

CREATE TABLE "stripe_customer_mappings" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "subject_type" TEXT NOT NULL,
  "subject_id" TEXT NOT NULL,
  "stripe_customer_id" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "subject_type", "subject_id"),
  UNIQUE ("environment", "stripe_customer_id")
);

CREATE TABLE "subscription_items" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_subscription_item_id" TEXT NOT NULL,
  "stripe_subscription_id" TEXT NOT NULL,
  "stripe_product_id" TEXT,
  "stripe_price_id" TEXT,
  "quantity" BIGINT,
  "metadata" JSONB NOT NULL,
  "raw" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_subscription_item_id")
);

CREATE TABLE "subscriptions" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_subscription_id" TEXT NOT NULL,
  "stripe_customer_id" TEXT NOT NULL,
  "subject_type" TEXT,
  "subject_id" TEXT,
  "status" TEXT NOT NULL,
  "current_period_start" TIMESTAMP,
  "current_period_end" TIMESTAMP,
  "cancel_at_period_end" BOOLEAN NOT NULL,
  "cancel_at" TIMESTAMP,
  "canceled_at" TIMESTAMP,
  "trial_start" TIMESTAMP,
  "trial_end" TIMESTAMP,
  "latest_invoice_id" TEXT,
  "metadata" JSONB NOT NULL,
  "raw" JSONB NOT NULL,
  "synced_at" TIMESTAMP NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_subscription_id")
);

CREATE TABLE "webhook_events" (
  "id" UUID NOT NULL,
  "environment" TEXT NOT NULL,
  "stripe_event_id" TEXT NOT NULL,
  "event_type" TEXT NOT NULL,
  "livemode" BOOLEAN NOT NULL,
  "stripe_account_id" TEXT,
  "object_type" TEXT,
  "object_id" TEXT,
  "processing_status" TEXT NOT NULL,
  "attempt_count" INTEGER NOT NULL,
  "last_error" TEXT,
  "payload" JSONB NOT NULL,
  "received_at" TIMESTAMP NOT NULL,
  "processed_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment", "stripe_event_id")
);

CREATE INDEX "idx_channels_pattern_1" ON "channels" ("pattern");

CREATE INDEX "idx_channels_enabled_2" ON "channels" ("enabled");

CREATE INDEX "idx_checkout_sessions_environment_status_1" ON "checkout_sessions" ("environment", "status");

CREATE INDEX "idx_checkout_sessions_environment_subject_type_subject_id_2" ON "checkout_sessions" ("environment", "subject_type", "subject_id");

CREATE INDEX "idx_checkout_sessions_environment_stripe_customer_id_3" ON "checkout_sessions" ("environment", "stripe_customer_id");

CREATE INDEX "idx_checkout_sessions_environment_stripe_checkout_s_dfa8674e" ON "checkout_sessions" ("environment", "stripe_checkout_session_id");

CREATE UNIQUE INDEX "uidx_checkout_sessions_environment_idempotency_key_5" ON "checkout_sessions" ("environment", "idempotency_key");

CREATE INDEX "idx_customer_portal_sessions_environment_status_1" ON "customer_portal_sessions" ("environment", "status");

CREATE INDEX "idx_customer_portal_sessions_environment_subject_ty_8396d619" ON "customer_portal_sessions" ("environment", "subject_type", "subject_id");

CREATE INDEX "idx_customer_portal_sessions_environment_stripe_cus_d26a9301" ON "customer_portal_sessions" ("environment", "stripe_customer_id");

CREATE INDEX "idx_customers_environment_deleted_1" ON "customers" ("environment", "deleted");

CREATE INDEX "idx_customers_environment_email_2" ON "customers" ("environment", "email");

CREATE INDEX "idx_customers_environment_stripe_created_at_3" ON "customers" ("environment", "stripe_created_at");

CREATE INDEX "idx_job_logs_job_id_1" ON "job_logs" ("job_id");

CREATE INDEX "idx_job_logs_executed_at_2" ON "job_logs" ("executed_at");

CREATE INDEX "idx_jobs_cron_job_id_1" ON "jobs" ("cron_job_id");

CREATE INDEX "idx_jobs_is_active_2" ON "jobs" ("is_active");

CREATE INDEX "idx_messages_channel_id_1" ON "messages" ("channel_id");

CREATE INDEX "idx_messages_channel_name_2" ON "messages" ("channel_name");

CREATE INDEX "idx_messages_created_at_3" ON "messages" ("created_at");

CREATE INDEX "idx_messages_event_name_4" ON "messages" ("event_name");

CREATE INDEX "idx_messages_sender_type_sender_id_5" ON "messages" ("sender_type", "sender_id");

CREATE INDEX "idx_payment_history_environment_subject_type_subject_id_1" ON "payment_history" ("environment", "subject_type", "subject_id");

CREATE INDEX "idx_payment_history_environment_stripe_customer_id_2" ON "payment_history" ("environment", "stripe_customer_id");

CREATE INDEX "idx_payment_history_environment_stripe_created_at_3" ON "payment_history" ("environment", "stripe_created_at");

CREATE UNIQUE INDEX "uidx_payment_history_environment_stripe_payment_intent_id_4" ON "payment_history" ("environment", "stripe_payment_intent_id");

CREATE UNIQUE INDEX "uidx_payment_history_environment_stripe_checkout_se_bb2baec9" ON "payment_history" ("environment", "stripe_checkout_session_id");

CREATE UNIQUE INDEX "uidx_payment_history_environment_stripe_invoice_id_6" ON "payment_history" ("environment", "stripe_invoice_id");

CREATE UNIQUE INDEX "uidx_payment_history_environment_stripe_refund_id_7" ON "payment_history" ("environment", "stripe_refund_id");

CREATE INDEX "idx_prices_environment_stripe_product_id_1" ON "prices" ("environment", "stripe_product_id");

CREATE INDEX "idx_prices_environment_lookup_key_2" ON "prices" ("environment", "lookup_key");

CREATE INDEX "idx_products_environment_active_1" ON "products" ("environment", "active");

CREATE INDEX "idx_services_project_id_1" ON "services" ("project_id");

CREATE INDEX "idx_services_status_2" ON "services" ("status");

CREATE INDEX "idx_stripe_customer_mappings_environment_subject_ty_4a836dae" ON "stripe_customer_mappings" ("environment", "subject_type", "subject_id");

CREATE INDEX "idx_subscription_items_environment_stripe_subscription_id_1" ON "subscription_items" ("environment", "stripe_subscription_id");

CREATE INDEX "idx_subscription_items_environment_stripe_price_id_2" ON "subscription_items" ("environment", "stripe_price_id");

CREATE INDEX "idx_subscriptions_environment_subject_type_subject_id_1" ON "subscriptions" ("environment", "subject_type", "subject_id");

CREATE INDEX "idx_subscriptions_environment_stripe_customer_id_2" ON "subscriptions" ("environment", "stripe_customer_id");

CREATE INDEX "idx_subscriptions_environment_status_3" ON "subscriptions" ("environment", "status");

CREATE INDEX "idx_webhook_events_environment_processing_status_1" ON "webhook_events" ("environment", "processing_status");

CREATE INDEX "idx_webhook_events_environment_object_type_object_id_2" ON "webhook_events" ("environment", "object_type", "object_id");

ALTER TABLE "job_logs" ADD CONSTRAINT "fk_job_logs_job_id_1" FOREIGN KEY ("job_id") REFERENCES "jobs" ("id");

ALTER TABLE "messages" ADD CONSTRAINT "fk_messages_channel_id_1" FOREIGN KEY ("channel_id") REFERENCES "channels" ("id");
