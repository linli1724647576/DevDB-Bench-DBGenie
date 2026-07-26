CREATE TABLE [tenants] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [code] NVARCHAR(64) NOT NULL UNIQUE,
  [name] NVARCHAR(200) NOT NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE [users] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [username] NVARCHAR(100) NOT NULL,
  [display_name] NVARCHAR(200) NULL,
  [email] NVARCHAR(320) NULL,
  [password_hash] NVARCHAR(500) NOT NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_users_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_users_tenant_username] UNIQUE ([tenant_id], [username])
);

CREATE TABLE [roles] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(150) NOT NULL,
  [description] NVARCHAR(500) NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_roles_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_roles_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [permissions] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(100) NOT NULL,
  [name] NVARCHAR(150) NOT NULL,
  [menu_path] NVARCHAR(500) NULL,
  [parent_permission_id] BIGINT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_permissions_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_permissions_parent] FOREIGN KEY ([parent_permission_id]) REFERENCES [permissions]([id]),
  CONSTRAINT [UQ_permissions_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [user_role_assignments] (
  [user_id] BIGINT NOT NULL,
  [role_id] BIGINT NOT NULL,
  [assigned_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_user_role_assignments] PRIMARY KEY ([user_id], [role_id]),
  CONSTRAINT [FK_user_roles_user] FOREIGN KEY ([user_id]) REFERENCES [users]([id]),
  CONSTRAINT [FK_user_roles_role] FOREIGN KEY ([role_id]) REFERENCES [roles]([id])
);

CREATE TABLE [role_permission_assignments] (
  [role_id] BIGINT NOT NULL,
  [permission_id] BIGINT NOT NULL,
  [assigned_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_role_permission_assignments] PRIMARY KEY ([role_id], [permission_id]),
  CONSTRAINT [FK_role_permissions_role] FOREIGN KEY ([role_id]) REFERENCES [roles]([id]),
  CONSTRAINT [FK_role_permissions_permission] FOREIGN KEY ([permission_id]) REFERENCES [permissions]([id])
);

CREATE TABLE [warehouses] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [address] NVARCHAR(500) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_warehouses_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_warehouses_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [storage_areas] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [warehouse_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [area_type] NVARCHAR(50) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_storage_areas_warehouses] FOREIGN KEY ([warehouse_id]) REFERENCES [warehouses]([id]),
  CONSTRAINT [UQ_storage_areas_warehouse_code] UNIQUE ([warehouse_id], [code])
);

CREATE TABLE [goods_locations] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [storage_area_id] BIGINT NOT NULL,
  [code] NVARCHAR(100) NOT NULL,
  [name] NVARCHAR(200) NULL,
  [location_type] NVARCHAR(50) NULL,
  [capacity] DECIMAL(18,4) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_goods_locations_areas] FOREIGN KEY ([storage_area_id]) REFERENCES [storage_areas]([id]),
  CONSTRAINT [UQ_goods_locations_area_code] UNIQUE ([storage_area_id], [code])
);

CREATE TABLE [suppliers] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [contact_name] NVARCHAR(150) NULL,
  [phone] NVARCHAR(50) NULL,
  [address] NVARCHAR(500) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_suppliers_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_suppliers_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [customers] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [contact_name] NVARCHAR(150) NULL,
  [phone] NVARCHAR(50) NULL,
  [address] NVARCHAR(500) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_customers_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_customers_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [goods_owners] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [contact_info] NVARCHAR(500) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_goods_owners_tenants] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_goods_owners_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [product_categories] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [parent_category_id] BIGINT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [description] NVARCHAR(500) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_product_categories_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_product_categories_parent] FOREIGN KEY ([parent_category_id]) REFERENCES [product_categories]([id]),
  CONSTRAINT [UQ_product_categories_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [product_models] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [category_id] BIGINT NOT NULL,
  [code] NVARCHAR(100) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [description] NVARCHAR(1000) NULL,
  [specification_json] NVARCHAR(MAX) NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_product_models_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_product_models_category] FOREIGN KEY ([category_id]) REFERENCES [product_categories]([id]),
  CONSTRAINT [UQ_product_models_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [sku_variants] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [product_model_id] BIGINT NOT NULL,
  [sku_code] NVARCHAR(100) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [barcode] NVARCHAR(100) NULL,
  [unit_of_measure] NVARCHAR(30) NULL,
  [attributes_json] NVARCHAR(MAX) NULL,
  [tracking_requires_serial] BIT NOT NULL DEFAULT 0,
  [tracking_requires_expiry] BIT NOT NULL DEFAULT 0,
  [default_unit_price] DECIMAL(18,4) NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_skus_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_skus_model] FOREIGN KEY ([product_model_id]) REFERENCES [product_models]([id]),
  CONSTRAINT [UQ_skus_tenant_code] UNIQUE ([tenant_id], [sku_code])
);

CREATE TABLE [stock_records] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [warehouse_id] BIGINT NOT NULL,
  [goods_location_id] BIGINT NOT NULL,
  [goods_owner_id] BIGINT NOT NULL,
  [sku_id] BIGINT NOT NULL,
  [serial_number] NVARCHAR(150) NULL,
  [expiry_date] DATE NULL,
  [unit_price] DECIMAL(18,4) NULL,
  [quantity_on_hand] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [quantity_reserved] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [put_away_at] DATETIME2 NULL,
  [freeze_state] NVARCHAR(30) NOT NULL DEFAULT 'available',
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_stock_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_stock_warehouse] FOREIGN KEY ([warehouse_id]) REFERENCES [warehouses]([id]),
  CONSTRAINT [FK_stock_location] FOREIGN KEY ([goods_location_id]) REFERENCES [goods_locations]([id]),
  CONSTRAINT [FK_stock_owner] FOREIGN KEY ([goods_owner_id]) REFERENCES [goods_owners]([id]),
  CONSTRAINT [FK_stock_sku] FOREIGN KEY ([sku_id]) REFERENCES [sku_variants]([id]),
  CONSTRAINT [CK_stock_quantities] CHECK ([quantity_on_hand] >= 0 AND [quantity_reserved] >= 0)
);

CREATE TABLE [advance_shipping_notices] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [document_number] NVARCHAR(100) NOT NULL,
  [supplier_id] BIGINT NOT NULL,
  [goods_owner_id] BIGINT NOT NULL,
  [warehouse_id] BIGINT NOT NULL,
  [expected_arrival_at] DATETIME2 NULL,
  [status] NVARCHAR(40) NOT NULL,
  [created_by_user_id] BIGINT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_asn_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_asn_supplier] FOREIGN KEY ([supplier_id]) REFERENCES [suppliers]([id]),
  CONSTRAINT [FK_asn_owner] FOREIGN KEY ([goods_owner_id]) REFERENCES [goods_owners]([id]),
  CONSTRAINT [FK_asn_warehouse] FOREIGN KEY ([warehouse_id]) REFERENCES [warehouses]([id]),
  CONSTRAINT [FK_asn_creator] FOREIGN KEY ([created_by_user_id]) REFERENCES [users]([id]),
  CONSTRAINT [UQ_asn_tenant_number] UNIQUE ([tenant_id], [document_number])
);

CREATE TABLE [inbound_receiving_lines] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [advance_shipping_notice_id] BIGINT NOT NULL,
  [line_number] INT NOT NULL,
  [sku_id] BIGINT NOT NULL,
  [expected_quantity] DECIMAL(18,4) NOT NULL,
  [received_quantity] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [sorting_quantity] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [put_away_quantity] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [serial_number] NVARCHAR(150) NULL,
  [expiry_date] DATE NULL,
  CONSTRAINT [FK_inbound_lines_asn] FOREIGN KEY ([advance_shipping_notice_id]) REFERENCES [advance_shipping_notices]([id]),
  CONSTRAINT [FK_inbound_lines_sku] FOREIGN KEY ([sku_id]) REFERENCES [sku_variants]([id]),
  CONSTRAINT [UQ_inbound_lines_number] UNIQUE ([advance_shipping_notice_id], [line_number])
);

CREATE TABLE [outbound_deliveries] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [document_number] NVARCHAR(100) NOT NULL,
  [customer_id] BIGINT NOT NULL,
  [warehouse_id] BIGINT NOT NULL,
  [requested_at] DATETIME2 NULL,
  [dispatch_at] DATETIME2 NULL,
  [status] NVARCHAR(40) NOT NULL,
  [created_by_user_id] BIGINT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_outbound_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_outbound_customer] FOREIGN KEY ([customer_id]) REFERENCES [customers]([id]),
  CONSTRAINT [FK_outbound_warehouse] FOREIGN KEY ([warehouse_id]) REFERENCES [warehouses]([id]),
  CONSTRAINT [FK_outbound_creator] FOREIGN KEY ([created_by_user_id]) REFERENCES [users]([id]),
  CONSTRAINT [UQ_outbound_tenant_number] UNIQUE ([tenant_id], [document_number])
);

CREATE TABLE [outbound_delivery_lines] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [outbound_delivery_id] BIGINT NOT NULL,
  [line_number] INT NOT NULL,
  [sku_id] BIGINT NOT NULL,
  [requested_quantity] DECIMAL(18,4) NOT NULL,
  [picked_quantity] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [fulfilled_quantity] DECIMAL(18,4) NOT NULL DEFAULT 0,
  [unit_price] DECIMAL(18,4) NULL,
  CONSTRAINT [FK_outbound_lines_delivery] FOREIGN KEY ([outbound_delivery_id]) REFERENCES [outbound_deliveries]([id]),
  CONSTRAINT [FK_outbound_lines_sku] FOREIGN KEY ([sku_id]) REFERENCES [sku_variants]([id]),
  CONSTRAINT [UQ_outbound_lines_number] UNIQUE ([outbound_delivery_id], [line_number])
);

CREATE TABLE [inventory_operations] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [operation_type] NVARCHAR(40) NOT NULL,
  [stock_record_id] BIGINT NULL,
  [sku_id] BIGINT NOT NULL,
  [goods_owner_id] BIGINT NULL,
  [source_location_id] BIGINT NULL,
  [destination_location_id] BIGINT NULL,
  [handled_by_user_id] BIGINT NULL,
  [quantity] DECIMAL(18,4) NOT NULL,
  [job_identifier] NVARCHAR(100) NULL,
  [status] NVARCHAR(40) NOT NULL,
  [reason] NVARCHAR(500) NULL,
  [occurred_at] DATETIME2 NOT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_inventory_operations_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_inventory_operations_stock] FOREIGN KEY ([stock_record_id]) REFERENCES [stock_records]([id]),
  CONSTRAINT [FK_inventory_operations_sku] FOREIGN KEY ([sku_id]) REFERENCES [sku_variants]([id]),
  CONSTRAINT [FK_inventory_operations_owner] FOREIGN KEY ([goods_owner_id]) REFERENCES [goods_owners]([id]),
  CONSTRAINT [FK_inventory_operations_source] FOREIGN KEY ([source_location_id]) REFERENCES [goods_locations]([id]),
  CONSTRAINT [FK_inventory_operations_destination] FOREIGN KEY ([destination_location_id]) REFERENCES [goods_locations]([id]),
  CONSTRAINT [FK_inventory_operations_handler] FOREIGN KEY ([handled_by_user_id]) REFERENCES [users]([id])
);

CREATE TABLE [approval_flows] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [document_type] NVARCHAR(100) NOT NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_approval_flows_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_approval_flows_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [approval_steps] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [approval_flow_id] BIGINT NOT NULL,
  [step_number] INT NOT NULL,
  [name] NVARCHAR(150) NOT NULL,
  [approver_role_id] BIGINT NOT NULL,
  [is_required] BIT NOT NULL DEFAULT 1,
  CONSTRAINT [FK_approval_steps_flow] FOREIGN KEY ([approval_flow_id]) REFERENCES [approval_flows]([id]),
  CONSTRAINT [FK_approval_steps_role] FOREIGN KEY ([approver_role_id]) REFERENCES [roles]([id]),
  CONSTRAINT [UQ_approval_steps_number] UNIQUE ([approval_flow_id], [step_number])
);

CREATE TABLE [document_number_rules] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [document_type] NVARCHAR(100) NOT NULL,
  [prefix] NVARCHAR(30) NULL,
  [date_format] NVARCHAR(30) NULL,
  [sequence_length] INT NOT NULL DEFAULT 6,
  [next_sequence_value] BIGINT NOT NULL DEFAULT 1,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_number_rules_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_number_rules_tenant_type] UNIQUE ([tenant_id], [document_type])
);

CREATE TABLE [document_approvals] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [approval_flow_id] BIGINT NOT NULL,
  [document_type] NVARCHAR(100) NOT NULL,
  [document_id] BIGINT NOT NULL,
  [current_step_number] INT NULL,
  [status] NVARCHAR(40) NOT NULL,
  [started_at] DATETIME2 NOT NULL,
  [completed_at] DATETIME2 NULL,
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_document_approvals_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_document_approvals_flow] FOREIGN KEY ([approval_flow_id]) REFERENCES [approval_flows]([id])
);

CREATE TABLE [freight_rates] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [carrier_name] NVARCHAR(200) NOT NULL,
  [route_origin] NVARCHAR(200) NOT NULL,
  [route_destination] NVARCHAR(200) NOT NULL,
  [rate_amount] DECIMAL(18,4) NOT NULL,
  [currency_code] CHAR(3) NOT NULL,
  [valid_from] DATE NOT NULL,
  [valid_to] DATE NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_freight_rates_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id])
);

CREATE TABLE [print_layouts] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [code] NVARCHAR(64) NOT NULL,
  [name] NVARCHAR(200) NOT NULL,
  [document_type] NVARCHAR(100) NOT NULL,
  [template_content] NVARCHAR(MAX) NOT NULL,
  [is_active] BIT NOT NULL DEFAULT 1,
  [created_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  [updated_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_print_layouts_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [UQ_print_layouts_tenant_code] UNIQUE ([tenant_id], [code])
);

CREATE TABLE [user_action_logs] (
  [id] BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  [tenant_id] BIGINT NOT NULL,
  [user_id] BIGINT NULL,
  [action_type] NVARCHAR(100) NOT NULL,
  [target_entity_type] NVARCHAR(100) NULL,
  [target_entity_id] BIGINT NULL,
  [description] NVARCHAR(MAX) NULL,
  [ip_address] NVARCHAR(64) NULL,
  [logged_at] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [FK_action_logs_tenant] FOREIGN KEY ([tenant_id]) REFERENCES [tenants]([id]),
  CONSTRAINT [FK_action_logs_user] FOREIGN KEY ([user_id]) REFERENCES [users]([id])
);

CREATE INDEX [IX_users_tenant_email] ON [users]([tenant_id], [email]);
CREATE INDEX [IX_warehouses_tenant_name] ON [warehouses]([tenant_id], [name]);
CREATE INDEX [IX_locations_area_code] ON [goods_locations]([storage_area_id], [code]);
CREATE INDEX [IX_suppliers_tenant_name] ON [suppliers]([tenant_id], [name]);
CREATE INDEX [IX_customers_tenant_name] ON [customers]([tenant_id], [name]);
CREATE INDEX [IX_goods_owners_tenant_name] ON [goods_owners]([tenant_id], [name]);
CREATE INDEX [IX_product_models_category_name] ON [product_models]([category_id], [name]);
CREATE INDEX [IX_skus_tenant_name] ON [sku_variants]([tenant_id], [name]);
CREATE INDEX [IX_stock_lookup] ON [stock_records]([tenant_id], [warehouse_id], [goods_location_id], [sku_id]);
CREATE INDEX [IX_stock_owner_age] ON [stock_records]([goods_owner_id], [put_away_at], [expiry_date]);
CREATE INDEX [IX_stock_serial_expiry] ON [stock_records]([serial_number], [expiry_date]);
CREATE INDEX [IX_asn_supplier_owner] ON [advance_shipping_notices]([tenant_id], [supplier_id], [goods_owner_id], [created_at]);
CREATE INDEX [IX_inbound_lines_sku] ON [inbound_receiving_lines]([sku_id], [advance_shipping_notice_id]);
CREATE INDEX [IX_outbound_customer_date] ON [outbound_deliveries]([tenant_id], [customer_id], [warehouse_id], [dispatch_at]);
CREATE INDEX [IX_outbound_lines_sku] ON [outbound_delivery_lines]([sku_id], [outbound_delivery_id]);
CREATE INDEX [IX_inventory_operations_job] ON [inventory_operations]([tenant_id], [job_identifier]);
CREATE INDEX [IX_inventory_operations_time] ON [inventory_operations]([tenant_id], [operation_type], [occurred_at]);
CREATE INDEX [IX_document_approvals_document] ON [document_approvals]([tenant_id], [document_type], [document_id]);
CREATE INDEX [IX_freight_rates_route] ON [freight_rates]([tenant_id], [carrier_name], [route_origin], [route_destination]);
CREATE INDEX [IX_action_logs_target] ON [user_action_logs]([tenant_id], [target_entity_type], [target_entity_id], [logged_at]);
