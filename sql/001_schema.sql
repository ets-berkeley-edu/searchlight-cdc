-- Direct Table CDC schema
-- Placeholders: {rds_schema_boa_app_rds_data}, {rds_app_boa_user}

CREATE SCHEMA IF NOT EXISTS {rds_schema_boa_app_rds_data};

GRANT USAGE
  ON SCHEMA {rds_schema_boa_app_rds_data}
  TO {rds_app_boa_user};

ALTER DEFAULT PRIVILEGES
  IN SCHEMA {rds_schema_boa_app_rds_data}
  GRANT SELECT ON TABLES TO {rds_app_boa_user};

COMMENT ON SCHEMA {rds_schema_boa_app_rds_data} IS
  'Direct Table CDC: search index for BOA-created advising notes and topics';
