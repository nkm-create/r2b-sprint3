# クラウド構成図

## 1. 概要

本ドキュメントは、学習塾時間割最適化システムのAWSインフラ構成を定義する。

### 1.1 参照ドキュメント

| ドキュメント | 内容 |
|------------|------|
| operations/operations-policy.md | 運用方針（技術スタック、スケーリング戦略） |
| data/data-list.md | データ一覧（29エンティティ） |
| ipo/ipo.md | IPO一覧（F001〜F123） |

### 1.2 設計原則

| 原則 | 説明 |
|------|------|
| 高可用性 | Multi-AZ構成、自動フェイルオーバー |
| スケーラビリティ | ECS Fargateによる水平スケール |
| セキュリティ | Defense in Depth（多層防御） |
| コスト最適化 | Fargate Spot活用、リザーブドインスタンス |
| 運用性 | IaC（Terraform）、監視・アラート自動化 |

---

## 2. 全体アーキテクチャ

### 2.1 論理構成図

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Internet                                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (ap-northeast-1)                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              Route 53 (DNS)                                        │  │
│  │                         juku-schedule.example.com                                  │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                          │                                               │
│                                          ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                      CloudFront (CDN + WAF + SSL/TLS)                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │  │
│  │  │ WAF (Firewall)  │  │ Edge Locations  │  │ Origin Shield   │                     │  │
│  │  │ - Rate Limit    │  │ - Tokyo Edge    │  │ - Origin Cache  │                     │  │
│  │  │ - SQL Injection │  │ - Osaka Edge    │  │                 │                     │  │
│  │  │ - XSS Protection│  │                 │  │                 │                     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                     │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                      │                                    │                              │
│          ┌───────────┴───────────┐            ┌───────────┴───────────┐                 │
│          │  Static Assets        │            │  Dynamic Content       │                 │
│          ▼                       │            ▼                        │                 │
│  ┌───────────────────┐           │    ┌───────────────────────────────┐│                 │
│  │   S3 Bucket       │           │    │        ALB (Public)           ││                 │
│  │ (Static Assets)   │           │    │   - Path-based Routing        ││                 │
│  │ - Next.js Build   │           │    │   - Health Checks             ││                 │
│  │ - Images/CSS/JS   │           │    │   - SSL Termination           ││                 │
│  └───────────────────┘           │    └───────────────┬───────────────┘│                 │
│                                  │                    │                │                 │
│  ┌───────────────────────────────┴────────────────────┴────────────────┴───────────────┐│
│  │                                    VPC (10.0.0.0/16)                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                           Public Subnets (10.0.0.0/20)                          │││
│  │  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐      │││
│  │  │  │   AZ-1a (10.0.1.0)  │  │   AZ-1c (10.0.2.0)  │  │   AZ-1d (10.0.3.0)  │      │││
│  │  │  │   - NAT Gateway     │  │   - NAT Gateway     │  │   (Reserved)        │      │││
│  │  │  │   - ALB ENI         │  │   - ALB ENI         │  │                     │      │││
│  │  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘      │││
│  │  └─────────────────────────────────────────────────────────────────────────────────┘││
│  │                                          │                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                          Private Subnets (10.0.16.0/20)                         │││
│  │  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐      │││
│  │  │  │   AZ-1a (10.0.17.0) │  │   AZ-1c (10.0.18.0) │  │   AZ-1d (10.0.19.0) │      │││
│  │  │  │                     │  │                     │  │   (Reserved)        │      │││
│  │  │  │ ┌─────────────────┐ │  │ ┌─────────────────┐ │  │                     │      │││
│  │  │  │ │ ECS Fargate     │ │  │ │ ECS Fargate     │ │  │                     │      │││
│  │  │  │ │ - Frontend      │ │  │ │ - Frontend      │ │  │                     │      │││
│  │  │  │ │ - Backend       │ │  │ │ - Backend       │ │  │                     │      │││
│  │  │  │ │ - Worker        │ │  │ │ - Worker        │ │  │                     │      │││
│  │  │  │ └─────────────────┘ │  │ └─────────────────┘ │  │                     │      │││
│  │  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘      │││
│  │  └─────────────────────────────────────────────────────────────────────────────────┘││
│  │                                          │                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                         Database Subnets (10.0.32.0/20)                         │││
│  │  │  ┌─────────────────────┐  ┌─────────────────────┐                               │││
│  │  │  │   AZ-1a (10.0.33.0) │  │   AZ-1c (10.0.34.0) │                               │││
│  │  │  │ ┌─────────────────┐ │  │ ┌─────────────────┐ │                               │││
│  │  │  │ │ RDS Aurora      │ │  │ │ RDS Aurora      │ │                               │││
│  │  │  │ │ (Primary)       │◄┼──┼►│ (Replica)       │ │                               │││
│  │  │  │ └─────────────────┘ │  │ └─────────────────┘ │                               │││
│  │  │  │ ┌─────────────────┐ │  │ ┌─────────────────┐ │                               │││
│  │  │  │ │ ElastiCache     │ │  │ │ ElastiCache     │ │                               │││
│  │  │  │ │ (Primary)       │◄┼──┼►│ (Replica)       │ │                               │││
│  │  │  │ └─────────────────┘ │  │ └─────────────────┘ │                               │││
│  │  │  └─────────────────────┘  └─────────────────────┘                               │││
│  │  └─────────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                              Management Services                                     ││
│  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐            ││
│  │  │ Secrets       │ │ CloudWatch    │ │ ECR           │ │ SNS           │            ││
│  │  │ Manager       │ │ - Logs        │ │ (Container    │ │ (Alerts)      │            ││
│  │  │ - DB Creds    │ │ - Metrics     │ │  Registry)    │ │               │            ││
│  │  │ - API Keys    │ │ - Alarms      │ │               │ │               │            ││
│  │  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 External Services                                        │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                                │
│  │ Google        │  │ Anthropic     │  │ Datadog       │                                │
│  │ Sheets API    │  │ Claude API    │  │ (APM/Logs)    │                                │
│  │ (希望データ取込) │  │ (LLM)         │  │               │                                │
│  └───────────────┘  └───────────────┘  └───────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 データフロー図

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow Architecture                                   │
└──────────────────────────────────────────────────────────────────────────────────────┘

[User Browser]
      │
      │ HTTPS (TLS 1.3)
      ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ CloudFront  │────►│ WAF         │────►│ S3 (Static) │ ← CSS/JS/Images
│ (CDN)       │     │             │     └─────────────┘
└──────┬──────┘     └─────────────┘
       │
       │ API Requests (/api/*)
       ▼
┌─────────────┐
│ ALB         │
│ (HTTPS)     │
└──────┬──────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
       ▼                                         ▼
┌─────────────┐                           ┌─────────────┐
│ Frontend    │                           │ Backend     │
│ (Next.js)   │──── API Calls ──────────►│ (FastAPI)   │
│ ECS Fargate │                           │ ECS Fargate │
└─────────────┘                           └──────┬──────┘
                                                 │
       ┌──────────────────┬──────────────────────┼──────────────────┐
       │                  │                      │                  │
       ▼                  ▼                      ▼                  ▼
┌─────────────┐    ┌─────────────┐       ┌─────────────┐    ┌─────────────┐
│ RDS Aurora  │    │ ElastiCache │       │ Worker      │    │ Secrets     │
│ PostgreSQL  │    │ Redis       │       │ (Celery)    │    │ Manager     │
│             │    │ - Session   │       │ ECS Fargate │    │ - API Keys  │
│ - 29 Tables │    │ - Cache     │       │             │    └─────────────┘
│ - PITR      │    │ - Queue     │       │ ┌─────────┐ │
└─────────────┘    └─────────────┘       │ │ OR-Tools│ │
                                         │ │ (Solver)│ │
                                         │ └─────────┘ │
                                         │ ┌─────────┐ │
                                         │ │ Claude  │─┼───► Anthropic API
                                         │ │ (LLM)   │ │
                                         │ └─────────┘ │
                                         └─────────────┘
                                                 │
                                                 ▼
                                         ┌─────────────┐
                                         │ Google      │
                                         │ Sheets API  │
                                         │ (希望データ) │
                                         └─────────────┘
```

---

## 3. ネットワーク設計

### 3.1 VPC構成

| 項目 | 値 | 説明 |
|------|-----|------|
| VPC CIDR | 10.0.0.0/16 | 65,536 IPアドレス |
| リージョン | ap-northeast-1 | 東京リージョン |
| AZ | 1a, 1c, (1d予備) | 2AZ + 予備 |

### 3.2 サブネット設計

| サブネット種別 | CIDR | AZ | 用途 |
|--------------|------|-----|------|
| Public-1a | 10.0.1.0/24 | ap-northeast-1a | NAT Gateway, ALB |
| Public-1c | 10.0.2.0/24 | ap-northeast-1c | NAT Gateway, ALB |
| Public-1d | 10.0.3.0/24 | ap-northeast-1d | 予備 |
| Private-1a | 10.0.17.0/24 | ap-northeast-1a | ECS Fargate |
| Private-1c | 10.0.18.0/24 | ap-northeast-1c | ECS Fargate |
| Private-1d | 10.0.19.0/24 | ap-northeast-1d | 予備 |
| Database-1a | 10.0.33.0/24 | ap-northeast-1a | RDS, ElastiCache |
| Database-1c | 10.0.34.0/24 | ap-northeast-1c | RDS, ElastiCache |

### 3.3 セキュリティグループ

| SG名 | Inbound | Outbound | 用途 |
|------|---------|----------|------|
| sg-alb | 443 (0.0.0.0/0) | All (VPC) | ALB |
| sg-frontend | 3000 (sg-alb) | All | Next.js |
| sg-backend | 8000 (sg-alb, sg-frontend) | All | FastAPI |
| sg-worker | - | All | Celery Worker |
| sg-rds | 5432 (sg-backend, sg-worker) | - | Aurora PostgreSQL |
| sg-redis | 6379 (sg-backend, sg-worker) | - | ElastiCache |

### 3.4 ネットワークACL

| NACL | サブネット | ルール |
|------|----------|--------|
| nacl-public | Public-* | 443/80 Inbound許可、Ephemeral Outbound許可 |
| nacl-private | Private-* | VPC内のみ許可 |
| nacl-database | Database-* | Private Subnetからのみ許可 |

---

## 4. コンピューティング

### 4.1 ECS Fargate構成

#### クラスター構成

| クラスター | 環境 | 用途 |
|-----------|------|------|
| juku-dev | Development | 開発環境 |
| juku-stg | Staging | ステージング環境 |
| juku-prd | Production | 本番環境 |

#### タスク定義

| サービス | vCPU | Memory | 最小タスク | 最大タスク | ポート |
|---------|------|--------|-----------|-----------|--------|
| frontend | 0.5 | 1 GB | 2 | 10 | 3000 |
| backend | 1 | 2 GB | 2 | 10 | 8000 |
| worker | 2 | 4 GB | 1 | 5 | - |

#### オートスケーリング

| サービス | メトリクス | ターゲット値 | クールダウン |
|---------|----------|------------|------------|
| frontend | CPU利用率 | 70% | 300秒 |
| backend | CPU利用率 | 70% | 300秒 |
| backend | リクエスト数/タスク | 1000/min | 300秒 |
| worker | SQSキュー深度 | 10 | 60秒 |

### 4.2 コンテナイメージ

```
ECR Repository Structure:
├── juku-frontend
│   ├── latest
│   ├── v1.0.0
│   └── v1.0.1
├── juku-backend
│   ├── latest
│   ├── v1.0.0
│   └── v1.0.1
└── juku-worker
    ├── latest
    ├── v1.0.0
    └── v1.0.1
```

---

## 5. データストア

### 5.1 RDS Aurora PostgreSQL

| 項目 | 値 |
|------|-----|
| エンジン | Aurora PostgreSQL 15 |
| インスタンスクラス | db.r6g.large (本番) / db.t4g.medium (開発) |
| ストレージ | Aurora Storage (自動拡張) |
| Multi-AZ | 有効（リードレプリカ1台） |
| 暗号化 | AES-256 (AWS KMS) |
| バックアップ保持期間 | 35日 |
| PITR | 有効（7日間） |
| パラメータグループ | カスタム（日本語設定、タイムゾーン） |

#### パフォーマンス設定

| パラメータ | 値 | 説明 |
|----------|-----|------|
| max_connections | 500 | 同時接続数上限 |
| shared_buffers | 256MB | 共有バッファ |
| work_mem | 64MB | ソート/ハッシュ用メモリ |
| effective_cache_size | 1GB | キャッシュサイズ |
| timezone | Asia/Tokyo | タイムゾーン |

### 5.2 ElastiCache Redis

| 項目 | 値 |
|------|-----|
| エンジン | Redis 7.0 |
| ノードタイプ | cache.r6g.large (本番) / cache.t4g.medium (開発) |
| レプリカ数 | 1 |
| Multi-AZ | 有効 |
| 暗号化 | 転送時・保存時ともに有効 |
| 自動フェイルオーバー | 有効 |

#### 用途別キー設計

| プレフィックス | 用途 | TTL |
|--------------|------|-----|
| session: | ユーザーセッション | 1時間 |
| refresh: | リフレッシュトークン | 14日 |
| cache:schedule: | 時間割キャッシュ | 5分 |
| cache:teacher: | 講師リストキャッシュ | 10分 |
| queue:celery | Celeryタスクキュー | - |
| lock: | 分散ロック | 30秒 |

### 5.3 S3バケット

| バケット名 | 用途 | アクセス | 暗号化 | ライフサイクル |
|-----------|------|---------|--------|--------------|
| juku-static-{env} | 静的アセット | CloudFront経由 | SSE-S3 | - |
| juku-exports-{env} | CSV/PDFエクスポート | 署名付きURL | SSE-S3 | 30日で削除 |
| juku-audit-{env} | 監査ログ | 内部のみ | SSE-KMS | 7年保持→Glacier |
| juku-backups-{env} | DBバックアップ | 内部のみ | SSE-KMS | 90日保持 |

---

## 6. セキュリティ

### 6.1 IAMロール

| ロール | 信頼関係 | ポリシー | 用途 |
|--------|---------|---------|------|
| ecsTaskExecutionRole | ecs-tasks.amazonaws.com | AmazonECSTaskExecutionRolePolicy, SecretsManagerReadWrite | タスク起動 |
| ecsTaskRole-frontend | ecs-tasks.amazonaws.com | S3ReadOnly, CloudWatchLogsFullAccess | フロントエンド |
| ecsTaskRole-backend | ecs-tasks.amazonaws.com | S3FullAccess, SecretsManagerReadWrite, RDSConnect | バックエンド |
| ecsTaskRole-worker | ecs-tasks.amazonaws.com | S3FullAccess, SecretsManagerReadWrite, RDSConnect, SQSFullAccess | ワーカー |

### 6.2 Secrets Manager

| シークレット名 | 内容 | ローテーション |
|--------------|------|--------------|
| juku/db/credentials | RDS認証情報 | 30日 |
| juku/redis/auth | Redis AUTH | 90日 |
| juku/api/anthropic | Claude APIキー | 90日 |
| juku/api/google | Google OAuth | 90日 |
| juku/jwt/keys | JWT署名キー | 180日 |

### 6.3 WAF ルール

| ルール | 説明 | アクション |
|--------|------|----------|
| AWS-AWSManagedRulesCommonRuleSet | 一般的な攻撃パターン | Block |
| AWS-AWSManagedRulesSQLiRuleSet | SQLインジェクション | Block |
| AWS-AWSManagedRulesKnownBadInputsRuleSet | 既知の悪意ある入力 | Block |
| RateLimit-API | API呼び出しレート制限 (1000/5min) | Block |
| RateLimit-Login | ログイン試行制限 (10/min) | Block |
| GeoMatch-JP | 日本国内のみ許可 | Allow (他はCount) |

### 6.4 ネットワークセキュリティ

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Architecture                         │
└─────────────────────────────────────────────────────────────────┘

[Internet]
    │
    │ TLS 1.3 Only
    ▼
┌─────────────────┐
│ CloudFront      │ ← AWS Shield Standard (DDoS防御)
│ + WAF           │ ← マネージドルール + カスタムルール
└────────┬────────┘
         │
         │ VPC Link (Private)
         ▼
┌─────────────────┐
│ ALB             │ ← セキュリティグループ (443のみ)
│ (Internal)      │ ← アクセスログ有効
└────────┬────────┘
         │
         │ Security Group
         ▼
┌─────────────────┐
│ ECS Fargate     │ ← タスクIAMロール (最小権限)
│ (Private Subnet)│ ← コンテナ内でroot禁止
└────────┬────────┘
         │
         │ Security Group (特定ポートのみ)
         ▼
┌─────────────────┐
│ RDS/Redis       │ ← 保存時暗号化 (KMS)
│ (DB Subnet)     │ ← 転送時暗号化 (TLS)
└─────────────────┘   ← IAM認証 (RDS)
```

---

## 7. 監視・ログ

### 7.1 CloudWatch構成

#### ロググループ

| ロググループ | 保持期間 | 用途 |
|------------|---------|------|
| /ecs/juku-frontend | 90日 | フロントエンドログ |
| /ecs/juku-backend | 90日 | バックエンドログ |
| /ecs/juku-worker | 90日 | ワーカーログ |
| /aws/rds/cluster/juku-prd | 90日 | RDSログ |
| /aws/elasticache/juku-prd | 30日 | Redisログ |
| /aws/alb/juku-prd | 90日 | ALBアクセスログ |

#### ダッシュボード

```
┌─────────────────────────────────────────────────────────────────┐
│                    CloudWatch Dashboard                          │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ Request Count   │ │ Error Rate      │ │ Response Time   │     │
│ │ [Line Graph]    │ │ [Line Graph]    │ │ [Line Graph]    │     │
│ │ 12,345 req/min  │ │ 0.5%            │ │ p99: 1.2s       │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│                                                                  │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ ECS CPU         │ │ ECS Memory      │ │ Task Count      │     │
│ │ [Area Graph]    │ │ [Area Graph]    │ │ [Number]        │     │
│ │ 45%             │ │ 60%             │ │ 6 tasks         │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│                                                                  │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ RDS Connections │ │ Redis Memory    │ │ LLM Latency     │     │
│ │ [Line Graph]    │ │ [Line Graph]    │ │ [Line Graph]    │     │
│ │ 150/500         │ │ 2.1 GB          │ │ p95: 1.1s       │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 アラーム設定

| アラーム名 | メトリクス | 閾値 | 期間 | アクション |
|-----------|----------|------|------|----------|
| HighErrorRate | 5xx errors | > 1% | 5分 | SNS → Slack |
| HighLatency | p99 latency | > 3s | 5分 | SNS → Slack |
| ECSHighCPU | CPU utilization | > 80% | 5分 | Scale Out |
| RDSHighConnections | DB connections | > 400 | 5分 | SNS → PagerDuty |
| LLMHighLatency | LLM p95 latency | > 2s | 5分 | SNS → Slack |
| LLMHighCost | Monthly cost | > $400 | 日次 | SNS → Email |

### 7.3 Datadog統合

| 機能 | 用途 |
|------|------|
| APM | アプリケーションパフォーマンス監視 |
| Infrastructure | ECS/RDS/Redisメトリクス |
| Logs | 統合ログ分析 |
| Synthetics | 外形監視（ログイン、時間割生成） |
| RUM | リアルユーザー監視（フロントエンド） |

---

## 8. 環境別構成

### 8.1 環境比較

| 項目 | Development | Staging | Production |
|------|-------------|---------|------------|
| ECS Fargate | 最小タスク1 | 最小タスク2 | 最小タスク2 |
| RDS | db.t4g.medium | db.r6g.large | db.r6g.large |
| Redis | cache.t4g.medium | cache.r6g.large | cache.r6g.large |
| Multi-AZ | 無効 | 有効 | 有効 |
| WAF | 有効（カウントモード） | 有効 | 有効 |
| Datadog | 無効 | 有効 | 有効 |
| 月額コスト目安 | $200 | $800 | $1,500 |

### 8.2 環境分離

```
AWS Organizations
└── Root
    ├── juku-dev (Development Account)
    │   └── VPC: 10.1.0.0/16
    ├── juku-stg (Staging Account)
    │   └── VPC: 10.2.0.0/16
    └── juku-prd (Production Account)
        └── VPC: 10.0.0.0/16
```

---

## 9. DR（災害復旧）

### 9.1 DR構成

```
┌─────────────────────────────────────────────────────────────────┐
│                      Primary Region (Tokyo)                      │
│                       ap-northeast-1                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ ECS Fargate     │  │ RDS Aurora      │  │ ElastiCache     │  │
│  │ (Active)        │  │ (Primary)       │  │ (Primary)       │  │
│  └─────────────────┘  └────────┬────────┘  └─────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                    Aurora Global Database
                         (非同期レプリケーション)
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                      DR Region (Osaka)                           │
│                       ap-northeast-3                             │
│  ┌─────────────────┐  ┌────────▼────────┐  ┌─────────────────┐  │
│  │ ECS Fargate     │  │ RDS Aurora      │  │ ElastiCache     │  │
│  │ (Standby)       │  │ (Secondary)     │  │ (Standby)       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 DR指標

| 指標 | 目標値 | 説明 |
|------|--------|------|
| RTO | 4時間 | 復旧時間目標 |
| RPO | 1時間 | 復旧ポイント目標 |
| フェイルオーバー | 15分 | Aurora自動フェイルオーバー |

### 9.3 フェイルオーバー手順

1. **検知**: CloudWatch / Datadogで障害検知
2. **判断**: インシデント対応チームがDR発動を判断
3. **DNS切替**: Route 53でDRリージョンへフェイルオーバー
4. **Aurora昇格**: Secondaryをプライマリに昇格
5. **ECS起動**: DRリージョンでECSタスク起動
6. **確認**: ヘルスチェック、動作確認
7. **通知**: ユーザーへの障害・復旧通知

---

## 10. コスト見積

### 10.1 月額コスト概算（本番環境）

| サービス | 構成 | 月額（USD） |
|---------|------|-----------|
| ECS Fargate | 6タスク × 24h | $300 |
| RDS Aurora | db.r6g.large × 2 | $400 |
| ElastiCache | cache.r6g.large × 2 | $200 |
| ALB | 1 ALB + トラフィック | $50 |
| CloudFront | 100GB転送 | $20 |
| S3 | 50GB + リクエスト | $10 |
| NAT Gateway | 2 × 24h + トラフィック | $100 |
| Secrets Manager | 10シークレット | $10 |
| CloudWatch | ログ/メトリクス | $50 |
| WAF | 1 Web ACL | $10 |
| Route 53 | 1 Hosted Zone | $1 |
| **Anthropic Claude** | LLM呼び出し | **$300** |
| Datadog | APM + Infra | $200 |
| **合計** | | **$1,651** |

### 10.2 コスト最適化施策

| 施策 | 削減効果 | 適用条件 |
|------|---------|---------|
| Fargate Spot | 最大70%削減 | Workerに適用 |
| Reserved Instances | 最大50%削減 | 1年コミット |
| Aurora Serverless v2 | 変動負荷対応 | 開発環境 |
| S3 Intelligent-Tiering | 自動階層化 | エクスポートファイル |

---

## 11. IaC（Infrastructure as Code）

### 11.1 ディレクトリ構成

```
infrastructure/
├── terraform/
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   ├── stg/
│   │   │   └── ...
│   │   └── prd/
│   │       └── ...
│   ├── modules/
│   │   ├── vpc/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── elasticache/
│   │   ├── alb/
│   │   ├── cloudfront/
│   │   ├── s3/
│   │   ├── waf/
│   │   └── monitoring/
│   └── shared/
│       ├── ecr/
│       └── route53/
└── scripts/
    ├── deploy.sh
    └── destroy.sh
```

### 11.2 Terraform状態管理

| 項目 | 設定 |
|------|------|
| Backend | S3 + DynamoDB（状態ロック） |
| ワークスペース | 環境ごとに分離 |
| 暗号化 | SSE-S3 |

---

## 12. 設計根拠

### 12.1 AWS選定理由

| 観点 | 理由 |
|------|------|
| 実績 | エンタープライズ採用実績が豊富 |
| マネージドサービス | Aurora, ECS Fargateによる運用負荷軽減 |
| セキュリティ | WAF, Secrets Manager, KMSの統合 |
| コスト | Fargate Spot, Reserved Instancesによる最適化 |
| 国内リージョン | 東京・大阪リージョンでDR構成可能 |

### 12.2 ECS Fargate選定理由

| 比較対象 | Fargateの優位性 |
|---------|----------------|
| EKS | 運用の簡素化（ノード管理不要） |
| EC2 | インスタンス管理不要、秒単位課金 |
| Lambda | 長時間処理（時間割生成）に対応 |

### 12.3 Aurora PostgreSQL選定理由

| 比較対象 | Auroraの優位性 |
|---------|---------------|
| 標準RDS | 3倍の性能、自動フェイルオーバー |
| DynamoDB | RDBMSの柔軟なクエリ、トランザクション |
| 自己管理 | バックアップ、パッチ適用の自動化 |

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-03-23 | 初版作成（VPC設計、ECS/RDS/Redis構成、セキュリティ、監視、DR） |
