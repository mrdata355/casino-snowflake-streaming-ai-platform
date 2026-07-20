locals {
  env           = upper(var.environment)
  database_name = "${upper(var.platform_prefix)}_${local.env}"
  workloads     = toset(["ingest", "transform", "feature", "cortex"])
}

resource "snowflake_database" "platform" {
  name                        = local.database_name
  comment                     = "${local.env} synthetic casino lakehouse"
  data_retention_time_in_days = local.env == "PROD" ? 7 : 1
}

resource "snowflake_schema" "layers" {
  for_each = toset(["BRONZE", "SILVER", "GOLD", "SEMANTIC", "FEATURES", "OPS", "TEMP"])
  database = snowflake_database.platform.name
  name     = each.value
  comment  = "${each.value} layer for ${local.database_name}"
}

resource "snowflake_resource_monitor" "workload" {
  for_each         = local.workloads
  name             = "RM_${upper(each.key)}_${local.env}"
  credit_quota     = var.monthly_credit_quotas[each.key]
  frequency        = "MONTHLY"
  start_timestamp  = "IMMEDIATELY"
  notify_triggers  = [75, 90]
  suspend_trigger  = 100
  suspend_immediate_trigger = 110
}

resource "snowflake_warehouse" "workload" {
  for_each                    = local.workloads
  name                        = "WH_${upper(each.key)}_${local.env}"
  warehouse_size              = var.warehouse_sizes[each.key]
  auto_suspend                = each.key == "ingest" ? 60 : 120
  auto_resume                 = true
  initially_suspended         = true
  max_cluster_count           = local.env == "PROD" ? 3 : 1
  min_cluster_count           = 1
  scaling_policy              = "ECONOMY"
  resource_monitor            = snowflake_resource_monitor.workload[each.key].fully_qualified_name
  statement_timeout_in_seconds = each.key == "feature" ? 3600 : 1800
  comment                     = "Isolated ${each.key} compute for ${local.database_name}"
}
