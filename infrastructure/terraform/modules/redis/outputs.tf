output "endpoint" {
  description = "Redisエンドポイント"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "port" {
  description = "Redisポート"
  value       = aws_elasticache_cluster.main.port
}

output "redis_url" {
  description = "Redis接続URL"
  value       = "redis://${aws_elasticache_cluster.main.cache_nodes[0].address}:${aws_elasticache_cluster.main.port}"
}

output "security_group_id" {
  description = "Redisセキュリティグループ ID"
  value       = aws_security_group.redis.id
}
