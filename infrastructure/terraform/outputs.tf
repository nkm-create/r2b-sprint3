# =============================================================================
# 学習塾時間割最適化システム - Terraform 出力定義
# =============================================================================

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "パブリックサブネットID"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "プライベートサブネットID"
  value       = module.vpc.private_subnet_ids
}

# -----------------------------------------------------------------------------
# RDS
# -----------------------------------------------------------------------------

output "rds_endpoint" {
  description = "RDSエンドポイント"
  value       = module.rds.endpoint
}

output "rds_port" {
  description = "RDSポート"
  value       = module.rds.port
}

# -----------------------------------------------------------------------------
# Redis
# -----------------------------------------------------------------------------

output "redis_endpoint" {
  description = "Redisエンドポイント"
  value       = module.redis.endpoint
}

# -----------------------------------------------------------------------------
# ECS
# -----------------------------------------------------------------------------

output "ecs_cluster_name" {
  description = "ECSクラスター名"
  value       = module.ecs.cluster_name
}

output "alb_dns_name" {
  description = "ALB DNS名"
  value       = module.ecs.alb_dns_name
}

output "backend_service_name" {
  description = "バックエンドサービス名"
  value       = module.ecs.backend_service_name
}

output "frontend_service_name" {
  description = "フロントエンドサービス名"
  value       = module.ecs.frontend_service_name
}
