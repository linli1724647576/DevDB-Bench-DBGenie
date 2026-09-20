CREATE TABLE [AccountLinks] (
  [Id] INT NOT NULL,
  [OculusID] INT NOT NULL,
  [PCOculusID] NVARCHAR(255) NOT NULL,
  [SteamID] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [AccountLinkRequests] (
  [Id] INT NOT NULL,
  [IP] NVARCHAR(MAX) NOT NULL,
  [OculusID] NVARCHAR(MAX) NOT NULL,
  [Random] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Achievements] (
  [Id] INT NOT NULL,
  [AchievementDescriptionId] INT NOT NULL,
  [AdditionalLevels] NVARCHAR(MAX),
  [Count] INT NOT NULL,
  [LevelId] INT,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [AchievementDescriptions] (
  [Id] INT NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  [Link] NVARCHAR(MAX),
  [Name] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [AchievementLevels] (
  [Id] INT NOT NULL,
  [AchievementDescriptionId] INT NOT NULL,
  [Color] NVARCHAR(MAX),
  [Description] NVARCHAR(MAX),
  [DetailedDescription] NVARCHAR(MAX),
  [Image] NVARCHAR(MAX) NOT NULL,
  [Level] INT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [SmallImage] NVARCHAR(MAX) NOT NULL,
  [Value] FLOAT,
  PRIMARY KEY ([Id])
);

CREATE TABLE [AliasRequests] (
  [Id] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Status] INT NOT NULL,
  [Timeset] INT NOT NULL,
  [Value] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [AuthIDs] (
  [Id] NVARCHAR(255) NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [AuthIPs] (
  [Id] INT NOT NULL,
  [IP] NVARCHAR(MAX) NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Auths] (
  [Id] INT NOT NULL,
  [Hint] NVARCHAR(MAX) NOT NULL,
  [Login] NVARCHAR(MAX) NOT NULL,
  [Password] NVARCHAR(MAX) NOT NULL,
  [Salt] VARBINARY(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Badges] (
  [Id] INT NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  [Hidden] BIT NOT NULL,
  [Image] NVARCHAR(MAX) NOT NULL,
  [Link] NVARCHAR(MAX),
  [PlayerId] NVARCHAR(255),
  [Priority] INT NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Bans] (
  [Id] INT NOT NULL,
  [BanReason] NVARCHAR(MAX) NOT NULL,
  [BannedBy] NVARCHAR(MAX) NOT NULL,
  [Duration] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [BeastiesNominations] (
  [Id] INT NOT NULL,
  [Category] NVARCHAR(255) NOT NULL,
  [LeaderboardId] NVARCHAR(255) NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Timepost] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [BeatSaverLinks] (
  [Id] NVARCHAR(255) NOT NULL,
  [BeatSaverId] NVARCHAR(MAX) NOT NULL,
  [RefreshToken] NVARCHAR(MAX) NOT NULL,
  [Timestamp] NVARCHAR(MAX) NOT NULL,
  [Token] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Clans] (
  [Id] INT NOT NULL,
  [AverageAccuracy] FLOAT NOT NULL,
  [AverageRank] FLOAT NOT NULL,
  [Bio] NVARCHAR(MAX) NOT NULL,
  [CaptureLeaderboardsCount] INT NOT NULL,
  [ClanRankingDiscordHook] NVARCHAR(MAX),
  [Color] NVARCHAR(255) NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  [DiscordInvite] NVARCHAR(MAX) NOT NULL,
  [GlobalMapX] FLOAT NOT NULL,
  [GlobalMapY] FLOAT NOT NULL,
  [Icon] NVARCHAR(MAX) NOT NULL,
  [LeaderID] NVARCHAR(255) NOT NULL,
  [MainPlayersCount] INT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [PlayerChangesCallback] NVARCHAR(MAX),
  [PlayersCount] INT NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Rank] INT NOT NULL,
  [RankedPoolPercentCaptured] FLOAT NOT NULL,
  [RichBioTimeset] INT NOT NULL,
  [Tag] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([Tag])
);

CREATE TABLE [ClanManagers] (
  [Id] INT NOT NULL,
  [ClanId] INT,
  [Permissions] INT NOT NULL,
  [PlayerId] NVARCHAR(255),
  PRIMARY KEY ([Id])
);

CREATE TABLE [ClanOrderChanges] (
  [Id] INT NOT NULL,
  [NewOrder] NVARCHAR(MAX) NOT NULL,
  [OldOrder] NVARCHAR(MAX) NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ClanRanking] (
  [Id] INT NOT NULL,
  [AverageAccuracy] FLOAT NOT NULL,
  [AverageRank] FLOAT NOT NULL,
  [ClanId] INT,
  [LastUpdateTime] INT NOT NULL,
  [LeaderboardId] NVARCHAR(255),
  [Pp] FLOAT NOT NULL,
  [Rank] INT NOT NULL,
  [TotalScore] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ClanUpdates] (
  [Id] INT NOT NULL,
  [ChangeDescription] NVARCHAR(MAX),
  [ClanId] INT,
  [PlayerId] NVARCHAR(255),
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [CountryChanges] (
  [Id] NVARCHAR(255) NOT NULL,
  [NewCountry] NVARCHAR(MAX) NOT NULL,
  [OldCountry] NVARCHAR(MAX) NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [CountryChangeBans] (
  [Id] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [CriteriaCommentary] (
  [Id] INT NOT NULL,
  [DiscordMessageId] NVARCHAR(MAX) NOT NULL,
  [EditTimeset] INT,
  [Edited] BIT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [RankQualificationId] INT,
  [Timeset] INT NOT NULL,
  [Value] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [cronTimestamps] (
  [Id] INT NOT NULL,
  [HistoriesTimestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [CustomModes] (
  [Id] INT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [DeveloperProfile] (
  [Id] INT NOT NULL,
  [GlobalWatermarkPermissions] BIT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [DifficultyDescription] (
  [Id] INT NOT NULL,
  [AccRating] FLOAT,
  [Bombs] INT NOT NULL,
  [Chains] INT NOT NULL,
  [CustomDifficultyName] NVARCHAR(MAX),
  [DifficultyName] NVARCHAR(255) NOT NULL,
  [DifficultyStatisticsId] INT,
  [Duration] FLOAT NOT NULL,
  [FeatureTags] INT NOT NULL,
  [Hash] NVARCHAR(255) NOT NULL,
  [LinearPercentage] FLOAT,
  [MapVersion] NVARCHAR(255),
  [MaxScore] INT NOT NULL,
  [MaxScoreGraphId] INT,
  [Mode] INT NOT NULL,
  [ModeName] NVARCHAR(255) NOT NULL,
  [ModifierValuesModifierId] INT,
  [ModifiersRatingId] INT,
  [MultiRating] FLOAT,
  [Njs] FLOAT NOT NULL,
  [NominatedTime] INT NOT NULL,
  [NoteJumpStartBeatOffset] FLOAT NOT NULL,
  [Notes] INT NOT NULL,
  [Nps] FLOAT NOT NULL,
  [PassRating] FLOAT,
  [PeakSustainedEBPM] FLOAT,
  [PredictedAcc] FLOAT,
  [QualifiedTime] INT NOT NULL,
  [RankedTime] INT NOT NULL,
  [Requirements] INT NOT NULL,
  [RequiresChroma] BIT NOT NULL,
  [RequiresCinema] BIT NOT NULL,
  [RequiresGroupLighting] BIT NOT NULL,
  [RequiresMappingExtensions] BIT NOT NULL,
  [RequiresNoodles] BIT NOT NULL,
  [RequiresOptionalProperties] BIT NOT NULL,
  [RequiresV3] BIT NOT NULL,
  [RequiresV3Pepega] BIT NOT NULL,
  [RequiresVNJS] BIT NOT NULL,
  [RequiresVivify] BIT NOT NULL,
  [Sliders] INT NOT NULL,
  [SongId] NVARCHAR(255),
  [SpeedTags] INT NOT NULL,
  [Stars] FLOAT,
  [Status] INT NOT NULL,
  [StyleTags] INT NOT NULL,
  [TechRating] FLOAT,
  [Type] INT NOT NULL,
  [TypeAcc] BIT NOT NULL,
  [TypeBombReset] BIT NOT NULL,
  [TypeFitbeat] BIT NOT NULL,
  [TypeLinear] BIT NOT NULL,
  [TypeMidspeed] BIT NOT NULL,
  [TypeSpeed] BIT NOT NULL,
  [TypeTech] BIT NOT NULL,
  [Value] INT NOT NULL,
  [Walls] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [DifficultyDescriptionExtension] (
  [Id] INT NOT NULL,
  [Context] INT NOT NULL,
  [DifficultyDescriptionId] INT,
  [MaxScoreLeft] INT NOT NULL,
  [MaxScoreRight] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [DifficultyStatistics] (
  [Id] INT NOT NULL,
  [BombAvoidances] INT NOT NULL,
  [CrouchWalls] INT NOT NULL,
  [CurvedSliders] INT NOT NULL,
  [DodgeWalls] INT NOT NULL,
  [LinearSwings] INT NOT NULL,
  [ParityErrors] INT NOT NULL,
  [SlantedWindows] INT NOT NULL,
  [Sliders] INT NOT NULL,
  [Stacks] INT NOT NULL,
  [Towers] INT NOT NULL,
  [Windows] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [EarthDayMaps] (
  [Id] INT NOT NULL,
  [Hash] NVARCHAR(MAX) NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([PlayerId])
);

CREATE TABLE [EventPlayer] (
  [Id] INT NOT NULL,
  [Country] NVARCHAR(MAX) NOT NULL,
  [CountryRank] INT NOT NULL,
  [EventName] NVARCHAR(MAX) NOT NULL,
  [EventRankingId] INT,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [PlayerName] NVARCHAR(MAX) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Rank] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [EventRankings] (
  [Id] INT NOT NULL,
  [AnimatedImage] NVARCHAR(MAX),
  [Description] NVARCHAR(MAX),
  [EndDate] INT NOT NULL,
  [EventType] INT NOT NULL,
  [FeaturedPlaylistId] INT,
  [Image] NVARCHAR(MAX) NOT NULL,
  [MainColor] NVARCHAR(MAX) NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [PageAlias] NVARCHAR(MAX),
  [PlaylistId] INT NOT NULL,
  [SecondaryColor] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ExternalStatus] (
  [Id] INT NOT NULL,
  [Details] NVARCHAR(MAX),
  [Link] NVARCHAR(MAX),
  [Responsible] NVARCHAR(MAX),
  [SongId] NVARCHAR(255),
  [Status] INT NOT NULL,
  [Timeset] INT NOT NULL,
  [Title] NVARCHAR(MAX),
  [TitleColor] NVARCHAR(MAX),
  PRIMARY KEY ([Id])
);

CREATE TABLE [FailedScores] (
  [Id] INT NOT NULL,
  [Accuracy] FLOAT NOT NULL,
  [BadCuts] INT NOT NULL,
  [BaseScore] INT NOT NULL,
  [BombCuts] INT NOT NULL,
  [CountryRank] INT NOT NULL,
  [Error] NVARCHAR(MAX) NOT NULL,
  [FalsePositive] BIT NOT NULL,
  [FullCombo] BIT NOT NULL,
  [Hmd] INT NOT NULL,
  [LeaderboardId] NVARCHAR(255),
  [MissedNotes] INT NOT NULL,
  [ModifiedScore] INT NOT NULL,
  [Modifiers] NVARCHAR(MAX) NOT NULL,
  [Pauses] INT NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Rank] INT NOT NULL,
  [Replay] NVARCHAR(MAX) NOT NULL,
  [Timeset] NVARCHAR(MAX) NOT NULL,
  [WallsHit] INT NOT NULL,
  [Weight] FLOAT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [FavoriteMaps] (
  [Id] INT NOT NULL,
  [Aspect] INT NOT NULL,
  [Comment] NVARCHAR(MAX),
  [LeaderboardId] NVARCHAR(255),
  [PlayerId] NVARCHAR(255),
  [RankVotingId] INT,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([RankVotingId])
);

CREATE TABLE [FeaturedPlaylist] (
  [Id] INT NOT NULL,
  [Cover] NVARCHAR(MAX) NOT NULL,
  [Description] NVARCHAR(MAX),
  [MapCount] INT NOT NULL,
  [Owner] NVARCHAR(MAX),
  [OwnerCover] NVARCHAR(MAX),
  [OwnerLink] NVARCHAR(MAX),
  [PlaylistLink] NVARCHAR(MAX) NOT NULL,
  [Title] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [GlobalMapChanges] (
  [Id] INT NOT NULL,
  [LeaderboardId] NVARCHAR(MAX),
  [NewClan1Capture] FLOAT,
  [NewClan1Id] INT,
  [NewClan1Pp] FLOAT,
  [NewClan2Capture] FLOAT,
  [NewClan2Id] INT,
  [NewClan2Pp] FLOAT,
  [NewClan3Capture] FLOAT,
  [NewClan3Id] INT,
  [NewClan3Pp] FLOAT,
  [NewX] FLOAT NOT NULL,
  [NewY] FLOAT NOT NULL,
  [OldClan1Capture] FLOAT,
  [OldClan1Id] INT,
  [OldClan1Pp] FLOAT,
  [OldClan2Capture] FLOAT,
  [OldClan2Id] INT,
  [OldClan2Pp] FLOAT,
  [OldClan3Capture] FLOAT,
  [OldClan3Id] INT,
  [OldClan3Pp] FLOAT,
  [OldX] FLOAT NOT NULL,
  [OldY] FLOAT NOT NULL,
  [PlayerAction] INT,
  [PlayerId] NVARCHAR(MAX),
  [ScoreId] INT,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [GlobalMapHistory] (
  [Id] INT NOT NULL,
  [AverageAccuracy] FLOAT NOT NULL,
  [AverageRank] FLOAT NOT NULL,
  [CaptureLeaderboardsCount] INT NOT NULL,
  [ClanId] INT NOT NULL,
  [GlobalMapCaptured] FLOAT NOT NULL,
  [MainPlayersCount] INT NOT NULL,
  [PlayersCount] INT NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Rank] INT NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Headsets] (
  [Id] INT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [Player] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [IdolBackgrounds] (
  [Id] INT NOT NULL,
  [Description] NVARCHAR(MAX),
  [GloballyAvailable] BIT NOT NULL,
  [ImageUrl] NVARCHAR(MAX) NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [ThumbnailUrl] NVARCHAR(MAX),
  PRIMARY KEY ([Id])
);

CREATE TABLE [IdolCanvases] (
  [Id] INT NOT NULL,
  [BackgroundId] INT NOT NULL,
  [CanvasState] NVARCHAR(MAX) NOT NULL,
  [LastUpdated] INT NOT NULL,
  [PlayerId] NVARCHAR(255),
  [SeenIdolIds] NVARCHAR(MAX),
  PRIMARY KEY ([Id]),
  UNIQUE ([PlayerId])
);

CREATE TABLE [IdolDecorations] (
  [Id] INT NOT NULL,
  [BigPicturePro] NVARCHAR(MAX) NOT NULL,
  [BigPictureRegular] NVARCHAR(MAX) NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  [GloballyAvailable] BIT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [SmallPicturePro] NVARCHAR(MAX) NOT NULL,
  [SmallPictureRegular] NVARCHAR(MAX) NOT NULL,
  [SongId] NVARCHAR(255),
  PRIMARY KEY ([Id])
);

CREATE TABLE [IdolDescriptions] (
  [Id] INT NOT NULL,
  [BigPicturePro] NVARCHAR(MAX) NOT NULL,
  [BigPictureRegular] NVARCHAR(MAX) NOT NULL,
  [Birthday] INT NOT NULL,
  [Bonus] BIT NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  [GloballyAvailable] BIT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [RewardGif] NVARCHAR(MAX),
  [SmallPicturePro] NVARCHAR(MAX) NOT NULL,
  [SmallPictureRegular] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [IngameAvatars] (
  [Id] INT NOT NULL,
  [PlayerID] NVARCHAR(255) NOT NULL,
  [Value] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [IpBans] (
  [Id] INT NOT NULL,
  [HashId] NVARCHAR(MAX) NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Leaderboards] (
  [Id] NVARCHAR(255) NOT NULL,
  [CapturedTime] INT,
  [ClanId] INT,
  [ClanRankingContested] BIT NOT NULL,
  [DifficultyId] INT NOT NULL,
  [FansCount] INT NOT NULL,
  [LastScoreTime] INT NOT NULL,
  [LeaderboardGroupId] INT,
  [MapOfTheDayId] INT,
  [NegativeVotes] INT NOT NULL,
  [PlayCount] INT NOT NULL,
  [Plays] INT NOT NULL,
  [PositiveVotes] INT NOT NULL,
  [QualificationId] INT,
  [ReweightId] INT,
  [SongId] NVARCHAR(255),
  [StarVotes] INT NOT NULL,
  [ThisWeekPlays] INT NOT NULL,
  [Timestamp] BIGINT NOT NULL,
  [TodayPlays] INT NOT NULL,
  [VoteStars] FLOAT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [LeaderboardChange] (
  [Id] INT NOT NULL,
  [LeaderboardId] NVARCHAR(255),
  [NewAccRating] FLOAT NOT NULL,
  [NewCriteriaMet] INT NOT NULL,
  [NewModifiersModifierId] INT,
  [NewModifiersRatingId] INT,
  [NewPassRating] FLOAT NOT NULL,
  [NewRankability] FLOAT NOT NULL,
  [NewStars] FLOAT NOT NULL,
  [NewTechRating] FLOAT NOT NULL,
  [NewType] INT NOT NULL,
  [OldAccRating] FLOAT NOT NULL,
  [OldCriteriaMet] INT NOT NULL,
  [OldModifiersModifierId] INT,
  [OldModifiersRatingId] INT,
  [OldPassRating] FLOAT NOT NULL,
  [OldRankability] FLOAT NOT NULL,
  [OldStars] FLOAT NOT NULL,
  [OldTechRating] FLOAT NOT NULL,
  [OldType] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [LeaderboardGroup] (
  [Id] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [LoginAttempts] (
  [Id] INT NOT NULL,
  [Count] INT NOT NULL,
  [IP] NVARCHAR(MAX) NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [LoginChanges] (
  [Id] INT NOT NULL,
  [NewLogin] NVARCHAR(MAX) NOT NULL,
  [OldLogin] NVARCHAR(MAX) NOT NULL,
  [PlayerId] INT NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [MapOfTheDay] (
  [Id] INT NOT NULL,
  [Description] NVARCHAR(MAX),
  [EventRankingId] INT,
  [SongId] NVARCHAR(255),
  [Timeend] INT NOT NULL,
  [Timestart] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [MapOfTheDayPoints] (
  [Id] INT NOT NULL,
  [EventPlayerId] INT,
  [MapOfTheDayId] INT NOT NULL,
  [Points] INT NOT NULL,
  [Rank] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [MapSwingData] (
  [Id] INT NOT NULL,
  [AngleStrain] FLOAT NOT NULL,
  [BombAvoidance] BIT NOT NULL,
  [BpmTime] FLOAT NOT NULL,
  [DifficultyStatisticsId] INT,
  [Direction] FLOAT NOT NULL,
  [DistanceDiff] FLOAT NOT NULL,
  [Forehand] BIT NOT NULL,
  [HitDistance] FLOAT NOT NULL,
  [IsLinear] BIT NOT NULL,
  [IsStream] BIT NOT NULL,
  [LowSpeedFalloff] FLOAT NOT NULL,
  [NjsBuff] FLOAT NOT NULL,
  [ParityErrors] BIT NOT NULL,
  [RepositioningDistance] FLOAT NOT NULL,
  [RotationAmount] FLOAT NOT NULL,
  [Stress] FLOAT NOT NULL,
  [StressMultiplier] FLOAT NOT NULL,
  [SwingDiff] FLOAT NOT NULL,
  [SwingFrequency] FLOAT NOT NULL,
  [SwingSpeed] FLOAT NOT NULL,
  [SwingTech] FLOAT NOT NULL,
  [WallBuff] FLOAT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Mappers] (
  [Id] INT NOT NULL,
  [Avatar] NVARCHAR(255) NOT NULL,
  [Curator] BIT,
  [Name] NVARCHAR(255) NOT NULL,
  [PlaylistUrl] NVARCHAR(255),
  [Status] INT NOT NULL,
  [VerifiedMapper] BIT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [MaxScoreGraph] (
  [Id] INT NOT NULL,
  [Graph] VARBINARY(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ModDescription] (
  [Id] INT NOT NULL,
  [Cover] NVARCHAR(MAX) NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  [DeveloperProfileId] INT,
  [Downloads] INT NOT NULL,
  [GithubLink] NVARCHAR(MAX) NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ModNews] (
  [Id] INT NOT NULL,
  [Body] NVARCHAR(MAX) NOT NULL,
  [Image] NVARCHAR(MAX) NOT NULL,
  [Owner] NVARCHAR(MAX) NOT NULL,
  [OwnerIcon] NVARCHAR(MAX) NOT NULL,
  [Timepost] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ModVersions] (
  [Id] INT NOT NULL,
  [GameVersion] NVARCHAR(MAX) NOT NULL,
  [Platform] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  [Version] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Modifiers] (
  [ModifierId] INT NOT NULL,
  [DA] FLOAT NOT NULL,
  [FS] FLOAT NOT NULL,
  [GN] FLOAT NOT NULL,
  [NA] FLOAT NOT NULL,
  [NB] FLOAT NOT NULL,
  [NF] FLOAT NOT NULL,
  [NO] FLOAT NOT NULL,
  [OP] FLOAT NOT NULL,
  [PM] FLOAT NOT NULL,
  [SA] FLOAT NOT NULL,
  [SC] FLOAT NOT NULL,
  [SF] FLOAT NOT NULL,
  [SS] FLOAT NOT NULL,
  PRIMARY KEY ([ModifierId])
);

CREATE TABLE [ModifiersRating] (
  [Id] INT NOT NULL,
  [BFSAccRating] FLOAT NOT NULL,
  [BFSPassRating] FLOAT NOT NULL,
  [BFSPeakSustainedEBPM] FLOAT NOT NULL,
  [BFSPredictedAcc] FLOAT NOT NULL,
  [BFSStars] FLOAT NOT NULL,
  [BFSTechRating] FLOAT NOT NULL,
  [BSFAccRating] FLOAT NOT NULL,
  [BSFPassRating] FLOAT NOT NULL,
  [BSFPeakSustainedEBPM] FLOAT NOT NULL,
  [BSFPredictedAcc] FLOAT NOT NULL,
  [BSFStars] FLOAT NOT NULL,
  [BSFTechRating] FLOAT NOT NULL,
  [FSAccRating] FLOAT NOT NULL,
  [FSPassRating] FLOAT NOT NULL,
  [FSPeakSustainedEBPM] FLOAT NOT NULL,
  [FSPredictedAcc] FLOAT NOT NULL,
  [FSStars] FLOAT NOT NULL,
  [FSTechRating] FLOAT NOT NULL,
  [SFAccRating] FLOAT NOT NULL,
  [SFPassRating] FLOAT NOT NULL,
  [SFPeakSustainedEBPM] FLOAT NOT NULL,
  [SFPredictedAcc] FLOAT NOT NULL,
  [SFStars] FLOAT NOT NULL,
  [SFTechRating] FLOAT NOT NULL,
  [SSAccRating] FLOAT NOT NULL,
  [SSPassRating] FLOAT NOT NULL,
  [SSPeakSustainedEBPM] FLOAT NOT NULL,
  [SSPredictedAcc] FLOAT NOT NULL,
  [SSStars] FLOAT NOT NULL,
  [SSTechRating] FLOAT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PatreonFeatures] (
  [Id] INT NOT NULL,
  [Bio] NVARCHAR(MAX) NOT NULL,
  [LeftSaberColor] NVARCHAR(MAX) NOT NULL,
  [Message] NVARCHAR(MAX) NOT NULL,
  [RightSaberColor] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Players] (
  [Id] NVARCHAR(255) NOT NULL,
  [AccPp] FLOAT NOT NULL,
  [Alias] NVARCHAR(255),
  [AllContextsPp] FLOAT NOT NULL,
  [Avatar] NVARCHAR(MAX) NOT NULL,
  [Banned] BIT NOT NULL,
  [Bot] BIT NOT NULL,
  [ClanOrder] NVARCHAR(MAX) NOT NULL,
  [Country] NVARCHAR(255) NOT NULL,
  [CountryRank] INT NOT NULL,
  [CreatedAt] INT NOT NULL,
  [DeveloperProfileId] INT,
  [Experience] INT NOT NULL,
  [ExternalProfileUrl] NVARCHAR(MAX) NOT NULL,
  [Inactive] BIT NOT NULL,
  [LastWeekCountryRank] INT NOT NULL,
  [LastWeekPp] FLOAT NOT NULL,
  [LastWeekRank] INT NOT NULL,
  [Level] INT NOT NULL,
  [MapperId] INT,
  [Name] NVARCHAR(255) NOT NULL,
  [OldAlias] NVARCHAR(255),
  [PassPp] FLOAT NOT NULL,
  [PatreonFeaturesId] INT,
  [Platform] NVARCHAR(MAX) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Prestige] INT NOT NULL,
  [ProfileSettingsId] INT,
  [Rank] INT NOT NULL,
  [RichBioTimeset] INT NOT NULL,
  [Role] NVARCHAR(MAX) NOT NULL,
  [ScoreStatsId] INT,
  [SpeedrunStart] INT NOT NULL,
  [TechPp] FLOAT NOT NULL,
  [Temporary] BIT NOT NULL,
  [TopClanId] INT,
  [WebAvatar] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([MapperId])
);

CREATE TABLE [PlayerBonusIdols] (
  [Id] INT NOT NULL,
  [IdolDescriptionId] INT NOT NULL,
  [PlayerId] NVARCHAR(255),
  [Reason] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PlayerChange] (
  [Id] INT NOT NULL,
  [Changer] NVARCHAR(MAX),
  [NewCountry] NVARCHAR(MAX),
  [NewName] NVARCHAR(MAX),
  [OldCountry] NVARCHAR(MAX),
  [OldName] NVARCHAR(MAX),
  [PlayerId] NVARCHAR(255),
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PlayerContextExtensions] (
  [Id] INT NOT NULL,
  [AccPp] FLOAT NOT NULL,
  [Alias] NVARCHAR(255),
  [Banned] BIT NOT NULL,
  [Context] INT NOT NULL,
  [Country] NVARCHAR(255) NOT NULL,
  [CountryRank] INT NOT NULL,
  [Experience] INT NOT NULL,
  [LastWeekCountryRank] INT NOT NULL,
  [LastWeekPp] FLOAT NOT NULL,
  [LastWeekRank] INT NOT NULL,
  [Level] INT NOT NULL,
  [Name] NVARCHAR(255) NOT NULL,
  [PassPp] FLOAT NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Prestige] INT NOT NULL,
  [Rank] INT NOT NULL,
  [ScoreStatsId] INT,
  [TechPp] FLOAT NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([PlayerId], [Context])
);

CREATE TABLE [Friends] (
  [Id] NVARCHAR(255) NOT NULL,
  [HideFriends] BIT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PlayerIdolDecorations] (
  [Id] INT NOT NULL,
  [IdolDecorationId] INT NOT NULL,
  [PlayerId] NVARCHAR(255),
  [Reason] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Stats] (
  [Id] INT NOT NULL,
  [APlays] INT NOT NULL,
  [AllHMDs] NVARCHAR(255) NOT NULL,
  [AnonimusReplayWatched] INT NOT NULL,
  [AuthorizedReplayWatched] INT NOT NULL,
  [AverageAccuracy] FLOAT NOT NULL,
  [AverageLeftTiming] FLOAT NOT NULL,
  [AverageRank] FLOAT NOT NULL,
  [AverageRankedAccuracy] FLOAT NOT NULL,
  [AverageRankedRank] FLOAT NOT NULL,
  [AverageRightTiming] FLOAT NOT NULL,
  [AverageUnrankedAccuracy] FLOAT NOT NULL,
  [AverageUnrankedRank] FLOAT NOT NULL,
  [AverageWeightedRankedAccuracy] FLOAT NOT NULL,
  [AverageWeightedRankedRank] FLOAT NOT NULL,
  [CountryTopPercentile] FLOAT NOT NULL,
  [DailyImprovements] INT NOT NULL,
  [FirstRankedScoreTime] INT NOT NULL,
  [FirstScoreTime] INT NOT NULL,
  [FirstUnrankedScoreTime] INT NOT NULL,
  [LastRankedScoreTime] INT NOT NULL,
  [LastScoreTime] INT NOT NULL,
  [LastUnrankedScoreTime] INT NOT NULL,
  [MaxStreak] INT NOT NULL,
  [MedianAccuracy] FLOAT NOT NULL,
  [MedianRankedAccuracy] FLOAT NOT NULL,
  [PeakRank] FLOAT NOT NULL,
  [RankedImprovementsCount] INT NOT NULL,
  [RankedMaxStreak] INT NOT NULL,
  [RankedPlayCount] INT NOT NULL,
  [RankedTop1Count] INT NOT NULL,
  [RankedTop1Score] INT NOT NULL,
  [ReplaysWatched] INT NOT NULL,
  [SPPlays] INT NOT NULL,
  [SPlays] INT NOT NULL,
  [SSPPlays] INT NOT NULL,
  [SSPlays] INT NOT NULL,
  [ScorePlaytime] FLOAT NOT NULL,
  [SteamPlaytime2Weeks] INT NOT NULL,
  [SteamPlaytimeForever] INT NOT NULL,
  [Top1Count] INT NOT NULL,
  [Top1Score] INT NOT NULL,
  [TopAccPP] FLOAT NOT NULL,
  [TopAccuracy] FLOAT NOT NULL,
  [TopBonusPP] FLOAT NOT NULL,
  [TopHMD] INT NOT NULL,
  [TopPassPP] FLOAT NOT NULL,
  [TopPercentile] FLOAT NOT NULL,
  [TopPlatform] NVARCHAR(MAX) NOT NULL,
  [TopPp] FLOAT NOT NULL,
  [TopRankedAccuracy] FLOAT NOT NULL,
  [TopTechPP] FLOAT NOT NULL,
  [TopUnrankedAccuracy] FLOAT NOT NULL,
  [TotalImprovementsCount] INT NOT NULL,
  [TotalPlayCount] INT NOT NULL,
  [TotalRankedScore] BIGINT NOT NULL,
  [TotalScore] BIGINT NOT NULL,
  [TotalUnrankedScore] BIGINT NOT NULL,
  [UnrankedImprovementsCount] INT NOT NULL,
  [UnrankedMaxStreak] INT NOT NULL,
  [UnrankedPlayCount] INT NOT NULL,
  [UnrankedTop1Count] INT NOT NULL,
  [UnrankedTop1Score] INT NOT NULL,
  [WatchedReplays] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PlayerSearches] (
  [Id] INT NOT NULL,
  [PlayerId] NVARCHAR(255),
  [Score] INT NOT NULL,
  [SearchId] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PlayerSocial] (
  [Id] INT NOT NULL,
  [Hidden] BIT NOT NULL,
  [Link] NVARCHAR(MAX) NOT NULL,
  [PlayerId] NVARCHAR(255),
  [Service] NVARCHAR(MAX) NOT NULL,
  [User] NVARCHAR(MAX) NOT NULL,
  [UserId] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [PlayerTreeOrnaments] (
  [Id] INT NOT NULL,
  [OrnamentId] INT NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [ScoreId] INT,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Playlists] (
  [Id] INT NOT NULL,
  [Deleted] BIT NOT NULL,
  [Guid] UNIQUEIDENTIFIER NOT NULL,
  [Hash] NVARCHAR(MAX),
  [IsShared] BIT NOT NULL,
  [Link] NVARCHAR(MAX) NOT NULL,
  [OwnerId] NVARCHAR(MAX) NOT NULL,
  [UserId] NVARCHAR(255),
  PRIMARY KEY ([Id])
);

CREATE TABLE [PredictedScores] (
  [Id] INT NOT NULL,
  [AccLeft] FLOAT NOT NULL,
  [AccPP] FLOAT NOT NULL,
  [AccRight] FLOAT NOT NULL,
  [Accuracy] FLOAT NOT NULL,
  [BadCuts] INT NOT NULL,
  [BaseScore] INT NOT NULL,
  [BombCuts] INT NOT NULL,
  [BonusPp] FLOAT NOT NULL,
  [CountryRank] INT NOT NULL,
  [FcAccuracy] FLOAT NOT NULL,
  [FcPp] FLOAT NOT NULL,
  [FullCombo] BIT NOT NULL,
  [LeaderboardId] NVARCHAR(255) NOT NULL,
  [MaxCombo] INT NOT NULL,
  [MissedNotes] INT NOT NULL,
  [ModifiedScore] INT NOT NULL,
  [Modifiers] NVARCHAR(MAX),
  [PassPP] FLOAT NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Priority] INT NOT NULL,
  [Qualification] BIT NOT NULL,
  [Rank] INT NOT NULL,
  [TechPP] FLOAT NOT NULL,
  [Timepost] INT NOT NULL,
  [WallsHit] INT NOT NULL,
  [Weight] FLOAT NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([PlayerId], [LeaderboardId])
);

CREATE TABLE [PrestiegeLevels] (
  [Id] INT NOT NULL,
  [BigIcon] NVARCHAR(MAX) NOT NULL,
  [Color] NVARCHAR(MAX) NOT NULL,
  [Level] INT NOT NULL,
  [PrestigeAnimationLink] NVARCHAR(MAX) NOT NULL,
  [SmallIcon] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ProfileSettings] (
  [Id] INT NOT NULL,
  [Bio] NVARCHAR(MAX),
  [EffectName] NVARCHAR(MAX),
  [HorizontalRichBio] BIT NOT NULL,
  [Hue] FLOAT,
  [LeftSaberColor] NVARCHAR(MAX),
  [Message] NVARCHAR(MAX),
  [ProfileAppearance] NVARCHAR(MAX),
  [ProfileCover] NVARCHAR(MAX),
  [RankedMapperSort] NVARCHAR(MAX),
  [RightSaberColor] NVARCHAR(MAX),
  [Saturation] FLOAT,
  [ShowAllRatings] BIT NOT NULL,
  [ShowBots] BIT NOT NULL,
  [ShowExplicitCovers] BIT NOT NULL,
  [ShowStatsPublic] BIT NOT NULL,
  [ShowStatsPublicPinned] BIT NOT NULL,
  [StarredFriends] NVARCHAR(MAX),
  PRIMARY KEY ([Id])
);

CREATE TABLE [PromotionHits] (
  [Id] INT NOT NULL,
  [Details] NVARCHAR(255) NOT NULL,
  [Promotion] INT NOT NULL,
  [Timeset] INT NOT NULL,
  [UniqueId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [QualificationChange] (
  [Id] INT NOT NULL,
  [NewAccRating] FLOAT NOT NULL,
  [NewCriteriaCommentary] NVARCHAR(MAX),
  [NewCriteriaMet] INT NOT NULL,
  [NewModifiersModifierId] INT,
  [NewPassRating] FLOAT NOT NULL,
  [NewRankability] FLOAT NOT NULL,
  [NewStars] FLOAT NOT NULL,
  [NewTechRating] FLOAT NOT NULL,
  [NewType] INT NOT NULL,
  [OldAccRating] FLOAT NOT NULL,
  [OldCriteriaCommentary] NVARCHAR(MAX),
  [OldCriteriaMet] INT NOT NULL,
  [OldModifiersModifierId] INT,
  [OldPassRating] FLOAT NOT NULL,
  [OldRankability] FLOAT NOT NULL,
  [OldStars] FLOAT NOT NULL,
  [OldTechRating] FLOAT NOT NULL,
  [OldType] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [RankQualificationId] INT,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [QualificationCommentary] (
  [Id] INT NOT NULL,
  [DiscordMessageId] NVARCHAR(MAX) NOT NULL,
  [EditTimeset] INT,
  [Edited] BIT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [RankQualificationId] INT,
  [Timeset] INT NOT NULL,
  [Value] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [QualificationVote] (
  [Id] INT NOT NULL,
  [DiscordRTMessageId] NVARCHAR(MAX),
  [EditTimeset] INT,
  [Edited] BIT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [RankQualificationId] INT,
  [Timeset] INT NOT NULL,
  [Value] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [RankQualification] (
  [Id] INT NOT NULL,
  [ApprovalTimeset] INT NOT NULL,
  [Approved] BIT NOT NULL,
  [Approvers] NVARCHAR(MAX),
  [CriteriaCheck] NVARCHAR(MAX),
  [CriteriaChecker] NVARCHAR(MAX),
  [CriteriaCommentary] NVARCHAR(MAX),
  [CriteriaMet] INT NOT NULL,
  [CriteriaTimeset] INT NOT NULL,
  [DiscordChannelId] NVARCHAR(MAX) NOT NULL,
  [DiscordRTChannelId] NVARCHAR(MAX) NOT NULL,
  [MapperAllowed] BIT NOT NULL,
  [MapperId] NVARCHAR(MAX),
  [MapperQualification] BIT NOT NULL,
  [ModifiersModifierId] INT,
  [ModifiersRatingId] INT,
  [QualityVote] INT NOT NULL,
  [RTMember] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [RankUpdate] (
  [Id] INT NOT NULL,
  [CriteriaCommentary] NVARCHAR(MAX),
  [CriteriaMet] INT NOT NULL,
  [Finished] BIT NOT NULL,
  [Keep] BIT NOT NULL,
  [ModifiersModifierId] INT NOT NULL,
  [ModifiersRatingId] INT,
  [PassRating] FLOAT NOT NULL,
  [PredictedAcc] FLOAT NOT NULL,
  [RTMember] NVARCHAR(MAX) NOT NULL,
  [Stars] FLOAT NOT NULL,
  [TechRating] FLOAT NOT NULL,
  [Timeset] INT NOT NULL,
  [Type] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [RankUpdateChange] (
  [Id] INT NOT NULL,
  [NewCriteriaCommentary] NVARCHAR(MAX),
  [NewCriteriaMet] INT NOT NULL,
  [NewKeep] BIT NOT NULL,
  [NewModifiersModifierId] INT,
  [NewStars] FLOAT NOT NULL,
  [NewType] INT NOT NULL,
  [OldCriteriaCommentary] NVARCHAR(MAX),
  [OldCriteriaMet] INT NOT NULL,
  [OldKeep] BIT NOT NULL,
  [OldModifiersModifierId] INT,
  [OldStars] FLOAT NOT NULL,
  [OldType] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [RankUpdateId] INT,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [RankVotings] (
  [ScoreId] INT NOT NULL,
  [Diff] NVARCHAR(MAX) NOT NULL,
  [Hash] NVARCHAR(MAX) NOT NULL,
  [LeaderboardId] NVARCHAR(MAX),
  [Mode] NVARCHAR(MAX) NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Rankability] FLOAT NOT NULL,
  [Stars] FLOAT NOT NULL,
  [Timeset] INT NOT NULL,
  [Type] INT NOT NULL,
  PRIMARY KEY ([ScoreId])
);

CREATE TABLE [WatchingSessions] (
  [Id] INT NOT NULL,
  [IP] NVARCHAR(MAX),
  [Player] NVARCHAR(MAX),
  [ScoreId] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ReservedTags] (
  [Id] INT NOT NULL,
  [Tag] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [SanitizerConfigs] (
  [Id] INT NOT NULL,
  [Type] INT NOT NULL,
  [Value] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ScheduledEventMaps] (
  [Id] INT NOT NULL,
  [EndDate] INT NOT NULL,
  [EventId] INT NOT NULL,
  [SongId] NVARCHAR(MAX) NOT NULL,
  [StartDate] INT NOT NULL,
  [VideoUrl] NVARCHAR(MAX),
  PRIMARY KEY ([Id])
);

CREATE TABLE [Scores] (
  [Id] INT NOT NULL,
  [AccLeft] FLOAT NOT NULL,
  [AccPP] FLOAT NOT NULL,
  [AccRight] FLOAT NOT NULL,
  [Accuracy] FLOAT NOT NULL,
  [AnonimusReplayWatched] INT NOT NULL,
  [AuthorizedReplayWatched] INT NOT NULL,
  [BadCuts] INT NOT NULL,
  [Banned] BIT NOT NULL,
  [BaseScore] INT NOT NULL,
  [BombCuts] INT NOT NULL,
  [BonusPp] FLOAT NOT NULL,
  [Bot] BIT NOT NULL,
  [Controller] INT NOT NULL,
  [Country] NVARCHAR(MAX),
  [CountryRank] INT NOT NULL,
  [Experience] FLOAT NOT NULL,
  [FcAccuracy] FLOAT NOT NULL,
  [FcPp] FLOAT NOT NULL,
  [FullCombo] BIT NOT NULL,
  [HasBFS] BIT NOT NULL,
  [HasBSF] BIT NOT NULL,
  [HasDA] BIT NOT NULL,
  [HasEZ] BIT NOT NULL,
  [HasFS] BIT NOT NULL,
  [HasGN] BIT NOT NULL,
  [HasHD] BIT NOT NULL,
  [HasNA] BIT NOT NULL,
  [HasNB] BIT NOT NULL,
  [HasNF] BIT NOT NULL,
  [HasNO] BIT NOT NULL,
  [HasOHP] BIT NOT NULL,
  [HasOP] BIT NOT NULL,
  [HasPM] BIT NOT NULL,
  [HasSA] BIT NOT NULL,
  [HasSC] BIT NOT NULL,
  [HasSF] BIT NOT NULL,
  [HasSMC] BIT NOT NULL,
  [HasSS] BIT NOT NULL,
  [HashId] NVARCHAR(255),
  [Hmd] INT NOT NULL,
  [IgnoreForStats] BIT NOT NULL,
  [LastTryTime] INT NOT NULL,
  [LeaderboardId] NVARCHAR(255) NOT NULL,
  [LeftHanded] BIT NOT NULL,
  [LeftTiming] FLOAT NOT NULL,
  [MaxCombo] INT NOT NULL,
  [MaxStreak] INT,
  [MetadataId] INT,
  [Migrated] BIT NOT NULL,
  [MissedNotes] INT NOT NULL,
  [Mistakes] INT NOT NULL,
  [ModifiedScore] INT NOT NULL,
  [ModifiedStars] FLOAT NOT NULL,
  [Modifiers] NVARCHAR(MAX),
  [PassPP] FLOAT NOT NULL,
  [Pauses] INT NOT NULL,
  [Platform] NVARCHAR(MAX) NOT NULL,
  [PlayCount] INT NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Priority] INT NOT NULL,
  [Qualification] BIT NOT NULL,
  [Rank] INT NOT NULL,
  [Replay] NVARCHAR(255),
  [ReplayOffsetsId] INT,
  [ReplayWatchedTotal] INT NOT NULL,
  [RightTiming] FLOAT NOT NULL,
  [ScoreImprovementId] INT,
  [SotwNominations] INT NOT NULL,
  [Speed] FLOAT NOT NULL,
  [Status] INT NOT NULL,
  [Suspicious] BIT NOT NULL,
  [TechPP] FLOAT NOT NULL,
  [Timepost] INT NOT NULL,
  [Timeset] NVARCHAR(MAX),
  [ValidContexts] INT NOT NULL,
  [ValidForGeneral] BIT NOT NULL,
  [WallsHit] INT NOT NULL,
  [Weight] FLOAT NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([PlayerId], [LeaderboardId], [ValidContexts])
);

CREATE TABLE [ScoreContextExtensions] (
  [Id] INT NOT NULL,
  [AccLeft] FLOAT NOT NULL,
  [AccPP] FLOAT NOT NULL,
  [AccRight] FLOAT NOT NULL,
  [Accuracy] FLOAT NOT NULL,
  [Banned] BIT NOT NULL,
  [BaseScore] INT NOT NULL,
  [BonusPp] FLOAT NOT NULL,
  [Bot] BIT NOT NULL,
  [Context] INT NOT NULL,
  [FcAccuracy] FLOAT NOT NULL,
  [FcPp] FLOAT NOT NULL,
  [HasBFS] BIT NOT NULL,
  [HasBSF] BIT NOT NULL,
  [HasDA] BIT NOT NULL,
  [HasEZ] BIT NOT NULL,
  [HasFS] BIT NOT NULL,
  [HasGN] BIT NOT NULL,
  [HasHD] BIT NOT NULL,
  [HasNA] BIT NOT NULL,
  [HasNB] BIT NOT NULL,
  [HasNF] BIT NOT NULL,
  [HasNO] BIT NOT NULL,
  [HasOHP] BIT NOT NULL,
  [HasOP] BIT NOT NULL,
  [HasPM] BIT NOT NULL,
  [HasSA] BIT NOT NULL,
  [HasSC] BIT NOT NULL,
  [HasSF] BIT NOT NULL,
  [HasSMC] BIT NOT NULL,
  [HasSS] BIT NOT NULL,
  [LeaderboardId] NVARCHAR(255) NOT NULL,
  [ModifiedScore] INT NOT NULL,
  [ModifiedStars] FLOAT NOT NULL,
  [Modifiers] NVARCHAR(MAX),
  [PassPP] FLOAT NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Priority] INT NOT NULL,
  [Qualification] BIT NOT NULL,
  [Rank] INT NOT NULL,
  [ScoreId] INT,
  [ScoreImprovementId] INT,
  [TechPP] FLOAT NOT NULL,
  [Timepost] INT NOT NULL,
  [Weight] FLOAT NOT NULL,
  PRIMARY KEY ([Id]),
  UNIQUE ([PlayerId], [LeaderboardId], [Context])
);

CREATE TABLE [ScoreExternalStatus] (
  [Id] INT NOT NULL,
  [Link] NVARCHAR(MAX),
  [LinkService] NVARCHAR(MAX),
  [LinkServiceIcon] NVARCHAR(MAX),
  [ScoreId] INT,
  [Status] INT NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ScoreImprovement] (
  [Id] INT NOT NULL,
  [AccLeft] FLOAT NOT NULL,
  [AccRight] FLOAT NOT NULL,
  [Accuracy] FLOAT NOT NULL,
  [AverageRankedAccuracy] FLOAT NOT NULL,
  [BadCuts] INT NOT NULL,
  [BombCuts] INT NOT NULL,
  [BonusPp] FLOAT NOT NULL,
  [MissedNotes] INT NOT NULL,
  [Modifiers] NVARCHAR(255) NOT NULL,
  [Pauses] INT NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Rank] INT NOT NULL,
  [Score] INT NOT NULL,
  [Timeset] NVARCHAR(MAX) NOT NULL,
  [TotalPp] FLOAT NOT NULL,
  [TotalRank] INT NOT NULL,
  [WallsHit] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ScoreMetadata] (
  [Id] INT NOT NULL,
  [Description] NVARCHAR(MAX),
  [HighlightedInfo] INT NOT NULL,
  [Link] NVARCHAR(MAX),
  [LinkService] NVARCHAR(MAX),
  [LinkServiceIcon] NVARCHAR(MAX),
  [PinnedContexts] INT NOT NULL,
  [Priority] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ScoreNominations] (
  [Id] INT NOT NULL,
  [Description] NVARCHAR(MAX),
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [ScoreId] INT NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ScoreRedirects] (
  [Id] INT NOT NULL,
  [NewScoreId] INT NOT NULL,
  [OldScoreId] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ScoreRemovalLogs] (
  [Id] INT NOT NULL,
  [AdminId] NVARCHAR(MAX) NOT NULL,
  [Replay] NVARCHAR(MAX) NOT NULL,
  [Timestamp] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Songs] (
  [Id] NVARCHAR(255) NOT NULL,
  [Author] NVARCHAR(MAX) NOT NULL,
  [Bpm] FLOAT NOT NULL,
  [Checked] BIT NOT NULL,
  [CollaboratorIds] NVARCHAR(MAX),
  [CoverImage] NVARCHAR(MAX) NOT NULL,
  [Description] NVARCHAR(MAX),
  [DownloadUrl] NVARCHAR(MAX) NOT NULL,
  [Duration] FLOAT NOT NULL,
  [Explicity] INT NOT NULL,
  [FullCoverImage] NVARCHAR(MAX),
  [Hash] NVARCHAR(255) NOT NULL,
  [IdolDescriptionId] INT,
  [IsBeastSaberAwarded] BIT NOT NULL,
  [IsBuildingBlocksAwarded] BIT NOT NULL,
  [IsCurated] BIT NOT NULL,
  [IsFeaturedOnCC] BIT NOT NULL,
  [IsMapOfTheWeek] BIT NOT NULL,
  [IsNoodleMonday] BIT NOT NULL,
  [LowerHash] NVARCHAR(255) NOT NULL,
  [MapCreator] INT NOT NULL,
  [MapVersion] NVARCHAR(255),
  [Mapper] NVARCHAR(MAX) NOT NULL,
  [MapperId] INT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [Refreshed] BIT NOT NULL,
  [Status] INT NOT NULL,
  [SubName] NVARCHAR(MAX),
  [Tags] NVARCHAR(MAX),
  [UploadTime] INT NOT NULL,
  [VideoPreviewUrl] NVARCHAR(MAX),
  PRIMARY KEY ([Id]),
  UNIQUE ([Hash]),
  UNIQUE ([LowerHash])
);

CREATE TABLE [SongSearches] (
  [Id] INT NOT NULL,
  [Score] INT NOT NULL,
  [SearchId] INT NOT NULL,
  [SongId] NVARCHAR(255),
  PRIMARY KEY ([Id])
);

CREATE TABLE [SongSuggestRefreshes] (
  [Id] INT NOT NULL,
  [File] NVARCHAR(MAX) NOT NULL,
  [SongsFile] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [SongsLastUpdateTimes] (
  [Id] INT NOT NULL,
  [Date] DATETIME NOT NULL,
  [Status] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Speedruns] (
  [Id] INT NOT NULL,
  [FinishTimeset] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Pp] FLOAT NOT NULL,
  [Record] BIT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [SurveyResponses] (
  [Id] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [SurveyId] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [TreeChampions] (
  [Id] INT NOT NULL,
  [BundleId] INT NOT NULL,
  [Day] INT NOT NULL,
  [Diffs] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [TreeMaps] (
  [Id] INT NOT NULL,
  [BundleId] INT NOT NULL,
  [SongId] NVARCHAR(MAX) NOT NULL,
  [Timestart] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [TreeOrnaments] (
  [Id] INT NOT NULL,
  [BundleId] INT NOT NULL,
  [Description] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [Users] (
  [Id] NVARCHAR(255) NOT NULL,
  [PlayerId] NVARCHAR(255) NOT NULL,
  [PlaylistsToInstall] NVARCHAR(MAX),
  PRIMARY KEY ([Id])
);

CREATE TABLE [UsernamePfpChangeBans] (
  [Id] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [VRControllers] (
  [Id] INT NOT NULL,
  [Name] NVARCHAR(MAX) NOT NULL,
  [Player] NVARCHAR(MAX) NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [VoterFeedback] (
  [Id] INT NOT NULL,
  [RTMember] NVARCHAR(MAX) NOT NULL,
  [RankVotingScoreId] INT,
  [Value] FLOAT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [WatermarkRequests] (
  [Id] INT NOT NULL,
  [PlayerId] NVARCHAR(MAX) NOT NULL,
  [Reason] NVARCHAR(MAX) NOT NULL,
  [Status] INT NOT NULL,
  [Timeset] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [ClanFeaturedPlaylist] (
  [ClansId] INT NOT NULL,
  [FeaturedPlaylistsId] INT NOT NULL,
  PRIMARY KEY ([ClansId], [FeaturedPlaylistsId])
);

CREATE TABLE [ClanPlayer] (
  [ClansId] INT NOT NULL,
  [PlayersId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([ClansId], [PlayersId])
);

CREATE TABLE [ClanUser] (
  [BannedClansId] INT NOT NULL,
  [BannedId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([BannedClansId], [BannedId])
);

CREATE TABLE [ClanUser1] (
  [ClanRequestId] INT NOT NULL,
  [RequestsId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([ClanRequestId], [RequestsId])
);

CREATE TABLE [EventPlayerMapOfTheDay] (
  [ChampionsId] INT NOT NULL,
  [MapOfTheDaysId] INT NOT NULL,
  PRIMARY KEY ([ChampionsId], [MapOfTheDaysId])
);

CREATE TABLE [EventRankingLeaderboard] (
  [EventsId] INT NOT NULL,
  [LeaderboardsId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([EventsId], [LeaderboardsId])
);

CREATE TABLE [FeaturedPlaylistLeaderboard] (
  [FeaturedPlaylistsId] INT NOT NULL,
  [LeaderboardsId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([FeaturedPlaylistsId], [LeaderboardsId])
);

CREATE TABLE [MapperSong] (
  [MappersId] INT NOT NULL,
  [SongsId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([MappersId], [SongsId])
);

CREATE TABLE [OpenIddictApplications] (
  [Id] NVARCHAR(255) NOT NULL,
  [ApplicationType] NVARCHAR(255),
  [ClientId] NVARCHAR(255),
  [ClientSecret] NVARCHAR(MAX),
  [ClientType] NVARCHAR(255),
  [ConcurrencyToken] NVARCHAR(255),
  [ConsentType] NVARCHAR(255),
  [DeveloperProfileId] INT,
  [DisplayName] NVARCHAR(MAX),
  [DisplayNames] NVARCHAR(MAX),
  [JsonWebKeySet] NVARCHAR(MAX),
  [Permissions] NVARCHAR(MAX),
  [PostLogoutRedirectUris] NVARCHAR(MAX),
  [Properties] NVARCHAR(MAX),
  [RedirectUris] NVARCHAR(MAX),
  [Requirements] NVARCHAR(MAX),
  [Settings] NVARCHAR(MAX),
  PRIMARY KEY ([Id]),
  UNIQUE ([ClientId])
);

CREATE TABLE [OpenIddictTokens] (
  [Id] NVARCHAR(255) NOT NULL,
  [ApplicationId] NVARCHAR(255),
  [ConcurrencyToken] NVARCHAR(255),
  [CreationDate] DATETIME,
  [ExpirationDate] DATETIME,
  [Payload] NVARCHAR(MAX),
  [Properties] NVARCHAR(MAX),
  [RedemptionDate] DATETIME,
  [ReferenceId] NVARCHAR(255),
  [Status] NVARCHAR(255),
  [Subject] NVARCHAR(255),
  [Type] NVARCHAR(255),
  PRIMARY KEY ([Id]),
  UNIQUE ([ReferenceId])
);

CREATE TABLE [PlayerPlayerFriends] (
  [FriendsId] NVARCHAR(255) NOT NULL,
  [PlayerFriendsId] NVARCHAR(255) NOT NULL,
  PRIMARY KEY ([FriendsId], [PlayerFriendsId])
);

CREATE TABLE [ReplayOffsets] (
  [Id] INT NOT NULL,
  [CustomData] INT NOT NULL,
  [Frames] INT NOT NULL,
  [Heights] INT NOT NULL,
  [Notes] INT NOT NULL,
  [Pauses] INT NOT NULL,
  [SaberOffsets] INT NOT NULL,
  [Walls] INT NOT NULL,
  PRIMARY KEY ([Id])
);

CREATE TABLE [BugReports] (
  [ActualBehavior] NVARCHAR(MAX),
  [ExpectedBehavior] NVARCHAR(MAX),
  [IsReproducible] BIT,
  [LogContent] NVARCHAR(MAX),
  [Platform] NVARCHAR(255),
  [Severity] INT NOT NULL,
  [StepsToReproduce] NVARCHAR(MAX),
  [Version] NVARCHAR(255)
);

CREATE TABLE [HelpRequests] (
  [AlreadyTried] NVARCHAR(MAX),
  [Category] INT NOT NULL,
  [ErrorMessage] NVARCHAR(MAX),
  [IsResolved] BIT NOT NULL,
  [Platform] NVARCHAR(255),
  [Resolution] NVARCHAR(MAX),
  [Urgency] INT NOT NULL,
  [UserResolvedAt] INT,
  [Version] NVARCHAR(255)
);

CREATE TABLE [Suggestions] (
  [Alternatives] NVARCHAR(MAX),
  [Category] INT NOT NULL,
  [Impact] NVARCHAR(255),
  [ProposedSolution] NVARCHAR(MAX),
  [TargetArea] NVARCHAR(255),
  [UseCase] NVARCHAR(MAX)
);

CREATE INDEX [idx_Achievements_AchievementDescriptionId_1] ON [Achievements] ([AchievementDescriptionId]);

CREATE INDEX [idx_Achievements_LevelId_2] ON [Achievements] ([LevelId]);

CREATE INDEX [idx_Achievements_PlayerId_3] ON [Achievements] ([PlayerId]);

CREATE INDEX [idx_AchievementLevels_AchievementDescriptionId_1] ON [AchievementLevels] ([AchievementDescriptionId]);

CREATE INDEX [idx_Badges_PlayerId_1] ON [Badges] ([PlayerId]);

CREATE INDEX [idx_ClanManagers_ClanId_1] ON [ClanManagers] ([ClanId]);

CREATE INDEX [idx_ClanManagers_PlayerId_2] ON [ClanManagers] ([PlayerId]);

CREATE INDEX [idx_ClanRanking_ClanId_1] ON [ClanRanking] ([ClanId]);

CREATE INDEX [idx_ClanRanking_LeaderboardId_2] ON [ClanRanking] ([LeaderboardId]);

CREATE INDEX [idx_ClanUpdates_ClanId_1] ON [ClanUpdates] ([ClanId]);

CREATE INDEX [idx_ClanUpdates_PlayerId_2] ON [ClanUpdates] ([PlayerId]);

CREATE INDEX [idx_CriteriaCommentary_RankQualificationId_1] ON [CriteriaCommentary] ([RankQualificationId]);

CREATE INDEX [idx_DifficultyDescription_DifficultyStatisticsId_1] ON [DifficultyDescription] ([DifficultyStatisticsId]);

CREATE INDEX [idx_DifficultyDescription_MaxScoreGraphId_2] ON [DifficultyDescription] ([MaxScoreGraphId]);

CREATE INDEX [idx_DifficultyDescription_ModifierValuesModifierId_3] ON [DifficultyDescription] ([ModifierValuesModifierId]);

CREATE INDEX [idx_DifficultyDescription_ModifiersRatingId_4] ON [DifficultyDescription] ([ModifiersRatingId]);

CREATE INDEX [idx_DifficultyDescription_SongId_5] ON [DifficultyDescription] ([SongId]);

CREATE INDEX [idx_DifficultyDescription_Status_6] ON [DifficultyDescription] ([Status]);

CREATE INDEX [idx_DifficultyDescription_Hash_ModeName_DifficultyName_7] ON [DifficultyDescription] ([Hash], [ModeName], [DifficultyName]);

CREATE INDEX [idx_DifficultyDescriptionExtension_DifficultyDescriptionId_1] ON [DifficultyDescriptionExtension] ([DifficultyDescriptionId]);

CREATE INDEX [idx_EventPlayer_EventRankingId_1] ON [EventPlayer] ([EventRankingId]);

CREATE INDEX [idx_EventPlayer_PlayerId_2] ON [EventPlayer] ([PlayerId]);

CREATE INDEX [idx_EventRankings_FeaturedPlaylistId_1] ON [EventRankings] ([FeaturedPlaylistId]);

CREATE INDEX [idx_ExternalStatus_SongId_1] ON [ExternalStatus] ([SongId]);

CREATE INDEX [idx_FailedScores_LeaderboardId_1] ON [FailedScores] ([LeaderboardId]);

CREATE INDEX [idx_FailedScores_PlayerId_2] ON [FailedScores] ([PlayerId]);

CREATE INDEX [idx_FavoriteMaps_LeaderboardId_1] ON [FavoriteMaps] ([LeaderboardId]);

CREATE INDEX [idx_FavoriteMaps_PlayerId_2] ON [FavoriteMaps] ([PlayerId]);

CREATE INDEX [idx_GlobalMapHistory_ClanId_1] ON [GlobalMapHistory] ([ClanId]);

CREATE INDEX [idx_IdolDecorations_SongId_1] ON [IdolDecorations] ([SongId]);

CREATE INDEX [idx_Leaderboards_ClanId_1] ON [Leaderboards] ([ClanId]);

CREATE INDEX [idx_Leaderboards_DifficultyId_2] ON [Leaderboards] ([DifficultyId]);

CREATE INDEX [idx_Leaderboards_LeaderboardGroupId_3] ON [Leaderboards] ([LeaderboardGroupId]);

CREATE INDEX [idx_Leaderboards_MapOfTheDayId_4] ON [Leaderboards] ([MapOfTheDayId]);

CREATE INDEX [idx_Leaderboards_QualificationId_5] ON [Leaderboards] ([QualificationId]);

CREATE INDEX [idx_Leaderboards_ReweightId_6] ON [Leaderboards] ([ReweightId]);

CREATE INDEX [idx_Leaderboards_SongId_7] ON [Leaderboards] ([SongId]);

CREATE INDEX [idx_LeaderboardChange_LeaderboardId_1] ON [LeaderboardChange] ([LeaderboardId]);

CREATE INDEX [idx_LeaderboardChange_NewModifiersModifierId_2] ON [LeaderboardChange] ([NewModifiersModifierId]);

CREATE INDEX [idx_LeaderboardChange_NewModifiersRatingId_3] ON [LeaderboardChange] ([NewModifiersRatingId]);

CREATE INDEX [idx_LeaderboardChange_OldModifiersModifierId_4] ON [LeaderboardChange] ([OldModifiersModifierId]);

CREATE INDEX [idx_LeaderboardChange_OldModifiersRatingId_5] ON [LeaderboardChange] ([OldModifiersRatingId]);

CREATE INDEX [idx_MapOfTheDay_EventRankingId_1] ON [MapOfTheDay] ([EventRankingId]);

CREATE INDEX [idx_MapOfTheDay_SongId_2] ON [MapOfTheDay] ([SongId]);

CREATE INDEX [idx_MapOfTheDayPoints_EventPlayerId_1] ON [MapOfTheDayPoints] ([EventPlayerId]);

CREATE INDEX [idx_MapOfTheDayPoints_MapOfTheDayId_2] ON [MapOfTheDayPoints] ([MapOfTheDayId]);

CREATE INDEX [idx_MapSwingData_DifficultyStatisticsId_1] ON [MapSwingData] ([DifficultyStatisticsId]);

CREATE INDEX [idx_ModDescription_DeveloperProfileId_1] ON [ModDescription] ([DeveloperProfileId]);

CREATE INDEX [idx_Players_Banned_1] ON [Players] ([Banned]);

CREATE INDEX [idx_Players_DeveloperProfileId_2] ON [Players] ([DeveloperProfileId]);

CREATE INDEX [idx_Players_PatreonFeaturesId_3] ON [Players] ([PatreonFeaturesId]);

CREATE INDEX [idx_Players_ProfileSettingsId_4] ON [Players] ([ProfileSettingsId]);

CREATE INDEX [idx_Players_Rank_5] ON [Players] ([Rank]);

CREATE INDEX [idx_Players_ScoreStatsId_6] ON [Players] ([ScoreStatsId]);

CREATE INDEX [idx_Players_TopClanId_7] ON [Players] ([TopClanId]);

CREATE INDEX [idx_Players_Banned_Pp_ScoreStatsId_8] ON [Players] ([Banned], [Pp], [ScoreStatsId]);

CREATE INDEX [idx_Players_Id_Alias_OldAlias_9] ON [Players] ([Id], [Alias], [OldAlias]);

CREATE INDEX [idx_PlayerBonusIdols_IdolDescriptionId_1] ON [PlayerBonusIdols] ([IdolDescriptionId]);

CREATE INDEX [idx_PlayerBonusIdols_PlayerId_2] ON [PlayerBonusIdols] ([PlayerId]);

CREATE INDEX [idx_PlayerChange_PlayerId_1] ON [PlayerChange] ([PlayerId]);

CREATE INDEX [idx_PlayerContextExtensions_ScoreStatsId_1] ON [PlayerContextExtensions] ([ScoreStatsId]);

CREATE INDEX [idx_PlayerIdolDecorations_IdolDecorationId_1] ON [PlayerIdolDecorations] ([IdolDecorationId]);

CREATE INDEX [idx_PlayerIdolDecorations_PlayerId_2] ON [PlayerIdolDecorations] ([PlayerId]);

CREATE INDEX [idx_Stats_LastRankedScoreTime_1] ON [Stats] ([LastRankedScoreTime]);

CREATE INDEX [idx_Stats_RankedPlayCount_2] ON [Stats] ([RankedPlayCount]);

CREATE INDEX [idx_PlayerSearches_PlayerId_1] ON [PlayerSearches] ([PlayerId]);

CREATE INDEX [idx_PlayerSocial_PlayerId_1] ON [PlayerSocial] ([PlayerId]);

CREATE INDEX [idx_PlayerTreeOrnaments_OrnamentId_1] ON [PlayerTreeOrnaments] ([OrnamentId]);

CREATE INDEX [idx_PlayerTreeOrnaments_PlayerId_2] ON [PlayerTreeOrnaments] ([PlayerId]);

CREATE INDEX [idx_PlayerTreeOrnaments_ScoreId_3] ON [PlayerTreeOrnaments] ([ScoreId]);

CREATE INDEX [idx_Playlists_UserId_1] ON [Playlists] ([UserId]);

CREATE INDEX [idx_PredictedScores_Accuracy_1] ON [PredictedScores] ([Accuracy]);

CREATE INDEX [idx_PredictedScores_LeaderboardId_2] ON [PredictedScores] ([LeaderboardId]);

CREATE INDEX [idx_PredictedScores_PlayerId_3] ON [PredictedScores] ([PlayerId]);

CREATE INDEX [idx_PredictedScores_Pp_4] ON [PredictedScores] ([Pp]);

CREATE INDEX [idx_PredictedScores_Timepost_5] ON [PredictedScores] ([Timepost]);

CREATE INDEX [idx_PredictedScores_Qualification_Pp_6] ON [PredictedScores] ([Qualification], [Pp]);

CREATE INDEX [idx_PredictedScores_PlayerId_Qualification_Pp_7] ON [PredictedScores] ([PlayerId], [Qualification], [Pp]);

CREATE INDEX [idx_QualificationChange_NewModifiersModifierId_1] ON [QualificationChange] ([NewModifiersModifierId]);

CREATE INDEX [idx_QualificationChange_OldModifiersModifierId_2] ON [QualificationChange] ([OldModifiersModifierId]);

CREATE INDEX [idx_QualificationChange_RankQualificationId_3] ON [QualificationChange] ([RankQualificationId]);

CREATE INDEX [idx_QualificationCommentary_RankQualificationId_1] ON [QualificationCommentary] ([RankQualificationId]);

CREATE INDEX [idx_QualificationVote_RankQualificationId_1] ON [QualificationVote] ([RankQualificationId]);

CREATE INDEX [idx_RankQualification_ModifiersModifierId_1] ON [RankQualification] ([ModifiersModifierId]);

CREATE INDEX [idx_RankQualification_ModifiersRatingId_2] ON [RankQualification] ([ModifiersRatingId]);

CREATE INDEX [idx_RankUpdate_ModifiersModifierId_1] ON [RankUpdate] ([ModifiersModifierId]);

CREATE INDEX [idx_RankUpdate_ModifiersRatingId_2] ON [RankUpdate] ([ModifiersRatingId]);

CREATE INDEX [idx_RankUpdateChange_NewModifiersModifierId_1] ON [RankUpdateChange] ([NewModifiersModifierId]);

CREATE INDEX [idx_RankUpdateChange_OldModifiersModifierId_2] ON [RankUpdateChange] ([OldModifiersModifierId]);

CREATE INDEX [idx_RankUpdateChange_RankUpdateId_3] ON [RankUpdateChange] ([RankUpdateId]);

CREATE INDEX [idx_WatchingSessions_ScoreId_1] ON [WatchingSessions] ([ScoreId]);

CREATE INDEX [idx_Scores_Accuracy_1] ON [Scores] ([Accuracy]);

CREATE INDEX [idx_Scores_MetadataId_2] ON [Scores] ([MetadataId]);

CREATE INDEX [idx_Scores_PlayerId_3] ON [Scores] ([PlayerId]);

CREATE INDEX [idx_Scores_Pp_4] ON [Scores] ([Pp]);

CREATE INDEX [idx_Scores_ReplayOffsetsId_5] ON [Scores] ([ReplayOffsetsId]);

CREATE INDEX [idx_Scores_ScoreImprovementId_6] ON [Scores] ([ScoreImprovementId]);

CREATE INDEX [idx_Scores_Timepost_7] ON [Scores] ([Timepost]);

CREATE INDEX [idx_Scores_Timepost_Replay_8] ON [Scores] ([Timepost], [Replay]);

CREATE INDEX [idx_Scores_Banned_Qualification_Pp_9] ON [Scores] ([Banned], [Qualification], [Pp]);

CREATE INDEX [idx_Scores_LeaderboardId_Banned_ValidForGeneral_10] ON [Scores] ([LeaderboardId], [Banned], [ValidForGeneral]);

CREATE INDEX [idx_Scores_PlayerId_LeaderboardId_ValidForGeneral_11] ON [Scores] ([PlayerId], [LeaderboardId], [ValidForGeneral]);

CREATE INDEX [idx_Scores_PlayerId_Banned_Qualification_Pp_12] ON [Scores] ([PlayerId], [Banned], [Qualification], [Pp]);

CREATE INDEX [idx_Scores_PlayerId_Banned_ValidForGeneral_Pp_Timepost_13] ON [Scores] ([PlayerId], [Banned], [ValidForGeneral], [Pp], [Timepost]);

CREATE INDEX [idx_ScoreContextExtensions_LeaderboardId_1] ON [ScoreContextExtensions] ([LeaderboardId]);

CREATE INDEX [idx_ScoreContextExtensions_ScoreId_2] ON [ScoreContextExtensions] ([ScoreId]);

CREATE INDEX [idx_ScoreContextExtensions_ScoreImprovementId_3] ON [ScoreContextExtensions] ([ScoreImprovementId]);

CREATE INDEX [idx_ScoreExternalStatus_ScoreId_1] ON [ScoreExternalStatus] ([ScoreId]);

CREATE INDEX [idx_Songs_IdolDescriptionId_1] ON [Songs] ([IdolDescriptionId]);

CREATE INDEX [idx_Songs_UploadTime_2] ON [Songs] ([UploadTime]);

CREATE INDEX [idx_SongSearches_SongId_1] ON [SongSearches] ([SongId]);

CREATE INDEX [idx_Users_PlayerId_1] ON [Users] ([PlayerId]);

CREATE INDEX [idx_VoterFeedback_RankVotingScoreId_1] ON [VoterFeedback] ([RankVotingScoreId]);

CREATE INDEX [idx_ClanFeaturedPlaylist_FeaturedPlaylistsId_1] ON [ClanFeaturedPlaylist] ([FeaturedPlaylistsId]);

CREATE INDEX [idx_ClanPlayer_PlayersId_1] ON [ClanPlayer] ([PlayersId]);

CREATE INDEX [idx_ClanUser_BannedId_1] ON [ClanUser] ([BannedId]);

CREATE INDEX [idx_ClanUser1_RequestsId_1] ON [ClanUser1] ([RequestsId]);

CREATE INDEX [idx_EventPlayerMapOfTheDay_MapOfTheDaysId_1] ON [EventPlayerMapOfTheDay] ([MapOfTheDaysId]);

CREATE INDEX [idx_EventRankingLeaderboard_LeaderboardsId_1] ON [EventRankingLeaderboard] ([LeaderboardsId]);

CREATE INDEX [idx_FeaturedPlaylistLeaderboard_LeaderboardsId_1] ON [FeaturedPlaylistLeaderboard] ([LeaderboardsId]);

CREATE INDEX [idx_MapperSong_SongsId_1] ON [MapperSong] ([SongsId]);

CREATE INDEX [idx_OpenIddictApplications_DeveloperProfileId_1] ON [OpenIddictApplications] ([DeveloperProfileId]);

CREATE INDEX [idx_OpenIddictTokens_ApplicationId_Status_Subject_Type_2] ON [OpenIddictTokens] ([ApplicationId], [Status], [Subject], [Type]);

CREATE INDEX [idx_PlayerPlayerFriends_PlayerFriendsId_1] ON [PlayerPlayerFriends] ([PlayerFriendsId]);

ALTER TABLE [Achievements] ADD CONSTRAINT [fk_Achievements_AchievementDescriptionId_1] FOREIGN KEY ([AchievementDescriptionId]) REFERENCES [AchievementDescriptions] ([Id]);

ALTER TABLE [Achievements] ADD CONSTRAINT [fk_Achievements_LevelId_2] FOREIGN KEY ([LevelId]) REFERENCES [AchievementLevels] ([Id]);

ALTER TABLE [Achievements] ADD CONSTRAINT [fk_Achievements_PlayerId_3] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [AchievementLevels] ADD CONSTRAINT [fk_AchievementLevels_AchievementDescriptionId_1] FOREIGN KEY ([AchievementDescriptionId]) REFERENCES [AchievementDescriptions] ([Id]);

ALTER TABLE [Badges] ADD CONSTRAINT [fk_Badges_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [ClanManagers] ADD CONSTRAINT [fk_ClanManagers_ClanId_1] FOREIGN KEY ([ClanId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanManagers] ADD CONSTRAINT [fk_ClanManagers_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [ClanRanking] ADD CONSTRAINT [fk_ClanRanking_ClanId_1] FOREIGN KEY ([ClanId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanRanking] ADD CONSTRAINT [fk_ClanRanking_LeaderboardId_2] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [ClanUpdates] ADD CONSTRAINT [fk_ClanUpdates_ClanId_1] FOREIGN KEY ([ClanId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanUpdates] ADD CONSTRAINT [fk_ClanUpdates_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [CriteriaCommentary] ADD CONSTRAINT [fk_CriteriaCommentary_RankQualificationId_1] FOREIGN KEY ([RankQualificationId]) REFERENCES [RankQualification] ([Id]);

ALTER TABLE [DifficultyDescription] ADD CONSTRAINT [fk_DifficultyDescription_DifficultyStatisticsId_1] FOREIGN KEY ([DifficultyStatisticsId]) REFERENCES [DifficultyStatistics] ([Id]);

ALTER TABLE [DifficultyDescription] ADD CONSTRAINT [fk_DifficultyDescription_MaxScoreGraphId_2] FOREIGN KEY ([MaxScoreGraphId]) REFERENCES [MaxScoreGraph] ([Id]);

ALTER TABLE [DifficultyDescription] ADD CONSTRAINT [fk_DifficultyDescription_ModifierValuesModifierId_3] FOREIGN KEY ([ModifierValuesModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [DifficultyDescription] ADD CONSTRAINT [fk_DifficultyDescription_ModifiersRatingId_4] FOREIGN KEY ([ModifiersRatingId]) REFERENCES [ModifiersRating] ([Id]);

ALTER TABLE [DifficultyDescription] ADD CONSTRAINT [fk_DifficultyDescription_SongId_5] FOREIGN KEY ([SongId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [DifficultyDescriptionExtension] ADD CONSTRAINT [fk_DifficultyDescriptionExtension_DifficultyDescriptionId_1] FOREIGN KEY ([DifficultyDescriptionId]) REFERENCES [DifficultyDescription] ([Id]);

ALTER TABLE [EarthDayMaps] ADD CONSTRAINT [fk_EarthDayMaps_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [EventPlayer] ADD CONSTRAINT [fk_EventPlayer_EventRankingId_1] FOREIGN KEY ([EventRankingId]) REFERENCES [EventRankings] ([Id]);

ALTER TABLE [EventPlayer] ADD CONSTRAINT [fk_EventPlayer_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [EventRankings] ADD CONSTRAINT [fk_EventRankings_FeaturedPlaylistId_1] FOREIGN KEY ([FeaturedPlaylistId]) REFERENCES [FeaturedPlaylist] ([Id]);

ALTER TABLE [ExternalStatus] ADD CONSTRAINT [fk_ExternalStatus_SongId_1] FOREIGN KEY ([SongId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [FailedScores] ADD CONSTRAINT [fk_FailedScores_LeaderboardId_1] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [FailedScores] ADD CONSTRAINT [fk_FailedScores_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [FavoriteMaps] ADD CONSTRAINT [fk_FavoriteMaps_LeaderboardId_1] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [FavoriteMaps] ADD CONSTRAINT [fk_FavoriteMaps_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [FavoriteMaps] ADD CONSTRAINT [fk_FavoriteMaps_RankVotingId_3] FOREIGN KEY ([RankVotingId]) REFERENCES [RankVotings] ([ScoreId]);

ALTER TABLE [GlobalMapHistory] ADD CONSTRAINT [fk_GlobalMapHistory_ClanId_1] FOREIGN KEY ([ClanId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [IdolCanvases] ADD CONSTRAINT [fk_IdolCanvases_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [IdolDecorations] ADD CONSTRAINT [fk_IdolDecorations_SongId_1] FOREIGN KEY ([SongId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_ClanId_1] FOREIGN KEY ([ClanId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_DifficultyId_2] FOREIGN KEY ([DifficultyId]) REFERENCES [DifficultyDescription] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_LeaderboardGroupId_3] FOREIGN KEY ([LeaderboardGroupId]) REFERENCES [LeaderboardGroup] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_MapOfTheDayId_4] FOREIGN KEY ([MapOfTheDayId]) REFERENCES [MapOfTheDay] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_QualificationId_5] FOREIGN KEY ([QualificationId]) REFERENCES [RankQualification] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_ReweightId_6] FOREIGN KEY ([ReweightId]) REFERENCES [RankUpdate] ([Id]);

ALTER TABLE [Leaderboards] ADD CONSTRAINT [fk_Leaderboards_SongId_7] FOREIGN KEY ([SongId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [LeaderboardChange] ADD CONSTRAINT [fk_LeaderboardChange_LeaderboardId_1] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [LeaderboardChange] ADD CONSTRAINT [fk_LeaderboardChange_NewModifiersModifierId_2] FOREIGN KEY ([NewModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [LeaderboardChange] ADD CONSTRAINT [fk_LeaderboardChange_NewModifiersRatingId_3] FOREIGN KEY ([NewModifiersRatingId]) REFERENCES [ModifiersRating] ([Id]);

ALTER TABLE [LeaderboardChange] ADD CONSTRAINT [fk_LeaderboardChange_OldModifiersModifierId_4] FOREIGN KEY ([OldModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [LeaderboardChange] ADD CONSTRAINT [fk_LeaderboardChange_OldModifiersRatingId_5] FOREIGN KEY ([OldModifiersRatingId]) REFERENCES [ModifiersRating] ([Id]);

ALTER TABLE [MapOfTheDay] ADD CONSTRAINT [fk_MapOfTheDay_EventRankingId_1] FOREIGN KEY ([EventRankingId]) REFERENCES [EventRankings] ([Id]);

ALTER TABLE [MapOfTheDay] ADD CONSTRAINT [fk_MapOfTheDay_SongId_2] FOREIGN KEY ([SongId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [MapOfTheDayPoints] ADD CONSTRAINT [fk_MapOfTheDayPoints_EventPlayerId_1] FOREIGN KEY ([EventPlayerId]) REFERENCES [EventPlayer] ([Id]);

ALTER TABLE [MapOfTheDayPoints] ADD CONSTRAINT [fk_MapOfTheDayPoints_MapOfTheDayId_2] FOREIGN KEY ([MapOfTheDayId]) REFERENCES [MapOfTheDay] ([Id]);

ALTER TABLE [MapSwingData] ADD CONSTRAINT [fk_MapSwingData_DifficultyStatisticsId_1] FOREIGN KEY ([DifficultyStatisticsId]) REFERENCES [DifficultyStatistics] ([Id]);

ALTER TABLE [ModDescription] ADD CONSTRAINT [fk_ModDescription_DeveloperProfileId_1] FOREIGN KEY ([DeveloperProfileId]) REFERENCES [DeveloperProfile] ([Id]);

ALTER TABLE [Players] ADD CONSTRAINT [fk_Players_DeveloperProfileId_1] FOREIGN KEY ([DeveloperProfileId]) REFERENCES [DeveloperProfile] ([Id]);

ALTER TABLE [Players] ADD CONSTRAINT [fk_Players_MapperId_2] FOREIGN KEY ([MapperId]) REFERENCES [Mappers] ([Id]);

ALTER TABLE [Players] ADD CONSTRAINT [fk_Players_PatreonFeaturesId_3] FOREIGN KEY ([PatreonFeaturesId]) REFERENCES [PatreonFeatures] ([Id]);

ALTER TABLE [Players] ADD CONSTRAINT [fk_Players_ProfileSettingsId_4] FOREIGN KEY ([ProfileSettingsId]) REFERENCES [ProfileSettings] ([Id]);

ALTER TABLE [Players] ADD CONSTRAINT [fk_Players_ScoreStatsId_5] FOREIGN KEY ([ScoreStatsId]) REFERENCES [Stats] ([Id]);

ALTER TABLE [Players] ADD CONSTRAINT [fk_Players_TopClanId_6] FOREIGN KEY ([TopClanId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [PlayerBonusIdols] ADD CONSTRAINT [fk_PlayerBonusIdols_IdolDescriptionId_1] FOREIGN KEY ([IdolDescriptionId]) REFERENCES [IdolDescriptions] ([Id]);

ALTER TABLE [PlayerBonusIdols] ADD CONSTRAINT [fk_PlayerBonusIdols_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerChange] ADD CONSTRAINT [fk_PlayerChange_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerContextExtensions] ADD CONSTRAINT [fk_PlayerContextExtensions_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerContextExtensions] ADD CONSTRAINT [fk_PlayerContextExtensions_ScoreStatsId_2] FOREIGN KEY ([ScoreStatsId]) REFERENCES [Stats] ([Id]);

ALTER TABLE [PlayerIdolDecorations] ADD CONSTRAINT [fk_PlayerIdolDecorations_IdolDecorationId_1] FOREIGN KEY ([IdolDecorationId]) REFERENCES [IdolDecorations] ([Id]);

ALTER TABLE [PlayerIdolDecorations] ADD CONSTRAINT [fk_PlayerIdolDecorations_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerSearches] ADD CONSTRAINT [fk_PlayerSearches_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerSocial] ADD CONSTRAINT [fk_PlayerSocial_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerTreeOrnaments] ADD CONSTRAINT [fk_PlayerTreeOrnaments_OrnamentId_1] FOREIGN KEY ([OrnamentId]) REFERENCES [TreeOrnaments] ([Id]);

ALTER TABLE [PlayerTreeOrnaments] ADD CONSTRAINT [fk_PlayerTreeOrnaments_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerTreeOrnaments] ADD CONSTRAINT [fk_PlayerTreeOrnaments_ScoreId_3] FOREIGN KEY ([ScoreId]) REFERENCES [Scores] ([Id]);

ALTER TABLE [Playlists] ADD CONSTRAINT [fk_Playlists_UserId_1] FOREIGN KEY ([UserId]) REFERENCES [Users] ([Id]);

ALTER TABLE [PredictedScores] ADD CONSTRAINT [fk_PredictedScores_LeaderboardId_1] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [PredictedScores] ADD CONSTRAINT [fk_PredictedScores_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [QualificationChange] ADD CONSTRAINT [fk_QualificationChange_NewModifiersModifierId_1] FOREIGN KEY ([NewModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [QualificationChange] ADD CONSTRAINT [fk_QualificationChange_OldModifiersModifierId_2] FOREIGN KEY ([OldModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [QualificationChange] ADD CONSTRAINT [fk_QualificationChange_RankQualificationId_3] FOREIGN KEY ([RankQualificationId]) REFERENCES [RankQualification] ([Id]);

ALTER TABLE [QualificationCommentary] ADD CONSTRAINT [fk_QualificationCommentary_RankQualificationId_1] FOREIGN KEY ([RankQualificationId]) REFERENCES [RankQualification] ([Id]);

ALTER TABLE [QualificationVote] ADD CONSTRAINT [fk_QualificationVote_RankQualificationId_1] FOREIGN KEY ([RankQualificationId]) REFERENCES [RankQualification] ([Id]);

ALTER TABLE [RankQualification] ADD CONSTRAINT [fk_RankQualification_ModifiersModifierId_1] FOREIGN KEY ([ModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [RankQualification] ADD CONSTRAINT [fk_RankQualification_ModifiersRatingId_2] FOREIGN KEY ([ModifiersRatingId]) REFERENCES [ModifiersRating] ([Id]);

ALTER TABLE [RankUpdate] ADD CONSTRAINT [fk_RankUpdate_ModifiersModifierId_1] FOREIGN KEY ([ModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [RankUpdate] ADD CONSTRAINT [fk_RankUpdate_ModifiersRatingId_2] FOREIGN KEY ([ModifiersRatingId]) REFERENCES [ModifiersRating] ([Id]);

ALTER TABLE [RankUpdateChange] ADD CONSTRAINT [fk_RankUpdateChange_NewModifiersModifierId_1] FOREIGN KEY ([NewModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [RankUpdateChange] ADD CONSTRAINT [fk_RankUpdateChange_OldModifiersModifierId_2] FOREIGN KEY ([OldModifiersModifierId]) REFERENCES [Modifiers] ([ModifierId]);

ALTER TABLE [RankUpdateChange] ADD CONSTRAINT [fk_RankUpdateChange_RankUpdateId_3] FOREIGN KEY ([RankUpdateId]) REFERENCES [RankUpdate] ([Id]);

ALTER TABLE [RankVotings] ADD CONSTRAINT [fk_RankVotings_ScoreId_1] FOREIGN KEY ([ScoreId]) REFERENCES [Scores] ([Id]);

ALTER TABLE [Scores] ADD CONSTRAINT [fk_Scores_LeaderboardId_1] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [Scores] ADD CONSTRAINT [fk_Scores_MetadataId_2] FOREIGN KEY ([MetadataId]) REFERENCES [ScoreMetadata] ([Id]);

ALTER TABLE [Scores] ADD CONSTRAINT [fk_Scores_PlayerId_3] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [Scores] ADD CONSTRAINT [fk_Scores_ReplayOffsetsId_4] FOREIGN KEY ([ReplayOffsetsId]) REFERENCES [ReplayOffsets] ([Id]);

ALTER TABLE [Scores] ADD CONSTRAINT [fk_Scores_ScoreImprovementId_5] FOREIGN KEY ([ScoreImprovementId]) REFERENCES [ScoreImprovement] ([Id]);

ALTER TABLE [ScoreContextExtensions] ADD CONSTRAINT [fk_ScoreContextExtensions_LeaderboardId_1] FOREIGN KEY ([LeaderboardId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [ScoreContextExtensions] ADD CONSTRAINT [fk_ScoreContextExtensions_PlayerId_2] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [ScoreContextExtensions] ADD CONSTRAINT [fk_ScoreContextExtensions_ScoreId_3] FOREIGN KEY ([ScoreId]) REFERENCES [Scores] ([Id]);

ALTER TABLE [ScoreContextExtensions] ADD CONSTRAINT [fk_ScoreContextExtensions_ScoreImprovementId_4] FOREIGN KEY ([ScoreImprovementId]) REFERENCES [ScoreImprovement] ([Id]);

ALTER TABLE [ScoreExternalStatus] ADD CONSTRAINT [fk_ScoreExternalStatus_ScoreId_1] FOREIGN KEY ([ScoreId]) REFERENCES [Scores] ([Id]);

ALTER TABLE [Songs] ADD CONSTRAINT [fk_Songs_IdolDescriptionId_1] FOREIGN KEY ([IdolDescriptionId]) REFERENCES [IdolDescriptions] ([Id]);

ALTER TABLE [SongSearches] ADD CONSTRAINT [fk_SongSearches_SongId_1] FOREIGN KEY ([SongId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [Users] ADD CONSTRAINT [fk_Users_PlayerId_1] FOREIGN KEY ([PlayerId]) REFERENCES [Players] ([Id]);

ALTER TABLE [VoterFeedback] ADD CONSTRAINT [fk_VoterFeedback_RankVotingScoreId_1] FOREIGN KEY ([RankVotingScoreId]) REFERENCES [RankVotings] ([ScoreId]);

ALTER TABLE [ClanFeaturedPlaylist] ADD CONSTRAINT [fk_ClanFeaturedPlaylist_ClansId_1] FOREIGN KEY ([ClansId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanFeaturedPlaylist] ADD CONSTRAINT [fk_ClanFeaturedPlaylist_FeaturedPlaylistsId_2] FOREIGN KEY ([FeaturedPlaylistsId]) REFERENCES [FeaturedPlaylist] ([Id]);

ALTER TABLE [ClanPlayer] ADD CONSTRAINT [fk_ClanPlayer_ClansId_1] FOREIGN KEY ([ClansId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanPlayer] ADD CONSTRAINT [fk_ClanPlayer_PlayersId_2] FOREIGN KEY ([PlayersId]) REFERENCES [Players] ([Id]);

ALTER TABLE [ClanUser] ADD CONSTRAINT [fk_ClanUser_BannedClansId_1] FOREIGN KEY ([BannedClansId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanUser] ADD CONSTRAINT [fk_ClanUser_BannedId_2] FOREIGN KEY ([BannedId]) REFERENCES [Users] ([Id]);

ALTER TABLE [ClanUser1] ADD CONSTRAINT [fk_ClanUser1_ClanRequestId_1] FOREIGN KEY ([ClanRequestId]) REFERENCES [Clans] ([Id]);

ALTER TABLE [ClanUser1] ADD CONSTRAINT [fk_ClanUser1_RequestsId_2] FOREIGN KEY ([RequestsId]) REFERENCES [Users] ([Id]);

ALTER TABLE [EventPlayerMapOfTheDay] ADD CONSTRAINT [fk_EventPlayerMapOfTheDay_ChampionsId_1] FOREIGN KEY ([ChampionsId]) REFERENCES [EventPlayer] ([Id]);

ALTER TABLE [EventPlayerMapOfTheDay] ADD CONSTRAINT [fk_EventPlayerMapOfTheDay_MapOfTheDaysId_2] FOREIGN KEY ([MapOfTheDaysId]) REFERENCES [MapOfTheDay] ([Id]);

ALTER TABLE [EventRankingLeaderboard] ADD CONSTRAINT [fk_EventRankingLeaderboard_EventsId_1] FOREIGN KEY ([EventsId]) REFERENCES [EventRankings] ([Id]);

ALTER TABLE [EventRankingLeaderboard] ADD CONSTRAINT [fk_EventRankingLeaderboard_LeaderboardsId_2] FOREIGN KEY ([LeaderboardsId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [FeaturedPlaylistLeaderboard] ADD CONSTRAINT [fk_FeaturedPlaylistLeaderboard_FeaturedPlaylistsId_1] FOREIGN KEY ([FeaturedPlaylistsId]) REFERENCES [FeaturedPlaylist] ([Id]);

ALTER TABLE [FeaturedPlaylistLeaderboard] ADD CONSTRAINT [fk_FeaturedPlaylistLeaderboard_LeaderboardsId_2] FOREIGN KEY ([LeaderboardsId]) REFERENCES [Leaderboards] ([Id]);

ALTER TABLE [MapperSong] ADD CONSTRAINT [fk_MapperSong_MappersId_1] FOREIGN KEY ([MappersId]) REFERENCES [Mappers] ([Id]);

ALTER TABLE [MapperSong] ADD CONSTRAINT [fk_MapperSong_SongsId_2] FOREIGN KEY ([SongsId]) REFERENCES [Songs] ([Id]);

ALTER TABLE [OpenIddictApplications] ADD CONSTRAINT [fk_OpenIddictApplications_DeveloperProfileId_1] FOREIGN KEY ([DeveloperProfileId]) REFERENCES [DeveloperProfile] ([Id]);

ALTER TABLE [OpenIddictTokens] ADD CONSTRAINT [fk_OpenIddictTokens_ApplicationId_1] FOREIGN KEY ([ApplicationId]) REFERENCES [OpenIddictApplications] ([Id]);

ALTER TABLE [PlayerPlayerFriends] ADD CONSTRAINT [fk_PlayerPlayerFriends_FriendsId_1] FOREIGN KEY ([FriendsId]) REFERENCES [Players] ([Id]);

ALTER TABLE [PlayerPlayerFriends] ADD CONSTRAINT [fk_PlayerPlayerFriends_PlayerFriendsId_2] FOREIGN KEY ([PlayerFriendsId]) REFERENCES [Friends] ([Id]);
