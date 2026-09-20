CREATE SEQUENCE IF NOT EXISTS seq_repository_index_scope_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_source_files_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_code_chunks_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_vector_embeddings_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_schema_versions_id START 1;

CREATE TABLE "repository_index_scope" (
  "id" BIGINT NOT NULL DEFAULT nextval('seq_repository_index_scope_id'),
  "scope_name" VARCHAR NOT NULL,
  "root_path" VARCHAR NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("root_path"),
  UNIQUE ("scope_name"),
  CHECK (length("root_path") > 0),
  CHECK (length("scope_name") > 0)
);

CREATE TABLE "source_files" (
  "id" BIGINT NOT NULL DEFAULT nextval('seq_source_files_id'),
  "repository_index_scope_id" BIGINT NOT NULL,
  "path" VARCHAR NOT NULL,
  "name" VARCHAR NOT NULL,
  "extension" VARCHAR,
  "detected_language" VARCHAR,
  "size_bytes" BIGINT NOT NULL,
  "content_hash" VARCHAR NOT NULL,
  "modification_time" TIMESTAMP NOT NULL,
  "indexed_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("repository_index_scope_id") REFERENCES "repository_index_scope" ("id"),
  UNIQUE ("repository_index_scope_id", "path"),
  CHECK ("size_bytes" >= 0),
  CHECK (length("path") > 0),
  CHECK (length("name") > 0)
);

CREATE TABLE "code_chunks" (
  "id" BIGINT NOT NULL DEFAULT nextval('seq_code_chunks_id'),
  "indexed_source_file_id" BIGINT NOT NULL,
  "chunk_kind" VARCHAR NOT NULL,
  "symbol_name" VARCHAR,
  "code_text" TEXT NOT NULL,
  "byte_start" BIGINT NOT NULL,
  "byte_end" BIGINT NOT NULL,
  "line_start" INTEGER NOT NULL,
  "line_end" INTEGER NOT NULL,
  "language" VARCHAR,
  "metadata" JSON,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("indexed_source_file_id") REFERENCES "source_files" ("id"),
  UNIQUE ("indexed_source_file_id", "byte_start", "byte_end"),
  CHECK ("byte_start" >= 0),
  CHECK ("byte_end" >= "byte_start"),
  CHECK ("line_start" >= 1),
  CHECK ("line_end" >= "line_start"),
  CHECK (length("chunk_kind") > 0)
);

CREATE TABLE "vector_embeddings" (
  "id" BIGINT NOT NULL DEFAULT nextval('seq_vector_embeddings_id'),
  "code_chunk_id" BIGINT NOT NULL,
  "embedding_provider" VARCHAR NOT NULL,
  "model" VARCHAR NOT NULL,
  "dimensions" INTEGER NOT NULL,
  "vector_data" DOUBLE[] NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("code_chunk_id") REFERENCES "code_chunks" ("id"),
  UNIQUE ("code_chunk_id", "embedding_provider", "model"),
  CHECK ("dimensions" > 0),
  CHECK (array_length("vector_data") = "dimensions"),
  CHECK (length("embedding_provider") > 0),
  CHECK (length("model") > 0)
);

CREATE TABLE "schema_versions" (
  "id" BIGINT NOT NULL DEFAULT nextval('seq_schema_versions_id'),
  "schema_version" VARCHAR NOT NULL,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id"),
  UNIQUE ("schema_version"),
  CHECK ("id" = 1),
  CHECK (length("schema_version") > 0)
);

CREATE INDEX "IX_source_files_scope_language"
  ON "source_files" ("repository_index_scope_id", "detected_language");
CREATE INDEX "IX_source_files_scope_modification_time"
  ON "source_files" ("repository_index_scope_id", "modification_time");
CREATE INDEX "IX_source_files_scope_content_hash"
  ON "source_files" ("repository_index_scope_id", "content_hash");
CREATE INDEX "IX_code_chunks_file_byte_start"
  ON "code_chunks" ("indexed_source_file_id", "byte_start");
CREATE INDEX "IX_code_chunks_file_line_start"
  ON "code_chunks" ("indexed_source_file_id", "line_start");
CREATE INDEX "IX_code_chunks_symbol_name" ON "code_chunks" ("symbol_name");
CREATE INDEX "IX_code_chunks_chunk_kind" ON "code_chunks" ("chunk_kind");
CREATE INDEX "IX_code_chunks_language" ON "code_chunks" ("language");
CREATE INDEX "IX_vector_embeddings_code_chunk_id"
  ON "vector_embeddings" ("code_chunk_id");
CREATE INDEX "IX_vector_embeddings_provider_model"
  ON "vector_embeddings" ("embedding_provider", "model");
