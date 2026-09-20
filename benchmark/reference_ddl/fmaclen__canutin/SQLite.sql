CREATE TABLE "AccountType" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "AssetType" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "Event" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "message" TEXT NOT NULL,
  "dismissAfter" INTEGER NOT NULL,
  "appearance" TEXT,
  "status" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "new_Account" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  "institution" TEXT,
  "isClosed" BOOLEAN NOT NULL,
  "isAutoCalculated" BOOLEAN NOT NULL,
  "isExcludedFromNetWorth" BOOLEAN NOT NULL,
  "balanceGroup" INTEGER NOT NULL,
  "accountTypeId" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("accountTypeId") REFERENCES "AccountType" ("id")
);

CREATE TABLE "new_Asset" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  "balanceGroup" INTEGER NOT NULL,
  "isSold" BOOLEAN NOT NULL,
  "symbol" TEXT,
  "assetTypeId" INTEGER NOT NULL,
  "isExcludedFromNetWorth" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("assetTypeId") REFERENCES "AssetType" ("id")
);

CREATE TABLE "Setting" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "TransactionCategoryGroup" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "Account" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  "institution" TEXT,
  "isClosed" BOOLEAN NOT NULL,
  "isAutoCalculated" BOOLEAN NOT NULL,
  "balanceGroup" INTEGER NOT NULL,
  "accountTypeId" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("accountTypeId") REFERENCES "AccountType" ("id")
);

CREATE TABLE "AccountBalanceStatement" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "value" REAL NOT NULL,
  "accountId" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("accountId") REFERENCES "Account" ("id")
);

CREATE TABLE "Asset" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  "balanceGroup" INTEGER NOT NULL,
  "isSold" BOOLEAN NOT NULL,
  "symbol" TEXT,
  "assetTypeId" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("assetTypeId") REFERENCES "AssetType" ("id")
);

CREATE TABLE "AssetBalanceStatement" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "value" REAL NOT NULL,
  "quantity" REAL,
  "cost" REAL,
  "assetId" INTEGER,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("assetId") REFERENCES "Asset" ("id")
);

CREATE TABLE "TransactionCategory" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "name" TEXT NOT NULL,
  "transactionCategoryId" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("transactionCategoryId") REFERENCES "TransactionCategoryGroup" ("id")
);

CREATE TABLE "new_Transaction" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "description" TEXT NOT NULL,
  "date" TIMESTAMP NOT NULL,
  "value" REAL NOT NULL,
  "isExcluded" BOOLEAN NOT NULL,
  "isPending" BOOLEAN NOT NULL,
  "categoryId" INTEGER NOT NULL,
  "accountId" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("categoryId") REFERENCES "TransactionCategory" ("id"),
  FOREIGN KEY ("accountId") REFERENCES "Account" ("id")
);

CREATE TABLE "Transaction" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "description" TEXT NOT NULL,
  "date" TIMESTAMP NOT NULL,
  "value" REAL NOT NULL,
  "isExcluded" BOOLEAN NOT NULL,
  "isPending" BOOLEAN NOT NULL,
  "categoryId" INTEGER NOT NULL,
  "accountId" INTEGER NOT NULL,
  "importedAt" TIMESTAMP,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("accountId") REFERENCES "Account" ("id"),
  FOREIGN KEY ("categoryId") REFERENCES "TransactionCategory" ("id")
);

CREATE TABLE "TransactionImport" (
  "id" INTEGER NOT NULL,
  "createdAt" TIMESTAMP NOT NULL,
  "updatedAt" TIMESTAMP NOT NULL,
  "description" TEXT NOT NULL,
  "date" TIMESTAMP NOT NULL,
  "value" REAL NOT NULL,
  "categoryName" TEXT NOT NULL,
  "isExcluded" BOOLEAN NOT NULL,
  "isPending" BOOLEAN NOT NULL,
  "accountId" INTEGER NOT NULL,
  "transactionId" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("accountId") REFERENCES "Account" ("id"),
  FOREIGN KEY ("transactionId") REFERENCES "Transaction" ("id")
);

CREATE UNIQUE INDEX "uidx_Setting_name_1" ON "Setting" ("name");

CREATE UNIQUE INDEX "uidx_TransactionCategoryGroup_name_1" ON "TransactionCategoryGroup" ("name");

CREATE UNIQUE INDEX "uidx_Account_name_1" ON "Account" ("name");

CREATE UNIQUE INDEX "uidx_AccountBalanceStatement_accountId_createdAt_1" ON "AccountBalanceStatement" ("accountId", "createdAt");

CREATE UNIQUE INDEX "uidx_Asset_name_1" ON "Asset" ("name");

CREATE UNIQUE INDEX "uidx_AssetBalanceStatement_assetId_createdAt_1" ON "AssetBalanceStatement" ("assetId", "createdAt");

CREATE UNIQUE INDEX "uidx_TransactionImport_transactionId_1" ON "TransactionImport" ("transactionId");
