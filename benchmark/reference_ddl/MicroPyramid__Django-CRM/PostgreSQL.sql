CREATE TABLE "board" (
  "id" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_archived" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "created_by_id" UUID,
  "org_id" UUID NOT NULL,
  "owner_id" UUID NOT NULL,
  "updated_by_id" UUID,
  PRIMARY KEY ("id")
);

CREATE TABLE "board_column" (
  "id" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "order" INTEGER NOT NULL,
  "color" VARCHAR(255) NOT NULL,
  "limit" INTEGER,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "board_id" UUID NOT NULL,
  "created_by_id" UUID,
  "org_id" UUID NOT NULL,
  "updated_by_id" UUID,
  PRIMARY KEY ("id"),
  UNIQUE ("board_id", "name")
);

CREATE TABLE "board_member" (
  "id" UUID NOT NULL,
  "role" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "board_id" UUID NOT NULL,
  "created_by_id" UUID,
  "org_id" UUID NOT NULL,
  "profile_id" UUID NOT NULL,
  "updated_by_id" UUID,
  PRIMARY KEY ("id"),
  UNIQUE ("board_id", "profile_id")
);

CREATE TABLE "board_task" (
  "id" UUID NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "order" INTEGER NOT NULL,
  "priority" VARCHAR(255) NOT NULL,
  "due_date" TIMESTAMP,
  "completed_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "account_id" UUID,
  "column_id" UUID NOT NULL,
  "contact_id" UUID,
  "created_by_id" UUID,
  "opportunity_id" UUID,
  "org_id" UUID NOT NULL,
  "updated_by_id" UUID,
  PRIMARY KEY ("id")
);

CREATE TABLE "task" (
  "id" UUID NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "priority" VARCHAR(255) NOT NULL,
  "due_date" DATE,
  "description" TEXT,
  "kanban_order" DECIMAL(18, 2) NOT NULL,
  "custom_fields" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "account_id" UUID,
  "case_id" UUID,
  "created_by_id" UUID,
  "lead_id" UUID,
  "opportunity_id" UUID,
  "org_id" UUID NOT NULL,
  "stage_id" UUID,
  "updated_by_id" UUID,
  PRIMARY KEY ("id")
);

CREATE TABLE "task_pipeline" (
  "id" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "is_default" BOOLEAN NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "created_by_id" UUID,
  "org_id" UUID NOT NULL,
  "updated_by_id" UUID,
  PRIMARY KEY ("id")
);

CREATE TABLE "task_stage" (
  "id" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "order" INTEGER NOT NULL,
  "color" VARCHAR(255) NOT NULL,
  "stage_type" VARCHAR(255) NOT NULL,
  "maps_to_status" VARCHAR(255),
  "wip_limit" INTEGER,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "created_by_id" UUID,
  "org_id" UUID NOT NULL,
  "pipeline_id" UUID NOT NULL,
  "updated_by_id" UUID,
  PRIMARY KEY ("id"),
  UNIQUE ("pipeline_id", "name")
);

CREATE INDEX "idx_board_org_id_created_at_1" ON "board" ("org_id", "created_at");

CREATE INDEX "idx_board_column_org_id_order_1" ON "board_column" ("org_id", "order");

CREATE INDEX "idx_board_member_org_id_created_at_1" ON "board_member" ("org_id", "created_at");

CREATE INDEX "idx_board_task_org_id_order_1" ON "board_task" ("org_id", "order");

CREATE INDEX "idx_task_status_1" ON "task" ("status");

CREATE INDEX "idx_task_due_date_2" ON "task" ("due_date");

CREATE INDEX "idx_task_org_id_created_at_3" ON "task" ("org_id", "created_at");

CREATE INDEX "idx_task_status_kanban_order_4" ON "task" ("status", "kanban_order");

CREATE INDEX "idx_task_stage_id_kanban_order_5" ON "task" ("stage_id", "kanban_order");

CREATE INDEX "idx_task_pipeline_org_id_created_at_1" ON "task_pipeline" ("org_id", "created_at");

CREATE INDEX "idx_task_stage_org_id_order_1" ON "task_stage" ("org_id", "order");

CREATE INDEX "idx_task_stage_pipeline_id_order_2" ON "task_stage" ("pipeline_id", "order");

ALTER TABLE "board_column" ADD CONSTRAINT "fk_board_column_board_id_1" FOREIGN KEY ("board_id") REFERENCES "board" ("id");

ALTER TABLE "board_member" ADD CONSTRAINT "fk_board_member_board_id_1" FOREIGN KEY ("board_id") REFERENCES "board" ("id");

ALTER TABLE "board_task" ADD CONSTRAINT "fk_board_task_column_id_1" FOREIGN KEY ("column_id") REFERENCES "board_column" ("id");

ALTER TABLE "task" ADD CONSTRAINT "fk_task_stage_id_1" FOREIGN KEY ("stage_id") REFERENCES "task_stage" ("id");

ALTER TABLE "task_stage" ADD CONSTRAINT "fk_task_stage_pipeline_id_1" FOREIGN KEY ("pipeline_id") REFERENCES "task_pipeline" ("id");
