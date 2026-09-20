CREATE TABLE "AvailableModels" (
  "Id" TEXT NOT NULL,
  "Metadata" TEXT NOT NULL,
  "CreatedAt" TEXT NOT NULL,
  "UpdatedAt" TEXT NOT NULL,
  "IsDownloaded" INTEGER NOT NULL,
  "IsValid" INTEGER NOT NULL,
  PRIMARY KEY ("Id")
);

CREATE TABLE "Conversations" (
  "Id" TEXT NOT NULL,
  "Title" TEXT NOT NULL,
  "CreatedByUserId" TEXT NOT NULL,
  "CreatedAt" TEXT NOT NULL,
  "UpdatedAt" TEXT,
  PRIMARY KEY ("Id")
);

CREATE TABLE "Messages" (
  "Id" TEXT NOT NULL,
  "ConversationId" TEXT NOT NULL,
  "SenderType" TEXT NOT NULL,
  "Content" TEXT NOT NULL,
  "SentAt" TEXT NOT NULL,
  "ResponseChoiceId" TEXT,
  PRIMARY KEY ("Id")
);

CREATE TABLE "ResponseChoices" (
  "Id" TEXT NOT NULL,
  "MessageId" TEXT NOT NULL,
  "CreatedAt" TEXT NOT NULL,
  PRIMARY KEY ("Id")
);

CREATE TABLE "SearchPathScores" (
  "Id" TEXT NOT NULL,
  "Path" TEXT NOT NULL,
  "Score" REAL NOT NULL,
  "ResponseChoiceId" TEXT NOT NULL,
  "CreatedAt" TEXT NOT NULL,
  PRIMARY KEY ("Id")
);

CREATE TABLE "Settings" (
  "Performance" INTEGER NOT NULL,
  "AllowedPaths" TEXT NOT NULL,
  "AllowedApplications" TEXT NOT NULL,
  "CreatedAt" TEXT NOT NULL,
  "UpdatedAt" TEXT,
  "AIModelProviderScope" TEXT,
  "TreeStructureSchedule" TEXT,
  "TreeStructureScheduleEnabled" INTEGER,
  "HuggingfaceApiKey" TEXT NOT NULL
);

CREATE INDEX "idx_AvailableModels_UpdatedAt_1" ON "AvailableModels" ("UpdatedAt");

CREATE INDEX "idx_AvailableModels_IsDownloaded_2" ON "AvailableModels" ("IsDownloaded");

CREATE INDEX "idx_Conversations_CreatedByUserId_1" ON "Conversations" ("CreatedByUserId");

CREATE INDEX "idx_Messages_ConversationId_1" ON "Messages" ("ConversationId");

CREATE INDEX "idx_Messages_SenderType_2" ON "Messages" ("SenderType");

CREATE INDEX "idx_Messages_SentAt_3" ON "Messages" ("SentAt");

CREATE INDEX "idx_Messages_ResponseChoiceId_4" ON "Messages" ("ResponseChoiceId");

CREATE INDEX "idx_ResponseChoices_MessageId_1" ON "ResponseChoices" ("MessageId");

CREATE INDEX "idx_SearchPathScores_ResponseChoiceId_1" ON "SearchPathScores" ("ResponseChoiceId");

CREATE INDEX "idx_SearchPathScores_Score_2" ON "SearchPathScores" ("Score");

ALTER TABLE "Messages" ADD CONSTRAINT "fk_Messages_ConversationId_1" FOREIGN KEY ("ConversationId") REFERENCES "Conversations" ("Id");

ALTER TABLE "ResponseChoices" ADD CONSTRAINT "fk_ResponseChoices_MessageId_1" FOREIGN KEY ("MessageId") REFERENCES "Messages" ("Id");

ALTER TABLE "SearchPathScores" ADD CONSTRAINT "fk_SearchPathScores_ResponseChoiceId_1" FOREIGN KEY ("ResponseChoiceId") REFERENCES "ResponseChoices" ("Id");
