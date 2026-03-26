output "endpoint" {
  description = "RDSエンドポイント"
  value       = aws_db_instance.main.endpoint
}

output "address" {
  description = "RDSアドレス"
  value       = aws_db_instance.main.address
}

output "port" {
  description = "RDSポート"
  value       = aws_db_instance.main.port
}

output "database_url" {
  description = "データベース接続URL"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/${var.db_name}"
  sensitive   = true
}

output "security_group_id" {
  description = "RDSセキュリティグループID"
  value       = aws_security_group.rds.id
}
