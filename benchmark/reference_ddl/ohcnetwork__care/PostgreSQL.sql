

CREATE TABLE "users_skill" (
  "id" INTEGER NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  UNIQUE ("name")
);

CREATE TABLE "users_userskill" (
  "id" INTEGER NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "skill_id" INTEGER,
  "user_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "users_userflag" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "flag" VARCHAR(255) NOT NULL,
  "user_id" BIGINT NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "users_plugconfig" (
  "id" BIGINT NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "meta" JSONB NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("slug")
);

CREATE TABLE "users_user" (
  "id" INTEGER NOT NULL,
  "password" VARCHAR(255) NOT NULL,
  "last_login" TIMESTAMP,
  "is_superuser" BOOLEAN NOT NULL,
  "first_name" VARCHAR(255) NOT NULL,
  "last_name" VARCHAR(255) NOT NULL,
  "email" VARCHAR(255) NOT NULL,
  "is_staff" BOOLEAN NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "date_joined" TIMESTAMP NOT NULL,
  "external_id" UUID NOT NULL,
  "username" VARCHAR(255) NOT NULL,
  "user_type" VARCHAR(255),
  "phone_number" VARCHAR(255) NOT NULL,
  "alt_phone_number" VARCHAR(255),
  "gender" VARCHAR(255),
  "old_gender" INTEGER,
  "age" INTEGER NOT NULL,
  "qualification" TEXT,
  "doctor_experience_commenced_on" DATE,
  "doctor_medical_council_registration" VARCHAR(255),
  "verified" BOOLEAN NOT NULL,
  "deleted" BOOLEAN NOT NULL,
  "pf_endpoint" TEXT,
  "pf_p256dh" TEXT,
  "pf_auth" TEXT,
  "created_by_id" INTEGER,
  "profile_picture_url" VARCHAR(255),
  "geo_organization_id" BIGINT,
  "mfa_settings" JSONB NOT NULL,
  "totp_secret" TEXT,
  "prefix" VARCHAR(255),
  "suffix" VARCHAR(255),
  "is_service_account" BOOLEAN NOT NULL,
  "preferences" JSONB NOT NULL,
  "cached_role_orgs" JSONB,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  UNIQUE ("username")
);

CREATE TABLE "security_permissionmodel" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "context" VARCHAR(255) NOT NULL,
  "temp_deleted" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  UNIQUE ("slug")
);

CREATE TABLE "security_rolemodel" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "context" VARCHAR(255) NOT NULL,
  "is_system" BOOLEAN NOT NULL,
  "temp_deleted" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "security_roleassociation" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "context" VARCHAR(255) NOT NULL,
  "context_id" BIGINT NOT NULL,
  "expiry" TIMESTAMP,
  "user_id" INTEGER NOT NULL,
  "role_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "security_rolepermission" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "temp_deleted" BOOLEAN NOT NULL,
  "permission_id" BIGINT NOT NULL,
  "role_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "facility_facility" (
  "id" INTEGER NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "is_active" BOOLEAN NOT NULL,
  "verified" BOOLEAN NOT NULL,
  "facility_type" INTEGER NOT NULL,
  "kasp_empanelled" BOOLEAN NOT NULL,
  "features" VARCHAR(255),
  "longitude" DECIMAL(18, 2),
  "latitude" DECIMAL(18, 2),
  "pincode" INTEGER,
  "address" TEXT NOT NULL,
  "oxygen_capacity" INTEGER NOT NULL,
  "type_b_cylinders" INTEGER NOT NULL,
  "type_c_cylinders" INTEGER NOT NULL,
  "type_d_cylinders" INTEGER NOT NULL,
  "expected_oxygen_requirement" INTEGER NOT NULL,
  "expected_type_b_cylinders" INTEGER NOT NULL,
  "expected_type_c_cylinders" INTEGER NOT NULL,
  "expected_type_d_cylinders" INTEGER NOT NULL,
  "phone_number" VARCHAR(255) NOT NULL,
  "corona_testing" BOOLEAN NOT NULL,
  "cover_image_url" VARCHAR(255),
  "middleware_address" VARCHAR(255),
  "created_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_organization" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "active" BOOLEAN NOT NULL,
  "org_type" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "has_children" BOOLEAN NOT NULL,
  "description" TEXT,
  "system_generated" BOOLEAN NOT NULL,
  "level_cache" INTEGER NOT NULL,
  "parent_cache" JSONB NOT NULL,
  "metadata" JSONB NOT NULL,
  "cached_parent_json" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "parent_id" BIGINT,
  "root_org_id" BIGINT,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_patient" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "gender" VARCHAR(255) NOT NULL,
  "phone_number" VARCHAR(255) NOT NULL,
  "emergency_phone_number" VARCHAR(255) NOT NULL,
  "address" TEXT NOT NULL,
  "permanent_address" TEXT NOT NULL,
  "pincode" INTEGER,
  "date_of_birth" DATE,
  "year_of_birth" INTEGER,
  "deceased_datetime" TIMESTAMP,
  "blood_group" VARCHAR(255) NOT NULL,
  "organization_cache" JSONB NOT NULL,
  "users_cache" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "geo_organization_id" BIGINT,
  "updated_by_id" INTEGER,
  "facility_identifiers" JSONB,
  "facility_tags" JSONB,
  "instance_identifiers" JSONB,
  "instance_tags" JSONB NOT NULL,
  "extensions" JSONB NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_encounter" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255),
  "status_history" JSONB NOT NULL,
  "encounter_class" VARCHAR(255),
  "encounter_class_history" JSONB NOT NULL,
  "period" JSONB NOT NULL,
  "hospitalization" JSONB NOT NULL,
  "priority" VARCHAR(255),
  "external_identifier" VARCHAR(255),
  "facility_organization_cache" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "facility_id" INTEGER NOT NULL,
  "updated_by_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  "appointment_id" BIGINT,
  "current_location_id" BIGINT,
  "tags" JSONB NOT NULL,
  "extensions" JSONB NOT NULL,
  "discharge_summary_advice" TEXT,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_facilityorganization" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "active" BOOLEAN NOT NULL,
  "org_type" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "has_children" BOOLEAN NOT NULL,
  "description" TEXT,
  "system_generated" BOOLEAN NOT NULL,
  "level_cache" INTEGER NOT NULL,
  "parent_cache" JSONB NOT NULL,
  "metadata" JSONB NOT NULL,
  "cached_parent_json" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "facility_id" INTEGER NOT NULL,
  "parent_id" BIGINT,
  "root_org_id" BIGINT,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_encounterorganization" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "organization_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_facilityorganizationuser" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "organization_id" BIGINT NOT NULL,
  "role_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_organizationuser" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "organization_id" BIGINT NOT NULL,
  "role_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_medicationstatement" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "reason" VARCHAR(255),
  "medication" JSONB NOT NULL,
  "effective_period" JSONB NOT NULL,
  "information_source" VARCHAR(255) NOT NULL,
  "dosage_text" TEXT,
  "note" TEXT,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_medicationrequest" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255),
  "status_reason" VARCHAR(255),
  "status_changed" TIMESTAMP,
  "intent" VARCHAR(255),
  "category" VARCHAR(255),
  "priority" VARCHAR(255),
  "do_not_perform" BOOLEAN NOT NULL,
  "method" JSONB,
  "authored_on" TIMESTAMP,
  "dosage_instruction" JSONB,
  "note" TEXT,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  "dispense_status" VARCHAR(255),
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_medicationadministration" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "status_reason" JSONB,
  "category" VARCHAR(255),
  "medication" JSONB NOT NULL,
  "authored_on" TIMESTAMP,
  "occurrence_period_start" TIMESTAMP NOT NULL,
  "occurrence_period_end" TIMESTAMP,
  "recorded" TIMESTAMP,
  "performer" JSONB NOT NULL,
  "dosage" JSONB,
  "note" TEXT,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT,
  "updated_by_id" INTEGER,
  "request_id" BIGINT,
  "patient_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_condition" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "clinical_status" VARCHAR(255),
  "verification_status" VARCHAR(255),
  "category" VARCHAR(255),
  "severity" VARCHAR(255),
  "code" JSONB NOT NULL,
  "body_site" JSONB NOT NULL,
  "onset" JSONB NOT NULL,
  "recorded_date" TIMESTAMP,
  "note" TEXT,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "patient_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_allergyintolerance" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "clinical_status" VARCHAR(255),
  "verification_status" VARCHAR(255),
  "category" VARCHAR(255),
  "criticality" VARCHAR(255),
  "code" JSONB NOT NULL,
  "onset" JSONB NOT NULL,
  "recorded_date" TIMESTAMP,
  "last_occurrence" TIMESTAMP,
  "note" TEXT,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "patient_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_patientorganization" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "organization_id" BIGINT NOT NULL,
  "patient_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_patientuser" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  "role_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "user_id" INTEGER NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_questionnaire" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "version" VARCHAR(255) NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "subject_type" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "styling_metadata" JSONB NOT NULL,
  "questions" JSONB NOT NULL,
  "organization_cache" JSONB NOT NULL,
  "internal_organization_cache" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  UNIQUE ("slug")
);

CREATE TABLE "emr_questionnaireresponse" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "subject_id" UUID NOT NULL,
  "responses" JSONB NOT NULL,
  "structured_responses" JSONB NOT NULL,
  "structured_response_type" VARCHAR(255),
  "created_by_id" INTEGER,
  "encounter_id" BIGINT,
  "patient_id" BIGINT NOT NULL,
  "questionnaire_id" BIGINT,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_observation" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "is_group" BOOLEAN NOT NULL,
  "category" JSONB NOT NULL,
  "main_code" JSONB NOT NULL,
  "alternate_coding" JSONB NOT NULL,
  "subject_type" VARCHAR(255) NOT NULL,
  "subject_id" UUID NOT NULL,
  "effective_datetime" TIMESTAMP,
  "performer" JSONB NOT NULL,
  "value_type" VARCHAR(255) NOT NULL,
  "value" JSONB NOT NULL,
  "note" TEXT,
  "body_site" JSONB NOT NULL,
  "method" JSONB NOT NULL,
  "reference_range" JSONB NOT NULL,
  "interpretation" VARCHAR(255) NOT NULL,
  "parent" UUID,
  "created_by_id" INTEGER,
  "data_entered_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  "questionnaire_response_id" BIGINT,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_resourcerequest" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "emergency" BOOLEAN NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "reason" TEXT NOT NULL,
  "referring_facility_contact_name" TEXT NOT NULL,
  "referring_facility_contact_number" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "category" VARCHAR(255) NOT NULL,
  "priority" INTEGER,
  "is_assigned_to_user" BOOLEAN NOT NULL,
  "approving_facility_id" INTEGER,
  "assigned_facility_id" INTEGER,
  "assigned_to_id" INTEGER,
  "created_by_id" INTEGER,
  "origin_facility_id" INTEGER NOT NULL,
  "related_patient_id" BIGINT,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_resourcerequestcomment" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "comment" TEXT NOT NULL,
  "created_by_id" INTEGER,
  "request_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_schedulableresource" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "facility_id" INTEGER NOT NULL,
  "updated_by_id" INTEGER,
  "user_id" INTEGER,
  "healthcare_service_id" BIGINT,
  "location_id" BIGINT,
  "resource_type" VARCHAR(255) NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_availabilityexception" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "reason" TEXT,
  "valid_from" DATE NOT NULL,
  "valid_to" DATE NOT NULL,
  "start_time" VARCHAR(255) NOT NULL,
  "end_time" VARCHAR(255) NOT NULL,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  "resource_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_schedule" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "valid_from" TIMESTAMP NOT NULL,
  "valid_to" TIMESTAMP NOT NULL,
  "created_by_id" INTEGER,
  "resource_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "is_public" BOOLEAN NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_availability" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "slot_type" VARCHAR(255) NOT NULL,
  "slot_size_in_minutes" INTEGER NOT NULL,
  "tokens_per_slot" INTEGER NOT NULL,
  "create_tokens" BOOLEAN NOT NULL,
  "reason" TEXT,
  "availability" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  "schedule_id" BIGINT NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_tokenbooking" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "booked_on" TIMESTAMP NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "reason_for_visit" TEXT,
  "booked_by_id" INTEGER,
  "created_by_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  "token_slot_id" BIGINT NOT NULL,
  "tags" JSONB NOT NULL,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_tokenslot" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "start_datetime" TIMESTAMP NOT NULL,
  "end_datetime" TIMESTAMP NOT NULL,
  "allocated" INTEGER NOT NULL,
  "availability_id" BIGINT,
  "created_by_id" INTEGER,
  "resource_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_valueset" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "compose" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "is_system_defined" BOOLEAN NOT NULL,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  UNIQUE ("slug")
);

CREATE TABLE "emr_facilitylocation" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "operational_status" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" VARCHAR(255) NOT NULL,
  "mode" VARCHAR(255) NOT NULL,
  "location_type" JSONB,
  "form" VARCHAR(255) NOT NULL,
  "facility_organization_cache" JSONB NOT NULL,
  "has_children" BOOLEAN NOT NULL,
  "level_cache" INTEGER NOT NULL,
  "parent_cache" JSONB NOT NULL,
  "metadata" JSONB NOT NULL,
  "cached_parent_json" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "facility_id" INTEGER NOT NULL,
  "parent_id" BIGINT,
  "root_location_id" BIGINT,
  "updated_by_id" INTEGER,
  "sort_index" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_facilitylocationorganization" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "location_id" BIGINT NOT NULL,
  "organization_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_facilitylocationencounter" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "start_datetime" TIMESTAMP NOT NULL,
  "end_datetime" TIMESTAMP,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "location_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_consent" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "category" VARCHAR(255) NOT NULL,
  "date" TIMESTAMP NOT NULL,
  "period" JSONB NOT NULL,
  "decision" VARCHAR(255) NOT NULL,
  "verification_details" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_device" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "identifier" VARCHAR(255),
  "status" VARCHAR(255) NOT NULL,
  "availability_status" VARCHAR(255) NOT NULL,
  "manufacturer" VARCHAR(255) NOT NULL,
  "manufacture_date" TIMESTAMP,
  "expiration_date" TIMESTAMP,
  "lot_number" VARCHAR(255),
  "serial_number" VARCHAR(255),
  "registered_name" VARCHAR(255),
  "user_friendly_name" VARCHAR(255),
  "model_number" VARCHAR(255),
  "part_number" VARCHAR(255),
  "contact" JSONB NOT NULL,
  "care_type" VARCHAR(255),
  "metadata" JSONB NOT NULL,
  "facility_organization_cache" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "current_encounter_id" BIGINT,
  "current_location_id" BIGINT,
  "facility_id" INTEGER NOT NULL,
  "managing_organization_id" BIGINT,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_account" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "billing_status" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "service_period" JSONB NOT NULL,
  "description" TEXT,
  "cached_items" JSONB NOT NULL,
  "total_net" DECIMAL(18, 2) NOT NULL,
  "total_gross" DECIMAL(18, 2) NOT NULL,
  "total_paid" DECIMAL(18, 2) NOT NULL,
  "total_balance" DECIMAL(18, 2) NOT NULL,
  "total_price_components" JSONB NOT NULL,
  "calculated_at" TIMESTAMP,
  "created_by_id" INTEGER,
  "facility_id" INTEGER NOT NULL,
  "patient_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_diagnosticreport" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "category" JSONB,
  "code" JSONB,
  "note" TEXT,
  "conclusion" TEXT,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT NOT NULL,
  "facility_id" INTEGER,
  "patient_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_healthcareservice" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "styling_metadata" JSONB,
  "name" VARCHAR(255) NOT NULL,
  "service_type" JSONB NOT NULL,
  "internal_type" VARCHAR(255),
  "locations" JSONB NOT NULL,
  "extra_details" TEXT NOT NULL,
  "created_by_id" INTEGER,
  "facility_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_formsubmission" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "response_dump" JSONB NOT NULL,
  "created_by_id" INTEGER,
  "encounter_id" BIGINT,
  "patient_id" BIGINT NOT NULL,
  "questionnaire_id" BIGINT NOT NULL,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);

CREATE TABLE "emr_template" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "slug" VARCHAR(255) NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "status" VARCHAR(255) NOT NULL,
  "template_data" TEXT NOT NULL,
  "template_type" VARCHAR(255) NOT NULL,
  "default_format" VARCHAR(255) NOT NULL,
  "context" VARCHAR(255) NOT NULL,
  "description" TEXT NOT NULL,
  "created_by_id" INTEGER,
  "facility_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id")
);


CREATE INDEX "idx_users_skill_created_date_2" ON "users_skill" ("created_date");

CREATE INDEX "idx_users_skill_modified_date_3" ON "users_skill" ("modified_date");

CREATE INDEX "idx_users_skill_deleted_4" ON "users_skill" ("deleted");


CREATE INDEX "idx_users_userskill_created_date_2" ON "users_userskill" ("created_date");

CREATE INDEX "idx_users_userskill_modified_date_3" ON "users_userskill" ("modified_date");

CREATE INDEX "idx_users_userskill_deleted_4" ON "users_userskill" ("deleted");

CREATE INDEX "idx_users_userflag_external_id_1" ON "users_userflag" ("external_id");

CREATE INDEX "idx_users_userflag_created_date_2" ON "users_userflag" ("created_date");

CREATE INDEX "idx_users_userflag_modified_date_3" ON "users_userflag" ("modified_date");

CREATE INDEX "idx_users_userflag_deleted_4" ON "users_userflag" ("deleted");


CREATE INDEX "idx_users_user_deleted_2" ON "users_user" ("deleted");


CREATE INDEX "idx_security_permissionmodel_created_date_2" ON "security_permissionmodel" ("created_date");

CREATE INDEX "idx_security_permissionmodel_modified_date_3" ON "security_permissionmodel" ("modified_date");

CREATE INDEX "idx_security_permissionmodel_deleted_4" ON "security_permissionmodel" ("deleted");



CREATE INDEX "idx_security_rolemodel_created_date_2" ON "security_rolemodel" ("created_date");

CREATE INDEX "idx_security_rolemodel_modified_date_3" ON "security_rolemodel" ("modified_date");

CREATE INDEX "idx_security_rolemodel_deleted_4" ON "security_rolemodel" ("deleted");


CREATE INDEX "idx_security_roleassociation_created_date_2" ON "security_roleassociation" ("created_date");

CREATE INDEX "idx_security_roleassociation_modified_date_3" ON "security_roleassociation" ("modified_date");

CREATE INDEX "idx_security_roleassociation_deleted_4" ON "security_roleassociation" ("deleted");


CREATE INDEX "idx_security_rolepermission_created_date_2" ON "security_rolepermission" ("created_date");

CREATE INDEX "idx_security_rolepermission_modified_date_3" ON "security_rolepermission" ("modified_date");

CREATE INDEX "idx_security_rolepermission_deleted_4" ON "security_rolepermission" ("deleted");


CREATE INDEX "idx_facility_facility_created_date_2" ON "facility_facility" ("created_date");

CREATE INDEX "idx_facility_facility_modified_date_3" ON "facility_facility" ("modified_date");

CREATE INDEX "idx_facility_facility_deleted_4" ON "facility_facility" ("deleted");


CREATE INDEX "idx_emr_organization_created_date_2" ON "emr_organization" ("created_date");

CREATE INDEX "idx_emr_organization_modified_date_3" ON "emr_organization" ("modified_date");

CREATE INDEX "idx_emr_organization_deleted_4" ON "emr_organization" ("deleted");


CREATE INDEX "idx_emr_patient_created_date_2" ON "emr_patient" ("created_date");

CREATE INDEX "idx_emr_patient_modified_date_3" ON "emr_patient" ("modified_date");

CREATE INDEX "idx_emr_patient_deleted_4" ON "emr_patient" ("deleted");


CREATE INDEX "idx_emr_encounter_created_date_2" ON "emr_encounter" ("created_date");

CREATE INDEX "idx_emr_encounter_modified_date_3" ON "emr_encounter" ("modified_date");

CREATE INDEX "idx_emr_encounter_deleted_4" ON "emr_encounter" ("deleted");


CREATE INDEX "idx_emr_facilityorganization_created_date_2" ON "emr_facilityorganization" ("created_date");

CREATE INDEX "idx_emr_facilityorganization_modified_date_3" ON "emr_facilityorganization" ("modified_date");

CREATE INDEX "idx_emr_facilityorganization_deleted_4" ON "emr_facilityorganization" ("deleted");


CREATE INDEX "idx_emr_encounterorganization_created_date_2" ON "emr_encounterorganization" ("created_date");

CREATE INDEX "idx_emr_encounterorganization_modified_date_3" ON "emr_encounterorganization" ("modified_date");

CREATE INDEX "idx_emr_encounterorganization_deleted_4" ON "emr_encounterorganization" ("deleted");


CREATE INDEX "idx_emr_facilityorganizationuser_created_date_2" ON "emr_facilityorganizationuser" ("created_date");

CREATE INDEX "idx_emr_facilityorganizationuser_modified_date_3" ON "emr_facilityorganizationuser" ("modified_date");

CREATE INDEX "idx_emr_facilityorganizationuser_deleted_4" ON "emr_facilityorganizationuser" ("deleted");


CREATE INDEX "idx_emr_organizationuser_created_date_2" ON "emr_organizationuser" ("created_date");

CREATE INDEX "idx_emr_organizationuser_modified_date_3" ON "emr_organizationuser" ("modified_date");

CREATE INDEX "idx_emr_organizationuser_deleted_4" ON "emr_organizationuser" ("deleted");


CREATE INDEX "idx_emr_medicationstatement_created_date_2" ON "emr_medicationstatement" ("created_date");

CREATE INDEX "idx_emr_medicationstatement_modified_date_3" ON "emr_medicationstatement" ("modified_date");

CREATE INDEX "idx_emr_medicationstatement_deleted_4" ON "emr_medicationstatement" ("deleted");


CREATE INDEX "idx_emr_medicationrequest_created_date_2" ON "emr_medicationrequest" ("created_date");

CREATE INDEX "idx_emr_medicationrequest_modified_date_3" ON "emr_medicationrequest" ("modified_date");

CREATE INDEX "idx_emr_medicationrequest_deleted_4" ON "emr_medicationrequest" ("deleted");


CREATE INDEX "idx_emr_medicationadministration_created_date_2" ON "emr_medicationadministration" ("created_date");

CREATE INDEX "idx_emr_medicationadministration_modified_date_3" ON "emr_medicationadministration" ("modified_date");

CREATE INDEX "idx_emr_medicationadministration_deleted_4" ON "emr_medicationadministration" ("deleted");


CREATE INDEX "idx_emr_condition_created_date_2" ON "emr_condition" ("created_date");

CREATE INDEX "idx_emr_condition_modified_date_3" ON "emr_condition" ("modified_date");

CREATE INDEX "idx_emr_condition_deleted_4" ON "emr_condition" ("deleted");


CREATE INDEX "idx_emr_allergyintolerance_created_date_2" ON "emr_allergyintolerance" ("created_date");

CREATE INDEX "idx_emr_allergyintolerance_modified_date_3" ON "emr_allergyintolerance" ("modified_date");

CREATE INDEX "idx_emr_allergyintolerance_deleted_4" ON "emr_allergyintolerance" ("deleted");


CREATE INDEX "idx_emr_patientorganization_created_date_2" ON "emr_patientorganization" ("created_date");

CREATE INDEX "idx_emr_patientorganization_modified_date_3" ON "emr_patientorganization" ("modified_date");

CREATE INDEX "idx_emr_patientorganization_deleted_4" ON "emr_patientorganization" ("deleted");


CREATE INDEX "idx_emr_patientuser_created_date_2" ON "emr_patientuser" ("created_date");

CREATE INDEX "idx_emr_patientuser_modified_date_3" ON "emr_patientuser" ("modified_date");

CREATE INDEX "idx_emr_patientuser_deleted_4" ON "emr_patientuser" ("deleted");


CREATE INDEX "idx_emr_questionnaire_created_date_2" ON "emr_questionnaire" ("created_date");

CREATE INDEX "idx_emr_questionnaire_modified_date_3" ON "emr_questionnaire" ("modified_date");

CREATE INDEX "idx_emr_questionnaire_deleted_4" ON "emr_questionnaire" ("deleted");


CREATE INDEX "idx_emr_questionnaireresponse_created_date_2" ON "emr_questionnaireresponse" ("created_date");

CREATE INDEX "idx_emr_questionnaireresponse_modified_date_3" ON "emr_questionnaireresponse" ("modified_date");

CREATE INDEX "idx_emr_questionnaireresponse_deleted_4" ON "emr_questionnaireresponse" ("deleted");


CREATE INDEX "idx_emr_observation_created_date_2" ON "emr_observation" ("created_date");

CREATE INDEX "idx_emr_observation_modified_date_3" ON "emr_observation" ("modified_date");

CREATE INDEX "idx_emr_observation_deleted_4" ON "emr_observation" ("deleted");


CREATE INDEX "idx_emr_resourcerequest_created_date_2" ON "emr_resourcerequest" ("created_date");

CREATE INDEX "idx_emr_resourcerequest_modified_date_3" ON "emr_resourcerequest" ("modified_date");

CREATE INDEX "idx_emr_resourcerequest_deleted_4" ON "emr_resourcerequest" ("deleted");


CREATE INDEX "idx_emr_resourcerequestcomment_created_date_2" ON "emr_resourcerequestcomment" ("created_date");

CREATE INDEX "idx_emr_resourcerequestcomment_modified_date_3" ON "emr_resourcerequestcomment" ("modified_date");

CREATE INDEX "idx_emr_resourcerequestcomment_deleted_4" ON "emr_resourcerequestcomment" ("deleted");


CREATE INDEX "idx_emr_schedulableresource_created_date_2" ON "emr_schedulableresource" ("created_date");

CREATE INDEX "idx_emr_schedulableresource_modified_date_3" ON "emr_schedulableresource" ("modified_date");

CREATE INDEX "idx_emr_schedulableresource_deleted_4" ON "emr_schedulableresource" ("deleted");


CREATE INDEX "idx_emr_availabilityexception_created_date_2" ON "emr_availabilityexception" ("created_date");

CREATE INDEX "idx_emr_availabilityexception_modified_date_3" ON "emr_availabilityexception" ("modified_date");

CREATE INDEX "idx_emr_availabilityexception_deleted_4" ON "emr_availabilityexception" ("deleted");


CREATE INDEX "idx_emr_schedule_created_date_2" ON "emr_schedule" ("created_date");

CREATE INDEX "idx_emr_schedule_modified_date_3" ON "emr_schedule" ("modified_date");

CREATE INDEX "idx_emr_schedule_deleted_4" ON "emr_schedule" ("deleted");


CREATE INDEX "idx_emr_availability_created_date_2" ON "emr_availability" ("created_date");

CREATE INDEX "idx_emr_availability_modified_date_3" ON "emr_availability" ("modified_date");

CREATE INDEX "idx_emr_availability_deleted_4" ON "emr_availability" ("deleted");


CREATE INDEX "idx_emr_tokenbooking_created_date_2" ON "emr_tokenbooking" ("created_date");

CREATE INDEX "idx_emr_tokenbooking_modified_date_3" ON "emr_tokenbooking" ("modified_date");

CREATE INDEX "idx_emr_tokenbooking_deleted_4" ON "emr_tokenbooking" ("deleted");


CREATE INDEX "idx_emr_tokenslot_created_date_2" ON "emr_tokenslot" ("created_date");

CREATE INDEX "idx_emr_tokenslot_modified_date_3" ON "emr_tokenslot" ("modified_date");

CREATE INDEX "idx_emr_tokenslot_deleted_4" ON "emr_tokenslot" ("deleted");


CREATE INDEX "idx_emr_valueset_created_date_2" ON "emr_valueset" ("created_date");

CREATE INDEX "idx_emr_valueset_modified_date_3" ON "emr_valueset" ("modified_date");

CREATE INDEX "idx_emr_valueset_deleted_4" ON "emr_valueset" ("deleted");


CREATE INDEX "idx_emr_facilitylocation_created_date_2" ON "emr_facilitylocation" ("created_date");

CREATE INDEX "idx_emr_facilitylocation_modified_date_3" ON "emr_facilitylocation" ("modified_date");

CREATE INDEX "idx_emr_facilitylocation_deleted_4" ON "emr_facilitylocation" ("deleted");


CREATE INDEX "idx_emr_facilitylocationorganization_created_date_2" ON "emr_facilitylocationorganization" ("created_date");

CREATE INDEX "idx_emr_facilitylocationorganization_modified_date_3" ON "emr_facilitylocationorganization" ("modified_date");

CREATE INDEX "idx_emr_facilitylocationorganization_deleted_4" ON "emr_facilitylocationorganization" ("deleted");


CREATE INDEX "idx_emr_facilitylocationencounter_created_date_2" ON "emr_facilitylocationencounter" ("created_date");

CREATE INDEX "idx_emr_facilitylocationencounter_modified_date_3" ON "emr_facilitylocationencounter" ("modified_date");

CREATE INDEX "idx_emr_facilitylocationencounter_deleted_4" ON "emr_facilitylocationencounter" ("deleted");


CREATE INDEX "idx_emr_consent_created_date_2" ON "emr_consent" ("created_date");

CREATE INDEX "idx_emr_consent_modified_date_3" ON "emr_consent" ("modified_date");

CREATE INDEX "idx_emr_consent_deleted_4" ON "emr_consent" ("deleted");


CREATE INDEX "idx_emr_device_created_date_2" ON "emr_device" ("created_date");

CREATE INDEX "idx_emr_device_modified_date_3" ON "emr_device" ("modified_date");

CREATE INDEX "idx_emr_device_deleted_4" ON "emr_device" ("deleted");


CREATE INDEX "idx_emr_account_created_date_2" ON "emr_account" ("created_date");

CREATE INDEX "idx_emr_account_modified_date_3" ON "emr_account" ("modified_date");

CREATE INDEX "idx_emr_account_deleted_4" ON "emr_account" ("deleted");


CREATE INDEX "idx_emr_diagnosticreport_created_date_2" ON "emr_diagnosticreport" ("created_date");

CREATE INDEX "idx_emr_diagnosticreport_modified_date_3" ON "emr_diagnosticreport" ("modified_date");

CREATE INDEX "idx_emr_diagnosticreport_deleted_4" ON "emr_diagnosticreport" ("deleted");


CREATE INDEX "idx_emr_healthcareservice_created_date_2" ON "emr_healthcareservice" ("created_date");

CREATE INDEX "idx_emr_healthcareservice_modified_date_3" ON "emr_healthcareservice" ("modified_date");

CREATE INDEX "idx_emr_healthcareservice_deleted_4" ON "emr_healthcareservice" ("deleted");


CREATE INDEX "idx_emr_formsubmission_created_date_2" ON "emr_formsubmission" ("created_date");

CREATE INDEX "idx_emr_formsubmission_modified_date_3" ON "emr_formsubmission" ("modified_date");

CREATE INDEX "idx_emr_formsubmission_deleted_4" ON "emr_formsubmission" ("deleted");


CREATE INDEX "idx_emr_template_created_date_2" ON "emr_template" ("created_date");

CREATE INDEX "idx_emr_template_modified_date_3" ON "emr_template" ("modified_date");

CREATE INDEX "idx_emr_template_deleted_4" ON "emr_template" ("deleted");

CREATE TABLE "emr_clinical_notes" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "title" VARCHAR(255),
  "message" TEXT NOT NULL,
  "patient_id" BIGINT NOT NULL,
  "encounter_id" BIGINT,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id"),
  FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id"),
  FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id"),
  FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id")
);

CREATE TABLE "emr_device_history" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "event_type" VARCHAR(64) NOT NULL,
  "start" TIMESTAMP,
  "end" TIMESTAMP,
  "serviced_on" TIMESTAMP,
  "note" TEXT,
  "device_id" BIGINT NOT NULL,
  "encounter_id" BIGINT,
  "location_id" BIGINT,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  FOREIGN KEY ("device_id") REFERENCES "emr_device" ("id"),
  FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id"),
  FOREIGN KEY ("location_id") REFERENCES "emr_facilitylocation" ("id"),
  FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id"),
  FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id")
);

CREATE TABLE "emr_file_artifacts" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "internal_name" VARCHAR(255) NOT NULL,
  "associating_id" VARCHAR(255) NOT NULL,
  "file_type" VARCHAR(255),
  "file_category" VARCHAR(255),
  "report_type" VARCHAR(255),
  "upload_completed" BOOLEAN NOT NULL,
  "is_archived" BOOLEAN NOT NULL,
  "archive_reason" TEXT,
  "archived_datetime" TIMESTAMP,
  "archived_by_id" INTEGER,
  "created_by_id" INTEGER,
  "template_id" BIGINT,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  FOREIGN KEY ("archived_by_id") REFERENCES "users_user" ("id"),
  FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id"),
  FOREIGN KEY ("template_id") REFERENCES "emr_template" ("id"),
  FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id")
);

CREATE TABLE "emr_questionnaire_scope" (
  "id" BIGINT NOT NULL,
  "external_id" UUID NOT NULL,
  "created_date" TIMESTAMP,
  "modified_date" TIMESTAMP,
  "deleted" BOOLEAN NOT NULL,
  "history" JSONB NOT NULL,
  "meta" JSONB NOT NULL,
  "scope_type" VARCHAR(64) NOT NULL,
  "organization_id" BIGINT,
  "facility_organization_id" BIGINT,
  "questionnaire_id" BIGINT NOT NULL,
  "created_by_id" INTEGER,
  "updated_by_id" INTEGER,
  PRIMARY KEY ("id"),
  UNIQUE ("external_id"),
  FOREIGN KEY ("organization_id") REFERENCES "emr_organization" ("id"),
  FOREIGN KEY ("facility_organization_id") REFERENCES "emr_facilityorganization" ("id"),
  FOREIGN KEY ("questionnaire_id") REFERENCES "emr_questionnaire" ("id"),
  FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id"),
  FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id")
);

ALTER TABLE "users_userskill" ADD CONSTRAINT "fk_users_userskill_skill_id_1" FOREIGN KEY ("skill_id") REFERENCES "users_skill" ("id");

ALTER TABLE "users_userskill" ADD CONSTRAINT "fk_users_userskill_user_id_2" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "users_userflag" ADD CONSTRAINT "fk_users_userflag_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "users_user" ADD CONSTRAINT "fk_users_user_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "users_user" ADD CONSTRAINT "fk_users_user_geo_organization_id_2" FOREIGN KEY ("geo_organization_id") REFERENCES "emr_organization" ("id");

ALTER TABLE "security_roleassociation" ADD CONSTRAINT "fk_security_roleassociation_user_id_1" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "security_roleassociation" ADD CONSTRAINT "fk_security_roleassociation_role_id_2" FOREIGN KEY ("role_id") REFERENCES "security_rolemodel" ("id");

ALTER TABLE "security_rolepermission" ADD CONSTRAINT "fk_security_rolepermission_permission_id_1" FOREIGN KEY ("permission_id") REFERENCES "security_permissionmodel" ("id");

ALTER TABLE "security_rolepermission" ADD CONSTRAINT "fk_security_rolepermission_role_id_2" FOREIGN KEY ("role_id") REFERENCES "security_rolemodel" ("id");

ALTER TABLE "facility_facility" ADD CONSTRAINT "fk_facility_facility_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_organization" ADD CONSTRAINT "fk_emr_organization_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_organization" ADD CONSTRAINT "fk_emr_organization_parent_id_2" FOREIGN KEY ("parent_id") REFERENCES "emr_organization" ("id");

ALTER TABLE "emr_organization" ADD CONSTRAINT "fk_emr_organization_root_org_id_3" FOREIGN KEY ("root_org_id") REFERENCES "emr_organization" ("id");

ALTER TABLE "emr_organization" ADD CONSTRAINT "fk_emr_organization_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_patient" ADD CONSTRAINT "fk_emr_patient_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_patient" ADD CONSTRAINT "fk_emr_patient_geo_organization_id_2" FOREIGN KEY ("geo_organization_id") REFERENCES "emr_organization" ("id");

ALTER TABLE "emr_patient" ADD CONSTRAINT "fk_emr_patient_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_encounter" ADD CONSTRAINT "fk_emr_encounter_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_encounter" ADD CONSTRAINT "fk_emr_encounter_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_encounter" ADD CONSTRAINT "fk_emr_encounter_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_encounter" ADD CONSTRAINT "fk_emr_encounter_patient_id_4" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_encounter" ADD CONSTRAINT "fk_emr_encounter_appointment_id_5" FOREIGN KEY ("appointment_id") REFERENCES "emr_tokenbooking" ("id");

ALTER TABLE "emr_encounter" ADD CONSTRAINT "fk_emr_encounter_current_location_id_6" FOREIGN KEY ("current_location_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_facilityorganization" ADD CONSTRAINT "fk_emr_facilityorganization_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilityorganization" ADD CONSTRAINT "fk_emr_facilityorganization_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_facilityorganization" ADD CONSTRAINT "fk_emr_facilityorganization_parent_id_3" FOREIGN KEY ("parent_id") REFERENCES "emr_facilityorganization" ("id");

ALTER TABLE "emr_facilityorganization" ADD CONSTRAINT "fk_emr_facilityorganization_root_org_id_4" FOREIGN KEY ("root_org_id") REFERENCES "emr_facilityorganization" ("id");

ALTER TABLE "emr_facilityorganization" ADD CONSTRAINT "fk_emr_facilityorganization_updated_by_id_5" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_encounterorganization" ADD CONSTRAINT "fk_emr_encounterorganization_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_encounterorganization" ADD CONSTRAINT "fk_emr_encounterorganization_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_encounterorganization" ADD CONSTRAINT "fk_emr_encounterorganization_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_encounterorganization" ADD CONSTRAINT "fk_emr_encounterorganization_organization_id_4" FOREIGN KEY ("organization_id") REFERENCES "emr_facilityorganization" ("id");

ALTER TABLE "emr_facilityorganizationuser" ADD CONSTRAINT "fk_emr_facilityorganizationuser_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilityorganizationuser" ADD CONSTRAINT "fk_emr_facilityorganizationuser_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "emr_facilityorganization" ("id");

ALTER TABLE "emr_facilityorganizationuser" ADD CONSTRAINT "fk_emr_facilityorganizationuser_role_id_3" FOREIGN KEY ("role_id") REFERENCES "security_rolemodel" ("id");

ALTER TABLE "emr_facilityorganizationuser" ADD CONSTRAINT "fk_emr_facilityorganizationuser_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilityorganizationuser" ADD CONSTRAINT "fk_emr_facilityorganizationuser_user_id_5" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_organizationuser" ADD CONSTRAINT "fk_emr_organizationuser_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_organizationuser" ADD CONSTRAINT "fk_emr_organizationuser_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "emr_organization" ("id");

ALTER TABLE "emr_organizationuser" ADD CONSTRAINT "fk_emr_organizationuser_role_id_3" FOREIGN KEY ("role_id") REFERENCES "security_rolemodel" ("id");

ALTER TABLE "emr_organizationuser" ADD CONSTRAINT "fk_emr_organizationuser_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_organizationuser" ADD CONSTRAINT "fk_emr_organizationuser_user_id_5" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationstatement" ADD CONSTRAINT "fk_emr_medicationstatement_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationstatement" ADD CONSTRAINT "fk_emr_medicationstatement_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_medicationstatement" ADD CONSTRAINT "fk_emr_medicationstatement_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationstatement" ADD CONSTRAINT "fk_emr_medicationstatement_patient_id_4" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_medicationrequest" ADD CONSTRAINT "fk_emr_medicationrequest_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationrequest" ADD CONSTRAINT "fk_emr_medicationrequest_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_medicationrequest" ADD CONSTRAINT "fk_emr_medicationrequest_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationrequest" ADD CONSTRAINT "fk_emr_medicationrequest_patient_id_4" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_medicationadministration" ADD CONSTRAINT "fk_emr_medicationadministration_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationadministration" ADD CONSTRAINT "fk_emr_medicationadministration_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_medicationadministration" ADD CONSTRAINT "fk_emr_medicationadministration_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_medicationadministration" ADD CONSTRAINT "fk_emr_medicationadministration_request_id_4" FOREIGN KEY ("request_id") REFERENCES "emr_medicationrequest" ("id");

ALTER TABLE "emr_medicationadministration" ADD CONSTRAINT "fk_emr_medicationadministration_patient_id_5" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_condition" ADD CONSTRAINT "fk_emr_condition_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_condition" ADD CONSTRAINT "fk_emr_condition_updated_by_id_2" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_condition" ADD CONSTRAINT "fk_emr_condition_encounter_id_3" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_condition" ADD CONSTRAINT "fk_emr_condition_patient_id_4" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_allergyintolerance" ADD CONSTRAINT "fk_emr_allergyintolerance_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_allergyintolerance" ADD CONSTRAINT "fk_emr_allergyintolerance_updated_by_id_2" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_allergyintolerance" ADD CONSTRAINT "fk_emr_allergyintolerance_encounter_id_3" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_allergyintolerance" ADD CONSTRAINT "fk_emr_allergyintolerance_patient_id_4" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_patientorganization" ADD CONSTRAINT "fk_emr_patientorganization_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_patientorganization" ADD CONSTRAINT "fk_emr_patientorganization_organization_id_2" FOREIGN KEY ("organization_id") REFERENCES "emr_organization" ("id");

ALTER TABLE "emr_patientorganization" ADD CONSTRAINT "fk_emr_patientorganization_patient_id_3" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_patientorganization" ADD CONSTRAINT "fk_emr_patientorganization_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_patientuser" ADD CONSTRAINT "fk_emr_patientuser_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_patientuser" ADD CONSTRAINT "fk_emr_patientuser_patient_id_2" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_patientuser" ADD CONSTRAINT "fk_emr_patientuser_role_id_3" FOREIGN KEY ("role_id") REFERENCES "security_rolemodel" ("id");

ALTER TABLE "emr_patientuser" ADD CONSTRAINT "fk_emr_patientuser_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_patientuser" ADD CONSTRAINT "fk_emr_patientuser_user_id_5" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_questionnaire" ADD CONSTRAINT "fk_emr_questionnaire_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_questionnaire" ADD CONSTRAINT "fk_emr_questionnaire_updated_by_id_2" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_questionnaireresponse" ADD CONSTRAINT "fk_emr_questionnaireresponse_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_questionnaireresponse" ADD CONSTRAINT "fk_emr_questionnaireresponse_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_questionnaireresponse" ADD CONSTRAINT "fk_emr_questionnaireresponse_patient_id_3" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_questionnaireresponse" ADD CONSTRAINT "fk_emr_questionnaireresponse_questionnaire_id_4" FOREIGN KEY ("questionnaire_id") REFERENCES "emr_questionnaire" ("id");

ALTER TABLE "emr_questionnaireresponse" ADD CONSTRAINT "fk_emr_questionnaireresponse_updated_by_id_5" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_observation" ADD CONSTRAINT "fk_emr_observation_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_observation" ADD CONSTRAINT "fk_emr_observation_data_entered_by_id_2" FOREIGN KEY ("data_entered_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_observation" ADD CONSTRAINT "fk_emr_observation_encounter_id_3" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_observation" ADD CONSTRAINT "fk_emr_observation_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_observation" ADD CONSTRAINT "fk_emr_observation_patient_id_5" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_observation" ADD CONSTRAINT "fk_emr_observation_questionnaire_response_id_6" FOREIGN KEY ("questionnaire_response_id") REFERENCES "emr_questionnaireresponse" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_approving_facility_id_1" FOREIGN KEY ("approving_facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_assigned_facility_id_2" FOREIGN KEY ("assigned_facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_assigned_to_id_3" FOREIGN KEY ("assigned_to_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_created_by_id_4" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_origin_facility_id_5" FOREIGN KEY ("origin_facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_related_patient_id_6" FOREIGN KEY ("related_patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_resourcerequest" ADD CONSTRAINT "fk_emr_resourcerequest_updated_by_id_7" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_resourcerequestcomment" ADD CONSTRAINT "fk_emr_resourcerequestcomment_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_resourcerequestcomment" ADD CONSTRAINT "fk_emr_resourcerequestcomment_request_id_2" FOREIGN KEY ("request_id") REFERENCES "emr_resourcerequest" ("id");

ALTER TABLE "emr_resourcerequestcomment" ADD CONSTRAINT "fk_emr_resourcerequestcomment_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_schedulableresource" ADD CONSTRAINT "fk_emr_schedulableresource_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_schedulableresource" ADD CONSTRAINT "fk_emr_schedulableresource_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_schedulableresource" ADD CONSTRAINT "fk_emr_schedulableresource_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_schedulableresource" ADD CONSTRAINT "fk_emr_schedulableresource_user_id_4" FOREIGN KEY ("user_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_schedulableresource" ADD CONSTRAINT "fk_emr_schedulableresource_healthcare_service_id_5" FOREIGN KEY ("healthcare_service_id") REFERENCES "emr_healthcareservice" ("id");

ALTER TABLE "emr_schedulableresource" ADD CONSTRAINT "fk_emr_schedulableresource_location_id_6" FOREIGN KEY ("location_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_availabilityexception" ADD CONSTRAINT "fk_emr_availabilityexception_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_availabilityexception" ADD CONSTRAINT "fk_emr_availabilityexception_updated_by_id_2" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_availabilityexception" ADD CONSTRAINT "fk_emr_availabilityexception_resource_id_3" FOREIGN KEY ("resource_id") REFERENCES "emr_schedulableresource" ("id");

ALTER TABLE "emr_schedule" ADD CONSTRAINT "fk_emr_schedule_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_schedule" ADD CONSTRAINT "fk_emr_schedule_resource_id_2" FOREIGN KEY ("resource_id") REFERENCES "emr_schedulableresource" ("id");

ALTER TABLE "emr_schedule" ADD CONSTRAINT "fk_emr_schedule_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_availability" ADD CONSTRAINT "fk_emr_availability_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_availability" ADD CONSTRAINT "fk_emr_availability_updated_by_id_2" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_availability" ADD CONSTRAINT "fk_emr_availability_schedule_id_3" FOREIGN KEY ("schedule_id") REFERENCES "emr_schedule" ("id");

ALTER TABLE "emr_tokenbooking" ADD CONSTRAINT "fk_emr_tokenbooking_booked_by_id_1" FOREIGN KEY ("booked_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_tokenbooking" ADD CONSTRAINT "fk_emr_tokenbooking_created_by_id_2" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_tokenbooking" ADD CONSTRAINT "fk_emr_tokenbooking_patient_id_3" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_tokenbooking" ADD CONSTRAINT "fk_emr_tokenbooking_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_tokenbooking" ADD CONSTRAINT "fk_emr_tokenbooking_token_slot_id_5" FOREIGN KEY ("token_slot_id") REFERENCES "emr_tokenslot" ("id");

ALTER TABLE "emr_tokenslot" ADD CONSTRAINT "fk_emr_tokenslot_availability_id_1" FOREIGN KEY ("availability_id") REFERENCES "emr_availability" ("id");

ALTER TABLE "emr_tokenslot" ADD CONSTRAINT "fk_emr_tokenslot_created_by_id_2" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_tokenslot" ADD CONSTRAINT "fk_emr_tokenslot_resource_id_3" FOREIGN KEY ("resource_id") REFERENCES "emr_schedulableresource" ("id");

ALTER TABLE "emr_tokenslot" ADD CONSTRAINT "fk_emr_tokenslot_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_valueset" ADD CONSTRAINT "fk_emr_valueset_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_valueset" ADD CONSTRAINT "fk_emr_valueset_updated_by_id_2" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilitylocation" ADD CONSTRAINT "fk_emr_facilitylocation_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilitylocation" ADD CONSTRAINT "fk_emr_facilitylocation_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_facilitylocation" ADD CONSTRAINT "fk_emr_facilitylocation_parent_id_3" FOREIGN KEY ("parent_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_facilitylocation" ADD CONSTRAINT "fk_emr_facilitylocation_root_location_id_4" FOREIGN KEY ("root_location_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_facilitylocation" ADD CONSTRAINT "fk_emr_facilitylocation_updated_by_id_5" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilitylocationorganization" ADD CONSTRAINT "fk_emr_facilitylocationorganization_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilitylocationorganization" ADD CONSTRAINT "fk_emr_facilitylocationorganization_location_id_2" FOREIGN KEY ("location_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_facilitylocationorganization" ADD CONSTRAINT "fk_emr_facilitylocationorganization_organization_id_3" FOREIGN KEY ("organization_id") REFERENCES "emr_facilityorganization" ("id");

ALTER TABLE "emr_facilitylocationorganization" ADD CONSTRAINT "fk_emr_facilitylocationorganization_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilitylocationencounter" ADD CONSTRAINT "fk_emr_facilitylocationencounter_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_facilitylocationencounter" ADD CONSTRAINT "fk_emr_facilitylocationencounter_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_facilitylocationencounter" ADD CONSTRAINT "fk_emr_facilitylocationencounter_location_id_3" FOREIGN KEY ("location_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_facilitylocationencounter" ADD CONSTRAINT "fk_emr_facilitylocationencounter_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_consent" ADD CONSTRAINT "fk_emr_consent_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_consent" ADD CONSTRAINT "fk_emr_consent_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_consent" ADD CONSTRAINT "fk_emr_consent_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_device" ADD CONSTRAINT "fk_emr_device_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_device" ADD CONSTRAINT "fk_emr_device_current_encounter_id_2" FOREIGN KEY ("current_encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_device" ADD CONSTRAINT "fk_emr_device_current_location_id_3" FOREIGN KEY ("current_location_id") REFERENCES "emr_facilitylocation" ("id");

ALTER TABLE "emr_device" ADD CONSTRAINT "fk_emr_device_facility_id_4" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_device" ADD CONSTRAINT "fk_emr_device_managing_organization_id_5" FOREIGN KEY ("managing_organization_id") REFERENCES "emr_facilityorganization" ("id");

ALTER TABLE "emr_device" ADD CONSTRAINT "fk_emr_device_updated_by_id_6" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_account" ADD CONSTRAINT "fk_emr_account_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_account" ADD CONSTRAINT "fk_emr_account_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_account" ADD CONSTRAINT "fk_emr_account_patient_id_3" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_account" ADD CONSTRAINT "fk_emr_account_updated_by_id_4" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_diagnosticreport" ADD CONSTRAINT "fk_emr_diagnosticreport_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_diagnosticreport" ADD CONSTRAINT "fk_emr_diagnosticreport_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_diagnosticreport" ADD CONSTRAINT "fk_emr_diagnosticreport_facility_id_3" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_diagnosticreport" ADD CONSTRAINT "fk_emr_diagnosticreport_patient_id_4" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_diagnosticreport" ADD CONSTRAINT "fk_emr_diagnosticreport_updated_by_id_5" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_healthcareservice" ADD CONSTRAINT "fk_emr_healthcareservice_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_healthcareservice" ADD CONSTRAINT "fk_emr_healthcareservice_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_healthcareservice" ADD CONSTRAINT "fk_emr_healthcareservice_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_formsubmission" ADD CONSTRAINT "fk_emr_formsubmission_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_formsubmission" ADD CONSTRAINT "fk_emr_formsubmission_encounter_id_2" FOREIGN KEY ("encounter_id") REFERENCES "emr_encounter" ("id");

ALTER TABLE "emr_formsubmission" ADD CONSTRAINT "fk_emr_formsubmission_patient_id_3" FOREIGN KEY ("patient_id") REFERENCES "emr_patient" ("id");

ALTER TABLE "emr_formsubmission" ADD CONSTRAINT "fk_emr_formsubmission_questionnaire_id_4" FOREIGN KEY ("questionnaire_id") REFERENCES "emr_questionnaire" ("id");

ALTER TABLE "emr_formsubmission" ADD CONSTRAINT "fk_emr_formsubmission_updated_by_id_5" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_template" ADD CONSTRAINT "fk_emr_template_created_by_id_1" FOREIGN KEY ("created_by_id") REFERENCES "users_user" ("id");

ALTER TABLE "emr_template" ADD CONSTRAINT "fk_emr_template_facility_id_2" FOREIGN KEY ("facility_id") REFERENCES "facility_facility" ("id");

ALTER TABLE "emr_template" ADD CONSTRAINT "fk_emr_template_updated_by_id_3" FOREIGN KEY ("updated_by_id") REFERENCES "users_user" ("id");
