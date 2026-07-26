CREATE TABLE "accounting_account" (
  "id" BIGINT NOT NULL,
  "account_number" INTEGER NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "account_type" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_open_reliabilities_account" BOOLEAN NOT NULL,
  "is_open_interest_account" BOOLEAN NOT NULL,
  "is_product_inventory_activa" BOOLEAN NOT NULL,
  "is_a_customer_payment_account" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "accounting_accountingperiod" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "begin" DATE NOT NULL,
  "end" DATE NOT NULL,
  "template_profit_loss_statement" BIGINT,
  "template_set_balance_sheet" BIGINT,
  PRIMARY KEY ("id")
);

CREATE TABLE "accounting_booking" (
  "id" BIGINT NOT NULL,
  "amount" DECIMAL(18, 2) NOT NULL,
  "description" VARCHAR(255),
  "booking_date" TIMESTAMP NOT NULL,
  "date_of_creation" TIMESTAMP NOT NULL,
  "last_modification" TIMESTAMP NOT NULL,
  "accounting_period" BIGINT NOT NULL,
  "booking_reference" BIGINT,
  "from_account" BIGINT NOT NULL,
  "last_modified_by" BIGINT,
  "staff" BIGINT,
  "to_account" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "accounting_productcategory" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "loss_account" BIGINT NOT NULL,
  "profit_account" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "accounting_taxaccountassignment" (
  "id" BIGINT NOT NULL,
  "tax" BIGINT NOT NULL,
  "activa_account" BIGINT,
  "passiva_account" BIGINT,
  PRIMARY KEY ("id"),
  UNIQUE ("tax")
);

CREATE TABLE "accounting_productcategoryassignment" (
  "id" BIGINT NOT NULL,
  "product_type" BIGINT NOT NULL,
  "category" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("product_type")
);

CREATE TABLE "crm_party" (
  "id" BIGINT NOT NULL,
  "display_name" VARCHAR(255) NOT NULL,
  "default_language" VARCHAR(255),
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "last_modified_by" BIGINT,
  "default_billing_cycle" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_partyemail" (
  "id" BIGINT NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_partygroup" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "role_type_scope" VARCHAR(255),
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_partygroupmembership" (
  "id" BIGINT NOT NULL,
  "party" BIGINT NOT NULL,
  "party_group" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_partyidentification" (
  "id" BIGINT NOT NULL,
  "scheme" VARCHAR(255) NOT NULL,
  "value" VARCHAR(255) NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "party" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_partyrole" (
  "id" BIGINT NOT NULL,
  "role_type" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "party" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_phonenumber" (
  "id" BIGINT NOT NULL,
  "phone_e164" VARCHAR(255) NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_address" (
  "id" BIGINT NOT NULL,
  "street" VARCHAR(255),
  "number" VARCHAR(255),
  "additional_address_line_1" VARCHAR(255),
  "additional_address_line_2" VARCHAR(255),
  "additional_address_line_3" VARCHAR(255),
  "zip_code" VARCHAR(255),
  "town" VARCHAR(255),
  "state" VARCHAR(255),
  "country" VARCHAR(255),
  "subdivision_code" VARCHAR(255),
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_addressassignment" (
  "id" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "address" BIGINT NOT NULL,
  "party" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_emailassignment" (
  "id" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "party" BIGINT NOT NULL,
  "email" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_phoneassignment" (
  "id" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "party" BIGINT NOT NULL,
  "phone" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_organization" (
  "party_ptr" BIGINT NOT NULL,
  "legal_form" VARCHAR(255),
  "legal_name" VARCHAR(255),
  "registration_number" VARCHAR(255),
  "legal_seat_country" VARCHAR(255),
  PRIMARY KEY ("party_ptr")
);

CREATE TABLE "crm_partycontact" (
  "party_ptr" BIGINT NOT NULL,
  "prefix" VARCHAR(255),
  "given_name" VARCHAR(255),
  "family_name" VARCHAR(255),
  "date_of_birth" DATE,
  "gdpr_consent_date" DATE,
  PRIMARY KEY ("party_ptr")
);

CREATE TABLE "crm_organizationmembership" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255),
  "position" VARCHAR(255),
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "organization" BIGINT NOT NULL,
  "contact" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_organizationrelationship" (
  "id" BIGINT NOT NULL,
  "relationship_type" VARCHAR(255) NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "child" BIGINT NOT NULL,
  "parent" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_customerbillingcycle" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "time_to_payment_date" INTEGER NOT NULL,
  "payment_reminder_time_to_payment" INTEGER NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_contract" (
  "id" BIGINT NOT NULL,
  "description" TEXT NOT NULL,
  "date_of_creation" TIMESTAMP NOT NULL,
  "last_modification" TIMESTAMP NOT NULL,
  "default_currency" BIGINT NOT NULL,
  "default_template_set" BIGINT,
  "last_modified_by" BIGINT NOT NULL,
  "staff" BIGINT,
  "buyer_party" BIGINT,
  "supplier_party" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_commercialdocument" (
  "id" BIGINT NOT NULL,
  "contract" BIGINT NOT NULL,
  "party_reference" VARCHAR(255) NOT NULL,
  "ext_business_appl_references" JSONB NOT NULL,
  "discount" DECIMAL(18, 2),
  "description" VARCHAR(255),
  "last_pricing_date" DATE,
  "last_calculated_price" DECIMAL(18, 2),
  "last_calculated_tax" DECIMAL(18, 2),
  "party" BIGINT NOT NULL,
  "staff" BIGINT,
  "currency" BIGINT NOT NULL,
  "date_of_creation" TIMESTAMP NOT NULL,
  "custom_date_field" DATE,
  "last_modification" TIMESTAMP NOT NULL,
  "last_modified_by" BIGINT,
  "template_set" BIGINT,
  "derived_from_commercial_document" BIGINT,
  "last_print_date" TIMESTAMP,
  "workspace" BIGINT NOT NULL,
  "document_type" VARCHAR(64) NOT NULL,
  "status" VARCHAR(64),
  "due_date" DATE,
  "valid_until" DATE,
  "issue_date" DATE,
  "payment_bank_reference" VARCHAR(255),
  "tracking_reference" VARCHAR(255),
  "iteration_number" INTEGER,
  "reason" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_position" (
  "id" BIGINT NOT NULL,
  "position_number" INTEGER NOT NULL,
  "quantity" DECIMAL(18, 2) NOT NULL,
  "description" TEXT,
  "discount" DECIMAL(18, 2),
  "sent_on" DATE,
  "overwrite_product_price" BOOLEAN NOT NULL,
  "position_price_per_unit" DECIMAL(18, 2),
  "last_pricing_date" DATE,
  "last_calculated_price" DECIMAL(18, 2),
  "last_calculated_tax" DECIMAL(18, 2),
  "product_type" BIGINT,
  "unit" BIGINT,
  "position_tax_rate" DECIMAL(18, 2),
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_commercialdocumentposition" (
  "position_ptr" BIGINT NOT NULL,
  "commercial_document" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("position_ptr")
);

CREATE TABLE "crm_textparagraphincommercialdocument" (
  "id" BIGINT NOT NULL,
  "commercial_document" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "text_paragraph" TEXT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_commercialdocumentmedia" (
  "id" BIGINT NOT NULL,
  "s3_url" VARCHAR(255) NOT NULL,
  "s3_key" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "media_type" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "last_updated_at" TIMESTAMP NOT NULL,
  "commercial_document" BIGINT NOT NULL,
  "pdf_export_process" BIGINT,
  "created_by" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_contractaddressassignment" (
  "id" BIGINT NOT NULL,
  "contract" BIGINT NOT NULL,
  "address" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_contractphoneassignment" (
  "id" BIGINT NOT NULL,
  "contract" BIGINT NOT NULL,
  "phone_number" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_contractemailassignment" (
  "id" BIGINT NOT NULL,
  "contract" BIGINT NOT NULL,
  "email" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_commercialdocumentaddressassignment" (
  "id" BIGINT NOT NULL,
  "document" BIGINT NOT NULL,
  "address" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_commercialdocumentphoneassignment" (
  "id" BIGINT NOT NULL,
  "document" BIGINT NOT NULL,
  "phone_number" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_commercialdocumentemailassignment" (
  "id" BIGINT NOT NULL,
  "document" BIGINT NOT NULL,
  "email" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_currency" (
  "id" BIGINT NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "short_name" VARCHAR(255) NOT NULL,
  "rounding" DECIMAL(18, 2),
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_unit" (
  "id" BIGINT NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "short_name" VARCHAR(255) NOT NULL,
  "fraction_factor_to_next_higher_unit" DECIMAL(18, 2),
  "is_a_fraction_of" BIGINT,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_tax" (
  "id" BIGINT NOT NULL,
  "tax_rate" DECIMAL(18, 2) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_currencytransform" (
  "id" BIGINT NOT NULL,
  "factor" DECIMAL(18, 2) NOT NULL,
  "from_currency" BIGINT NOT NULL,
  "to_currency" BIGINT NOT NULL,
  "product_type" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_unittransform" (
  "id" BIGINT NOT NULL,
  "factor" DECIMAL(18, 2) NOT NULL,
  "from_unit" BIGINT NOT NULL,
  "to_unit" BIGINT NOT NULL,
  "product_type" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_pdfexportprocess" (
  "id" BIGINT NOT NULL,
  "source_model" VARCHAR(255) NOT NULL,
  "source_id" BIGINT NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "result_url" VARCHAR(255) NOT NULL,
  "error_message" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "template_set" BIGINT,
  "triggered_by" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_workspace" (
  "id" BIGINT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "color" VARCHAR(255),
  "description" TEXT NOT NULL,
  "external_workspace_reference" VARCHAR(255) NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "date_added" DATE NOT NULL,
  "last_modified" DATE NOT NULL,
  "organization" BIGINT,
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "crm_roleinworkspace" (
  "id" BIGINT NOT NULL,
  "role" VARCHAR(255) NOT NULL,
  "group" INTEGER NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("group", "workspace", "role")
);

CREATE TABLE "crm_workspaceswitchevent" (
  "id" BIGINT NOT NULL,
  "timestamp" TIMESTAMP NOT NULL,
  "from_workspace" BIGINT,
  "to_workspace" BIGINT NOT NULL,
  "user" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_producttype" (
  "id" BIGINT NOT NULL,
  "description" TEXT,
  "title" VARCHAR(255) NOT NULL,
  "product_type_identifier" VARCHAR(255),
  "last_modification" TIMESTAMP NOT NULL,
  "date_of_creation" TIMESTAMP NOT NULL,
  "last_modified_by" BIGINT,
  "default_unit" BIGINT NOT NULL,
  "tax" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_product" (
  "id" BIGINT NOT NULL,
  "identifier" VARCHAR(255),
  "product_type" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_customergrouptransform" (
  "id" BIGINT NOT NULL,
  "factor" DECIMAL(18, 2) NOT NULL,
  "product_type" BIGINT NOT NULL,
  "from_party_group" BIGINT NOT NULL,
  "to_party_group" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_price" (
  "id" BIGINT NOT NULL,
  "price" DECIMAL(18, 2) NOT NULL,
  "valid_from" DATE,
  "valid_until" DATE,
  "currency" BIGINT NOT NULL,
  "unit" BIGINT NOT NULL,
  "party_group" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_productprice" (
  "price_ptr" BIGINT NOT NULL,
  "product_type" BIGINT NOT NULL,
  PRIMARY KEY ("price_ptr")
);

CREATE TABLE "crm_reportingperiodstatus" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_done" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_resourcetype" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_tasklinktype" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_taskstatus" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_done" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_agreementstatus" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_agreed" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_agreementtype" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_estimationstatus" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_obsolete" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_projectlinktype" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_projectstatus" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_done" BOOLEAN NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_resource" (
  "id" BIGINT NOT NULL,
  "resource_manager" BIGINT,
  "resource_type" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_humanresource" (
  "resource_ptr" BIGINT NOT NULL,
  "user" BIGINT NOT NULL,
  PRIMARY KEY ("resource_ptr")
);

CREATE TABLE "crm_project" (
  "id" BIGINT NOT NULL,
  "project_name" VARCHAR(255),
  "description" TEXT,
  "date_of_creation" TIMESTAMP NOT NULL,
  "last_modification" TIMESTAMP NOT NULL,
  "default_currency" BIGINT NOT NULL,
  "default_template_set" BIGINT,
  "last_modified_by" BIGINT NOT NULL,
  "project_manager" BIGINT,
  "project_status" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_genericprojectlink" (
  "id" BIGINT NOT NULL,
  "object_id" INTEGER NOT NULL,
  "date_of_creation" TIMESTAMP NOT NULL,
  "content_type" INTEGER NOT NULL,
  "last_modified_by" BIGINT NOT NULL,
  "project" BIGINT NOT NULL,
  "project_link_type" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_reportingperiod" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "begin" DATE NOT NULL,
  "end" DATE NOT NULL,
  "project" BIGINT NOT NULL,
  "status" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_resourcemanager" (
  "id" BIGINT NOT NULL,
  "user" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_resourceprice" (
  "price_ptr" BIGINT NOT NULL,
  "resource" BIGINT NOT NULL,
  PRIMARY KEY ("price_ptr")
);

CREATE TABLE "crm_task" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255),
  "description" TEXT,
  "last_status_change" DATE NOT NULL,
  "project" BIGINT NOT NULL,
  "status" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_estimation" (
  "id" BIGINT NOT NULL,
  "date_from" DATE NOT NULL,
  "date_until" DATE NOT NULL,
  "amount" DECIMAL(18, 2),
  "status" BIGINT NOT NULL,
  "resource" BIGINT NOT NULL,
  "reporting_period" BIGINT NOT NULL,
  "task" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_agreement" (
  "id" BIGINT NOT NULL,
  "date_from" DATE NOT NULL,
  "date_until" DATE NOT NULL,
  "amount" DECIMAL(18, 2),
  "unit" BIGINT NOT NULL,
  "status" BIGINT NOT NULL,
  "type" BIGINT NOT NULL,
  "resource" BIGINT NOT NULL,
  "costs" BIGINT NOT NULL,
  "task" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_generictasklink" (
  "id" BIGINT NOT NULL,
  "object_id" INTEGER NOT NULL,
  "date_of_creation" TIMESTAMP NOT NULL,
  "content_type" INTEGER NOT NULL,
  "last_modified_by" BIGINT NOT NULL,
  "task" BIGINT NOT NULL,
  "task_link_type" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_work" (
  "id" BIGINT NOT NULL,
  "date" DATE NOT NULL,
  "start_time" TIMESTAMP,
  "stop_time" TIMESTAMP,
  "worked_hours" DECIMAL(18, 2),
  "short_description" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "reporting_period" BIGINT NOT NULL,
  "task" BIGINT NOT NULL,
  "human_resource" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_subscription" (
  "id" BIGINT NOT NULL,
  "contract" BIGINT NOT NULL,
  "subscription_type" BIGINT,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_subscriptionsubscriptionevent" (
  "id" BIGINT NOT NULL,
  "event_date" DATE,
  "event" VARCHAR(255) NOT NULL,
  "subscriptions" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "crm_subscriptiontype" (
  "id" BIGINT NOT NULL,
  "cancellation_period" INTEGER,
  "automatic_contract_extension" INTEGER,
  "automatic_contract_extension_reminder" INTEGER,
  "minimum_duration" INTEGER,
  "payment_interval" INTEGER,
  "contract_document" VARCHAR(255),
  "product_type" BIGINT,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_documenttemplate" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255),
  "xsl_file" VARCHAR(255) NOT NULL,
  "fop_config_file" VARCHAR(255),
  "logo" VARCHAR(255),
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_templateset" (
  "id" BIGINT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "balance_sheet_statement_template" BIGINT,
  "despatch_advice_template" BIGINT,
  "invoice_template" BIGINT,
  "monthly_project_summary_template" BIGINT,
  "payment_reminder_template" BIGINT,
  "profit_loss_statement_template" BIGINT,
  "purchase_order_template" BIGINT,
  "quotation_template" BIGINT,
  "sales_order_template" BIGINT,
  "work_report_template" BIGINT,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_userextension" (
  "id" BIGINT NOT NULL,
  "default_currency" BIGINT NOT NULL,
  "default_template_set" BIGINT NOT NULL,
  "user" INTEGER NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_textparagraphindocumenttemplate" (
  "id" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "text_paragraph" TEXT NOT NULL,
  "document_template" BIGINT NOT NULL,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_useraddressassignment" (
  "id" BIGINT NOT NULL,
  "user" INTEGER NOT NULL,
  "address" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_userphoneassignment" (
  "id" BIGINT NOT NULL,
  "user" INTEGER NOT NULL,
  "phone_number" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "djangoUserExtension_useremailassignment" (
  "id" BIGINT NOT NULL,
  "user" INTEGER NOT NULL,
  "email" BIGINT NOT NULL,
  "purpose" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "valid_from" DATE,
  "valid_to" DATE,
  "workspace" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_crm_roleinworkspace_group_workspace_1" ON "crm_roleinworkspace" ("group", "workspace");

CREATE INDEX "idx_crm_workspaceswitchevent_user_timestamp_1" ON "crm_workspaceswitchevent" ("user", "timestamp");

ALTER TABLE "accounting_accountingperiod" ADD CONSTRAINT "fk_accounting_accountingperiod_template_profit_loss_9db9ad23" FOREIGN KEY ("template_profit_loss_statement") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "accounting_accountingperiod" ADD CONSTRAINT "fk_accounting_accountingperiod_template_set_balance_sheet_2" FOREIGN KEY ("template_set_balance_sheet") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "accounting_booking" ADD CONSTRAINT "fk_accounting_booking_accounting_period_1" FOREIGN KEY ("accounting_period") REFERENCES "accounting_accountingperiod" ("id");

ALTER TABLE "accounting_booking" ADD CONSTRAINT "fk_accounting_booking_from_account_3" FOREIGN KEY ("from_account") REFERENCES "accounting_account" ("id");

ALTER TABLE "accounting_booking" ADD CONSTRAINT "fk_accounting_booking_to_account_4" FOREIGN KEY ("to_account") REFERENCES "accounting_account" ("id");

ALTER TABLE "accounting_productcategory" ADD CONSTRAINT "fk_accounting_productcategory_loss_account_1" FOREIGN KEY ("loss_account") REFERENCES "accounting_account" ("id");

ALTER TABLE "accounting_productcategory" ADD CONSTRAINT "fk_accounting_productcategory_profit_account_2" FOREIGN KEY ("profit_account") REFERENCES "accounting_account" ("id");

ALTER TABLE "accounting_taxaccountassignment" ADD CONSTRAINT "fk_accounting_taxaccountassignment_tax_1" FOREIGN KEY ("tax") REFERENCES "crm_tax" ("id");

ALTER TABLE "accounting_taxaccountassignment" ADD CONSTRAINT "fk_accounting_taxaccountassignment_activa_account_2" FOREIGN KEY ("activa_account") REFERENCES "accounting_account" ("id");

ALTER TABLE "accounting_taxaccountassignment" ADD CONSTRAINT "fk_accounting_taxaccountassignment_passiva_account_3" FOREIGN KEY ("passiva_account") REFERENCES "accounting_account" ("id");

ALTER TABLE "accounting_productcategoryassignment" ADD CONSTRAINT "fk_accounting_productcategoryassignment_product_type_1" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "accounting_productcategoryassignment" ADD CONSTRAINT "fk_accounting_productcategoryassignment_category_2" FOREIGN KEY ("category") REFERENCES "accounting_productcategory" ("id");

ALTER TABLE "crm_party" ADD CONSTRAINT "fk_crm_party_default_billing_cycle_1" FOREIGN KEY ("default_billing_cycle") REFERENCES "crm_customerbillingcycle" ("id");

ALTER TABLE "crm_party" ADD CONSTRAINT "fk_crm_party_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_partyemail" ADD CONSTRAINT "fk_crm_partyemail_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_partygroup" ADD CONSTRAINT "fk_crm_partygroup_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_partygroupmembership" ADD CONSTRAINT "fk_crm_partygroupmembership_party_1" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_partygroupmembership" ADD CONSTRAINT "fk_crm_partygroupmembership_party_group_2" FOREIGN KEY ("party_group") REFERENCES "crm_partygroup" ("id");

ALTER TABLE "crm_partygroupmembership" ADD CONSTRAINT "fk_crm_partygroupmembership_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_partyidentification" ADD CONSTRAINT "fk_crm_partyidentification_party_1" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_partyidentification" ADD CONSTRAINT "fk_crm_partyidentification_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_partyrole" ADD CONSTRAINT "fk_crm_partyrole_party_1" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_partyrole" ADD CONSTRAINT "fk_crm_partyrole_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_phonenumber" ADD CONSTRAINT "fk_crm_phonenumber_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_address" ADD CONSTRAINT "fk_crm_address_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_addressassignment" ADD CONSTRAINT "fk_crm_addressassignment_address_1" FOREIGN KEY ("address") REFERENCES "crm_address" ("id");

ALTER TABLE "crm_addressassignment" ADD CONSTRAINT "fk_crm_addressassignment_party_2" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_addressassignment" ADD CONSTRAINT "fk_crm_addressassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_emailassignment" ADD CONSTRAINT "fk_crm_emailassignment_party_1" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_emailassignment" ADD CONSTRAINT "fk_crm_emailassignment_email_2" FOREIGN KEY ("email") REFERENCES "crm_partyemail" ("id");

ALTER TABLE "crm_emailassignment" ADD CONSTRAINT "fk_crm_emailassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_phoneassignment" ADD CONSTRAINT "fk_crm_phoneassignment_party_1" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_phoneassignment" ADD CONSTRAINT "fk_crm_phoneassignment_phone_2" FOREIGN KEY ("phone") REFERENCES "crm_phonenumber" ("id");

ALTER TABLE "crm_phoneassignment" ADD CONSTRAINT "fk_crm_phoneassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_organization" ADD CONSTRAINT "fk_crm_organization_party_ptr_1" FOREIGN KEY ("party_ptr") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_partycontact" ADD CONSTRAINT "fk_crm_partycontact_party_ptr_1" FOREIGN KEY ("party_ptr") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_organizationmembership" ADD CONSTRAINT "fk_crm_organizationmembership_organization_1" FOREIGN KEY ("organization") REFERENCES "crm_organization" ("party_ptr");

ALTER TABLE "crm_organizationmembership" ADD CONSTRAINT "fk_crm_organizationmembership_contact_2" FOREIGN KEY ("contact") REFERENCES "crm_partycontact" ("party_ptr");

ALTER TABLE "crm_organizationmembership" ADD CONSTRAINT "fk_crm_organizationmembership_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_organizationrelationship" ADD CONSTRAINT "fk_crm_organizationrelationship_child_1" FOREIGN KEY ("child") REFERENCES "crm_organization" ("party_ptr");

ALTER TABLE "crm_organizationrelationship" ADD CONSTRAINT "fk_crm_organizationrelationship_parent_2" FOREIGN KEY ("parent") REFERENCES "crm_organization" ("party_ptr");

ALTER TABLE "crm_organizationrelationship" ADD CONSTRAINT "fk_crm_organizationrelationship_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_customerbillingcycle" ADD CONSTRAINT "fk_crm_customerbillingcycle_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_contract" ADD CONSTRAINT "fk_crm_contract_default_currency_1" FOREIGN KEY ("default_currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "crm_contract" ADD CONSTRAINT "fk_crm_contract_default_template_set_2" FOREIGN KEY ("default_template_set") REFERENCES "djangoUserExtension_templateset" ("id");

ALTER TABLE "crm_contract" ADD CONSTRAINT "fk_crm_contract_buyer_party_3" FOREIGN KEY ("buyer_party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_contract" ADD CONSTRAINT "fk_crm_contract_supplier_party_4" FOREIGN KEY ("supplier_party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_contract" ADD CONSTRAINT "fk_crm_contract_workspace_5" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_commercialdocument" ADD CONSTRAINT "fk_crm_commercialdocument_contract_1" FOREIGN KEY ("contract") REFERENCES "crm_contract" ("id");

ALTER TABLE "crm_commercialdocument" ADD CONSTRAINT "fk_crm_commercialdocument_party_2" FOREIGN KEY ("party") REFERENCES "crm_party" ("id");

ALTER TABLE "crm_commercialdocument" ADD CONSTRAINT "fk_crm_commercialdocument_currency_3" FOREIGN KEY ("currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "crm_commercialdocument" ADD CONSTRAINT "fk_crm_commercialdocument_template_set_4" FOREIGN KEY ("template_set") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "crm_commercialdocument" ADD CONSTRAINT "fk_crm_commercialdocument_derived_from_commercial_document_5" FOREIGN KEY ("derived_from_commercial_document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_commercialdocument" ADD CONSTRAINT "fk_crm_commercialdocument_workspace_6" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_position" ADD CONSTRAINT "fk_crm_position_product_type_1" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "crm_position" ADD CONSTRAINT "fk_crm_position_unit_2" FOREIGN KEY ("unit") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_commercialdocumentposition" ADD CONSTRAINT "fk_crm_commercialdocumentposition_position_ptr_1" FOREIGN KEY ("position_ptr") REFERENCES "crm_position" ("id");

ALTER TABLE "crm_commercialdocumentposition" ADD CONSTRAINT "fk_crm_commercialdocumentposition_commercial_document_2" FOREIGN KEY ("commercial_document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_commercialdocumentposition" ADD CONSTRAINT "fk_crm_commercialdocumentposition_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_textparagraphincommercialdocument" ADD CONSTRAINT "fk_crm_textparagraphincommercialdocument_commercial_e049b2e6" FOREIGN KEY ("commercial_document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_textparagraphincommercialdocument" ADD CONSTRAINT "fk_crm_textparagraphincommercialdocument_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_commercialdocumentmedia" ADD CONSTRAINT "fk_crm_commercialdocumentmedia_commercial_document_1" FOREIGN KEY ("commercial_document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_commercialdocumentmedia" ADD CONSTRAINT "fk_crm_commercialdocumentmedia_pdf_export_process_2" FOREIGN KEY ("pdf_export_process") REFERENCES "crm_pdfexportprocess" ("id");

ALTER TABLE "crm_commercialdocumentmedia" ADD CONSTRAINT "fk_crm_commercialdocumentmedia_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_contractaddressassignment" ADD CONSTRAINT "fk_crm_contractaddressassignment_contract_1" FOREIGN KEY ("contract") REFERENCES "crm_contract" ("id");

ALTER TABLE "crm_contractaddressassignment" ADD CONSTRAINT "fk_crm_contractaddressassignment_address_2" FOREIGN KEY ("address") REFERENCES "crm_address" ("id");

ALTER TABLE "crm_contractaddressassignment" ADD CONSTRAINT "fk_crm_contractaddressassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_contractphoneassignment" ADD CONSTRAINT "fk_crm_contractphoneassignment_contract_1" FOREIGN KEY ("contract") REFERENCES "crm_contract" ("id");

ALTER TABLE "crm_contractphoneassignment" ADD CONSTRAINT "fk_crm_contractphoneassignment_phone_number_2" FOREIGN KEY ("phone_number") REFERENCES "crm_phonenumber" ("id");

ALTER TABLE "crm_contractphoneassignment" ADD CONSTRAINT "fk_crm_contractphoneassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_contractemailassignment" ADD CONSTRAINT "fk_crm_contractemailassignment_contract_1" FOREIGN KEY ("contract") REFERENCES "crm_contract" ("id");

ALTER TABLE "crm_contractemailassignment" ADD CONSTRAINT "fk_crm_contractemailassignment_email_2" FOREIGN KEY ("email") REFERENCES "crm_partyemail" ("id");

ALTER TABLE "crm_contractemailassignment" ADD CONSTRAINT "fk_crm_contractemailassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_commercialdocumentaddressassignment" ADD CONSTRAINT "fk_crm_commercialdocumentaddressassignment_document_1" FOREIGN KEY ("document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_commercialdocumentaddressassignment" ADD CONSTRAINT "fk_crm_commercialdocumentaddressassignment_address_2" FOREIGN KEY ("address") REFERENCES "crm_address" ("id");

ALTER TABLE "crm_commercialdocumentaddressassignment" ADD CONSTRAINT "fk_crm_commercialdocumentaddressassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_commercialdocumentphoneassignment" ADD CONSTRAINT "fk_crm_commercialdocumentphoneassignment_document_1" FOREIGN KEY ("document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_commercialdocumentphoneassignment" ADD CONSTRAINT "fk_crm_commercialdocumentphoneassignment_phone_number_2" FOREIGN KEY ("phone_number") REFERENCES "crm_phonenumber" ("id");

ALTER TABLE "crm_commercialdocumentphoneassignment" ADD CONSTRAINT "fk_crm_commercialdocumentphoneassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_commercialdocumentemailassignment" ADD CONSTRAINT "fk_crm_commercialdocumentemailassignment_document_1" FOREIGN KEY ("document") REFERENCES "crm_commercialdocument" ("id");

ALTER TABLE "crm_commercialdocumentemailassignment" ADD CONSTRAINT "fk_crm_commercialdocumentemailassignment_email_2" FOREIGN KEY ("email") REFERENCES "crm_partyemail" ("id");

ALTER TABLE "crm_commercialdocumentemailassignment" ADD CONSTRAINT "fk_crm_commercialdocumentemailassignment_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_unit" ADD CONSTRAINT "fk_crm_unit_is_a_fraction_of_1" FOREIGN KEY ("is_a_fraction_of") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_currencytransform" ADD CONSTRAINT "fk_crm_currencytransform_from_currency_1" FOREIGN KEY ("from_currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "crm_currencytransform" ADD CONSTRAINT "fk_crm_currencytransform_to_currency_2" FOREIGN KEY ("to_currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "crm_currencytransform" ADD CONSTRAINT "fk_crm_currencytransform_product_type_3" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "crm_unittransform" ADD CONSTRAINT "fk_crm_unittransform_from_unit_1" FOREIGN KEY ("from_unit") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_unittransform" ADD CONSTRAINT "fk_crm_unittransform_to_unit_2" FOREIGN KEY ("to_unit") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_unittransform" ADD CONSTRAINT "fk_crm_unittransform_product_type_3" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "crm_pdfexportprocess" ADD CONSTRAINT "fk_crm_pdfexportprocess_template_set_1" FOREIGN KEY ("template_set") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "crm_pdfexportprocess" ADD CONSTRAINT "fk_crm_pdfexportprocess_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_workspace" ADD CONSTRAINT "fk_crm_workspace_organization_1" FOREIGN KEY ("organization") REFERENCES "crm_organization" ("party_ptr");

ALTER TABLE "crm_roleinworkspace" ADD CONSTRAINT "fk_crm_roleinworkspace_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_workspaceswitchevent" ADD CONSTRAINT "fk_crm_workspaceswitchevent_from_workspace_1" FOREIGN KEY ("from_workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_workspaceswitchevent" ADD CONSTRAINT "fk_crm_workspaceswitchevent_to_workspace_2" FOREIGN KEY ("to_workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_producttype" ADD CONSTRAINT "fk_crm_producttype_default_unit_1" FOREIGN KEY ("default_unit") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_producttype" ADD CONSTRAINT "fk_crm_producttype_tax_2" FOREIGN KEY ("tax") REFERENCES "crm_tax" ("id");

ALTER TABLE "crm_producttype" ADD CONSTRAINT "fk_crm_producttype_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_product" ADD CONSTRAINT "fk_crm_product_product_type_1" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "crm_product" ADD CONSTRAINT "fk_crm_product_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_customergrouptransform" ADD CONSTRAINT "fk_crm_customergrouptransform_product_type_1" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "crm_customergrouptransform" ADD CONSTRAINT "fk_crm_customergrouptransform_from_party_group_2" FOREIGN KEY ("from_party_group") REFERENCES "crm_partygroup" ("id");

ALTER TABLE "crm_customergrouptransform" ADD CONSTRAINT "fk_crm_customergrouptransform_to_party_group_3" FOREIGN KEY ("to_party_group") REFERENCES "crm_partygroup" ("id");

ALTER TABLE "crm_customergrouptransform" ADD CONSTRAINT "fk_crm_customergrouptransform_workspace_4" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_price" ADD CONSTRAINT "fk_crm_price_currency_1" FOREIGN KEY ("currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "crm_price" ADD CONSTRAINT "fk_crm_price_unit_2" FOREIGN KEY ("unit") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_price" ADD CONSTRAINT "fk_crm_price_party_group_3" FOREIGN KEY ("party_group") REFERENCES "crm_partygroup" ("id");

ALTER TABLE "crm_price" ADD CONSTRAINT "fk_crm_price_workspace_4" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_productprice" ADD CONSTRAINT "fk_crm_productprice_price_ptr_1" FOREIGN KEY ("price_ptr") REFERENCES "crm_price" ("id");

ALTER TABLE "crm_productprice" ADD CONSTRAINT "fk_crm_productprice_product_type_2" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "crm_resource" ADD CONSTRAINT "fk_crm_resource_resource_manager_1" FOREIGN KEY ("resource_manager") REFERENCES "crm_resourcemanager" ("id");

ALTER TABLE "crm_resource" ADD CONSTRAINT "fk_crm_resource_resource_type_2" FOREIGN KEY ("resource_type") REFERENCES "crm_resourcetype" ("id");

ALTER TABLE "crm_resource" ADD CONSTRAINT "fk_crm_resource_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_humanresource" ADD CONSTRAINT "fk_crm_humanresource_resource_ptr_1" FOREIGN KEY ("resource_ptr") REFERENCES "crm_resource" ("id");

ALTER TABLE "crm_humanresource" ADD CONSTRAINT "fk_crm_humanresource_user_2" FOREIGN KEY ("user") REFERENCES "djangoUserExtension_userextension" ("id");

ALTER TABLE "crm_project" ADD CONSTRAINT "fk_crm_project_default_currency_1" FOREIGN KEY ("default_currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "crm_project" ADD CONSTRAINT "fk_crm_project_default_template_set_2" FOREIGN KEY ("default_template_set") REFERENCES "djangoUserExtension_templateset" ("id");

ALTER TABLE "crm_project" ADD CONSTRAINT "fk_crm_project_project_status_3" FOREIGN KEY ("project_status") REFERENCES "crm_projectstatus" ("id");

ALTER TABLE "crm_project" ADD CONSTRAINT "fk_crm_project_workspace_4" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_genericprojectlink" ADD CONSTRAINT "fk_crm_genericprojectlink_project_1" FOREIGN KEY ("project") REFERENCES "crm_project" ("id");

ALTER TABLE "crm_genericprojectlink" ADD CONSTRAINT "fk_crm_genericprojectlink_project_link_type_2" FOREIGN KEY ("project_link_type") REFERENCES "crm_projectlinktype" ("id");

ALTER TABLE "crm_genericprojectlink" ADD CONSTRAINT "fk_crm_genericprojectlink_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_reportingperiod" ADD CONSTRAINT "fk_crm_reportingperiod_project_1" FOREIGN KEY ("project") REFERENCES "crm_project" ("id");

ALTER TABLE "crm_reportingperiod" ADD CONSTRAINT "fk_crm_reportingperiod_status_2" FOREIGN KEY ("status") REFERENCES "crm_reportingperiodstatus" ("id");

ALTER TABLE "crm_reportingperiod" ADD CONSTRAINT "fk_crm_reportingperiod_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_resourcemanager" ADD CONSTRAINT "fk_crm_resourcemanager_user_1" FOREIGN KEY ("user") REFERENCES "djangoUserExtension_userextension" ("id");

ALTER TABLE "crm_resourcemanager" ADD CONSTRAINT "fk_crm_resourcemanager_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_resourceprice" ADD CONSTRAINT "fk_crm_resourceprice_price_ptr_1" FOREIGN KEY ("price_ptr") REFERENCES "crm_price" ("id");

ALTER TABLE "crm_resourceprice" ADD CONSTRAINT "fk_crm_resourceprice_resource_2" FOREIGN KEY ("resource") REFERENCES "crm_resource" ("id");

ALTER TABLE "crm_task" ADD CONSTRAINT "fk_crm_task_project_1" FOREIGN KEY ("project") REFERENCES "crm_project" ("id");

ALTER TABLE "crm_task" ADD CONSTRAINT "fk_crm_task_status_2" FOREIGN KEY ("status") REFERENCES "crm_taskstatus" ("id");

ALTER TABLE "crm_task" ADD CONSTRAINT "fk_crm_task_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_estimation" ADD CONSTRAINT "fk_crm_estimation_status_1" FOREIGN KEY ("status") REFERENCES "crm_estimationstatus" ("id");

ALTER TABLE "crm_estimation" ADD CONSTRAINT "fk_crm_estimation_resource_2" FOREIGN KEY ("resource") REFERENCES "crm_resource" ("id");

ALTER TABLE "crm_estimation" ADD CONSTRAINT "fk_crm_estimation_reporting_period_3" FOREIGN KEY ("reporting_period") REFERENCES "crm_reportingperiod" ("id");

ALTER TABLE "crm_estimation" ADD CONSTRAINT "fk_crm_estimation_task_4" FOREIGN KEY ("task") REFERENCES "crm_task" ("id");

ALTER TABLE "crm_estimation" ADD CONSTRAINT "fk_crm_estimation_workspace_5" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_unit_1" FOREIGN KEY ("unit") REFERENCES "crm_unit" ("id");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_status_2" FOREIGN KEY ("status") REFERENCES "crm_agreementstatus" ("id");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_type_3" FOREIGN KEY ("type") REFERENCES "crm_agreementtype" ("id");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_resource_4" FOREIGN KEY ("resource") REFERENCES "crm_resource" ("id");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_costs_5" FOREIGN KEY ("costs") REFERENCES "crm_resourceprice" ("price_ptr");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_task_6" FOREIGN KEY ("task") REFERENCES "crm_task" ("id");

ALTER TABLE "crm_agreement" ADD CONSTRAINT "fk_crm_agreement_workspace_7" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_generictasklink" ADD CONSTRAINT "fk_crm_generictasklink_task_1" FOREIGN KEY ("task") REFERENCES "crm_task" ("id");

ALTER TABLE "crm_generictasklink" ADD CONSTRAINT "fk_crm_generictasklink_task_link_type_2" FOREIGN KEY ("task_link_type") REFERENCES "crm_tasklinktype" ("id");

ALTER TABLE "crm_generictasklink" ADD CONSTRAINT "fk_crm_generictasklink_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_work" ADD CONSTRAINT "fk_crm_work_reporting_period_1" FOREIGN KEY ("reporting_period") REFERENCES "crm_reportingperiod" ("id");

ALTER TABLE "crm_work" ADD CONSTRAINT "fk_crm_work_task_2" FOREIGN KEY ("task") REFERENCES "crm_task" ("id");

ALTER TABLE "crm_work" ADD CONSTRAINT "fk_crm_work_human_resource_3" FOREIGN KEY ("human_resource") REFERENCES "crm_humanresource" ("resource_ptr");

ALTER TABLE "crm_work" ADD CONSTRAINT "fk_crm_work_workspace_4" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "crm_subscription" ADD CONSTRAINT "fk_crm_subscription_contract_1" FOREIGN KEY ("contract") REFERENCES "crm_contract" ("id");

ALTER TABLE "crm_subscription" ADD CONSTRAINT "fk_crm_subscription_subscription_type_2" FOREIGN KEY ("subscription_type") REFERENCES "crm_subscriptiontype" ("id");

ALTER TABLE "crm_subscriptionsubscriptionevent" ADD CONSTRAINT "fk_crm_subscriptionsubscriptionevent_subscriptions_1" FOREIGN KEY ("subscriptions") REFERENCES "crm_subscription" ("id");

ALTER TABLE "crm_subscriptiontype" ADD CONSTRAINT "fk_crm_subscriptiontype_product_type_1" FOREIGN KEY ("product_type") REFERENCES "crm_producttype" ("id");

ALTER TABLE "djangoUserExtension_documenttemplate" ADD CONSTRAINT "fk_djangoUserExtension_documenttemplate_workspace_1" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_balance_sheet_st_39aa2228" FOREIGN KEY ("balance_sheet_statement_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_despatch_advice__f32795bc" FOREIGN KEY ("despatch_advice_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_invoice_template_3" FOREIGN KEY ("invoice_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_monthly_project__e2b4fe82" FOREIGN KEY ("monthly_project_summary_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_payment_reminder_ecd50d77" FOREIGN KEY ("payment_reminder_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_profit_loss_stat_2e87d338" FOREIGN KEY ("profit_loss_statement_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_purchase_order_template_7" FOREIGN KEY ("purchase_order_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_quotation_template_8" FOREIGN KEY ("quotation_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_sales_order_template_9" FOREIGN KEY ("sales_order_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_work_report_template_10" FOREIGN KEY ("work_report_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_templateset" ADD CONSTRAINT "fk_djangoUserExtension_templateset_workspace_11" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "djangoUserExtension_userextension" ADD CONSTRAINT "fk_djangoUserExtension_userextension_default_currency_1" FOREIGN KEY ("default_currency") REFERENCES "crm_currency" ("id");

ALTER TABLE "djangoUserExtension_userextension" ADD CONSTRAINT "fk_djangoUserExtension_userextension_default_template_set_2" FOREIGN KEY ("default_template_set") REFERENCES "djangoUserExtension_templateset" ("id");

ALTER TABLE "djangoUserExtension_userextension" ADD CONSTRAINT "fk_djangoUserExtension_userextension_workspace_3" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "djangoUserExtension_textparagraphindocumenttemplate" ADD CONSTRAINT "fk_djangoUserExtension_textparagraphindocumenttempl_455fa68b" FOREIGN KEY ("document_template") REFERENCES "djangoUserExtension_documenttemplate" ("id");

ALTER TABLE "djangoUserExtension_textparagraphindocumenttemplate" ADD CONSTRAINT "fk_djangoUserExtension_textparagraphindocumenttempl_5901092e" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "djangoUserExtension_useraddressassignment" ADD CONSTRAINT "fk_djangoUserExtension_useraddressassignment_address_1" FOREIGN KEY ("address") REFERENCES "crm_address" ("id");

ALTER TABLE "djangoUserExtension_useraddressassignment" ADD CONSTRAINT "fk_djangoUserExtension_useraddressassignment_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "djangoUserExtension_userphoneassignment" ADD CONSTRAINT "fk_djangoUserExtension_userphoneassignment_phone_number_1" FOREIGN KEY ("phone_number") REFERENCES "crm_phonenumber" ("id");

ALTER TABLE "djangoUserExtension_userphoneassignment" ADD CONSTRAINT "fk_djangoUserExtension_userphoneassignment_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");

ALTER TABLE "djangoUserExtension_useremailassignment" ADD CONSTRAINT "fk_djangoUserExtension_useremailassignment_email_1" FOREIGN KEY ("email") REFERENCES "crm_partyemail" ("id");

ALTER TABLE "djangoUserExtension_useremailassignment" ADD CONSTRAINT "fk_djangoUserExtension_useremailassignment_workspace_2" FOREIGN KEY ("workspace") REFERENCES "crm_workspace" ("id");
