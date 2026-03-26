output "cluster_id" {
  description = "ECSクラスターID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECSクラスター名"
  value       = aws_ecs_cluster.main.name
}

output "alb_dns_name" {
  description = "ALB DNS名"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "backend_service_name" {
  description = "バックエンドサービス名"
  value       = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  description = "フロントエンドサービス名"
  value       = aws_ecs_service.frontend.name
}

output "ecs_security_group_id" {
  description = "ECSセキュリティグループID"
  value       = aws_security_group.ecs.id
}
