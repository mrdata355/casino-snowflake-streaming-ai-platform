terraform {
  required_version = ">= 1.8.0"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.18.0"
    }
  }
}

provider "snowflake" {
  organization_name = var.snowflake_organization
  account_name      = var.snowflake_account
  user              = var.snowflake_user
  role              = var.snowflake_role
  authenticator     = "SNOWFLAKE_JWT"
  private_key       = var.snowflake_private_key
}
