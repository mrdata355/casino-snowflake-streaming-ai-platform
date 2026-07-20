variable "environment" {
  type        = string
  description = "Deployment environment."
  validation {
    condition     = contains(["DEV", "QA", "PROD"], upper(var.environment))
    error_message = "environment must be DEV, QA, or PROD"
  }
}
variable "platform_prefix" { type = string; default = "CASINO" }
variable "snowflake_organization" { type = string; sensitive = true }
variable "snowflake_account" { type = string; sensitive = true }
variable "snowflake_user" { type = string; sensitive = true }
variable "snowflake_role" { type = string; default = "SYSADMIN" }
variable "snowflake_private_key" { type = string; sensitive = true }
variable "warehouse_sizes" {
  type = map(string)
  default = {
    ingest    = "XSMALL"
    transform = "SMALL"
    feature   = "SMALL"
    cortex    = "XSMALL"
  }
}
variable "monthly_credit_quotas" {
  type = map(number)
  default = {
    ingest    = 20
    transform = 40
    feature   = 30
    cortex    = 20
  }
}
