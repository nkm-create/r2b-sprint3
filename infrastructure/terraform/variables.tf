# =============================================================================
# 学習塾時間割最適化システム - Terraform 変数定義
# =============================================================================

# -----------------------------------------------------------------------------
# 一般設定
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "プロジェクト名"
  type        = string
  default     = "r2b"
}

variable "environment" {
  description = "環境名 (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

# -----------------------------------------------------------------------------
# ネットワーク設定
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "VPC CIDR ブロック"
  type        = string
  default     = "10.0.0.0/16"
}

# -----------------------------------------------------------------------------
# データベース設定
# -----------------------------------------------------------------------------

variable "db_instance_class" {
  description = "RDS インスタンスクラス"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "データベース名"
  type        = string
  default     = "r2b"
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  default     = "r2b_admin"
  sensitive   = true
}

variable "db_password" {
  description = "データベースパスワード"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Redis設定
# -----------------------------------------------------------------------------

variable "redis_node_type" {
  description = "ElastiCache ノードタイプ"
  type        = string
  default     = "cache.t3.micro"
}

# -----------------------------------------------------------------------------
# ECS設定
# -----------------------------------------------------------------------------

variable "backend_image" {
  description = "バックエンドDockerイメージ"
  type        = string
  default     = ""
}

variable "frontend_image" {
  description = "フロントエンドDockerイメージ"
  type        = string
  default     = ""
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
