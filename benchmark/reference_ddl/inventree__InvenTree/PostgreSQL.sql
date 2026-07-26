CREATE TABLE "RuleSet" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "can_view" BOOLEAN NOT NULL,
  "can_add" BOOLEAN NOT NULL,
  "can_change" BOOLEAN NOT NULL,
  "can_delete" BOOLEAN NOT NULL,
  "group_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("name", "group_id")
);

CREATE TABLE "Owner" (
  "id" INTEGER NOT NULL,
  "owner_id" INTEGER,
  "owner_type_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("owner_type_id", "owner_id")
);

CREATE TABLE "User" (
  "id" INTEGER NOT NULL,
  "username" VARCHAR(150) NOT NULL,
  "email" VARCHAR(254),
  "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
  "date_joined" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("username")
);

CREATE TABLE "Plugin" (
  "id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "version" VARCHAR(64),
  "active" BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY ("id"),
  UNIQUE ("key")
);

CREATE TABLE "Machine" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "machine_type" VARCHAR(255) NOT NULL,
  "status" VARCHAR(64) NOT NULL,
  "plugin_id" INTEGER,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "ApiToken" (
  "id" INTEGER NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255),
  "expiry" DATE NOT NULL,
  "revoked" BOOLEAN NOT NULL,
  "user_id" INTEGER NOT NULL,
  "last_seen" DATE,
  PRIMARY KEY ("id")
);

CREATE TABLE "UserProfile" (
  "id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "language" VARCHAR(255),
  "theme" JSONB,
  "displayname" VARCHAR(255),
  "location" VARCHAR(255),
  "active" BOOLEAN NOT NULL,
  "primary_group_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "Build" (
  "id" INTEGER NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "quantity" INTEGER NOT NULL,
  "status" INTEGER NOT NULL,
  "creation_date" DATE NOT NULL,
  "completion_date" DATE,
  "part_id" INTEGER NOT NULL,
  "parent_id" INTEGER,
  "reference" VARCHAR(255) NOT NULL,
  "target_date" DATE,
  "responsible_id" INTEGER,
  "priority" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("reference")
);

CREATE TABLE "BuildItem" (
  "id" INTEGER NOT NULL,
  "quantity" DECIMAL(18, 2) NOT NULL,
  "stock_item_id" INTEGER NOT NULL,
  "install_into_id" INTEGER,
  "build_line_id" INTEGER NOT NULL,
  "metadata" JSONB,
  PRIMARY KEY ("id"),
  UNIQUE ("build_line_id", "stock_item_id", "install_into_id")
);

CREATE TABLE "BuildLine" (
  "id" INTEGER NOT NULL,
  "quantity" DECIMAL(18, 2) NOT NULL,
  "bom_item_id" INTEGER NOT NULL,
  "build_id" INTEGER NOT NULL,
  "consumed" DECIMAL(18, 2) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("build_id", "bom_item_id")
);

CREATE TABLE "InvenTreeSetting" (
  "id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "value" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("key")
);

CREATE TABLE "InvenTreeUserSetting" (
  "id" INTEGER NOT NULL,
  "value" VARCHAR(255),
  "key" VARCHAR(255) NOT NULL,
  "user_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("key", "user_id")
);

CREATE TABLE "ColorTheme" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255),
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id")
);

CREATE TABLE "NotificationEntry" (
  "id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "user_id" INTEGER NOT NULL,
  "updated" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("key", "user_id")
);

CREATE TABLE "Company" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "website" VARCHAR(255),
  "address" VARCHAR(255),
  "phone" VARCHAR(255),
  "email" VARCHAR(255),
  "contact" VARCHAR(255),
  "is_customer" BOOLEAN NOT NULL,
  "is_supplier" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "Contact" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "phone" VARCHAR(255),
  "email" VARCHAR(255),
  "role" VARCHAR(255),
  "company_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "SupplierPart" (
  "id" INTEGER NOT NULL,
  "SKU" VARCHAR(255) NOT NULL,
  "base_cost" DECIMAL(18, 2) NOT NULL,
  "multiple" INTEGER NOT NULL,
  "minimum" INTEGER NOT NULL,
  "lead_time" VARCHAR(255),
  "supplier_id" INTEGER NOT NULL,
  "part_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "SupplierPriceBreak" (
  "id" INTEGER NOT NULL,
  "quantity" INTEGER NOT NULL,
  "cost" DECIMAL(18, 2) NOT NULL,
  "part_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "Part" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "minimum_stock" INTEGER NOT NULL,
  "units" VARCHAR(255),
  "buildable" BOOLEAN NOT NULL,
  "consumable" BOOLEAN NOT NULL,
  "trackable" BOOLEAN NOT NULL,
  "purchaseable" BOOLEAN NOT NULL,
  "active" BOOLEAN NOT NULL,
  "category_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "PartCategory" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "default_keywords" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "PartAttachment" (
  "id" INTEGER NOT NULL,
  "attachment" VARCHAR(255) NOT NULL,
  "comment" VARCHAR(255) NOT NULL,
  "part_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "BomItem" (
  "id" INTEGER NOT NULL,
  "quantity" INTEGER NOT NULL,
  "overage" VARCHAR(255),
  "note" VARCHAR(255),
  "part_id" INTEGER NOT NULL,
  "sub_part_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "PartStar" (
  "id" INTEGER NOT NULL,
  "part_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "PurchaseOrder" (
  "id" INTEGER NOT NULL,
  "reference" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "creation_date" DATE NOT NULL,
  "issue_date" DATE,
  "notes" TEXT,
  "created_by_id" INTEGER,
  "supplier_id" INTEGER NOT NULL,
  "status" VARCHAR(64) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("reference")
);

CREATE TABLE "PurchaseOrderLineItem" (
  "id" INTEGER NOT NULL,
  "quantity" INTEGER NOT NULL,
  "reference" VARCHAR(255),
  "received" INTEGER NOT NULL,
  "order_id" INTEGER NOT NULL,
  "supplier_part_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "StockItem" (
  "id" INTEGER NOT NULL,
  "serial" INTEGER,
  "quantity" INTEGER NOT NULL,
  "status" INTEGER NOT NULL,
  "belongs_to_id" INTEGER,
  "location_id" INTEGER,
  "part_id" INTEGER NOT NULL,
  "supplier_part_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("part_id", "serial")
);

CREATE TABLE "StockLocation" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "parent_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("name", "parent_id")
);

CREATE TABLE "StockItemTracking" (
  "id" INTEGER NOT NULL,
  "date" TIMESTAMP NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "notes" TEXT,
  "system" BOOLEAN NOT NULL,
  "quantity" INTEGER NOT NULL,
  "item_id" INTEGER NOT NULL,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "ReportAsset" (
  "id" INTEGER NOT NULL,
  "asset" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "template_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "ReportTemplate" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "template" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "TestReport" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "template" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "part_filters" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "PluginConfig" (
  "id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255),
  "active" BOOLEAN NOT NULL,
  "plugin_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("key")
);

CREATE TABLE "MachineConfig" (
  "id" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "machine_type" VARCHAR(255) NOT NULL,
  "driver" VARCHAR(255) NOT NULL,
  "active" BOOLEAN NOT NULL,
  "machine_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("name")
);

CREATE TABLE "MachineSetting" (
  "id" INTEGER NOT NULL,
  "key" VARCHAR(255) NOT NULL,
  "value" VARCHAR(255),
  "config_type" VARCHAR(255) NOT NULL,
  "machine_config_id" UUID NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("machine_config_id", "config_type", "key")
);

CREATE TABLE "DataImportSession" (
  "id" BIGINT NOT NULL,
  "timestamp" TIMESTAMP NOT NULL,
  "data_file" VARCHAR(255) NOT NULL,
  "columns" JSONB,
  "model_type" VARCHAR(255) NOT NULL,
  "status" INTEGER NOT NULL,
  "field_defaults" JSONB,
  "user_id" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "DataImportRow" (
  "id" BIGINT NOT NULL,
  "row_index" INTEGER NOT NULL,
  "row_data" JSONB,
  "data" JSONB,
  "errors" JSONB,
  "valid" BOOLEAN NOT NULL,
  "complete" BOOLEAN NOT NULL,
  "session_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "DataImportColumnMap" (
  "id" BIGINT NOT NULL,
  "field" VARCHAR(255) NOT NULL,
  "column" VARCHAR(255),
  "session_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "uidx_ApiToken_key_1" ON "ApiToken" ("key");

CREATE UNIQUE INDEX "uidx_UserProfile_user_id_1" ON "UserProfile" ("user_id");

CREATE INDEX "idx_user_active" ON "User" ("is_active", "username");
CREATE INDEX "idx_apitoken_user_active" ON "ApiToken" ("user_id", "revoked", "expiry");
CREATE INDEX "idx_build_part_status" ON "Build" ("part_id", "status");
CREATE INDEX "idx_build_parent" ON "Build" ("parent_id");
CREATE INDEX "idx_build_responsible" ON "Build" ("responsible_id");
CREATE INDEX "idx_builditem_stock" ON "BuildItem" ("stock_item_id");
CREATE INDEX "idx_buildline_build" ON "BuildLine" ("build_id");
CREATE INDEX "idx_usersetting_user" ON "InvenTreeUserSetting" ("user_id");
CREATE INDEX "idx_notification_user_updated" ON "NotificationEntry" ("user_id", "updated");
CREATE INDEX "idx_company_supplier" ON "Company" ("is_supplier", "name");
CREATE INDEX "idx_company_customer" ON "Company" ("is_customer", "name");
CREATE INDEX "idx_contact_company" ON "Contact" ("company_id");
CREATE INDEX "idx_supplierpart_supplier" ON "SupplierPart" ("supplier_id");
CREATE INDEX "idx_supplierpart_part" ON "SupplierPart" ("part_id");
CREATE INDEX "idx_pricebreak_supplierpart" ON "SupplierPriceBreak" ("part_id", "quantity");
CREATE INDEX "idx_part_active_name" ON "Part" ("active", "name");
CREATE INDEX "idx_part_category" ON "Part" ("category_id");
CREATE INDEX "idx_partattachment_part" ON "PartAttachment" ("part_id");
CREATE INDEX "idx_bomitem_part" ON "BomItem" ("part_id");
CREATE INDEX "idx_bomitem_subpart" ON "BomItem" ("sub_part_id");
CREATE INDEX "idx_partstar_user" ON "PartStar" ("user_id", "part_id");
CREATE INDEX "idx_purchaseorder_supplier_status" ON "PurchaseOrder" ("supplier_id", "status");
CREATE INDEX "idx_purchaseorder_created_by" ON "PurchaseOrder" ("created_by_id");
CREATE INDEX "idx_poline_order" ON "PurchaseOrderLineItem" ("order_id");
CREATE INDEX "idx_poline_supplierpart" ON "PurchaseOrderLineItem" ("supplier_part_id");
CREATE INDEX "idx_stockitem_location" ON "StockItem" ("location_id");
CREATE INDEX "idx_stockitem_part" ON "StockItem" ("part_id");
CREATE INDEX "idx_stockitem_supplierpart" ON "StockItem" ("supplier_part_id");
CREATE INDEX "idx_stocklocation_parent" ON "StockLocation" ("parent_id");
CREATE INDEX "idx_stocktracking_item_date" ON "StockItemTracking" ("item_id", "date");
CREATE INDEX "idx_reportasset_template" ON "ReportAsset" ("template_id");
CREATE INDEX "idx_pluginconfig_plugin" ON "PluginConfig" ("plugin_id");
CREATE INDEX "idx_machine_plugin" ON "Machine" ("plugin_id");
CREATE INDEX "idx_machineconfig_machine" ON "MachineConfig" ("machine_id");
CREATE INDEX "idx_machinesetting_config" ON "MachineSetting" ("machine_config_id");
CREATE INDEX "idx_importsession_user_status" ON "DataImportSession" ("user_id", "status");
CREATE INDEX "idx_importrow_session_valid" ON "DataImportRow" ("session_id", "valid");
CREATE INDEX "idx_importcolumn_session" ON "DataImportColumnMap" ("session_id");

ALTER TABLE "ApiToken" ADD CONSTRAINT "fk_apitoken_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "UserProfile" ADD CONSTRAINT "fk_userprofile_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "Machine" ADD CONSTRAINT "fk_machine_plugin" FOREIGN KEY ("plugin_id") REFERENCES "Plugin" ("id");
ALTER TABLE "Build" ADD CONSTRAINT "fk_build_part" FOREIGN KEY ("part_id") REFERENCES "Part" ("id");
ALTER TABLE "Build" ADD CONSTRAINT "fk_build_parent" FOREIGN KEY ("parent_id") REFERENCES "Build" ("id");
ALTER TABLE "Build" ADD CONSTRAINT "fk_build_responsible" FOREIGN KEY ("responsible_id") REFERENCES "User" ("id");
ALTER TABLE "BuildItem" ADD CONSTRAINT "fk_builditem_stock" FOREIGN KEY ("stock_item_id") REFERENCES "StockItem" ("id");
ALTER TABLE "BuildItem" ADD CONSTRAINT "fk_builditem_install_into" FOREIGN KEY ("install_into_id") REFERENCES "StockItem" ("id");
ALTER TABLE "BuildItem" ADD CONSTRAINT "fk_builditem_line" FOREIGN KEY ("build_line_id") REFERENCES "BuildLine" ("id");
ALTER TABLE "BuildLine" ADD CONSTRAINT "fk_buildline_bom" FOREIGN KEY ("bom_item_id") REFERENCES "BomItem" ("id");
ALTER TABLE "BuildLine" ADD CONSTRAINT "fk_buildline_build" FOREIGN KEY ("build_id") REFERENCES "Build" ("id");
ALTER TABLE "InvenTreeUserSetting" ADD CONSTRAINT "fk_usersetting_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "ColorTheme" ADD CONSTRAINT "fk_colortheme_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "NotificationEntry" ADD CONSTRAINT "fk_notification_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "Contact" ADD CONSTRAINT "fk_contact_company" FOREIGN KEY ("company_id") REFERENCES "Company" ("id");
ALTER TABLE "SupplierPart" ADD CONSTRAINT "fk_supplierpart_supplier" FOREIGN KEY ("supplier_id") REFERENCES "Company" ("id");
ALTER TABLE "SupplierPart" ADD CONSTRAINT "fk_supplierpart_part" FOREIGN KEY ("part_id") REFERENCES "Part" ("id");
ALTER TABLE "SupplierPriceBreak" ADD CONSTRAINT "fk_pricebreak_supplierpart" FOREIGN KEY ("part_id") REFERENCES "SupplierPart" ("id");
ALTER TABLE "Part" ADD CONSTRAINT "fk_part_category" FOREIGN KEY ("category_id") REFERENCES "PartCategory" ("id");
ALTER TABLE "PartAttachment" ADD CONSTRAINT "fk_partattachment_part" FOREIGN KEY ("part_id") REFERENCES "Part" ("id");
ALTER TABLE "BomItem" ADD CONSTRAINT "fk_bomitem_part" FOREIGN KEY ("part_id") REFERENCES "Part" ("id");
ALTER TABLE "BomItem" ADD CONSTRAINT "fk_bomitem_subpart" FOREIGN KEY ("sub_part_id") REFERENCES "Part" ("id");
ALTER TABLE "PartStar" ADD CONSTRAINT "fk_partstar_part" FOREIGN KEY ("part_id") REFERENCES "Part" ("id");
ALTER TABLE "PartStar" ADD CONSTRAINT "fk_partstar_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "PurchaseOrder" ADD CONSTRAINT "fk_purchaseorder_creator" FOREIGN KEY ("created_by_id") REFERENCES "User" ("id");
ALTER TABLE "PurchaseOrder" ADD CONSTRAINT "fk_purchaseorder_supplier" FOREIGN KEY ("supplier_id") REFERENCES "Company" ("id");
ALTER TABLE "PurchaseOrderLineItem" ADD CONSTRAINT "fk_poline_order" FOREIGN KEY ("order_id") REFERENCES "PurchaseOrder" ("id");
ALTER TABLE "PurchaseOrderLineItem" ADD CONSTRAINT "fk_poline_supplierpart" FOREIGN KEY ("supplier_part_id") REFERENCES "SupplierPart" ("id");
ALTER TABLE "StockItem" ADD CONSTRAINT "fk_stockitem_parent" FOREIGN KEY ("belongs_to_id") REFERENCES "StockItem" ("id");
ALTER TABLE "StockItem" ADD CONSTRAINT "fk_stockitem_location" FOREIGN KEY ("location_id") REFERENCES "StockLocation" ("id");
ALTER TABLE "StockItem" ADD CONSTRAINT "fk_stockitem_part" FOREIGN KEY ("part_id") REFERENCES "Part" ("id");
ALTER TABLE "StockItem" ADD CONSTRAINT "fk_stockitem_supplierpart" FOREIGN KEY ("supplier_part_id") REFERENCES "SupplierPart" ("id");
ALTER TABLE "StockLocation" ADD CONSTRAINT "fk_stocklocation_parent" FOREIGN KEY ("parent_id") REFERENCES "StockLocation" ("id");
ALTER TABLE "StockItemTracking" ADD CONSTRAINT "fk_stocktracking_item" FOREIGN KEY ("item_id") REFERENCES "StockItem" ("id");
ALTER TABLE "StockItemTracking" ADD CONSTRAINT "fk_stocktracking_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "ReportAsset" ADD CONSTRAINT "fk_reportasset_template" FOREIGN KEY ("template_id") REFERENCES "ReportTemplate" ("id");
ALTER TABLE "PluginConfig" ADD CONSTRAINT "fk_pluginconfig_plugin" FOREIGN KEY ("plugin_id") REFERENCES "Plugin" ("id");
ALTER TABLE "MachineConfig" ADD CONSTRAINT "fk_machineconfig_machine" FOREIGN KEY ("machine_id") REFERENCES "Machine" ("id");
ALTER TABLE "MachineSetting" ADD CONSTRAINT "fk_machinesetting_config" FOREIGN KEY ("machine_config_id") REFERENCES "MachineConfig" ("id");
ALTER TABLE "DataImportSession" ADD CONSTRAINT "fk_importsession_user" FOREIGN KEY ("user_id") REFERENCES "User" ("id");
ALTER TABLE "DataImportRow" ADD CONSTRAINT "fk_importrow_session" FOREIGN KEY ("session_id") REFERENCES "DataImportSession" ("id");
ALTER TABLE "DataImportColumnMap" ADD CONSTRAINT "fk_importcolumn_session" FOREIGN KEY ("session_id") REFERENCES "DataImportSession" ("id");
