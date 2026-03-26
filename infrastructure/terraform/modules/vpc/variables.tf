variable "name_prefix" {
  description = "リソース名のプレフィックス"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR ブロック"
  type        = string
}

variable "azs" {
  description = "使用するアベイラビリティゾーン"
  type        = list(string)
}

variable "tags" {
  description = "共通タグ"
  type        = map(string)
  default     = {}
}
