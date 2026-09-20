CREATE TABLE "ffadminuser" (
  "id" INTEGER NOT NULL,
  "password" VARCHAR(255) NOT NULL,
  "last_login" TIMESTAMP,
  "is_superuser" BOOLEAN NOT NULL,
  "username" VARCHAR(255) NOT NULL,
  "first_name" VARCHAR(255) NOT NULL,
  "last_name" VARCHAR(255) NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "is_staff" BOOLEAN NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "date_joined" TIMESTAMP NOT NULL,
  "uuid" UUID NOT NULL,
  "marketing_consent_given" BOOLEAN NOT NULL,
  "onboarding_data" TEXT,
  PRIMARY KEY ("id"),
  UNIQUE ("username"),
  UNIQUE ("uuid")
);

CREATE TABLE "hubspotlead" (
  "id" INTEGER NOT NULL,
  "hubspot_id" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("hubspot_id"),
  UNIQUE ("user_id")
);

CREATE TABLE "hubspottracker" (
  "id" INTEGER NOT NULL,
  "hubspot_cookie" VARCHAR(255),
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "user_id" INTEGER NOT NULL,
  "utm_data" JSONB,
  PRIMARY KEY ("id"),
  UNIQUE ("hubspot_cookie"),
  UNIQUE ("user_id")
);

CREATE TABLE "userpermissiongroup" (
  "id" INTEGER NOT NULL,
  "ldap_dn" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("ldap_dn")
);

CREATE TABLE "userpermissiongroupmembership" (
  "id" INTEGER NOT NULL,
  "userpermissiongroup_id" INTEGER NOT NULL,
  "ffadminuser_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "organisation" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "project" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "organisation_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "environment" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "api_key" VARCHAR(255) NOT NULL,
  "project_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("api_key")
);

CREATE TABLE "identity" (
  "id" INTEGER NOT NULL,
  "identifier" VARCHAR(255) NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "environment_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("environment_id", "identifier")
);

CREATE TABLE "feature" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "initial_value" VARCHAR(255),
  "description" TEXT,
  "project_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "featurestate" (
  "id" INTEGER NOT NULL,
  "enabled" BOOLEAN NOT NULL,
  "value" VARCHAR(255),
  "environment_id" INTEGER,
  "feature_id" INTEGER NOT NULL,
  "identity_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("feature_id", "environment_id", "identity_id")
);

CREATE TABLE "trait" (
  "id" INTEGER NOT NULL,
  "trait_key" VARCHAR(255) NOT NULL,
  "value_type" VARCHAR(255),
  "boolean_value" BOOLEAN,
  "integer_value" INTEGER,
  "string_value" VARCHAR(255),
  "float_value" DOUBLE PRECISION,
  "created_date" TIMESTAMP NOT NULL,
  "identity_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("trait_key", "identity_id")
);

CREATE TABLE "masterapikey" (
  "id" VARCHAR(255) NOT NULL,
  "prefix" VARCHAR(255) NOT NULL,
  "hashed_key" VARCHAR(255) NOT NULL,
  "created" TIMESTAMP NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "revoked" BOOLEAN NOT NULL,
  "expiry_date" TIMESTAMP,
  "organisation_id" INTEGER NOT NULL,
  "deleted_at" TIMESTAMP,
  "is_admin" BOOLEAN NOT NULL,
  "created_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("prefix")
);

CREATE TABLE "auditlog" (
  "id" INTEGER NOT NULL,
  "created_date" TIMESTAMP NOT NULL,
  "log" TEXT NOT NULL,
  "author_id" INTEGER,
  "environment_id" INTEGER,
  "related_object_id" INTEGER,
  "related_object_type" VARCHAR(255),
  PRIMARY KEY ("id")
);

CREATE TABLE "userpermissiongrouporganisationpermission" (
  "id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL,
  "organisation_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "userorganisationpermission" (
  "id" INTEGER NOT NULL,
  "organisation_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "segment" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "segmentcondition" (
  "id" INTEGER NOT NULL,
  "trait_key" VARCHAR(255) NOT NULL,
  "condition_type" VARCHAR(255) NOT NULL,
  "match_value" TEXT,
  "segment_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "segmentmembershipcount" (
  "id" INTEGER NOT NULL,
  "count" INTEGER NOT NULL,
  "last_synced_at" TIMESTAMP NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "segment_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("segment_id", "environment_id")
);

CREATE TABLE "changerequest" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "deleted_at" TIMESTAMP,
  "committed_at" TIMESTAMP,
  "committed_by_id" INTEGER,
  "environment_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "changerequestapproval" (
  "id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "approved_at" TIMESTAMP,
  "change_request_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("user_id", "change_request_id")
);

CREATE TABLE "multivariatefeatureoption" (
  "id" INTEGER NOT NULL,
  "type" VARCHAR(255),
  "boolean_value" BOOLEAN,
  "integer_value" INTEGER,
  "string_value" VARCHAR(255),
  "default_percentage_allocation" DOUBLE PRECISION,
  "feature_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "multivariatefeaturestatevalue" (
  "id" INTEGER NOT NULL,
  "percentage_allocation" DOUBLE PRECISION,
  "feature_state_id" INTEGER NOT NULL,
  "multivariate_feature_option_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "metadatametadatafield" (
  "id" BIGINT NOT NULL,
  "uuid" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "organisation_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid"),
  UNIQUE ("name", "organisation_id")
);

CREATE TABLE "metadatametadatamodelfield" (
  "id" BIGINT NOT NULL,
  "uuid" UUID NOT NULL,
  "content_type_id" INTEGER NOT NULL,
  "field_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid"),
  UNIQUE ("field_id", "content_type_id")
);

CREATE TABLE "metadatametadatamodelfieldrequirement" (
  "id" BIGINT NOT NULL,
  "uuid" UUID NOT NULL,
  "object_id" INTEGER NOT NULL,
  "content_type_id" INTEGER NOT NULL,
  "model_field_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid"),
  UNIQUE ("content_type_id", "object_id", "model_field_id")
);

CREATE TABLE "metadata" (
  "id" BIGINT NOT NULL,
  "uuid" UUID NOT NULL,
  "object_id" INTEGER NOT NULL,
  "field_value" VARCHAR(255) NOT NULL,
  "content_type_id" INTEGER NOT NULL,
  "model_field_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid"),
  UNIQUE ("model_field_id", "content_type_id", "object_id")
);

CREATE TABLE "userpasswordresetrequest" (
  "id" INTEGER NOT NULL,
  "requested_at" TIMESTAMP NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "mfamethod" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "secret" VARCHAR(255) NOT NULL,
  "is_primary" BOOLEAN NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "backup_codes" VARCHAR(255) NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "apiusagebucket" (
  "id" BIGINT NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "resource" INTEGER NOT NULL,
  "total_count" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "bucket_size" INTEGER NOT NULL,
  "labels" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "featureevaluationbucket" (
  "id" BIGINT NOT NULL,
  "feature_name" VARCHAR(255) NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "total_count" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "bucket_size" INTEGER NOT NULL,
  "labels" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "featureevaluationraw" (
  "id" BIGINT NOT NULL,
  "feature_name" VARCHAR(255) NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "evaluation_count" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "identity_identifier" VARCHAR(255),
  "enabled_when_evaluated" BOOLEAN,
  "labels" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "apiusageraw" (
  "id" BIGINT NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "host" VARCHAR(255) NOT NULL,
  "resource" INTEGER NOT NULL,
  "count" INTEGER NOT NULL,
  "labels" JSONB NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "environmentfeatureversion" (
  "uuid" UUID NOT NULL,
  "deleted_at" TIMESTAMP,
  "description" TEXT,
  "created_at" TIMESTAMP NOT NULL,
  "updated_at" TIMESTAMP NOT NULL,
  "published_at" TIMESTAMP,
  "live_from" TIMESTAMP,
  "change_request_id" INTEGER,
  "created_by_id" INTEGER,
  "environment_id" INTEGER NOT NULL,
  "feature_id" INTEGER NOT NULL,
  "published_by_id" INTEGER,
  PRIMARY KEY ("uuid")
);

CREATE TABLE "releasepipeline" (
  "id" INTEGER NOT NULL,
  "deleted_at" TIMESTAMP,
  "uuid" UUID NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "published_at" TIMESTAMP,
  "project_id" INTEGER NOT NULL,
  "published_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid")
);

CREATE TABLE "pipelinestage" (
  "id" INTEGER NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "order" INTEGER NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "pipeline_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("pipeline_id", "order")
);

CREATE TABLE "pipelinestageaction" (
  "id" INTEGER NOT NULL,
  "action_type" VARCHAR(255) NOT NULL,
  "action_body" JSONB,
  "stage_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "featureexternalresource" (
  "id" INTEGER NOT NULL,
  "url" VARCHAR(255) NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "metadata" TEXT,
  "feature_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("feature_id", "url")
);

CREATE TABLE "featurehealthevent" (
  "id" INTEGER NOT NULL,
  "uuid" UUID NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "type" VARCHAR(255) NOT NULL,
  "provider_name" VARCHAR(255),
  "reason" TEXT,
  "environment_id" INTEGER,
  "feature_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid")
);

CREATE TABLE "featureimport" (
  "id" INTEGER NOT NULL,
  "strategy" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "data" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "environment_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "featureexport" (
  "id" INTEGER NOT NULL,
  "data" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "environment_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "warehouseconnection" (
  "id" INTEGER NOT NULL,
  "deleted_at" TIMESTAMP,
  "uuid" UUID NOT NULL,
  "warehouse_type" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "environment_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid")
);

CREATE TABLE "featureflagcodereferencesscan" (
  "id" INTEGER NOT NULL,
  "repository_url" VARCHAR(255) NOT NULL,
  "vcs_provider" VARCHAR(255) NOT NULL,
  "revision" VARCHAR(255) NOT NULL,
  "code_references" JSONB NOT NULL,
  "created_at" TIMESTAMP NOT NULL,
  "project_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "integrationconfiguration" (
  "id" INTEGER NOT NULL,
  "provider" VARCHAR(64) NOT NULL,
  "project_id" INTEGER,
  "environment_id" INTEGER,
  "settings" JSONB NOT NULL,
  "enabled" BOOLEAN NOT NULL DEFAULT TRUE,
  "created_at" TIMESTAMP NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("provider", "project_id", "environment_id")
);

CREATE TABLE "githubconfiguration" (
  "id" INTEGER NOT NULL,
  "deleted_at" TIMESTAMP,
  "uuid" UUID NOT NULL,
  "installation_id" VARCHAR(255) NOT NULL,
  "organisation_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid"),
  UNIQUE ("organisation_id")
);

CREATE TABLE "githubrepository" (
  "id" INTEGER NOT NULL,
  "deleted_at" TIMESTAMP,
  "uuid" UUID NOT NULL,
  "repository_owner" VARCHAR(255) NOT NULL,
  "repository_name" VARCHAR(255) NOT NULL,
  "github_configuration_id" INTEGER NOT NULL,
  "project_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("uuid"),
  UNIQUE ("github_configuration_id", "project_id", "repository_owner", "repository_name")
);

CREATE TABLE "userpermissiongroupenvironmentpermission" (
  "id" INTEGER NOT NULL,
  "admin" BOOLEAN NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "userenvironmentpermission" (
  "id" INTEGER NOT NULL,
  "admin" BOOLEAN NOT NULL,
  "environment_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

CREATE INDEX "idx_masterapikey_created_1" ON "masterapikey" ("created");

CREATE INDEX "idx_featureevaluationraw_feature_name_1" ON "featureevaluationraw" ("feature_name");

CREATE INDEX "idx_featureevaluationraw_created_at_2" ON "featureevaluationraw" ("created_at");

CREATE INDEX "idx_apiusageraw_environment_id_created_at_1" ON "apiusageraw" ("environment_id", "created_at");

CREATE INDEX "idx_environmentfeatureversion_environment_id_feature_id_1" ON "environmentfeatureversion" ("environment_id", "feature_id");

CREATE INDEX "idx_project_organisation" ON "project" ("organisation_id");
CREATE INDEX "idx_environment_project" ON "environment" ("project_id");
CREATE INDEX "idx_identity_environment_identifier" ON "identity" ("environment_id", "identifier");
CREATE INDEX "idx_feature_project_name" ON "feature" ("project_id", "name");
CREATE INDEX "idx_featurestate_environment_feature" ON "featurestate" ("environment_id", "feature_id");
CREATE INDEX "idx_featurestate_identity" ON "featurestate" ("identity_id");
CREATE INDEX "idx_trait_identity_key" ON "trait" ("identity_id", "trait_key");
CREATE INDEX "idx_masterapikey_organisation" ON "masterapikey" ("organisation_id");
CREATE INDEX "idx_auditlog_environment_created" ON "auditlog" ("environment_id", "created_date");
CREATE INDEX "idx_group_membership_user" ON "userpermissiongroupmembership" ("ffadminuser_id");
CREATE INDEX "idx_group_org_permission" ON "userpermissiongrouporganisationpermission" ("organisation_id", "group_id");
CREATE INDEX "idx_user_org_permission" ON "userorganisationpermission" ("user_id", "organisation_id");
CREATE INDEX "idx_segmentcondition_segment" ON "segmentcondition" ("segment_id");
CREATE INDEX "idx_segmentmembership_environment" ON "segmentmembershipcount" ("environment_id", "segment_id");
CREATE INDEX "idx_changerequest_environment_created" ON "changerequest" ("environment_id", "created_at");
CREATE INDEX "idx_changerequestapproval_request" ON "changerequestapproval" ("change_request_id");
CREATE INDEX "idx_multivariateoption_feature" ON "multivariatefeatureoption" ("feature_id");
CREATE INDEX "idx_multivariatestate_featurestate" ON "multivariatefeaturestatevalue" ("feature_state_id");
CREATE INDEX "idx_metadatafield_organisation" ON "metadatametadatafield" ("organisation_id");
CREATE INDEX "idx_metadata_object" ON "metadata" ("content_type_id", "object_id");
CREATE INDEX "idx_featureevaluationraw_environment_created" ON "featureevaluationraw" ("environment_id", "created_at");
CREATE INDEX "idx_apiusagebucket_environment_created" ON "apiusagebucket" ("environment_id", "created_at");
CREATE INDEX "idx_featureevaluationbucket_environment_created" ON "featureevaluationbucket" ("environment_id", "created_at");
CREATE INDEX "idx_pipeline_project" ON "releasepipeline" ("project_id");
CREATE INDEX "idx_pipelinestage_pipeline_order" ON "pipelinestage" ("pipeline_id", "order");
CREATE INDEX "idx_pipelineaction_stage" ON "pipelinestageaction" ("stage_id");
CREATE INDEX "idx_externalresource_feature" ON "featureexternalresource" ("feature_id");
CREATE INDEX "idx_featurehealth_feature_created" ON "featurehealthevent" ("feature_id", "created_at");
CREATE INDEX "idx_featureimport_environment_created" ON "featureimport" ("environment_id", "created_at");
CREATE INDEX "idx_featureexport_environment_created" ON "featureexport" ("environment_id", "created_at");
CREATE INDEX "idx_warehouse_environment" ON "warehouseconnection" ("environment_id");
CREATE INDEX "idx_codescan_project_created" ON "featureflagcodereferencesscan" ("project_id", "created_at");
CREATE INDEX "idx_integration_project_provider" ON "integrationconfiguration" ("project_id", "provider");
CREATE INDEX "idx_integration_environment_provider" ON "integrationconfiguration" ("environment_id", "provider");
CREATE INDEX "idx_githubrepository_configuration" ON "githubrepository" ("github_configuration_id");
CREATE INDEX "idx_githubrepository_project" ON "githubrepository" ("project_id");
CREATE INDEX "idx_group_environment_permission" ON "userpermissiongroupenvironmentpermission" ("environment_id", "group_id");
CREATE INDEX "idx_user_environment_permission" ON "userenvironmentpermission" ("user_id", "environment_id");

ALTER TABLE "hubspotlead" ADD CONSTRAINT "fk_hubspotlead_user_id_1" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "hubspottracker" ADD CONSTRAINT "fk_hubspottracker_user_id_1" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "userpermissiongroupmembership" ADD CONSTRAINT "fk_userpermissiongroupmembership_userpermissiongroup_id_1" FOREIGN KEY ("userpermissiongroup_id") REFERENCES "userpermissiongroup" ("id");

ALTER TABLE "userpermissiongroupmembership" ADD CONSTRAINT "fk_userpermissiongroupmembership_ffadminuser_id_2" FOREIGN KEY ("ffadminuser_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "project" ADD CONSTRAINT "fk_project_organisation_id_1" FOREIGN KEY ("organisation_id") REFERENCES "organisation" ("id");

ALTER TABLE "environment" ADD CONSTRAINT "fk_environment_project_id_1" FOREIGN KEY ("project_id") REFERENCES "project" ("id");

ALTER TABLE "identity" ADD CONSTRAINT "fk_identity_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "feature" ADD CONSTRAINT "fk_feature_project_id_1" FOREIGN KEY ("project_id") REFERENCES "project" ("id");

ALTER TABLE "featurestate" ADD CONSTRAINT "fk_featurestate_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "featurestate" ADD CONSTRAINT "fk_featurestate_feature_id_2" FOREIGN KEY ("feature_id") REFERENCES "feature" ("id");

ALTER TABLE "featurestate" ADD CONSTRAINT "fk_featurestate_identity_id_3" FOREIGN KEY ("identity_id") REFERENCES "identity" ("id");

ALTER TABLE "trait" ADD CONSTRAINT "fk_trait_identity_id_1" FOREIGN KEY ("identity_id") REFERENCES "identity" ("id");

ALTER TABLE "masterapikey" ADD CONSTRAINT "fk_masterapikey_organisation_id_1" FOREIGN KEY ("organisation_id") REFERENCES "organisation" ("id");

ALTER TABLE "masterapikey" ADD CONSTRAINT "fk_masterapikey_created_by_id_2" FOREIGN KEY ("created_by_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "auditlog" ADD CONSTRAINT "fk_auditlog_author_id_1" FOREIGN KEY ("author_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "auditlog" ADD CONSTRAINT "fk_auditlog_environment_id_2" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "userpermissiongrouporganisationpermission" ADD CONSTRAINT "fk_userpermissiongrouporganisationpermission_group_id_1" FOREIGN KEY ("group_id") REFERENCES "userpermissiongroup" ("id");

ALTER TABLE "userpermissiongrouporganisationpermission" ADD CONSTRAINT "fk_userpermissiongrouporganisationpermission_organi_c6e47c82" FOREIGN KEY ("organisation_id") REFERENCES "organisation" ("id");

ALTER TABLE "userorganisationpermission" ADD CONSTRAINT "fk_userorganisationpermission_organisation_id_1" FOREIGN KEY ("organisation_id") REFERENCES "organisation" ("id");

ALTER TABLE "userorganisationpermission" ADD CONSTRAINT "fk_userorganisationpermission_user_id_2" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "segmentcondition" ADD CONSTRAINT "fk_segmentcondition_segment_id_1" FOREIGN KEY ("segment_id") REFERENCES "segment" ("id");

ALTER TABLE "segmentmembershipcount" ADD CONSTRAINT "fk_segmentmembershipcount_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "segmentmembershipcount" ADD CONSTRAINT "fk_segmentmembershipcount_segment_id_2" FOREIGN KEY ("segment_id") REFERENCES "segment" ("id");

ALTER TABLE "changerequest" ADD CONSTRAINT "fk_changerequest_committed_by_id_1" FOREIGN KEY ("committed_by_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "changerequest" ADD CONSTRAINT "fk_changerequest_environment_id_2" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "changerequest" ADD CONSTRAINT "fk_changerequest_user_id_3" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "changerequestapproval" ADD CONSTRAINT "fk_changerequestapproval_change_request_id_1" FOREIGN KEY ("change_request_id") REFERENCES "changerequest" ("id");

ALTER TABLE "changerequestapproval" ADD CONSTRAINT "fk_changerequestapproval_user_id_2" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "multivariatefeatureoption" ADD CONSTRAINT "fk_multivariatefeatureoption_feature_id_1" FOREIGN KEY ("feature_id") REFERENCES "feature" ("id");

ALTER TABLE "multivariatefeaturestatevalue" ADD CONSTRAINT "fk_multivariatefeaturestatevalue_feature_state_id_1" FOREIGN KEY ("feature_state_id") REFERENCES "featurestate" ("id");

ALTER TABLE "multivariatefeaturestatevalue" ADD CONSTRAINT "fk_multivariatefeaturestatevalue_multivariate_featu_2dc31b0a" FOREIGN KEY ("multivariate_feature_option_id") REFERENCES "multivariatefeatureoption" ("id");

ALTER TABLE "metadatametadatafield" ADD CONSTRAINT "fk_metadatametadatafield_organisation_id_1" FOREIGN KEY ("organisation_id") REFERENCES "organisation" ("id");

ALTER TABLE "metadatametadatamodelfield" ADD CONSTRAINT "fk_metadatametadatamodelfield_field_id_1" FOREIGN KEY ("field_id") REFERENCES "metadatametadatafield" ("id");

ALTER TABLE "metadatametadatamodelfieldrequirement" ADD CONSTRAINT "fk_metadatametadatamodelfieldrequirement_model_field_id_1" FOREIGN KEY ("model_field_id") REFERENCES "metadatametadatamodelfield" ("id");

ALTER TABLE "metadata" ADD CONSTRAINT "fk_metadata_model_field_id_1" FOREIGN KEY ("model_field_id") REFERENCES "metadatametadatamodelfield" ("id");

ALTER TABLE "userpasswordresetrequest" ADD CONSTRAINT "fk_userpasswordresetrequest_user_id_1" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "mfamethod" ADD CONSTRAINT "fk_mfamethod_user_id_1" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "environmentfeatureversion" ADD CONSTRAINT "fk_environmentfeatureversion_change_request_id_1" FOREIGN KEY ("change_request_id") REFERENCES "changerequest" ("id");

ALTER TABLE "environmentfeatureversion" ADD CONSTRAINT "fk_environmentfeatureversion_created_by_id_2" FOREIGN KEY ("created_by_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "environmentfeatureversion" ADD CONSTRAINT "fk_environmentfeatureversion_environment_id_3" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "environmentfeatureversion" ADD CONSTRAINT "fk_environmentfeatureversion_feature_id_4" FOREIGN KEY ("feature_id") REFERENCES "feature" ("id");

ALTER TABLE "environmentfeatureversion" ADD CONSTRAINT "fk_environmentfeatureversion_published_by_id_5" FOREIGN KEY ("published_by_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "releasepipeline" ADD CONSTRAINT "fk_releasepipeline_project_id_1" FOREIGN KEY ("project_id") REFERENCES "project" ("id");

ALTER TABLE "releasepipeline" ADD CONSTRAINT "fk_releasepipeline_published_by_id_2" FOREIGN KEY ("published_by_id") REFERENCES "ffadminuser" ("id");

ALTER TABLE "pipelinestage" ADD CONSTRAINT "fk_pipelinestage_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "pipelinestage" ADD CONSTRAINT "fk_pipelinestage_pipeline_id_2" FOREIGN KEY ("pipeline_id") REFERENCES "releasepipeline" ("id");

ALTER TABLE "pipelinestageaction" ADD CONSTRAINT "fk_pipelinestageaction_stage_id_1" FOREIGN KEY ("stage_id") REFERENCES "pipelinestage" ("id");

ALTER TABLE "featureexternalresource" ADD CONSTRAINT "fk_featureexternalresource_feature_id_1" FOREIGN KEY ("feature_id") REFERENCES "feature" ("id");

ALTER TABLE "featurehealthevent" ADD CONSTRAINT "fk_featurehealthevent_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "featurehealthevent" ADD CONSTRAINT "fk_featurehealthevent_feature_id_2" FOREIGN KEY ("feature_id") REFERENCES "feature" ("id");

ALTER TABLE "featureimport" ADD CONSTRAINT "fk_featureimport_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "featureexport" ADD CONSTRAINT "fk_featureexport_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "warehouseconnection" ADD CONSTRAINT "fk_warehouseconnection_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "featureflagcodereferencesscan" ADD CONSTRAINT "fk_featureflagcodereferencesscan_project_id_1" FOREIGN KEY ("project_id") REFERENCES "project" ("id");

ALTER TABLE "integrationconfiguration" ADD CONSTRAINT "fk_integrationconfiguration_project_id" FOREIGN KEY ("project_id") REFERENCES "project" ("id");

ALTER TABLE "integrationconfiguration" ADD CONSTRAINT "fk_integrationconfiguration_environment_id" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "githubconfiguration" ADD CONSTRAINT "fk_githubconfiguration_organisation_id_1" FOREIGN KEY ("organisation_id") REFERENCES "organisation" ("id");

ALTER TABLE "githubrepository" ADD CONSTRAINT "fk_githubrepository_github_configuration_id_1" FOREIGN KEY ("github_configuration_id") REFERENCES "githubconfiguration" ("id");

ALTER TABLE "githubrepository" ADD CONSTRAINT "fk_githubrepository_project_id_2" FOREIGN KEY ("project_id") REFERENCES "project" ("id");

ALTER TABLE "userpermissiongroupenvironmentpermission" ADD CONSTRAINT "fk_userpermissiongroupenvironmentpermission_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "userpermissiongroupenvironmentpermission" ADD CONSTRAINT "fk_userpermissiongroupenvironmentpermission_group_id_2" FOREIGN KEY ("group_id") REFERENCES "userpermissiongroup" ("id");

ALTER TABLE "userenvironmentpermission" ADD CONSTRAINT "fk_userenvironmentpermission_environment_id_1" FOREIGN KEY ("environment_id") REFERENCES "environment" ("id");

ALTER TABLE "userenvironmentpermission" ADD CONSTRAINT "fk_userenvironmentpermission_user_id_2" FOREIGN KEY ("user_id") REFERENCES "ffadminuser" ("id");
