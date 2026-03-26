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

variable "db_instance_class" {
  description = "RDSインスタンスクラス"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "データベース名"
  type        = string
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "データベースパスワード"
  type        = string
  sensitive   = true
}

variable "multi_az" {
  description = "マルチAZ配置"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "削除保護"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "最終スナップショットをスキップ"
  type        = bool
  default     = true
}

variable "tags" {
  description = "共通タグ"
  type        = map(string)
  default     = {}
}
