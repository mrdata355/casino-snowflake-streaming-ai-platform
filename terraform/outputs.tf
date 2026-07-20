output "database_name" { value = snowflake_database.platform.name }
output "schema_names" { value = sort([for schema in snowflake_schema.layers : schema.name]) }
output "warehouse_names" { value = { for key, warehouse in snowflake_warehouse.workload : key => warehouse.name } }
output "resource_monitor_names" { value = { for key, monitor in snowflake_resource_monitor.workload : key => monitor.name } }
