variable "name_prefix" {
  description = "リソース名のプレフィックス"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "プライベートサブネットID"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "ECSセキュリティグループID"
  type        = string
}

variable "node_type" {
  description = "ElastiCacheノードタイプ"
  type        = string
  default     = "cache.t3.micro"
}

variable "tags" {
  description = "共通タグ"
  type        = map(string)
  default     = {}
}
