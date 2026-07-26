CREATE TABLE `failed_jobs` (
  `id` BIGINT NOT NULL,
  `uuid` VARCHAR(255) NOT NULL,
  `connection` TEXT NOT NULL,
  `queue` TEXT NOT NULL,
  `payload` TEXT NOT NULL,
  `exception` TEXT NOT NULL,
  `failed_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `kategori` (
  `id` INTEGER NOT NULL,
  `nama_kategori` VARCHAR(255),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `migrations` (
  `id` INTEGER NOT NULL,
  `migration` VARCHAR(255) NOT NULL,
  `batch` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `password_resets` (
  `email` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` DATETIME
);

CREATE TABLE `personal_access_tokens` (
  `id` BIGINT NOT NULL,
  `tokenable_type` VARCHAR(255) NOT NULL,
  `tokenable_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `token` VARCHAR(64) NOT NULL,
  `abilities` TEXT,
  `last_used_at` DATETIME,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `produk` (
  `id` INTEGER NOT NULL,
  `id_kategori` INTEGER NOT NULL,
  `gambar` VARCHAR(255),
  `nama_produk` VARCHAR(255),
  `deskripsi` TEXT,
  `harga_jual` INTEGER NOT NULL,
  `created_at` DATETIME,
  `updated_at` DATETIME,
  `deleted_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE TABLE `users` (
  `id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `phone` VARCHAR(25),
  `address` TEXT,
  `email_verified_at` DATETIME,
  `password` VARCHAR(255) NOT NULL,
  `remember_token` VARCHAR(100),
  `created_at` DATETIME,
  `updated_at` DATETIME,
  PRIMARY KEY (`id`)
);

CREATE INDEX `idx_password_resets_email_1` ON `password_resets` (`email`);
