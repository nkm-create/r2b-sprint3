# Infrastructure as Code

学習塾時間割最適化システムの AWS インフラを Terraform で管理します。

## 構成

```
infrastructure/
└── terraform/
    ├── main.tf              # メイン設定
    ├── variables.tf         # 変数定義
    ├── outputs.tf           # 出力定義
    ├── modules/
    │   ├── vpc/             # VPC モジュール
    │   ├── rds/             # RDS PostgreSQL モジュール
    │   ├── redis/           # ElastiCache Redis モジュール
    │   └── ecs/             # ECS Fargate モジュール
    └── environments/
        ├── dev/             # 開発環境設定
        └── prod/            # 本番環境設定
```

## 前提条件

- Terraform >= 1.6.0
- AWS CLI 設定済み
- 適切な IAM 権限

## 使い方

### 1. 初期化

```bash
cd infrastructure/terraform
terraform init
```

### 2. 開発環境へのデプロイ

```bash
# 変数設定
export TF_VAR_db_password="your-secure-password"

# プラン確認
terraform plan -var-file=environments/dev/terraform.tfvars

# 適用
terraform apply -var-file=environments/dev/terraform.tfvars
```

### 3. 本番環境へのデプロイ

```bash
# 変数設定
export TF_VAR_db_password="your-secure-password"

# プラン確認
terraform plan -var-file=environments/prod/terraform.tfvars

# 適用
terraform apply -var-file=environments/prod/terraform.tfvars
```

## リソース

### VPC

- VPC (10.0.0.0/16 for dev, 10.1.0.0/16 for prod)
- パブリックサブネット x 2 AZ
- プライベートサブネット x 2 AZ
- NAT Gateway x 2 AZ
- Internet Gateway

### RDS

- PostgreSQL 16
- マルチAZ (本番環境)
- 暗号化有効
- 自動バックアップ 7日間

### ElastiCache

- Redis 7.1
- 単一ノード (開発) / クラスター (本番)

### ECS Fargate

- ALB
- Backend サービス (FastAPI)
- Frontend サービス (Next.js)
- CloudWatch Logs

## コスト見積もり（月額）

### 開発環境

| リソース | インスタンス | 概算コスト |
|---------|-------------|-----------|
| RDS | db.t3.micro | ~$15 |
| ElastiCache | cache.t3.micro | ~$12 |
| ECS Fargate | 0.25 vCPU / 512MB x 2 | ~$20 |
| ALB | - | ~$20 |
| NAT Gateway | x 2 | ~$65 |
| **合計** | | **~$130/月** |

### 本番環境

| リソース | インスタンス | 概算コスト |
|---------|-------------|-----------|
| RDS | db.t3.small (MultiAZ) | ~$50 |
| ElastiCache | cache.t3.small | ~$25 |
| ECS Fargate | 0.5 vCPU / 1GB x 4 | ~$80 |
| ALB | - | ~$20 |
| NAT Gateway | x 2 | ~$65 |
| **合計** | | **~$240/月** |

## セキュリティ

- すべてのデータベースはプライベートサブネットに配置
- セキュリティグループで最小権限のアクセス制御
- RDS/Redis は暗号化有効
- IAM ロールによるアクセス制御

## 注意事項

- 本番環境では `deletion_protection` を有効にすることを推奨
- シークレット（DB パスワード等）は AWS Secrets Manager での管理を検討
- CI/CD パイプラインでの自動デプロイを推奨
