# クラウド構成図

## 1. 概要

本ドキュメントは、学習塾時間割最適化システムのAWSインフラ構成を定義する。
インフラはTerraformでコード管理する。

### 1.1 参照ドキュメント

| ドキュメント | 内容 |
|------------|------|
| requirements-v1/non-functional-requirements.md | 非機能要件 |
| requirements-v1/P009_時間割作成画面.md | LLM活用仕様 |
| operations/operations-policy.md | 運用方針 |
| data/data-list.md | データ一覧（29エンティティ） |

### 1.2 設計原則

| 原則 | 説明 |
|------|------|
| IaC | Terraformで全インフラをコード管理 |
| コスト最適化 | インフラ月額 $80以内、LLMコスト $500以内（1000教室想定） |
| 必要十分 | 非機能要件を満たす最小構成 |
| マネージドサービス活用 | 運用負荷を下げるためAWSマネージドサービスを優先 |
| 段階的拡張 | 将来のスケールアウトに対応可能な設計 |

### 1.3 非機能要件との対応

| 非機能要件 | 目標値 | 本構成での対応 |
|-----------|--------|--------------|
| 月間稼働率 | 99.5% | ALB + Multi-AZ RDS + CloudWatch |
| 同時接続 | 100ユーザー | ECS Fargate + ALB |
| レスポンス | 1秒以内 | CloudFront + 適切なインデックス |
| LLMレスポンス | 500ms〜1.5秒 | Claude API直接呼び出し |
| RTO | 4時間 | RDS自動バックアップ + Terraform再構築 |
| RPO | 1時間 | RDS自動バックアップ（5分間隔） |

---

## 2. アーキテクチャ概要

### 2.1 技術選定

| レイヤー | 選定技術 | 選定理由 |
|---------|---------|---------|
| CDN | CloudFront | AWSネイティブ、S3連携容易 |
| フロントエンド | S3 + CloudFront | 静的ホスティング、低コスト |
| ロードバランサ | ALB | ヘルスチェック、HTTPS終端 |
| コンピュート | ECS Fargate | コンテナ管理不要、オートスケーリング |
| データベース | RDS PostgreSQL | マネージド、自動バックアップ |
| キャッシュ | ElastiCache Redis | マネージドRedis |
| ストレージ | S3 | 高耐久性、低コスト |
| 監視 | CloudWatch | AWSネイティブ監視 |
| シークレット | Secrets Manager | セキュアなシークレット管理 |
| **LLM API** | **Anthropic Claude API** | 説明生成、改善提案に使用 |

### 2.2 全体構成図

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Internet                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Route 53 (DNS)                                   │
│                         *.example.com                                    │
└─────────────────────────────────────────────────────────────────────────┘
          │                                           │
          │ 静的コンテンツ                              │ API (/api/*)
          ▼                                           ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ CloudFront               │              │ CloudFront               │
│ (Static Assets)          │              │ (API Distribution)       │
│                          │              │                          │
│ - Edge Cache             │              │ - HTTPS終端              │
│ - Gzip圧縮               │              │ - Cache無効              │
│ - S3オリジン             │              │ - ALBオリジン            │
└────────────┬─────────────┘              └────────────┬─────────────┘
             │                                         │
             ▼                                         ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ S3 Bucket                │              │ ALB (Application LB)     │
│ (Frontend)               │              │                          │
│                          │              │ - Target: ECS Fargate    │
│ - Next.js Static Export  │              │ - Health Check           │
│ - React SPA              │              │ - HTTPS (ACM証明書)       │
│                          │              │                          │
│ 月額: ~$1                │              │ 月額: ~$16               │
└──────────────────────────┘              └────────────┬─────────────┘
                                                       │
┌──────────────────────────────────────────────────────┼──────────────────┐
│                              VPC (10.0.0.0/16)       │                  │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     Public Subnets (Multi-AZ)                       ││
│  │  ┌─────────────────────┐        ┌─────────────────────┐             ││
│  │  │ NAT Gateway (AZ-a)  │        │ NAT Gateway (AZ-c)  │             ││
│  │  │ (※コスト削減時は1つ) │        │ (※本番のみ)        │             ││
│  │  └─────────────────────┘        └─────────────────────┘             ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                          │                              │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     Private Subnets (Multi-AZ)                      ││
│  │                                                                     ││
│  │   ┌─────────────────────────────────────────────────────────────┐   ││
│  │   │              ECS Fargate Cluster                            │   ││
│  │   │                                                             │   ││
│  │   │   ┌─────────────────┐    ┌─────────────────┐               │   ││
│  │   │   │ Backend Service │    │ Worker Service  │               │   ││
│  │   │   │ (FastAPI)       │    │ (Celery)        │               │   ││
│  │   │   │                 │    │                 │               │   ││
│  │   │   │ - 0.5 vCPU      │    │ - 1 vCPU        │               │   ││
│  │   │   │ - 1 GB RAM      │    │ - 2 GB RAM      │               │   ││
│  │   │   │ - 2 tasks       │    │ - 1 task        │               │   ││
│  │   │   │                 │    │ - OR-Tools      │               │   ││
│  │   │   └─────────────────┘    └─────────────────┘               │   ││
│  │   │                                                             │   ││
│  │   │   月額: ~$25 (Backend) + ~$18 (Worker)                      │   ││
│  │   └─────────────────────────────────────────────────────────────┘   ││
│  │                                                                     ││
│  │   ┌─────────────────────────────────────────────────────────────┐   ││
│  │   │ RDS PostgreSQL                  ElastiCache Redis           │   ││
│  │   │ (db.t4g.micro)                  (cache.t4g.micro)           │   ││
│  │   │                                                             │   ││
│  │   │ - Multi-AZ: Off (コスト削減)     - 1ノード                   │   ││
│  │   │ - 20GB gp3                      - セッション/キャッシュ       │   ││
│  │   │ - 自動バックアップ 7日           │                           │   ││
│  │   │                                                             │   ││
│  │   │ 月額: ~$13                      月額: ~$9                    │   ││
│  │   └─────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         外部サービス連携                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │ Anthropic       │  │ Google Sheets   │  │ SES             │          │
│  │ Claude API      │  │ API             │  │ (メール送信)     │          │
│  │                 │  │                 │  │                 │          │
│  │ - Evaluator説明 │  │ - 希望データ取込  │  │ - 通知メール     │          │
│  │ - Advisor提案   │  │                 │  │                 │          │
│  │                 │  │                 │  │                 │          │
│  │ 月額: ~$9       │  │ 月額: $0        │  │ 月額: ~$1        │          │
│  │ (100教室想定)   │  │                 │  │                 │          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. LLM連携設計

### 3.1 LLM使用箇所

P009時間割作成画面のエージェントアーキテクチャにおいて、以下でLLMを使用。

| コンポーネント | LLM用途 | 呼び出し頻度 |
|--------------|---------|-------------|
| Evaluator | 違反の説明生成、背景分析 | 改善ループごと（最大10回/生成） |
| Advisor | 改善提案、トレードオフ説明、対話応答 | 改善ループごと + ユーザー質問時 |

### 3.2 LLM API設計

```
┌───────────────────────────────────────────────────────────────┐
│ ECS Fargate (Backend)                                         │
│                                                               │
│  ┌─────────────────┐     ┌─────────────────┐                 │
│  │ Evaluator       │     │ Advisor         │                 │
│  │ Service         │     │ Service         │                 │
│  └────────┬────────┘     └────────┬────────┘                 │
│           │                       │                           │
│           └───────────┬───────────┘                           │
│                       ▼                                       │
│           ┌─────────────────────┐                             │
│           │ LLM Client          │                             │
│           │ (anthropic-sdk)     │                             │
│           │                     │                             │
│           │ - リトライ (3回)     │                             │
│           │ - タイムアウト (3秒)  │                             │
│           │ - フォールバック     │                             │
│           └──────────┬──────────┘                             │
│                      │                                        │
└──────────────────────┼────────────────────────────────────────┘
                       │ HTTPS (NAT Gateway経由)
                       ▼
              ┌─────────────────┐
              │ Anthropic API   │
              │ (Claude 3)      │
              │                 │
              │ api.anthropic.  │
              │ com             │
              └─────────────────┘
```

### 3.3 フォールバック機構

| 状況 | 検知方法 | 対応 |
|------|---------|------|
| API呼び出し失敗 | HTTPエラー/例外 | テンプレートベース出力 |
| レスポンス遅延（>3秒） | タイムアウト | テンプレート出力 |
| 出力パースエラー | JSONパース失敗 | 再試行（最大2回）→ テンプレート |
| APIレート制限 | 429エラー | 指数バックオフ + テンプレート |

### 3.4 LLMコスト管理

| 項目 | 設定値 |
|------|--------|
| 月額上限 | $500（1000教室想定） |
| 教室あたり上限 | $0.50/月 |
| アラート閾値 | 80%到達で通知 |
| 超過時対応 | テンプレートモードに切り替え |

**コスト見積もり（Claude 3 Haiku想定）**:

| 項目 | 計算 | 月額 |
|------|------|------|
| 時間割生成/月 | 4回/教室 × 100教室 | 400回 |
| LLM呼び出し/生成 | 20回（Evaluator 10 + Advisor 10） | 8,000回 |
| 入力トークン/回 | 2,000トークン | 16Mトークン |
| 出力トークン/回 | 500トークン | 4Mトークン |
| **合計コスト** | $0.25/1M入力 + $1.25/1M出力 | **約$9/月** |

---

## 4. コスト内訳

### 4.1 環境別コスト

#### Production（目標: $100以内）

| カテゴリ | サービス | スペック | 月額 | 備考 |
|---------|---------|---------|------|------|
| **ネットワーク** | Route 53 | 1 Hosted Zone | $0.50 | |
| | CloudFront | 100GB転送 | $8.50 | |
| | ALB | 1 ALB | $16.00 | |
| | NAT Gateway | 1個（AZ-a） | $32.00 | ※最大コスト要因 |
| **コンピュート** | ECS Fargate (Backend) | 0.5vCPU/1GB × 2 | $25.00 | |
| | ECS Fargate (Worker) | 1vCPU/2GB × 1 | $18.00 | OR-Tools用 |
| **データベース** | RDS PostgreSQL | db.t4g.micro | $13.00 | 20GB gp3 |
| | ElastiCache Redis | cache.t4g.micro | $9.00 | |
| **ストレージ** | S3 (Frontend) | 1GB | $0.02 | |
| | S3 (Backups) | 10GB | $0.23 | |
| **監視** | CloudWatch | Logs + Metrics | $5.00 | |
| | Secrets Manager | 5 secrets | $2.00 | |
| **メール** | SES | 1,000通/月 | $0.10 | |
| **AWSインフラ小計** | | | **$129** | |
| **LLM** | Anthropic Claude | 100教室想定 | **$9** | |
| **合計** | | | **$138** | |

#### コスト削減オプション

| 削減項目 | 変更内容 | 削減額 | 影響 |
|---------|---------|--------|------|
| NAT Gateway削除 | VPCエンドポイント使用 | -$32 | S3/ECR/SecretsManagerのみ対応 |
| Fargate Spot | Worker を Spot に | -$9 | 中断リスクあり |
| Reserved Capacity | 1年予約 | -20% | 長期コミット必要 |

**コスト削減後（推奨構成）**:

| 項目 | 月額 |
|------|------|
| AWS インフラ | $75 |
| LLM | $9 |
| **合計** | **$84** |

#### Staging

| サービス | スペック | 月額 | 備考 |
|---------|---------|------|------|
| CloudFront + S3 | - | $1 | |
| ALB | 1 | $16 | |
| ECS Fargate | 0.25vCPU/0.5GB × 1 | $9 | 最小構成 |
| RDS PostgreSQL | db.t4g.micro | $13 | |
| NAT Gateway | なし（VPCエンドポイント） | $0 | |
| **合計** | | **$39** | |

#### Development

| サービス | 月額 | 備考 |
|---------|------|------|
| ローカルDocker | $0 | docker-compose |
| LocalStack | $0 | AWS互換ローカル環境 |
| **合計** | **$0** | |

### 4.2 コスト目標との比較

| 環境 | 目標（1/10） | 実績 | 達成 |
|------|-------------|------|------|
| Development | $20 | $0 | ✓ |
| Staging | $80 | $39 | ✓ |
| Production | $150 | $84 | ✓ |
| **合計** | **$250** | **$123** | ✓ |

---

## 5. Terraform構成

### 5.1 ディレクトリ構成

```
terraform/
├── modules/
│   ├── network/           # VPC, Subnets, Security Groups
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/               # ECS Cluster, Services, Task Definitions
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/               # RDS PostgreSQL
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── elasticache/       # ElastiCache Redis
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cdn/               # CloudFront, S3
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── alb/               # Application Load Balancer
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── monitoring/        # CloudWatch, Alarms
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── shared/
    └── backend/           # Terraform state管理用S3/DynamoDB
        └── main.tf
```

### 5.2 モジュール構成例

#### network モジュール

```hcl
# modules/network/main.tf

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project}-${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project}-${var.environment}-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project}-${var.environment}-private-${count.index + 1}"
  }
}

# VPC Endpoints (NAT Gateway代替でコスト削減)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids = aws_route_table.private[*].id
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}
```

#### ecs モジュール

```hcl
# modules/ecs/main.tf

resource "aws_ecs_cluster" "main" {
  name = "${var.project}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = var.environment == "production" ? "enabled" : "disabled"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project}-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${var.ecr_repository_url}:${var.image_tag}"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment }
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn },
        { name = "REDIS_URL", valueFrom = var.redis_url_secret_arn },
        { name = "SECRET_KEY", valueFrom = var.secret_key_secret_arn },
        { name = "ANTHROPIC_API_KEY", valueFrom = var.anthropic_api_key_secret_arn }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project}-${var.environment}/backend"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

resource "aws_ecs_service" "backend" {
  name            = "${var.project}-${var.environment}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.backend_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "backend"
    container_port   = 8000
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Worker Service (Celery + OR-Tools)
resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project}-${var.environment}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name    = "worker"
      image   = "${var.ecr_repository_url}:${var.image_tag}"
      command = ["celery", "-A", "app.worker", "worker", "--loglevel=info"]

      environment = [
        { name = "ENVIRONMENT", value = var.environment }
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn },
        { name = "REDIS_URL", valueFrom = var.redis_url_secret_arn },
        { name = "ANTHROPIC_API_KEY", valueFrom = var.anthropic_api_key_secret_arn }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project}-${var.environment}/worker"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "worker" {
  name            = "${var.project}-${var.environment}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.worker_security_group_id]
    assign_public_ip = false
  }
}
```

### 5.3 環境別変数

```hcl
# environments/production/terraform.tfvars

project     = "juku-scheduler"
environment = "production"
region      = "ap-northeast-1"

vpc_cidr           = "10.0.0.0/16"
availability_zones = ["ap-northeast-1a", "ap-northeast-1c"]

# ECS Backend
backend_cpu           = 512   # 0.5 vCPU
backend_memory        = 1024  # 1 GB
backend_desired_count = 2

# ECS Worker
worker_cpu           = 1024  # 1 vCPU
worker_memory        = 2048  # 2 GB (OR-Tools用)
worker_desired_count = 1

# RDS
rds_instance_class    = "db.t4g.micro"
rds_allocated_storage = 20
rds_multi_az          = false  # コスト削減

# ElastiCache
elasticache_node_type = "cache.t4g.micro"
elasticache_num_nodes = 1

# CloudWatch
enable_container_insights = true
log_retention_days        = 30
```

### 5.4 Terraform実行フロー

```bash
# 初期セットアップ
cd terraform/shared/backend
terraform init
terraform apply

# 環境デプロイ（例: production）
cd terraform/environments/production
terraform init -backend-config=backend.tf
terraform plan
terraform apply

# 差分確認
terraform plan -out=tfplan

# 適用
terraform apply tfplan
```

---

## 6. セキュリティ設計

### 6.1 ネットワークセキュリティ

```
┌──────────────────────────────────────────────────────────────┐
│ Security Groups                                              │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ ALB SG       │───►│ Backend SG   │───►│ RDS SG       │   │
│  │              │    │              │    │              │   │
│  │ Inbound:     │    │ Inbound:     │    │ Inbound:     │   │
│  │ - 443 (any)  │    │ - 8000 (ALB) │    │ - 5432       │   │
│  │              │    │              │    │   (Backend)  │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                             │                                │
│                             ▼                                │
│                      ┌──────────────┐    ┌──────────────┐   │
│                      │ Worker SG    │───►│ ElastiCache  │   │
│                      │              │    │ SG           │   │
│                      │ Inbound:     │    │              │   │
│                      │ - None       │    │ Inbound:     │   │
│                      │ (egress only)│    │ - 6379       │   │
│                      └──────────────┘    │   (ECS)      │   │
│                                          └──────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 IAMロール設計

| ロール | 用途 | 主な権限 |
|--------|------|---------|
| ECS Execution Role | タスク起動時 | ECR Pull, Secrets Manager Read, CloudWatch Logs |
| ECS Task Role | タスク実行中 | S3 Read/Write, SES Send |
| CI/CD Role | GitHub Actions | ECR Push, ECS Deploy |

### 6.3 シークレット管理

| シークレット | 保存先 | 用途 |
|------------|--------|------|
| DATABASE_URL | Secrets Manager | RDS接続文字列 |
| REDIS_URL | Secrets Manager | ElastiCache接続文字列 |
| SECRET_KEY | Secrets Manager | JWT署名キー |
| ANTHROPIC_API_KEY | Secrets Manager | Claude API認証 |

---

## 7. 監視・アラート

### 7.1 CloudWatch構成

| 監視項目 | メトリクス | アラート閾値 |
|---------|----------|-------------|
| ECS CPU使用率 | CPUUtilization | > 80% |
| ECS メモリ使用率 | MemoryUtilization | > 80% |
| ALB エラー率 | HTTPCode_ELB_5XX_Count | > 10/min |
| ALB レイテンシ | TargetResponseTime | > 3秒 |
| RDS CPU使用率 | CPUUtilization | > 80% |
| RDS 接続数 | DatabaseConnections | > 80% of max |
| RDS ストレージ | FreeStorageSpace | < 2GB |

### 7.2 ログ構成

| ログ種別 | 保存先 | 保持期間 |
|---------|--------|---------|
| アプリケーションログ | CloudWatch Logs | 30日 |
| ALB アクセスログ | S3 | 90日 |
| RDS 監査ログ | CloudWatch Logs | 90日 |
| LLM呼び出しログ | CloudWatch Logs | 30日 |

### 7.3 アラート通知

```hcl
# SNSトピック
resource "aws_sns_topic" "alerts" {
  name = "${var.project}-${var.environment}-alerts"
}

# CloudWatchアラーム例
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${var.project}-${var.environment}-ecs-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.backend.name
  }
}
```

---

## 8. CI/CD パイプライン

### 8.1 GitHub Actions ワークフロー

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

env:
  AWS_REGION: ap-northeast-1
  ECR_REPOSITORY: juku-scheduler

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster juku-scheduler-production \
            --service juku-scheduler-production-backend \
            --force-new-deployment

          aws ecs update-service \
            --cluster juku-scheduler-production \
            --service juku-scheduler-production-worker \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster juku-scheduler-production \
            --services juku-scheduler-production-backend
```

### 8.2 Terraform CI/CD

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['terraform/**']
  pull_request:
    paths: ['terraform/**']

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: terraform/environments/production

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ap-northeast-1

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -no-color
        if: github.event_name == 'pull_request'

      - name: Terraform Apply
        run: terraform apply -auto-approve
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

---

## 9. バックアップ・DR

### 9.1 バックアップ設定

| 対象 | 方式 | 頻度 | 保持期間 |
|------|------|------|---------|
| RDS | 自動スナップショット | 日次 | 7日間 |
| RDS | 手動スナップショット | 週次 | 30日間 |
| S3 (Frontend) | バージョニング | 即時 | 30日間 |
| Terraform State | S3 バージョニング | 変更時 | 無制限 |

### 9.2 災害復旧手順

| ステップ | 時間 | 内容 |
|---------|------|------|
| 1. 検知 | 0-5分 | CloudWatch アラート |
| 2. 判断 | 5-15分 | 障害レベル判定 |
| 3. インフラ復旧 | 15-30分 | terraform apply |
| 4. DB復旧 | 10-30分 | RDS スナップショットから復元 |
| 5. 動作確認 | 10-20分 | ヘルスチェック |
| **合計RTO** | **1-2時間** | 目標4時間以内 ✓ |

---

## 10. 非機能要件との整合性確認

| 要件カテゴリ | 要件 | 本構成での対応 | 充足 |
|------------|------|--------------|------|
| **性能** | ダッシュボード 1秒以内 | CloudFront + S3 | ✓ |
| | 時間割生成 小規模30秒 | ECS Worker (2GB RAM) | ✓ |
| | 同時100ユーザー | ECS + ALB | ✓ |
| **LLM** | レスポンス 500ms〜1.5秒 | Claude API直接呼び出し | ✓ |
| | 可用性 99.5% | フォールバック機構 | ✓ |
| | コスト $500/月以内 | 使用量監視 + 上限設定 | ✓ |
| **可用性** | 99.5% 稼働率 | Multi-AZ ALB + CloudWatch | ✓ |
| | RTO 4時間 | Terraform + RDS復元 | ✓ (1-2時間) |
| | RPO 1時間 | RDS自動バックアップ | ✓ (5分間隔) |
| **セキュリティ** | TLS 1.3 | CloudFront + ACM | ✓ |
| | JWT認証 | FastAPI + ElastiCache | ✓ |
| | 保存時暗号化 | RDS暗号化 + S3 SSE | ✓ |
| | 監査ログ1年保持 | CloudWatch + S3 | ✓ |
| **拡張性** | 水平スケーリング | ECS Auto Scaling | ✓ |
| | ステートレス設計 | ElastiCache セッション | ✓ |
| **保守性** | CI/CD | GitHub Actions | ✓ |
| | IaC | Terraform | ✓ |
| | ログ集約 | CloudWatch Logs | ✓ |

---

## 11. 制約事項・トレードオフ

### 11.1 本構成の制約

| 制約 | 影響 | 緩和策 |
|------|------|--------|
| Single-AZ RDS | DB障害時のダウンタイム | 自動バックアップ + 迅速な復旧 |
| NAT Gateway 1個 | AZ障害時の外部通信断 | VPCエンドポイント活用 |
| Fargate Spot未使用 | コスト削減余地あり | 安定性優先 |

### 11.2 コスト最適化のトレードオフ

| 従来構成 | 新構成 | トレードオフ |
|---------|--------|------------|
| Multi-AZ RDS | Single-AZ RDS | 可用性99.99%→99.5%（要件内） |
| NAT Gateway 2個 | VPCエンドポイント | 一部外部通信に制限 |
| Reserved Instances | オンデマンド | 柔軟性優先、長期コミット回避 |

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-03-23 | 初版作成（AWS構成） |
| 2026-03-23 | 低コスト構成に全面改訂（VPS + マネージドサービス構成） |
| 2026-03-23 | LLM活用要件に対応、非機能要件との整合性更新 |
| 2026-03-23 | AWS + Terraform構成に改訂（ECS Fargate, RDS, ElastiCache） |
