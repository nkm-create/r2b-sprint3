variable "name_prefix" {
  description = "リソース名のプレフィックス"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "パブリックサブネットID"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "プライベートサブネットID"
  type        = list(string)
}

variable "backend_image" {
  description = "バックエンドDockerイメージ"
  type        = string
}

variable "frontend_image" {
  description = "フロントエンドDockerイメージ"
  type        = string
}

variable "backend_cpu" {
  description = "バックエンドCPU単位"
  type        = number
  default     = 256
}

variable "backend_memory" {
  description = "バックエンドメモリ (MB)"
  type        = number
  default     = 512
}

variable "frontend_cpu" {
  description = "フロントエンドCPU単位"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "フロントエンドメモリ (MB)"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "バックエンドタスク数"
  type        = number
  default     = 1
}

variable "frontend_desired_count" {
  description = "フロントエンドタスク数"
  type        = number
  default     = 1
}

variable "database_url" {
  description = "データベース接続URL"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Redis接続URL"
  type        = string
}

variable "tags" {
  description = "共通タグ"
  type        = map(string)
  default     = {}
}
