CREATE TABLE "AspNetRoles" (
  "Id" TEXT NOT NULL,
  "ConcurrencyStamp" TEXT,
  "Name" TEXT,
  "NormalizedName" TEXT,
  PRIMARY KEY ("Id")
);

CREATE TABLE "AspNetRoleClaims" (
  "Id" INTEGER NOT NULL,
  "ClaimType" TEXT,
  "ClaimValue" TEXT,
  "RoleId" TEXT NOT NULL,
  PRIMARY KEY ("Id"),
  FOREIGN KEY ("RoleId") REFERENCES "AspNetRoles" ("Id")
);

CREATE TABLE "AspNetUsers" (
  "Id" TEXT NOT NULL,
  "AccessFailedCount" INTEGER NOT NULL,
  "ConcurrencyStamp" TEXT,
  "Email" TEXT,
  "EmailConfirmed" INTEGER NOT NULL,
  "LockoutEnabled" INTEGER NOT NULL,
  "LockoutEnd" TEXT,
  "NormalizedEmail" TEXT,
  "NormalizedUserName" TEXT,
  "PasswordHash" TEXT,
  "PhoneNumber" TEXT,
  "PhoneNumberConfirmed" INTEGER NOT NULL,
  "SecurityStamp" TEXT,
  "TwoFactorEnabled" INTEGER NOT NULL,
  "UserName" TEXT,
  PRIMARY KEY ("Id")
);

CREATE TABLE "Todos" (
  "Id" INTEGER NOT NULL,
  "IsComplete" INTEGER NOT NULL,
  "OwnerId" TEXT NOT NULL,
  "Title" TEXT NOT NULL,
  PRIMARY KEY ("Id"),
  FOREIGN KEY ("OwnerId") REFERENCES "AspNetUsers" ("Id")
);

CREATE TABLE "AspNetUserClaims" (
  "Id" INTEGER NOT NULL,
  "ClaimType" TEXT,
  "ClaimValue" TEXT,
  "UserId" TEXT NOT NULL,
  PRIMARY KEY ("Id"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id")
);

CREATE TABLE "AspNetUserLogins" (
  "LoginProvider" TEXT NOT NULL,
  "ProviderKey" TEXT NOT NULL,
  "ProviderDisplayName" TEXT,
  "UserId" TEXT NOT NULL,
  PRIMARY KEY ("LoginProvider", "ProviderKey"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id")
);

CREATE TABLE "AspNetUserRoles" (
  "UserId" TEXT NOT NULL,
  "RoleId" TEXT NOT NULL,
  PRIMARY KEY ("UserId", "RoleId"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id"),
  FOREIGN KEY ("RoleId") REFERENCES "AspNetRoles" ("Id")
);

CREATE TABLE "AspNetUserTokens" (
  "UserId" TEXT NOT NULL,
  "LoginProvider" TEXT NOT NULL,
  "Name" TEXT NOT NULL,
  "Value" TEXT,
  PRIMARY KEY ("UserId", "LoginProvider", "Name"),
  FOREIGN KEY ("UserId") REFERENCES "AspNetUsers" ("Id")
);

CREATE UNIQUE INDEX "uidx_AspNetRoles_NormalizedName_1" ON "AspNetRoles" ("NormalizedName");

CREATE INDEX "idx_AspNetRoleClaims_RoleId_1" ON "AspNetRoleClaims" ("RoleId");

CREATE INDEX "idx_AspNetUsers_NormalizedEmail_1" ON "AspNetUsers" ("NormalizedEmail");

CREATE UNIQUE INDEX "uidx_AspNetUsers_NormalizedUserName_2" ON "AspNetUsers" ("NormalizedUserName");

CREATE INDEX "idx_Todos_OwnerId_1" ON "Todos" ("OwnerId");

CREATE INDEX "idx_AspNetUserClaims_UserId_1" ON "AspNetUserClaims" ("UserId");

CREATE INDEX "idx_AspNetUserLogins_UserId_1" ON "AspNetUserLogins" ("UserId");

CREATE INDEX "idx_AspNetUserRoles_RoleId_1" ON "AspNetUserRoles" ("RoleId");
