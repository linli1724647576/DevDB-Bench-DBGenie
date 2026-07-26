CREATE TABLE `article` (
  `id` INTEGER NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `content` TEXT NOT NULL,
  `publish_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  `count` INTEGER NOT NULL,
  `editor` INTEGER NOT NULL,
  `status` INTEGER NOT NULL,
  `author_id` INTEGER NOT NULL,
  `classification_id` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `author` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `website` VARCHAR(255) NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `tag` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `classification` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `article_articlemanager` (
  `id` INTEGER NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `links` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `link` VARCHAR(255) NOT NULL,
  `avatar` VARCHAR(255) NOT NULL,
  `desc` VARCHAR(255) NOT NULL,
  `weights` INTEGER,
  `email` VARCHAR(255),
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `carousel_img` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255) NOT NULL,
  `path` VARCHAR(255) NOT NULL,
  `link` VARCHAR(255),
  `weights` INTEGER,
  `img_type` INTEGER NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `music` (
  `id` INTEGER NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `url` VARCHAR(255) NOT NULL,
  `cover` VARCHAR(255) NOT NULL,
  `artist` VARCHAR(255),
  `lrc` VARCHAR(255),
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `subscription` (
  `id` INTEGER NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `visitor` (
  `id` INTEGER NOT NULL,
  `nickname` VARCHAR(255) NOT NULL,
  `avatar` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `website` VARCHAR(255),
  `blogger` TINYINT(1) NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `owner_message` (
  `id` INTEGER NOT NULL,
  `summary` VARCHAR(255),
  `message` TEXT NOT NULL,
  `editor` INTEGER NOT NULL,
  `created_at` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `comment` (
  `id` INTEGER NOT NULL,
  `content` TEXT NOT NULL,
  `target` VARCHAR(255),
  `anchor` VARCHAR(255),
  `ip_address` VARCHAR(255),
  `country` VARCHAR(255),
  `province` VARCHAR(255),
  `city` VARCHAR(255),
  `parent_id` INTEGER,
  `reply_to_id` INTEGER,
  `user_id` INTEGER NOT NULL,
  `created_time` DATETIME NOT NULL,
  `last_update` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `article_tags` (
  `id` INTEGER NOT NULL,
  `article_id` INTEGER NOT NULL,
  `tag_id` INTEGER NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`article_id`, `tag_id`)
);

ALTER TABLE `article` ADD CONSTRAINT `fk_article_author_id_1` FOREIGN KEY (`author_id`) REFERENCES `author` (`id`);

ALTER TABLE `article` ADD CONSTRAINT `fk_article_classification_id_2` FOREIGN KEY (`classification_id`) REFERENCES `classification` (`id`);

ALTER TABLE `comment` ADD CONSTRAINT `fk_comment_parent_id_1` FOREIGN KEY (`parent_id`) REFERENCES `comment` (`id`);

ALTER TABLE `comment` ADD CONSTRAINT `fk_comment_reply_to_id_2` FOREIGN KEY (`reply_to_id`) REFERENCES `visitor` (`id`);

ALTER TABLE `comment` ADD CONSTRAINT `fk_comment_user_id_3` FOREIGN KEY (`user_id`) REFERENCES `visitor` (`id`);

ALTER TABLE `article_tags` ADD CONSTRAINT `fk_article_tags_article_id_1` FOREIGN KEY (`article_id`) REFERENCES `article` (`id`);

ALTER TABLE `article_tags` ADD CONSTRAINT `fk_article_tags_tag_id_2` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`);

CREATE INDEX `idx_article_status_publish_time` ON `article` (`status`, `publish_time`);
CREATE INDEX `idx_article_classification_status_publish_time` ON `article` (`classification_id`, `status`, `publish_time`);
CREATE INDEX `idx_article_tags_tag_article` ON `article_tags` (`tag_id`, `article_id`);
CREATE INDEX `idx_carousel_img_weights_id` ON `carousel_img` (`weights`, `id`);
CREATE INDEX `idx_links_weights_id` ON `links` (`weights`, `id`);
CREATE INDEX `idx_comment_created_time_id` ON `comment` (`created_time` DESC, `id`);
