CREATE TABLE "event_execution" (
  "event_handler_name" TEXT NOT NULL,
  "event_name" TEXT NOT NULL,
  "execution_id" TEXT NOT NULL,
  "message_id" TEXT NOT NULL,
  "json_data" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("event_handler_name", "event_name", "execution_id")
);

CREATE TABLE "locks" (
  "lock_id" TEXT NOT NULL,
  "lease_expiration" TIMESTAMP NOT NULL,
  PRIMARY KEY ("lock_id")
);

CREATE TABLE "meta_event_handler" (
  "id" INTEGER NOT NULL,
  "name" TEXT NOT NULL,
  "event" TEXT NOT NULL,
  "active" INTEGER NOT NULL,
  "json_data" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("id")
);

CREATE TABLE "meta_task_def" (
  "name" TEXT NOT NULL,
  "json_data" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("name")
);

CREATE TABLE "meta_workflow_def" (
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  "name" TEXT NOT NULL,
  "version" INTEGER NOT NULL,
  "latest_version" INTEGER NOT NULL,
  "json_data" TEXT NOT NULL,
  PRIMARY KEY ("name", "version")
);

CREATE TABLE "poll_data" (
  "queue_name" TEXT NOT NULL,
  "domain" TEXT NOT NULL,
  "json_data" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("queue_name", "domain")
);

CREATE TABLE "queue" (
  "queue_name" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  PRIMARY KEY ("queue_name")
);

CREATE TABLE "queue_message" (
  "queue_name" TEXT NOT NULL,
  "message_id" TEXT NOT NULL,
  "deliver_on" TIMESTAMP,
  "priority" INTEGER,
  "popped" INTEGER,
  "offset_time_seconds" INTEGER,
  "payload" TEXT,
  "created_on" TIMESTAMP NOT NULL,
  PRIMARY KEY ("queue_name", "message_id")
);

CREATE TABLE "task" (
  "task_id" TEXT NOT NULL,
  "json_data" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("task_id")
);

CREATE TABLE "task_execution_logs" (
  "log_id" INTEGER NOT NULL,
  "task_id" TEXT NOT NULL,
  "log" TEXT NOT NULL,
  "created_time" TIMESTAMP NOT NULL,
  PRIMARY KEY ("log_id")
);

CREATE TABLE "task_in_progress" (
  "task_def_name" TEXT NOT NULL,
  "task_id" TEXT NOT NULL,
  "workflow_id" TEXT NOT NULL,
  "in_progress_status" INTEGER NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("task_def_name", "task_id")
);

CREATE TABLE "task_index" (
  "task_id" TEXT NOT NULL,
  "task_type" TEXT NOT NULL,
  "task_def_name" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "start_time" TIMESTAMP NOT NULL,
  "update_time" TIMESTAMP NOT NULL,
  "workflow_type" TEXT NOT NULL,
  "json_data" TEXT NOT NULL,
  PRIMARY KEY ("task_id")
);

CREATE TABLE "task_scheduled" (
  "workflow_id" TEXT NOT NULL,
  "task_key" TEXT NOT NULL,
  "task_id" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("workflow_id", "task_key")
);

CREATE TABLE "workflow" (
  "workflow_id" TEXT NOT NULL,
  "correlation_id" TEXT,
  "json_data" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("workflow_id")
);

CREATE TABLE "workflow_def_to_workflow" (
  "workflow_def" TEXT NOT NULL,
  "date_str" TEXT NOT NULL,
  "workflow_id" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("workflow_def", "date_str", "workflow_id")
);

CREATE TABLE "workflow_index" (
  "workflow_id" TEXT NOT NULL,
  "correlation_id" TEXT,
  "workflow_type" TEXT NOT NULL,
  "start_time" TIMESTAMP NOT NULL,
  "status" TEXT NOT NULL,
  "json_data" TEXT NOT NULL,
  "update_time" TIMESTAMP NOT NULL,
  PRIMARY KEY ("workflow_id")
);

CREATE TABLE "workflow_pending" (
  "workflow_type" TEXT NOT NULL,
  "workflow_id" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("workflow_type", "workflow_id")
);

CREATE TABLE "workflow_to_task" (
  "workflow_id" TEXT NOT NULL,
  "task_id" TEXT NOT NULL,
  "created_on" TIMESTAMP,
  "modified_on" TIMESTAMP,
  PRIMARY KEY ("workflow_id", "task_id")
);

CREATE INDEX "idx_meta_event_handler_name_1" ON "meta_event_handler" ("name");

CREATE INDEX "idx_meta_event_handler_event_2" ON "meta_event_handler" ("event");

CREATE INDEX "idx_meta_workflow_def_name_1" ON "meta_workflow_def" ("name");

CREATE INDEX "idx_poll_data_queue_name_1" ON "poll_data" ("queue_name");

CREATE INDEX "idx_queue_message_queue_name_priority_popped_delive_b79521dd" ON "queue_message" ("queue_name", "priority", "popped", "deliver_on", "created_on");

CREATE INDEX "idx_task_execution_logs_task_id_1" ON "task_execution_logs" ("task_id");

CREATE INDEX "idx_task_index_status_1" ON "task_index" ("status");

CREATE INDEX "idx_task_index_task_def_name_2" ON "task_index" ("task_def_name");

CREATE INDEX "idx_task_index_task_id_3" ON "task_index" ("task_id");

CREATE INDEX "idx_task_index_task_type_4" ON "task_index" ("task_type");

CREATE INDEX "idx_task_index_update_time_5" ON "task_index" ("update_time");

CREATE INDEX "idx_task_index_workflow_type_6" ON "task_index" ("workflow_type");

CREATE INDEX "idx_workflow_correlation_id_1" ON "workflow" ("correlation_id");

CREATE INDEX "idx_workflow_index_correlation_id_1" ON "workflow_index" ("correlation_id");

CREATE INDEX "idx_workflow_index_start_time_2" ON "workflow_index" ("start_time");

CREATE INDEX "idx_workflow_index_status_3" ON "workflow_index" ("status");

CREATE INDEX "idx_workflow_index_workflow_type_4" ON "workflow_index" ("workflow_type");

CREATE INDEX "idx_workflow_pending_workflow_type_1" ON "workflow_pending" ("workflow_type");

CREATE INDEX "idx_workflow_to_task_workflow_id_1" ON "workflow_to_task" ("workflow_id");

ALTER TABLE "task_execution_logs"
  ADD CONSTRAINT "fk_task_execution_logs_task"
  FOREIGN KEY ("task_id") REFERENCES "task" ("task_id");

ALTER TABLE "task_in_progress"
  ADD CONSTRAINT "fk_task_in_progress_task_def"
  FOREIGN KEY ("task_def_name") REFERENCES "meta_task_def" ("name");

ALTER TABLE "task_in_progress"
  ADD CONSTRAINT "fk_task_in_progress_task"
  FOREIGN KEY ("task_id") REFERENCES "task" ("task_id");

ALTER TABLE "task_in_progress"
  ADD CONSTRAINT "fk_task_in_progress_workflow"
  FOREIGN KEY ("workflow_id") REFERENCES "workflow" ("workflow_id");

ALTER TABLE "task_scheduled"
  ADD CONSTRAINT "fk_task_scheduled_workflow"
  FOREIGN KEY ("workflow_id") REFERENCES "workflow" ("workflow_id");

ALTER TABLE "task_scheduled"
  ADD CONSTRAINT "fk_task_scheduled_task"
  FOREIGN KEY ("task_id") REFERENCES "task" ("task_id");

ALTER TABLE "task_index"
  ADD CONSTRAINT "fk_task_index_task"
  FOREIGN KEY ("task_id") REFERENCES "task" ("task_id");

ALTER TABLE "workflow_def_to_workflow"
  ADD CONSTRAINT "fk_workflow_def_to_workflow_workflow"
  FOREIGN KEY ("workflow_id") REFERENCES "workflow" ("workflow_id");

ALTER TABLE "workflow_pending"
  ADD CONSTRAINT "fk_workflow_pending_workflow"
  FOREIGN KEY ("workflow_id") REFERENCES "workflow" ("workflow_id");

ALTER TABLE "workflow_to_task"
  ADD CONSTRAINT "fk_workflow_to_task_workflow"
  FOREIGN KEY ("workflow_id") REFERENCES "workflow" ("workflow_id");

ALTER TABLE "workflow_to_task"
  ADD CONSTRAINT "fk_workflow_to_task_task"
  FOREIGN KEY ("task_id") REFERENCES "task" ("task_id");

ALTER TABLE "workflow_index"
  ADD CONSTRAINT "fk_workflow_index_workflow"
  FOREIGN KEY ("workflow_id") REFERENCES "workflow" ("workflow_id");

ALTER TABLE "event_execution"
  ADD CONSTRAINT "fk_event_execution_workflow"
  FOREIGN KEY ("execution_id") REFERENCES "workflow" ("workflow_id");
