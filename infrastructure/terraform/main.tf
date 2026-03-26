# =============================================================================
# 学習塾時間割最適化システム - Terraform メイン設定
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # リモートステート設定（本番環境用）
  # backend "s3" {
  #   bucket         = "r2b-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "ap-northeast-1"
  #   encrypt        = true
  #   dynamodb_table = "r2b-terraform-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# =============================================================================
# データソース
# =============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# =============================================================================
# ローカル変数
# =============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  azs = slice(data.aws_availability_zones.available.names, 0, 2)

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# =============================================================================
# モジュール呼び出し
# =============================================================================

module "vpc" {
  source = "./modules/vpc"

  name_prefix = local.name_prefix
  vpc_cidr    = var.vpc_cidr
  azs         = local.azs

  tags = local.common_tags
}

module "rds" {
  source = "./modules/rds"

  name_prefix         = local.name_prefix
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  db_instance_class   = var.db_instance_class
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password

  ecs_security_group_id = module.ecs.ecs_security_group_id

  tags = local.common_tags
}

module "redis" {
  source = "./modules/redis"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_type          = var.redis_node_type

  ecs_security_group_id = module.ecs.ecs_security_group_id

  tags = local.common_tags
}

module "ecs" {
  source = "./modules/ecs"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids

  backend_image      = var.backend_image
  frontend_image     = var.frontend_image

  backend_cpu        = var.backend_cpu
  backend_memory     = var.backend_memory
  frontend_cpu       = var.frontend_cpu
  frontend_memory    = var.frontend_memory

  backend_desired_count  = var.backend_desired_count
  frontend_desired_count = var.frontend_desired_count

  database_url  = module.rds.database_url
  redis_url     = module.redis.redis_url

  tags = local.common_tags
}
