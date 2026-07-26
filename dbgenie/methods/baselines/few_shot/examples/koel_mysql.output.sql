CREATE TABLE users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE roles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_roles_name (name)
) ENGINE=InnoDB;

CREATE TABLE permissions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_permissions_name (name)
) ENGINE=InnoDB;

CREATE TABLE user_roles (
    user_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, role_id),
    KEY ix_user_roles_role (role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE role_permissions (
    role_id BIGINT UNSIGNED NOT NULL,
    permission_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    KEY ix_role_permissions_permission (permission_id),
    CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE albums (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    artist_name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_albums_artist_title (artist_name, title)
) ENGINE=InnoDB;

CREATE TABLE songs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    album_id BIGINT UNSIGNED NULL,
    title VARCHAR(255) NOT NULL,
    disc_number SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    track_number SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    file_path VARCHAR(1024) NOT NULL,
    file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    duration_seconds INT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_songs_file_path (file_path),
    KEY ix_songs_album_order (album_id, disc_number, track_number, title),
    CONSTRAINT fk_songs_album FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE playlists (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_playlists_user (user_id),
    CONSTRAINT fk_playlists_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE playlist_songs (
    playlist_id BIGINT UNSIGNED NOT NULL,
    song_id BIGINT UNSIGNED NOT NULL,
    position INT UNSIGNED NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, song_id),
    UNIQUE KEY uq_playlist_songs_position (playlist_id, position),
    KEY ix_playlist_songs_song (song_id),
    CONSTRAINT fk_playlist_songs_playlist FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
    CONSTRAINT fk_playlist_songs_song FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE favorites (
    user_id BIGINT UNSIGNED NOT NULL,
    song_id BIGINT UNSIGNED NOT NULL,
    position INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, song_id),
    UNIQUE KEY uq_favorites_position (user_id, position),
    KEY ix_favorites_song (song_id),
    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_favorites_song FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE interactions (
    user_id BIGINT UNSIGNED NOT NULL,
    song_id BIGINT UNSIGNED NOT NULL,
    play_count INT UNSIGNED NOT NULL DEFAULT 0,
    last_played_at DATETIME NULL,
    PRIMARY KEY (user_id, song_id),
    KEY ix_interactions_recent (user_id, last_played_at),
    KEY ix_interactions_song (song_id),
    CONSTRAINT fk_interactions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_interactions_song FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE podcast_user_subscriptions (
    user_id BIGINT UNSIGNED NOT NULL,
    podcast_id BIGINT UNSIGNED NOT NULL,
    subscribed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, podcast_id),
    KEY ix_podcast_subscriptions_podcast (podcast_id),
    CONSTRAINT fk_podcast_subscriptions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE themes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    configuration JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_themes_user_created (user_id, created_at),
    CONSTRAINT fk_themes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE embeds (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    public_token VARCHAR(128) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id BIGINT UNSIGNED NOT NULL,
    expires_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_embeds_public_token (public_token),
    KEY ix_embeds_owner_resource (user_id, resource_type, resource_id),
    CONSTRAINT fk_embeds_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE duplicate_uploads (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    original_song_id BIGINT UNSIGNED NOT NULL,
    duplicate_path VARCHAR(1024) NOT NULL,
    duplicate_file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_duplicate_uploads_user_created (user_id, created_at),
    KEY ix_duplicate_uploads_song (original_song_id),
    CONSTRAINT fk_duplicate_uploads_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_duplicate_uploads_song FOREIGN KEY (original_song_id) REFERENCES songs (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE transcodes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    song_id BIGINT UNSIGNED NOT NULL,
    format VARCHAR(32) NOT NULL,
    bitrate_kbps INT UNSIGNED NULL,
    file_path VARCHAR(1024) NOT NULL,
    file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_transcodes_song_format_bitrate (song_id, format, bitrate_kbps),
    KEY ix_transcodes_song (song_id),
    CONSTRAINT fk_transcodes_song FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE agent_conversations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_agent_conversations_user_updated (user_id, updated_at),
    CONSTRAINT fk_agent_conversations_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE agent_messages (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    conversation_id BIGINT UNSIGNED NOT NULL,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    tool_calls JSON NULL,
    tool_results JSON NULL,
    usage_metadata JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_agent_messages_conversation_created (conversation_id, created_at),
    CONSTRAINT fk_agent_messages_conversation FOREIGN KEY (conversation_id) REFERENCES agent_conversations (id) ON DELETE CASCADE,
    CONSTRAINT ck_agent_messages_role CHECK (role IN ('system', 'user', 'assistant', 'tool'))
) ENGINE=InnoDB;
