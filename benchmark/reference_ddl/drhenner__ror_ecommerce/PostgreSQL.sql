CREATE TABLE "accounting_adjustments" (
  "id" INTEGER NOT NULL,
  "adjustable_id" INTEGER NOT NULL,
  "adjustable_type" VARCHAR(255) NOT NULL,
  "amount" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "notes" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "accounts" (
  "id" INTEGER NOT NULL,
  "account_type" VARCHAR(255) NOT NULL,
  "active" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP,
  "monthly_charge" DECIMAL(18, 2) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "addresses" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "address1" VARCHAR(255) NOT NULL,
  "address2" VARCHAR(255),
  "address_type" VARCHAR(255),
  "addressable_id" INTEGER NOT NULL,
  "addressable_type" VARCHAR(255) NOT NULL,
  "alternative_phone" VARCHAR(255),
  "billing_default" BOOLEAN,
  "city" VARCHAR(255) NOT NULL,
  "country_id" INTEGER,
  "created_at" TIMESTAMP,
  "default" BOOLEAN,
  "first_name" VARCHAR(255),
  "last_name" VARCHAR(255),
  "phone_id" INTEGER,
  "state_id" INTEGER,
  "state_name" VARCHAR(255),
  "updated_at" TIMESTAMP,
  "zip_code" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "batches" (
  "id" INTEGER NOT NULL,
  "batchable_id" INTEGER,
  "batchable_type" VARCHAR(255),
  "created_at" TIMESTAMP,
  "name" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "brands" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "cart_items" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "cart_id" INTEGER,
  "created_at" TIMESTAMP,
  "item_type" VARCHAR(255) NOT NULL,
  "quantity" INTEGER,
  "updated_at" TIMESTAMP,
  "user_id" INTEGER,
  "variant_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "carts" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "customer_id" INTEGER,
  "updated_at" TIMESTAMP,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "comments" (
  "id" INTEGER NOT NULL,
  "commentable_id" INTEGER,
  "commentable_type" VARCHAR(255),
  "created_at" TIMESTAMP,
  "created_by" INTEGER,
  "note" TEXT,
  "updated_at" TIMESTAMP,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "countries" (
  "id" INTEGER NOT NULL,
  "abbreviation" VARCHAR(255),
  "active" BOOLEAN,
  "name" VARCHAR(255),
  "shipping_zone_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "coupons" (
  "id" INTEGER NOT NULL,
  "amount" DECIMAL(18, 2),
  "code" VARCHAR(255) NOT NULL,
  "combine" BOOLEAN,
  "created_at" TIMESTAMP,
  "description" TEXT NOT NULL,
  "expires_at" TIMESTAMP,
  "minimum_value" DECIMAL(18, 2),
  "percent" INTEGER,
  "starts_at" TIMESTAMP,
  "type" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "deals" (
  "id" INTEGER NOT NULL,
  "buy_quantity" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "deal_type" VARCHAR(255) NOT NULL,
  "deleted_at" TIMESTAMP,
  "get_amount" INTEGER,
  "get_percentage" INTEGER,
  "product_type_id" INTEGER NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "image_groups" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "name" VARCHAR(255) NOT NULL,
  "product_id" INTEGER NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "images" (
  "id" INTEGER NOT NULL,
  "caption" VARCHAR(255),
  "created_at" TIMESTAMP,
  "image_height" INTEGER,
  "image_width" INTEGER,
  "imageable_id" INTEGER,
  "imageable_type" VARCHAR(255),
  "position" INTEGER,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "inventories" (
  "id" INTEGER NOT NULL,
  "count_on_hand" INTEGER,
  "count_pending_from_supplier" INTEGER,
  "count_pending_to_customer" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "invoices" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN NOT NULL,
  "amount" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "credited_amount" DECIMAL(18, 2),
  "invoice_type" VARCHAR(255) NOT NULL,
  "order_id" INTEGER NOT NULL,
  "state" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "newsletters" (
  "id" INTEGER NOT NULL,
  "autosubscribe" BOOLEAN NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "notifications" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "notifiable_id" INTEGER NOT NULL,
  "notifiable_type" VARCHAR(255) NOT NULL,
  "send_at" TIMESTAMP,
  "sent_at" TIMESTAMP,
  "type" VARCHAR(255) NOT NULL,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "order_items" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "order_id" INTEGER NOT NULL,
  "price" DECIMAL(18, 2),
  "shipment_id" INTEGER,
  "shipping_rate_id" INTEGER,
  "state" VARCHAR(255) NOT NULL,
  "tax_rate_id" INTEGER,
  "total" DECIMAL(18, 2),
  "updated_at" TIMESTAMP,
  "variant_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "orders" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN NOT NULL,
  "bill_address_id" INTEGER,
  "calculated_at" TIMESTAMP,
  "completed_at" TIMESTAMP,
  "coupon_id" INTEGER,
  "created_at" TIMESTAMP,
  "credited_amount" DECIMAL(18, 2),
  "email" VARCHAR(255),
  "ip_address" VARCHAR(255),
  "number" VARCHAR(255),
  "ship_address_id" INTEGER,
  "shipments_count" INTEGER,
  "shipped" BOOLEAN NOT NULL,
  "state" VARCHAR(255),
  "updated_at" TIMESTAMP,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "payment_profiles" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "address_id" INTEGER,
  "card_name" VARCHAR(255),
  "cc_type" VARCHAR(255),
  "created_at" TIMESTAMP,
  "default" BOOLEAN,
  "first_name" VARCHAR(255),
  "last_digits" VARCHAR(255),
  "last_name" VARCHAR(255),
  "month" VARCHAR(255),
  "payment_cim_id" VARCHAR(255),
  "updated_at" TIMESTAMP,
  "user_id" INTEGER,
  "year" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "payments" (
  "id" INTEGER NOT NULL,
  "action" VARCHAR(255),
  "amount" INTEGER,
  "confirmation_id" VARCHAR(255),
  "created_at" TIMESTAMP,
  "error" VARCHAR(255),
  "error_code" VARCHAR(255),
  "invoice_id" INTEGER,
  "message" VARCHAR(255),
  "params" TEXT,
  "success" BOOLEAN,
  "test" BOOLEAN,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "phones" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "number" VARCHAR(255) NOT NULL,
  "phone_type" VARCHAR(255),
  "phoneable_id" INTEGER NOT NULL,
  "phoneable_type" VARCHAR(255) NOT NULL,
  "primary" BOOLEAN,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "product_properties" (
  "id" INTEGER NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "position" INTEGER,
  "product_id" INTEGER NOT NULL,
  "property_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "product_types" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "lft" INTEGER,
  "name" VARCHAR(255) NOT NULL,
  "parent_id" INTEGER,
  "rgt" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "products" (
  "id" INTEGER NOT NULL,
  "available_at" TIMESTAMP,
  "brand_id" INTEGER,
  "created_at" TIMESTAMP,
  "deleted_at" TIMESTAMP,
  "description" TEXT,
  "description_markup" TEXT,
  "featured" BOOLEAN,
  "meta_description" VARCHAR(255),
  "meta_keywords" VARCHAR(255),
  "name" VARCHAR(255) NOT NULL,
  "permalink" VARCHAR(255) NOT NULL,
  "product_keywords" TEXT,
  "product_type_id" INTEGER NOT NULL,
  "product_template" VARCHAR(255),
  "shipping_category_id" INTEGER NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("permalink")
);

CREATE TABLE "properties" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "display_name" VARCHAR(255),
  "identifing_name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "purchase_order_variants" (
  "id" INTEGER NOT NULL,
  "cost" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "is_received" BOOLEAN,
  "purchase_order_id" INTEGER NOT NULL,
  "quantity" INTEGER NOT NULL,
  "updated_at" TIMESTAMP,
  "variant_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "purchase_orders" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "estimated_arrival_on" DATE,
  "invoice_number" VARCHAR(255),
  "notes" VARCHAR(255),
  "ordered_at" TIMESTAMP NOT NULL,
  "state" VARCHAR(255),
  "supplier_id" INTEGER NOT NULL,
  "total_cost" DECIMAL(18, 2) NOT NULL,
  "tracking_number" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "referral_bonuses" (
  "id" INTEGER NOT NULL,
  "amount" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "name" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "referral_programs" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP,
  "description" TEXT,
  "name" VARCHAR(255) NOT NULL,
  "referral_bonus_id" INTEGER NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "referrals" (
  "id" INTEGER NOT NULL,
  "applied" BOOLEAN,
  "clicked_at" TIMESTAMP,
  "created_at" TIMESTAMP,
  "email" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255),
  "purchased_at" TIMESTAMP,
  "referral_program_id" INTEGER NOT NULL,
  "referral_type" VARCHAR(255) NOT NULL,
  "referral_user_id" INTEGER,
  "referring_user_id" INTEGER NOT NULL,
  "registered_at" TIMESTAMP,
  "sent_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "return_authorizations" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "amount" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "created_by" INTEGER,
  "number" VARCHAR(255),
  "order_id" INTEGER NOT NULL,
  "restocking_fee" DECIMAL(18, 2),
  "state" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "return_items" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "order_item_id" INTEGER NOT NULL,
  "return_authorization_id" INTEGER NOT NULL,
  "return_condition" VARCHAR(255),
  "return_reason" VARCHAR(255),
  "returned" BOOLEAN,
  "updated_at" TIMESTAMP,
  "updated_by" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "roles" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "sales" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "ends_at" TIMESTAMP,
  "percent_off" DECIMAL(18, 2),
  "product_id" INTEGER,
  "starts_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "shipments" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN NOT NULL,
  "address_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "number" VARCHAR(255) NOT NULL,
  "order_id" INTEGER,
  "shipped_at" TIMESTAMP,
  "shipping_method_id" INTEGER NOT NULL,
  "state" VARCHAR(255) NOT NULL,
  "tracking" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "shipping_categories" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "shipping_methods" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "name" VARCHAR(255) NOT NULL,
  "shipping_zone_id" INTEGER NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "shipping_rates" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "created_at" TIMESTAMP,
  "minimum_charge" DECIMAL(18, 2) NOT NULL,
  "position" INTEGER,
  "rate" DECIMAL(18, 2) NOT NULL,
  "shipping_category_id" INTEGER NOT NULL,
  "shipping_method_id" INTEGER NOT NULL,
  "rate_type" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "shipping_zones" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "slugs" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "name" VARCHAR(255),
  "scope" VARCHAR(255),
  "sequence" INTEGER NOT NULL,
  "sluggable_id" INTEGER,
  "sluggable_type" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("name", "sluggable_type", "sequence", "scope")
);

CREATE TABLE "states" (
  "id" INTEGER NOT NULL,
  "abbreviation" VARCHAR(255) NOT NULL,
  "country_id" INTEGER NOT NULL,
  "described_as" VARCHAR(255),
  "name" VARCHAR(255) NOT NULL,
  "shipping_zone_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "store_credits" (
  "id" INTEGER NOT NULL,
  "amount" DECIMAL(18, 2),
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "suppliers" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "email" VARCHAR(255),
  "name" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "tax_rates" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "country_id" INTEGER,
  "end_date" DATE,
  "percentage" DECIMAL(18, 2) NOT NULL,
  "start_date" DATE NOT NULL,
  "state_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "transaction_accounts" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP,
  "name" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "transaction_ledgers" (
  "id" INTEGER NOT NULL,
  "accountable_id" INTEGER,
  "accountable_type" VARCHAR(255),
  "created_at" TIMESTAMP,
  "credit" DECIMAL(18, 2) NOT NULL,
  "debit" DECIMAL(18, 2) NOT NULL,
  "period" VARCHAR(255),
  "tax_amount" DECIMAL(18, 2),
  "transaction_account_id" INTEGER,
  "transaction_id" INTEGER,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "transactions" (
  "id" INTEGER NOT NULL,
  "batch_id" INTEGER,
  "created_at" TIMESTAMP,
  "type" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "user_roles" (
  "id" INTEGER NOT NULL,
  "role_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "users" (
  "id" INTEGER NOT NULL,
  "access_token" VARCHAR(255),
  "account_id" INTEGER,
  "comments_count" INTEGER,
  "created_at" TIMESTAMP,
  "crypted_password" VARCHAR(255),
  "customer_cim_id" VARCHAR(255),
  "email" VARCHAR(255),
  "first_name" VARCHAR(255),
  "last_name" VARCHAR(255),
  "password_salt" VARCHAR(255),
  "perishable_token" VARCHAR(255),
  "persistence_token" VARCHAR(255),
  "state" VARCHAR(255),
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("access_token"),
  UNIQUE ("email"),
  UNIQUE ("perishable_token"),
  UNIQUE ("persistence_token")
);

CREATE TABLE "users_newsletters" (
  "id" INTEGER NOT NULL,
  "newsletter_id" INTEGER,
  "updated_at" TIMESTAMP NOT NULL,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "variant_properties" (
  "id" INTEGER NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "primary" BOOLEAN,
  "property_id" INTEGER NOT NULL,
  "variant_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "variant_suppliers" (
  "id" INTEGER NOT NULL,
  "active" BOOLEAN,
  "cost" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "max_quantity" INTEGER,
  "min_quantity" INTEGER,
  "supplier_id" INTEGER NOT NULL,
  "total_quantity_supplied" INTEGER,
  "updated_at" TIMESTAMP,
  "variant_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "variants" (
  "id" INTEGER NOT NULL,
  "cost" DECIMAL(18, 2) NOT NULL,
  "created_at" TIMESTAMP,
  "deleted_at" TIMESTAMP,
  "image_group_id" INTEGER,
  "inventory_id" INTEGER,
  "master" BOOLEAN NOT NULL,
  "name" VARCHAR(255),
  "price" DECIMAL(18, 2) NOT NULL,
  "product_id" INTEGER NOT NULL,
  "sku" VARCHAR(255) NOT NULL,
  "updated_at" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_accounting_adjustments_adjustable_id_1" ON "accounting_adjustments" ("adjustable_id");

CREATE INDEX "idx_addresses_addressable_id_1" ON "addresses" ("addressable_id");

CREATE INDEX "idx_addresses_addressable_type_2" ON "addresses" ("addressable_type");

CREATE INDEX "idx_addresses_state_id_3" ON "addresses" ("state_id");

CREATE INDEX "idx_batches_batchable_id_1" ON "batches" ("batchable_id");

CREATE INDEX "idx_batches_batchable_type_2" ON "batches" ("batchable_type");

CREATE INDEX "idx_cart_items_cart_id_1" ON "cart_items" ("cart_id");

CREATE INDEX "idx_cart_items_item_type_id_2" ON "cart_items" ("item_type");

CREATE INDEX "idx_cart_items_user_id_3" ON "cart_items" ("user_id");

CREATE INDEX "idx_cart_items_variant_id_4" ON "cart_items" ("variant_id");

CREATE INDEX "idx_carts_customer_id_1" ON "carts" ("customer_id");

CREATE INDEX "idx_carts_user_id_2" ON "carts" ("user_id");

CREATE INDEX "idx_comments_commentable_id_1" ON "comments" ("commentable_id");

CREATE INDEX "idx_comments_commentable_type_2" ON "comments" ("commentable_type");

CREATE INDEX "idx_comments_created_by_3" ON "comments" ("created_by");

CREATE INDEX "idx_comments_user_id_4" ON "comments" ("user_id");

CREATE INDEX "idx_countries_active_1" ON "countries" ("active");

CREATE INDEX "idx_countries_name_2" ON "countries" ("name");

CREATE INDEX "idx_countries_shipping_zone_id_active_3" ON "countries" ("shipping_zone_id", "active");

CREATE INDEX "idx_coupons_code_1" ON "coupons" ("code");

CREATE INDEX "idx_coupons_expires_at_2" ON "coupons" ("expires_at");

CREATE INDEX "idx_deals_buy_quantity_1" ON "deals" ("buy_quantity");

CREATE INDEX "idx_deals_deal_type_id_2" ON "deals" ("deal_type");

CREATE INDEX "idx_deals_product_type_id_3" ON "deals" ("product_type_id");

CREATE INDEX "idx_image_groups_product_id_1" ON "image_groups" ("product_id");

CREATE INDEX "idx_images_imageable_id_1" ON "images" ("imageable_id");

CREATE INDEX "idx_images_imageable_type_2" ON "images" ("imageable_type");

CREATE INDEX "idx_images_position_3" ON "images" ("position");

CREATE INDEX "idx_invoices_order_id_1" ON "invoices" ("order_id");

CREATE INDEX "idx_notifications_notifiable_type_notifiable_id_1" ON "notifications" ("notifiable_type", "notifiable_id");

CREATE INDEX "idx_notifications_type_user_id_2" ON "notifications" ("type", "user_id");

CREATE INDEX "idx_notifications_user_id_3" ON "notifications" ("user_id");

CREATE INDEX "idx_order_items_order_id_1" ON "order_items" ("order_id");

CREATE INDEX "idx_order_items_shipment_id_2" ON "order_items" ("shipment_id");

CREATE INDEX "idx_order_items_shipping_rate_id_3" ON "order_items" ("shipping_rate_id");

CREATE INDEX "idx_order_items_tax_rate_id_4" ON "order_items" ("tax_rate_id");

CREATE INDEX "idx_order_items_variant_id_5" ON "order_items" ("variant_id");

CREATE INDEX "idx_orders_bill_address_id_1" ON "orders" ("bill_address_id");

CREATE INDEX "idx_orders_coupon_id_2" ON "orders" ("coupon_id");

CREATE INDEX "idx_orders_email_3" ON "orders" ("email");

CREATE INDEX "idx_orders_number_4" ON "orders" ("number");

CREATE INDEX "idx_orders_ship_address_id_5" ON "orders" ("ship_address_id");

CREATE INDEX "idx_orders_user_id_6" ON "orders" ("user_id");

CREATE INDEX "idx_payment_profiles_address_id_1" ON "payment_profiles" ("address_id");

CREATE INDEX "idx_payment_profiles_user_id_2" ON "payment_profiles" ("user_id");

CREATE INDEX "idx_payments_invoice_id_1" ON "payments" ("invoice_id");

CREATE INDEX "idx_phones_phone_type_id_1" ON "phones" ("phone_type");

CREATE INDEX "idx_phones_phoneable_id_2" ON "phones" ("phoneable_id");

CREATE INDEX "idx_phones_phoneable_type_3" ON "phones" ("phoneable_type");

CREATE INDEX "idx_product_properties_product_id_1" ON "product_properties" ("product_id");

CREATE INDEX "idx_product_properties_property_id_2" ON "product_properties" ("property_id");

CREATE INDEX "idx_product_types_lft_1" ON "product_types" ("lft");

CREATE INDEX "idx_product_types_parent_id_2" ON "product_types" ("parent_id");

CREATE INDEX "idx_product_types_rgt_3" ON "product_types" ("rgt");

CREATE INDEX "idx_products_brand_id_1" ON "products" ("brand_id");

CREATE INDEX "idx_products_deleted_at_2" ON "products" ("deleted_at");

CREATE INDEX "idx_products_name_3" ON "products" ("name");

CREATE UNIQUE INDEX "uidx_products_permalink_4" ON "products" ("permalink");

CREATE INDEX "idx_products_product_type_id_5" ON "products" ("product_type_id");

CREATE INDEX "idx_products_prototype_id_6" ON "products" ("product_template");

CREATE INDEX "idx_products_shipping_category_id_7" ON "products" ("shipping_category_id");

CREATE INDEX "idx_purchase_order_variants_purchase_order_id_1" ON "purchase_order_variants" ("purchase_order_id");

CREATE INDEX "idx_purchase_order_variants_variant_id_2" ON "purchase_order_variants" ("variant_id");

CREATE INDEX "idx_purchase_orders_supplier_id_1" ON "purchase_orders" ("supplier_id");

CREATE INDEX "idx_purchase_orders_tracking_number_2" ON "purchase_orders" ("tracking_number");

CREATE INDEX "idx_referral_programs_referral_bonus_id_1" ON "referral_programs" ("referral_bonus_id");

CREATE INDEX "idx_referrals_email_1" ON "referrals" ("email");

CREATE INDEX "idx_referrals_referral_program_id_2" ON "referrals" ("referral_program_id");

CREATE INDEX "idx_referrals_referral_type_id_3" ON "referrals" ("referral_type");

CREATE INDEX "idx_referrals_referral_user_id_4" ON "referrals" ("referral_user_id");

CREATE INDEX "idx_referrals_referring_user_id_5" ON "referrals" ("referring_user_id");

CREATE INDEX "idx_return_authorizations_created_by_1" ON "return_authorizations" ("created_by");

CREATE INDEX "idx_return_authorizations_number_2" ON "return_authorizations" ("number");

CREATE INDEX "idx_return_authorizations_order_id_3" ON "return_authorizations" ("order_id");

CREATE INDEX "idx_return_authorizations_user_id_4" ON "return_authorizations" ("user_id");

CREATE INDEX "idx_return_items_order_item_id_1" ON "return_items" ("order_item_id");

CREATE INDEX "idx_return_items_return_authorization_id_2" ON "return_items" ("return_authorization_id");

CREATE INDEX "idx_return_items_return_condition_id_3" ON "return_items" ("return_condition");

CREATE INDEX "idx_return_items_return_reason_id_4" ON "return_items" ("return_reason");

CREATE INDEX "idx_return_items_updated_by_5" ON "return_items" ("updated_by");

CREATE INDEX "idx_roles_name_1" ON "roles" ("name");

CREATE INDEX "idx_sales_product_id_1" ON "sales" ("product_id");

CREATE INDEX "idx_shipments_address_id_1" ON "shipments" ("address_id");

CREATE INDEX "idx_shipments_number_2" ON "shipments" ("number");

CREATE INDEX "idx_shipments_order_id_3" ON "shipments" ("order_id");

CREATE INDEX "idx_shipments_shipping_method_id_4" ON "shipments" ("shipping_method_id");

CREATE INDEX "idx_shipping_methods_shipping_zone_id_1" ON "shipping_methods" ("shipping_zone_id");

CREATE INDEX "idx_shipping_rates_shipping_category_id_1" ON "shipping_rates" ("shipping_category_id");

CREATE INDEX "idx_shipping_rates_shipping_method_id_2" ON "shipping_rates" ("shipping_method_id");

CREATE INDEX "idx_shipping_rates_shipping_rate_type_id_3" ON "shipping_rates" ("rate_type");

CREATE UNIQUE INDEX "uidx_slugs_name_sluggable_type_sequence_scope_1" ON "slugs" ("name", "sluggable_type", "sequence", "scope");

CREATE INDEX "idx_slugs_sluggable_id_2" ON "slugs" ("sluggable_id");

CREATE INDEX "idx_states_abbreviation_1" ON "states" ("abbreviation");

CREATE INDEX "idx_states_country_id_2" ON "states" ("country_id");

CREATE INDEX "idx_states_name_3" ON "states" ("name");

CREATE INDEX "idx_store_credits_user_id_1" ON "store_credits" ("user_id");

CREATE INDEX "idx_tax_rates_state_id_1" ON "tax_rates" ("state_id");

CREATE INDEX "idx_transaction_ledgers_accountable_id_1" ON "transaction_ledgers" ("accountable_id");

CREATE INDEX "idx_transaction_ledgers_transaction_account_id_2" ON "transaction_ledgers" ("transaction_account_id");

CREATE INDEX "idx_transaction_ledgers_transaction_id_3" ON "transaction_ledgers" ("transaction_id");

CREATE INDEX "idx_transactions_batch_id_1" ON "transactions" ("batch_id");

CREATE INDEX "idx_user_roles_role_id_1" ON "user_roles" ("role_id");

CREATE INDEX "idx_user_roles_user_id_2" ON "user_roles" ("user_id");

CREATE UNIQUE INDEX "uidx_users_access_token_1" ON "users" ("access_token");

CREATE UNIQUE INDEX "uidx_users_email_2" ON "users" ("email");

CREATE INDEX "idx_users_first_name_3" ON "users" ("first_name");

CREATE INDEX "idx_users_last_name_4" ON "users" ("last_name");

CREATE UNIQUE INDEX "uidx_users_perishable_token_5" ON "users" ("perishable_token");

CREATE UNIQUE INDEX "uidx_users_persistence_token_6" ON "users" ("persistence_token");

CREATE INDEX "idx_users_newsletters_newsletter_id_1" ON "users_newsletters" ("newsletter_id");

CREATE INDEX "idx_users_newsletters_user_id_2" ON "users_newsletters" ("user_id");

CREATE INDEX "idx_variant_properties_property_id_1" ON "variant_properties" ("property_id");

CREATE INDEX "idx_variant_properties_variant_id_2" ON "variant_properties" ("variant_id");

CREATE INDEX "idx_variant_suppliers_supplier_id_1" ON "variant_suppliers" ("supplier_id");

CREATE INDEX "idx_variant_suppliers_variant_id_2" ON "variant_suppliers" ("variant_id");

CREATE INDEX "idx_variants_inventory_id_1" ON "variants" ("inventory_id");

CREATE INDEX "idx_variants_product_id_2" ON "variants" ("product_id");

CREATE INDEX "idx_variants_sku_3" ON "variants" ("sku");

CREATE TABLE "media_assets" (
  "id" INTEGER NOT NULL,
  "filename" VARCHAR(255) NOT NULL,
  "content_type" VARCHAR(255),
  "byte_size" BIGINT,
  "checksum" VARCHAR(255),
  "storage_key" VARCHAR(255) NOT NULL,
  "metadata" TEXT,
  "record_id" BIGINT,
  "record_type" VARCHAR(255),
  "variant_digest" VARCHAR(255),
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("storage_key")
);
