CREATE TABLE "chunk" (
  "id" BIGSERIAL NOT NULL,
  "contents" TEXT NOT NULL,
  "embedding" REAL[],
  "embeddings" REAL[][],
  "bm25_tokens" JSONB,
  "is_table" BOOLEAN,
  "table_type" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "chunk_retrieved_result" (
  "query_id" BIGINT NOT NULL,
  "pipeline_id" BIGINT NOT NULL,
  "chunk_id" BIGINT NOT NULL,
  "rel_score" DOUBLE PRECISION,
  PRIMARY KEY ("query_id", "pipeline_id", "chunk_id")
);

CREATE TABLE "document" (
  "id" BIGSERIAL NOT NULL,
  "path" BIGINT,
  "filename" TEXT,
  "author" TEXT,
  "title" TEXT,
  "doc_metadata" JSONB,
  PRIMARY KEY ("id")
);

CREATE TABLE "evaluation_result" (
  "query_id" BIGINT NOT NULL,
  "pipeline_id" BIGINT NOT NULL,
  "metric_id" BIGINT NOT NULL,
  "metric_result" DOUBLE PRECISION NOT NULL,
  PRIMARY KEY ("query_id", "pipeline_id", "metric_id")
);

CREATE TABLE "executor_result" (
  "query_id" BIGINT NOT NULL,
  "pipeline_id" BIGINT NOT NULL,
  "generation_result" TEXT,
  "token_usage" JSONB,
  "execution_time" INTEGER,
  "result_metadata" JSONB,
  PRIMARY KEY ("query_id", "pipeline_id")
);

CREATE TABLE "file" (
  "id" BIGSERIAL NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "path" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "image_chunk" (
  "id" BIGSERIAL NOT NULL,
  "parent_page" BIGINT,
  "contents" BYTEA NOT NULL,
  "mimetype" VARCHAR(255) NOT NULL,
  "embedding" REAL[],
  "embeddings" REAL[][],
  PRIMARY KEY ("id")
);

CREATE TABLE "image_chunk_retrieved_result" (
  "query_id" BIGINT NOT NULL,
  "pipeline_id" BIGINT NOT NULL,
  "image_chunk_id" BIGINT NOT NULL,
  "rel_score" DOUBLE PRECISION,
  PRIMARY KEY ("query_id", "pipeline_id", "image_chunk_id")
);

CREATE TABLE "metric" (
  "id" BIGSERIAL NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "page" (
  "id" BIGSERIAL NOT NULL,
  "page_num" INTEGER NOT NULL,
  "document_id" BIGINT NOT NULL,
  "image_contents" BYTEA,
  "mimetype" VARCHAR(255),
  "page_metadata" JSONB,
  PRIMARY KEY ("id"),
  UNIQUE ("document_id", "page_num")
);

CREATE TABLE "page_chunk_relation" (
  "page_id" BIGINT NOT NULL,
  "chunk_id" BIGINT NOT NULL,
  PRIMARY KEY ("page_id", "chunk_id")
);

CREATE TABLE "pipeline" (
  "id" BIGSERIAL NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "config" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "query" (
  "id" BIGSERIAL NOT NULL,
  "contents" TEXT NOT NULL,
  "query_to_llm" TEXT,
  "generation_gt" TEXT[],
  "embedding" REAL[],
  "embeddings" REAL[][],
  "bm25_tokens" JSONB,
  PRIMARY KEY ("id")
);

CREATE TABLE "retrieval_relation" (
  "query_id" BIGINT NOT NULL,
  "group_index" INTEGER NOT NULL,
  "group_order" INTEGER NOT NULL,
  "chunk_id" BIGINT,
  "image_chunk_id" BIGINT,
  "score" INTEGER,
  PRIMARY KEY ("query_id", "group_index", "group_order")
);

CREATE TABLE "summary" (
  "pipeline_id" BIGINT NOT NULL,
  "metric_id" BIGINT NOT NULL,
  "metric_result" DOUBLE PRECISION NOT NULL,
  "token_usage" JSONB,
  "execution_time" INTEGER,
  "result_metadata" JSONB,
  PRIMARY KEY ("pipeline_id", "metric_id")
);

ALTER TABLE "chunk_retrieved_result" ADD CONSTRAINT "fk_chunk_retrieved_result_query_id_1" FOREIGN KEY ("query_id") REFERENCES "query" ("id");

ALTER TABLE "chunk_retrieved_result" ADD CONSTRAINT "fk_chunk_retrieved_result_pipeline_id_2" FOREIGN KEY ("pipeline_id") REFERENCES "pipeline" ("id");

ALTER TABLE "chunk_retrieved_result" ADD CONSTRAINT "fk_chunk_retrieved_result_chunk_id_3" FOREIGN KEY ("chunk_id") REFERENCES "chunk" ("id");

ALTER TABLE "document" ADD CONSTRAINT "fk_document_path_1" FOREIGN KEY ("path") REFERENCES "file" ("id");

ALTER TABLE "evaluation_result" ADD CONSTRAINT "fk_evaluation_result_query_id_1" FOREIGN KEY ("query_id") REFERENCES "query" ("id");

ALTER TABLE "evaluation_result" ADD CONSTRAINT "fk_evaluation_result_pipeline_id_2" FOREIGN KEY ("pipeline_id") REFERENCES "pipeline" ("id");

ALTER TABLE "evaluation_result" ADD CONSTRAINT "fk_evaluation_result_metric_id_3" FOREIGN KEY ("metric_id") REFERENCES "metric" ("id");

ALTER TABLE "executor_result" ADD CONSTRAINT "fk_executor_result_query_id_1" FOREIGN KEY ("query_id") REFERENCES "query" ("id");

ALTER TABLE "executor_result" ADD CONSTRAINT "fk_executor_result_pipeline_id_2" FOREIGN KEY ("pipeline_id") REFERENCES "pipeline" ("id");

ALTER TABLE "image_chunk" ADD CONSTRAINT "fk_image_chunk_parent_page_1" FOREIGN KEY ("parent_page") REFERENCES "page" ("id");

ALTER TABLE "image_chunk_retrieved_result" ADD CONSTRAINT "fk_image_chunk_retrieved_result_query_id_1" FOREIGN KEY ("query_id") REFERENCES "query" ("id");

ALTER TABLE "image_chunk_retrieved_result" ADD CONSTRAINT "fk_image_chunk_retrieved_result_pipeline_id_2" FOREIGN KEY ("pipeline_id") REFERENCES "pipeline" ("id");

ALTER TABLE "image_chunk_retrieved_result" ADD CONSTRAINT "fk_image_chunk_retrieved_result_image_chunk_id_3" FOREIGN KEY ("image_chunk_id") REFERENCES "image_chunk" ("id");

ALTER TABLE "page" ADD CONSTRAINT "fk_page_document_id_1" FOREIGN KEY ("document_id") REFERENCES "document" ("id");

ALTER TABLE "page_chunk_relation" ADD CONSTRAINT "fk_page_chunk_relation_page_id_1" FOREIGN KEY ("page_id") REFERENCES "page" ("id");

ALTER TABLE "page_chunk_relation" ADD CONSTRAINT "fk_page_chunk_relation_chunk_id_2" FOREIGN KEY ("chunk_id") REFERENCES "chunk" ("id");

ALTER TABLE "retrieval_relation" ADD CONSTRAINT "fk_retrieval_relation_query_id_1" FOREIGN KEY ("query_id") REFERENCES "query" ("id");

ALTER TABLE "retrieval_relation" ADD CONSTRAINT "fk_retrieval_relation_chunk_id_2" FOREIGN KEY ("chunk_id") REFERENCES "chunk" ("id");

ALTER TABLE "retrieval_relation" ADD CONSTRAINT "fk_retrieval_relation_image_chunk_id_3" FOREIGN KEY ("image_chunk_id") REFERENCES "image_chunk" ("id");

ALTER TABLE "summary" ADD CONSTRAINT "fk_summary_pipeline_id_1" FOREIGN KEY ("pipeline_id") REFERENCES "pipeline" ("id");

ALTER TABLE "summary" ADD CONSTRAINT "fk_summary_metric_id_2" FOREIGN KEY ("metric_id") REFERENCES "metric" ("id");

CREATE INDEX "idx_file_type" ON "file" ("type");
CREATE INDEX "idx_summary_metric_score_pipeline" ON "summary" ("metric_id", "metric_result" DESC, "pipeline_id");
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX "idx_query_contents_trgm" ON "query" USING GIN ("contents" gin_trgm_ops);
