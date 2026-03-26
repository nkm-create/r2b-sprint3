# DB設計書

> IPO一覧とデータ項目一覧から作成した学習塾時間割最適化システムのデータベース設計

## 1. 概要

### 1.1 参照ドキュメント

| ドキュメント | 内容 |
|------------|------|
| ipo/ipo.md | IPO一覧（F001〜F123） |
| data-list/data-list.md | データ項目一覧（29エンティティ） |
| cloud/cloud-architecture.md | クラウド構成（AWS RDS PostgreSQL） |
| requirements-v1/*.md | 各画面の要件定義書 |

### 1.2 設計方針

| 方針 | 内容 |
|------|------|
| DBエンジン | PostgreSQL 15（RDS） |
| 文字コード | UTF-8 |
| タイムゾーン | Asia/Tokyo (UTC+9) |
| 命名規則 | スネークケース（小文字）、テーブル名は複数形 |
| 主キー | UUID（自動生成） |
| 論理削除 | deleted_at カラムによる |
| 監査カラム | created_at, updated_at を全テーブルに付与 |

### 1.3 クラウド構成との整合性

| 項目 | クラウド構成 | DB設計への反映 |
|------|------------|--------------|
| DBエンジン | RDS PostgreSQL (db.t4g.micro) | JSONB, UUID, 配列型を使用可能 |
| ストレージ | S3 | ファイルの実体はS3、DBにはパス不保存 |
| 認証方式 | 自前認証（JWT） | users.password_hash が必要 |
| Read Replica | なし（Single-AZ） | 正規化優先、非正規化は最小限 |
| バックアップ | RDS自動スナップショット | RPO 5分（要件: 1時間）を満たす |

---

## 2. テーブル一覧

### 2.1 カテゴリ別テーブル一覧

| # | カテゴリ | テーブル名 | 目的 | バージョン管理 |
|---|---------|-----------|------|--------------|
| **認証・ユーザー** |
| 1 | | users | システムユーザー | - |
| 2 | | password_reset_tokens | パスワードリセットトークン | - |
| 3 | | refresh_tokens | リフレッシュトークン | - |
| **組織** |
| 4 | | areas | エリア（教室グループ） | - |
| 5 | | classrooms | 教室 | - |
| 6 | | user_classrooms | ユーザー-教室（中間） | - |
| 7 | | user_areas | ユーザー-エリア（中間） | - |
| **教室設定** |
| 8 | | classroom_settings | 教室設定 | - |
| 9 | | time_slots | 時間枠定義 | - |
| 10 | | google_form_connections | Google Form連携設定 | - |
| **講師** |
| 11 | | teachers | 講師マスタ | **必須** |
| 12 | | teacher_subjects | 講師-科目（中間） | - |
| 13 | | teacher_grades | 講師-学年（中間） | - |
| **生徒** |
| 14 | | students | 生徒マスタ | **必須** |
| 15 | | student_subjects | 生徒-科目別コマ数（中間） | - |
| **共通マスタ** |
| 16 | | subjects | 科目マスタ（システム固定） | - |
| 17 | | ng_relations | NG関係 | - |
| **希望データ** |
| 18 | | teacher_shift_preferences | 講師シフト希望 | 推奨 |
| 19 | | student_preferences | 生徒受講希望 | 推奨 |
| **ターム・制約** |
| 20 | | terms | ターム | - |
| 21 | | term_constraints | ターム固有制約 | 推奨 |
| 22 | | policies | 全体ポリシー設定 | 推奨 |
| 23 | | policy_templates | ポリシーテンプレート | - |
| **時間割** |
| 24 | | schedules | 時間割 | **必須** |
| 25 | | schedule_slots | 時間割コマ | - |
| **欠席・振替** |
| 26 | | absences | 欠席記録 | - |
| 27 | | substitutions | 振替記録 | - |
| **通知・監査** |
| 28 | | notifications | 通知 | - |
| 29 | | audit_logs | 監査ログ | - |

### 2.2 バージョン管理方針

| 区分 | 対象テーブル | 管理方法 |
|------|------------|---------|
| **必須** | teachers, students, schedules | version_number + is_current フラグ |
| **推奨** | teacher_shift_preferences, student_preferences, term_constraints, policies | term_id による実質的なスナップショット |

---

## 3. ER図

```mermaid
erDiagram
    %% ========== 認証・ユーザー ==========
    users ||--o{ user_classrooms : "所属"
    users ||--o{ user_areas : "担当"
    users ||--o{ password_reset_tokens : "発行"
    users ||--o{ refresh_tokens : "発行"
    users ||--o{ notifications : "受信"
    users ||--o{ audit_logs : "実行"

    users {
        uuid user_id PK
        varchar email UK
        varchar password_hash
        varchar name
        user_role role
        user_status status
        int login_failed_count
        timestamp locked_until
        boolean force_password_change
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    password_reset_tokens {
        uuid token_id PK
        uuid user_id FK
        varchar token_hash
        timestamp expires_at
        timestamp used_at
        timestamp created_at
    }

    refresh_tokens {
        uuid refresh_token_id PK
        uuid user_id FK
        varchar token_hash
        timestamp expires_at
        varchar device_info
        varchar ip_address
        boolean is_revoked
        timestamp revoked_at
        timestamp created_at
    }

    %% ========== 組織 ==========
    areas ||--o{ classrooms : "含む"
    areas ||--o{ user_areas : "割当"

    areas {
        uuid area_id PK
        varchar area_name
        timestamp created_at
        timestamp updated_at
    }

    classrooms ||--o{ user_classrooms : "割当"
    classrooms ||--|| classroom_settings : "設定"
    classrooms ||--o{ time_slots : "定義"
    classrooms ||--o{ google_form_connections : "連携"
    classrooms ||--o{ teachers : "所属"
    classrooms ||--o{ students : "所属"
    classrooms ||--o{ terms : "管理"
    classrooms ||--o{ policy_templates : "保存"

    classrooms {
        uuid classroom_id PK
        uuid area_id FK
        varchar classroom_code UK
        varchar classroom_name
        varchar address
        varchar phone_number
        classroom_status status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    user_classrooms {
        uuid user_id PK_FK
        uuid classroom_id PK_FK
        timestamp deleted_at
    }

    user_areas {
        uuid user_id PK_FK
        uuid area_id PK_FK
    }

    %% ========== 教室設定 ==========
    classroom_settings {
        uuid classroom_id PK_FK
        int booth_count
        int weekday_slots
        int saturday_slots
        varchar operating_days
        timestamp created_at
        timestamp updated_at
    }

    time_slots {
        uuid time_slot_id PK
        uuid classroom_id FK
        day_type day_type
        int slot_number
        time start_time
        time end_time
    }

    google_form_connections {
        uuid connection_id PK
        uuid classroom_id FK
        google_form_data_type data_type
        varchar spreadsheet_url
        varchar sheet_name
        jsonb column_mapping
        text oauth_token_encrypted
        timestamp last_sync_at
        timestamp created_at
        timestamp updated_at
    }

    %% ========== 講師 ==========
    teachers ||--o{ teacher_subjects : "指導可能"
    teachers ||--o{ teacher_grades : "指導可能"
    teachers ||--o{ teacher_shift_preferences : "希望"
    teachers ||--o{ ng_relations : "NG関係"
    teachers ||--o{ schedule_slots : "担当"

    teachers {
        uuid teacher_version_id PK
        varchar teacher_id
        uuid classroom_id FK
        int version_number
        boolean is_current
        timestamp valid_from
        timestamp valid_to
        teacher_change_reason change_reason_type
        varchar change_reason_note
        varchar name
        gender gender
        int min_slots_per_week
        int max_slots_per_week
        int max_consecutive_slots
        boolean has_jhs_exam_experience
        boolean has_hs_exam_experience
        university_rank university_rank
        teacher_status status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    teacher_subjects {
        uuid teacher_version_id PK_FK
        varchar subject_id PK_FK
    }

    teacher_grades {
        uuid teacher_version_id PK_FK
        grade grade PK
    }

    %% ========== 生徒 ==========
    students ||--o{ student_subjects : "受講"
    students ||--o{ student_preferences : "希望"
    students ||--o{ ng_relations : "NG関係"
    students ||--o{ schedule_slots : "受講(生徒1)"
    students ||--o{ schedule_slots : "受講(生徒2)"

    students {
        uuid student_version_id PK
        varchar student_id
        uuid classroom_id FK
        int version_number
        boolean is_current
        timestamp valid_from
        timestamp valid_to
        student_change_reason change_reason_type
        varchar change_reason_note
        varchar name
        grade grade
        int max_consecutive_slots
        varchar preferred_teacher_id FK
        preferred_gender preferred_teacher_gender
        aspiration_level aspiration_level
        enrollment_purpose enrollment_purpose
        student_status status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    student_subjects {
        uuid student_version_id PK_FK
        varchar subject_id PK_FK
        int slots_per_week
    }

    %% ========== 共通マスタ ==========
    subjects ||--o{ teacher_subjects : "関連"
    subjects ||--o{ student_subjects : "関連"
    subjects ||--o{ schedule_slots : "科目"

    subjects {
        varchar subject_id PK
        varchar subject_name
        grade_category grade_category
        subject_category subject_category
        boolean is_jhs_exam_target
        boolean is_hs_exam_target
    }

    ng_relations {
        uuid ng_relation_id PK
        varchar teacher_id FK
        varchar student_id FK
        ng_created_by created_by
        timestamp created_at
    }

    %% ========== 希望データ ==========
    terms ||--o{ teacher_shift_preferences : "対象"
    terms ||--o{ student_preferences : "対象"

    teacher_shift_preferences {
        uuid preference_id PK
        varchar teacher_id FK
        uuid classroom_id FK
        uuid term_id FK
        day_of_week day_of_week
        int slot_number
        teacher_preference_value preference_value
        boolean is_manually_edited
        timestamp synced_at
        timestamp created_at
        timestamp updated_at
    }

    student_preferences {
        uuid preference_id PK
        varchar student_id FK
        uuid classroom_id FK
        uuid term_id FK
        day_of_week day_of_week
        int slot_number
        student_preference_value preference_value
        boolean is_manually_edited
        timestamp synced_at
        timestamp created_at
        timestamp updated_at
    }

    %% ========== ターム・制約 ==========
    terms ||--o{ term_constraints : "設定"
    terms ||--o{ policies : "設定"
    terms ||--o{ schedules : "含む"

    terms {
        uuid term_id PK
        uuid classroom_id FK
        varchar term_name
        date start_date
        date end_date
        term_status status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    term_constraints {
        uuid constraint_id PK
        uuid term_id FK
        constraint_target_type target_type
        varchar target_id
        constraint_type constraint_type
        jsonb constraint_value
        timestamp created_at
        timestamp updated_at
    }

    policies {
        uuid policy_id PK
        uuid term_id FK
        policy_type policy_type
        boolean is_enabled
        jsonb parameters
        timestamp created_at
        timestamp updated_at
    }

    policy_templates {
        uuid template_id PK
        uuid classroom_id FK
        varchar template_name
        jsonb policies
        timestamp created_at
        timestamp updated_at
    }

    %% ========== 時間割 ==========
    schedules ||--o{ schedule_slots : "含む"
    schedules ||--o{ schedules : "派生元"

    schedules {
        uuid schedule_id PK
        uuid term_id FK
        int version
        schedule_status status
        uuid parent_version_id FK
        jsonb master_snapshot
        jsonb generation_config
        decimal fulfillment_rate
        decimal soft_constraint_rate
        timestamp confirmed_at
        uuid confirmed_by FK
        timestamp created_at
        timestamp updated_at
    }

    schedule_slots ||--o{ absences : "欠席"

    schedule_slots {
        uuid slot_id PK
        uuid schedule_id FK
        day_of_week day_of_week
        int slot_number
        int booth_number
        varchar teacher_id FK
        varchar student1_id FK
        varchar student2_id FK
        varchar subject_id FK
        slot_type slot_type
        slot_status status
        timestamp created_at
        timestamp updated_at
    }

    %% ========== 欠席・振替 ==========
    absences ||--o| substitutions : "振替"

    absences {
        uuid absence_id PK
        uuid slot_id FK
        absent_type absent_type
        varchar absent_person_id
        varchar absence_reason
        boolean needs_substitution
        substitution_status substitution_status
        uuid registered_by FK
        timestamp created_at
        timestamp updated_at
    }

    substitutions {
        uuid substitution_id PK
        uuid absence_id FK
        uuid original_slot_id FK
        uuid new_slot_id FK
        substitution_type substitution_type
        int priority_score
        uuid confirmed_by FK
        timestamp confirmed_at
        timestamp created_at
    }

    %% ========== 通知・監査 ==========
    notifications {
        uuid notification_id PK
        uuid user_id FK
        uuid classroom_id FK
        notification_type notification_type
        severity severity
        varchar title
        varchar message
        varchar link_url
        boolean is_read
        timestamp read_at
        timestamp created_at
    }

    audit_logs {
        uuid log_id PK
        uuid user_id FK
        varchar action
        varchar entity_type
        varchar entity_id
        jsonb old_value
        jsonb new_value
        varchar ip_address
        varchar user_agent
        timestamp created_at
    }
```

---

## 4. テーブル詳細

### 4.1 users（ユーザー）

**目的**: システムにアクセスするユーザーの認証・認可情報を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| user_id | UUID | PK | 主キー（自動生成） |
| email | VARCHAR(255) | UK, NN | ログインID |
| password_hash | VARCHAR(255) | NN | bcrypt (cost=12) |
| name | VARCHAR(50) | NN | 氏名 |
| role | user_role | NN | classroom_manager / area_manager / system_admin |
| status | user_status | NN | active / inactive |
| login_failed_count | INTEGER | DEFAULT 0 | ログイン失敗回数 |
| locked_until | TIMESTAMP | | 5回失敗で30分ロック |
| force_password_change | BOOLEAN | DEFAULT true | 初回パスワード変更要求 |
| last_login_at | TIMESTAMP | | 最終ログイン日時 |
| created_at | TIMESTAMP | NN, DEFAULT now() | 作成日時 |
| updated_at | TIMESTAMP | NN, DEFAULT now() | 更新日時 |
| deleted_at | TIMESTAMP | | 論理削除 |

**インデックス**:
- `idx_users_email` ON (email) - ログイン検索用
- `idx_users_role` ON (role) WHERE deleted_at IS NULL - 役割別検索用

---

### 4.2 areas（エリア）

**目的**: 複数教室をグループ化したエリアを管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| area_id | UUID | PK | 主キー |
| area_name | VARCHAR(100) | NN | エリア名 |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

---

### 4.3 classrooms（教室）

**目的**: 教室の基本情報を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| classroom_id | UUID | PK | 主キー |
| area_id | UUID | FK(areas) NN | 所属エリア |
| classroom_code | VARCHAR(20) | UK, NN | 教室コード（英数字） |
| classroom_name | VARCHAR(100) | NN | 教室名 |
| address | VARCHAR(200) | | 住所 |
| phone_number | VARCHAR(20) | | 電話番号 |
| status | classroom_status | NN | operating / closed |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |
| deleted_at | TIMESTAMP | | 論理削除 |

**インデックス**:
- `idx_classrooms_area_id` ON (area_id) WHERE deleted_at IS NULL
- `idx_classrooms_code` ON (classroom_code)

---

### 4.4 user_classrooms（ユーザー-教室）

**目的**: ユーザー（教室長）と教室の紐付け

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| user_id | UUID | PK, FK(users) | ユーザーID |
| classroom_id | UUID | PK, FK(classrooms) | 教室ID |
| deleted_at | TIMESTAMP | | 論理削除 |

---

### 4.5 user_areas（ユーザー-エリア）

**目的**: ユーザー（エリアマネジャー）と担当エリアの紐付け

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| user_id | UUID | PK, FK(users) | ユーザーID |
| area_id | UUID | PK, FK(areas) | エリアID |

---

### 4.6 classroom_settings（教室設定）

**目的**: 教室ごとの営業設定を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| classroom_id | UUID | PK, FK(classrooms) | 教室ID |
| booth_count | INTEGER | NN | ブース数（同時実施可能コマ数） |
| weekday_slots | INTEGER | NN, DEFAULT 4 | 平日時限数 |
| saturday_slots | INTEGER | NN, DEFAULT 5 | 土曜時限数 |
| operating_days | VARCHAR(20) | NN | 営業曜日（例: "mon,tue,wed,thu,fri,sat"） |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

---

### 4.7 time_slots（時間枠）

**目的**: 各教室の時限ごとの開始・終了時刻を定義

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| time_slot_id | UUID | PK | 主キー |
| classroom_id | UUID | FK(classrooms) NN | 教室ID |
| day_type | day_type | NN | weekday / saturday |
| slot_number | INTEGER | NN | 時限番号（1, 2, 3...） |
| start_time | TIME | NN | 開始時刻 |
| end_time | TIME | NN | 終了時刻 |

**UK**: (classroom_id, day_type, slot_number)

---

### 4.8 google_form_connections（Google Form連携設定）

**目的**: Google Formからのデータ取り込み設定を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| connection_id | UUID | PK | 主キー |
| classroom_id | UUID | FK(classrooms) NN | 教室ID |
| data_type | google_form_data_type | NN | teacher_shift / student_preference |
| spreadsheet_url | VARCHAR(500) | NN | スプレッドシートURL |
| sheet_name | VARCHAR(100) | NN | シート名 |
| column_mapping | JSONB | NN | カラムマッピング設定 |
| oauth_token_encrypted | TEXT | NN | OAuthトークン（暗号化） |
| last_sync_at | TIMESTAMP | | 最終同期日時 |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

---

### 4.9 teachers（講師マスタ）

**目的**: 講師情報をバージョン管理付きで管理

**バージョン管理対象**

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| teacher_version_id | UUID | PK | バージョンごとの主キー |
| teacher_id | VARCHAR(20) | NN | 不変ID（例: T001） |
| classroom_id | UUID | FK(classrooms) NN | 教室ID |
| version_number | INTEGER | NN | バージョン番号（1から開始） |
| is_current | BOOLEAN | NN | 現在有効なバージョンか |
| valid_from | TIMESTAMP | NN | 有効開始日時 |
| valid_to | TIMESTAMP | | 有効終了日時（現行はnull） |
| change_reason_type | teacher_change_reason | NN | 変更理由種別 |
| change_reason_note | VARCHAR(500) | | 変更理由補足（OTHERの場合は必須） |
| name | VARCHAR(50) | NN | 氏名 |
| gender | gender | NN | male / female |
| min_slots_per_week | INTEGER | NN | 最小コマ/週 |
| max_slots_per_week | INTEGER | NN | 最大コマ/週 |
| max_consecutive_slots | INTEGER | NN | 最大連続コマ（1〜4） |
| has_jhs_exam_experience | BOOLEAN | DEFAULT false | 中学受験経験 |
| has_hs_exam_experience | BOOLEAN | DEFAULT false | 高校受験経験 |
| university_rank | university_rank | | A / B / C / null |
| status | teacher_status | NN | active / inactive |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |
| deleted_at | TIMESTAMP | | 論理削除 |

**UK**: (teacher_id, classroom_id, version_number)

**インデックス**:
- `idx_teachers_current` ON (classroom_id, is_current) WHERE is_current = true AND deleted_at IS NULL
- `idx_teachers_teacher_id` ON (teacher_id, classroom_id)

---

### 4.10 teacher_subjects（講師-指導可能科目）

**目的**: 講師が指導可能な科目を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| teacher_version_id | UUID | PK, FK(teachers) | 講師バージョンID |
| subject_id | VARCHAR(20) | PK, FK(subjects) | 科目ID |

---

### 4.11 teacher_grades（講師-指導可能学年）

**目的**: 講師が指導可能な学年を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| teacher_version_id | UUID | PK, FK(teachers) | 講師バージョンID |
| grade | grade | PK | ele1〜ele6, jhs1〜jhs3, hs1〜hs3 |

---

### 4.12 students（生徒マスタ）

**目的**: 生徒情報をバージョン管理付きで管理

**バージョン管理対象**

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| student_version_id | UUID | PK | バージョンごとの主キー |
| student_id | VARCHAR(20) | NN | 不変ID（例: S001） |
| classroom_id | UUID | FK(classrooms) NN | 教室ID |
| version_number | INTEGER | NN | バージョン番号 |
| is_current | BOOLEAN | NN | 現在有効なバージョンか |
| valid_from | TIMESTAMP | NN | 有効開始日時 |
| valid_to | TIMESTAMP | | 有効終了日時 |
| change_reason_type | student_change_reason | NN | 変更理由種別 |
| change_reason_note | VARCHAR(500) | | 変更理由補足 |
| name | VARCHAR(50) | NN | 氏名 |
| grade | grade | NN | 学年 |
| max_consecutive_slots | INTEGER | NN | 最大連続コマ（1〜4） |
| preferred_teacher_id | VARCHAR(20) | FK(teachers.teacher_id) | 希望講師ID |
| preferred_teacher_gender | preferred_gender | | 講師希望性別（male/female/any） |
| aspiration_level | aspiration_level | | 志望レベル（A/B/C） |
| enrollment_purpose | enrollment_purpose | | 通塾目的 |
| status | student_status | NN | active / inactive |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |
| deleted_at | TIMESTAMP | | 論理削除 |

**UK**: (student_id, classroom_id, version_number)

**インデックス**:
- `idx_students_current` ON (classroom_id, is_current) WHERE is_current = true AND deleted_at IS NULL
- `idx_students_student_id` ON (student_id, classroom_id)

---

### 4.13 student_subjects（生徒-科目別コマ数）

**目的**: 生徒の受講科目と週あたりコマ数を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| student_version_id | UUID | PK, FK(students) | 生徒バージョンID |
| subject_id | VARCHAR(20) | PK, FK(subjects) | 科目ID |
| slots_per_week | INTEGER | NN | 週あたりコマ数（1以上） |

---

### 4.14 subjects（科目マスタ）

**目的**: システム固定の科目マスタ（27科目）

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| subject_id | VARCHAR(20) | PK | 科目ID（例: ELE_MATH_PUB） |
| subject_name | VARCHAR(50) | NN | 科目名（例: 公立算数） |
| grade_category | grade_category | NN | elementary / junior_high / high_school |
| subject_category | subject_category | NN | english / math / japanese / science / social |
| is_jhs_exam_target | BOOLEAN | NN | 中受対象フラグ |
| is_hs_exam_target | BOOLEAN | NN | 高受対象フラグ |

**備考**: 管理画面からの追加・削除不可。変更はシステム改修として対応。

---

### 4.15 ng_relations（NG関係）

**目的**: 講師-生徒間のNG関係を管理（相互設定）

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| ng_relation_id | UUID | PK | 主キー |
| teacher_id | VARCHAR(20) | FK, NN | 講師ID |
| student_id | VARCHAR(20) | FK, NN | 生徒ID |
| created_by | ng_created_by | NN | teacher / student |
| created_at | TIMESTAMP | NN | 作成日時 |

**UK**: (teacher_id, student_id)

---

### 4.16 teacher_shift_preferences（講師シフト希望）

**目的**: ターム単位での講師の勤務可能時間帯を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| preference_id | UUID | PK | 主キー |
| teacher_id | VARCHAR(20) | FK, NN | 講師ID |
| classroom_id | UUID | FK, NN | 教室ID |
| term_id | UUID | FK, NN | タームID |
| day_of_week | day_of_week | NN | 曜日 |
| slot_number | INTEGER | NN | 時限番号 |
| preference_value | teacher_preference_value | NN | available(○) / unavailable(×) |
| is_manually_edited | BOOLEAN | NN, DEFAULT false | 手動編集済みフラグ |
| synced_at | TIMESTAMP | | Google Form同期日時 |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**UK**: (teacher_id, term_id, day_of_week, slot_number)

**インデックス**:
- `idx_teacher_prefs_term` ON (term_id, teacher_id)

---

### 4.17 student_preferences（生徒受講希望）

**目的**: ターム単位での生徒の受講可能時間帯を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| preference_id | UUID | PK | 主キー |
| student_id | VARCHAR(20) | FK, NN | 生徒ID |
| classroom_id | UUID | FK, NN | 教室ID |
| term_id | UUID | FK, NN | タームID |
| day_of_week | day_of_week | NN | 曜日 |
| slot_number | INTEGER | NN | 時限番号 |
| preference_value | student_preference_value | NN | preferred(○) / unavailable(×) / possible(△) |
| is_manually_edited | BOOLEAN | NN, DEFAULT false | 手動編集済みフラグ |
| synced_at | TIMESTAMP | | Google Form同期日時 |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**UK**: (student_id, term_id, day_of_week, slot_number)

**インデックス**:
- `idx_student_prefs_term` ON (term_id, student_id)

---

### 4.18 terms（ターム）

**目的**: 時間割の期間単位を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| term_id | UUID | PK | 主キー |
| classroom_id | UUID | FK, NN | 教室ID |
| term_name | VARCHAR(50) | NN | ターム名（例: 2025年4月） |
| start_date | DATE | NN | 開始日 |
| end_date | DATE | NN | 終了日 |
| status | term_status | NN | creating / confirmed / archived |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |
| deleted_at | TIMESTAMP | | 論理削除 |

**インデックス**:
- `idx_terms_classroom` ON (classroom_id, status) WHERE deleted_at IS NULL

---

### 4.19 term_constraints（ターム固有制約）

**目的**: ターム単位での講師・生徒・教室の個別制約を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| constraint_id | UUID | PK | 主キー |
| term_id | UUID | FK, NN | タームID |
| target_type | constraint_target_type | NN | teacher / student / classroom |
| target_id | VARCHAR(50) | NN | 講師ID / 生徒ID / 教室ID |
| constraint_type | constraint_type | NN | max_slots / min_slots / max_consecutive / booth_capacity / etc. |
| constraint_value | JSONB | NN | 制約値（種別に応じた構造） |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**備考**: target_type=classroom の場合、target_idにはclassroom_id（UUID）を格納。constraint_type=booth_capacityでブース上限のターム調整を保存。

**インデックス**:
- `idx_term_constraints_term` ON (term_id, target_type, target_id)

---

### 4.20 policies（全体ポリシー設定）

**目的**: ターム単位での全体ポリシー（P001〜P006）を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| policy_id | UUID | PK | 主キー |
| term_id | UUID | FK, NN | タームID |
| policy_type | policy_type | NN | P001 / P002 / P003 / P004 / P005 / P006 |
| is_enabled | BOOLEAN | NN, DEFAULT true | 有効/無効 |
| parameters | JSONB | NN | ポリシーパラメータ |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**UK**: (term_id, policy_type)

---

### 4.21 policy_templates（ポリシーテンプレート）

**目的**: 再利用可能なポリシー設定を保存

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| template_id | UUID | PK | 主キー |
| classroom_id | UUID | FK, NN | 教室ID |
| template_name | VARCHAR(100) | NN | テンプレート名 |
| policies | JSONB | NN | 全ポリシーの設定値 |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

---

### 4.22 schedules（時間割）

**目的**: 時間割をバージョン管理付きで管理

**バージョン管理対象**

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| schedule_id | UUID | PK | 主キー |
| term_id | UUID | FK, NN | タームID |
| version | INTEGER | NN | バージョン番号（1から開始） |
| status | schedule_status | NN | draft / confirmed / archived |
| parent_version_id | UUID | FK | 派生元バージョンID |
| master_snapshot | JSONB | NN | 作成時のマスタバージョン参照 |
| generation_config | JSONB | | 生成設定（再現性のため） |
| fulfillment_rate | DECIMAL(5,2) | | 充足率（キャッシュ） |
| soft_constraint_rate | DECIMAL(5,2) | | ソフト制約達成率（キャッシュ） |
| confirmed_at | TIMESTAMP | | 確定日時 |
| confirmed_by | UUID | FK(users) | 確定者ID |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**インデックス**:
- `idx_schedules_term` ON (term_id, status)
- `idx_schedules_confirmed` ON (term_id) WHERE status = 'confirmed'

---

### 4.23 schedule_slots（時間割コマ）

**目的**: 時間割の各コマ（講師-生徒の割り当て）を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| slot_id | UUID | PK | 主キー |
| schedule_id | UUID | FK, NN | 時間割ID |
| day_of_week | day_of_week | NN | 曜日 |
| slot_number | INTEGER | NN | 時限番号 |
| booth_number | INTEGER | NN | ブース番号 |
| teacher_id | VARCHAR(20) | FK, NN | 講師ID |
| student1_id | VARCHAR(20) | FK, NN | 生徒1 ID |
| student2_id | VARCHAR(20) | FK | 生徒2 ID（1対2の場合） |
| subject_id | VARCHAR(20) | FK, NN | 科目ID |
| slot_type | slot_type | NN | one_to_two / one_to_one |
| status | slot_status | NN | scheduled / absent / substituted |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**インデックス**:
- `idx_schedule_slots_schedule` ON (schedule_id, day_of_week, slot_number)
- `idx_schedule_slots_teacher` ON (schedule_id, teacher_id)
- `idx_schedule_slots_student1` ON (schedule_id, student1_id)

---

### 4.24 absences（欠席記録）

**目的**: 講師・生徒の欠席を記録

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| absence_id | UUID | PK | 主キー |
| slot_id | UUID | FK, NN | 欠席対象コマID |
| absent_type | absent_type | NN | teacher / student |
| absent_person_id | VARCHAR(20) | NN | 欠席者ID |
| absence_reason | VARCHAR(200) | | 欠席理由 |
| needs_substitution | BOOLEAN | NN, DEFAULT true | 振替希望有無 |
| substitution_status | substitution_status | NN | pending / completed / cancelled |
| registered_by | UUID | FK(users), NN | 登録者ID |
| created_at | TIMESTAMP | NN | 作成日時 |
| updated_at | TIMESTAMP | NN | 更新日時 |

**インデックス**:
- `idx_absences_slot` ON (slot_id)
- `idx_absences_status` ON (substitution_status) WHERE substitution_status = 'pending'

---

### 4.25 substitutions（振替記録）

**目的**: 振替の確定情報を記録

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| substitution_id | UUID | PK | 主キー |
| absence_id | UUID | FK, NN | 欠席ID |
| original_slot_id | UUID | FK, NN | 元コマID |
| new_slot_id | UUID | FK, NN | 振替先コマID |
| substitution_type | substitution_type | NN | reschedule / substitute |
| priority_score | INTEGER | | 候補選択時の優先度スコア |
| confirmed_by | UUID | FK(users), NN | 確定者ID |
| confirmed_at | TIMESTAMP | NN | 確定日時 |
| created_at | TIMESTAMP | NN | 作成日時 |

---

### 4.26 notifications（通知）

**目的**: ユーザーへの通知を管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| notification_id | UUID | PK | 主キー |
| user_id | UUID | FK, NN | 通知先ユーザーID |
| classroom_id | UUID | FK | 関連教室ID |
| notification_type | notification_type | NN | fulfillment_low / unanswered_preference / etc. |
| severity | severity | NN | critical / warning / info |
| title | VARCHAR(100) | NN | タイトル |
| message | VARCHAR(500) | NN | メッセージ |
| link_url | VARCHAR(500) | | リンクURL |
| is_read | BOOLEAN | NN, DEFAULT false | 既読フラグ |
| read_at | TIMESTAMP | | 既読日時 |
| created_at | TIMESTAMP | NN | 作成日時 |

**インデックス**:
- `idx_notifications_user_unread` ON (user_id, is_read) WHERE is_read = false
- `idx_notifications_user_created` ON (user_id, created_at DESC)

---

### 4.27 password_reset_tokens（パスワードリセットトークン）

**目的**: パスワードリセット用の一時トークンを管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| token_id | UUID | PK | 主キー |
| user_id | UUID | FK, NN | ユーザーID |
| token_hash | VARCHAR(255) | NN | トークンハッシュ |
| expires_at | TIMESTAMP | NN | 有効期限（発行から24時間） |
| used_at | TIMESTAMP | | 使用日時 |
| created_at | TIMESTAMP | NN | 作成日時 |

**インデックス**:
- `idx_password_reset_tokens_user` ON (user_id)
- `idx_password_reset_tokens_expires` ON (expires_at) WHERE used_at IS NULL

---

### 4.28 refresh_tokens（リフレッシュトークン）

**目的**: JWT認証のリフレッシュトークンを管理

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| refresh_token_id | UUID | PK | 主キー |
| user_id | UUID | FK, NN | ユーザーID |
| token_hash | VARCHAR(255) | NN | SHA-256 ハッシュ |
| expires_at | TIMESTAMP | NN | 有効期限（発行から7日） |
| device_info | VARCHAR(500) | | User-Agent等 |
| ip_address | VARCHAR(45) | | 発行時のIP |
| is_revoked | BOOLEAN | NN, DEFAULT false | 失効フラグ |
| revoked_at | TIMESTAMP | | 失効日時 |
| created_at | TIMESTAMP | NN | 作成日時 |

**インデックス**:
- `idx_refresh_tokens_user` ON (user_id) WHERE is_revoked = false
- `idx_refresh_tokens_hash` ON (token_hash)

---

### 4.29 audit_logs（監査ログ）

**目的**: システム操作の監査証跡を記録

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| log_id | UUID | PK | 主キー |
| user_id | UUID | FK | 操作ユーザーID（システム操作時はnull） |
| action | VARCHAR(50) | NN | CREATE / UPDATE / DELETE / LOGIN / etc. |
| entity_type | VARCHAR(50) | NN | Teacher / Student / Schedule / etc. |
| entity_id | VARCHAR(50) | | エンティティID |
| old_value | JSONB | | 変更前値 |
| new_value | JSONB | | 変更後値 |
| ip_address | VARCHAR(45) | | IPアドレス |
| user_agent | VARCHAR(500) | | ユーザーエージェント |
| created_at | TIMESTAMP | NN | 作成日時 |

**インデックス**:
- `idx_audit_logs_user` ON (user_id, created_at DESC)
- `idx_audit_logs_entity` ON (entity_type, entity_id, created_at DESC)
- `idx_audit_logs_created` ON (created_at DESC)

**パーティショニング**: 月単位でパーティショニング推奨（データ量が増加した場合）

---

## 5. ENUM定義

### 5.1 PostgreSQL CREATE TYPE文

```sql
-- ユーザー関連
CREATE TYPE user_role AS ENUM ('classroom_manager', 'area_manager', 'system_admin');
CREATE TYPE user_status AS ENUM ('active', 'inactive');

-- 教室関連
CREATE TYPE classroom_status AS ENUM ('operating', 'closed');
CREATE TYPE day_type AS ENUM ('weekday', 'saturday');
CREATE TYPE day_of_week AS ENUM ('mon', 'tue', 'wed', 'thu', 'fri', 'sat');
CREATE TYPE google_form_data_type AS ENUM ('teacher_shift', 'student_preference');

-- 講師・生徒関連
CREATE TYPE gender AS ENUM ('male', 'female');
CREATE TYPE preferred_gender AS ENUM ('male', 'female', 'any');
CREATE TYPE grade AS ENUM ('ele1', 'ele2', 'ele3', 'ele4', 'ele5', 'ele6', 'jhs1', 'jhs2', 'jhs3', 'hs1', 'hs2', 'hs3');
CREATE TYPE university_rank AS ENUM ('A', 'B', 'C');
CREATE TYPE aspiration_level AS ENUM ('A', 'B', 'C');
CREATE TYPE enrollment_purpose AS ENUM ('hs_exam', 'jhs_exam', 'internal', 'remedial', 'other');
CREATE TYPE teacher_status AS ENUM ('active', 'inactive');
CREATE TYPE student_status AS ENUM ('active', 'inactive');
CREATE TYPE teacher_change_reason AS ENUM ('SCHEDULE_CHANGE', 'SUBJECT_CHANGE', 'GRADE_CHANGE', 'NG_CHANGE', 'STATUS_CHANGE', 'INITIAL', 'OTHER');
CREATE TYPE student_change_reason AS ENUM ('COURSE_CHANGE', 'GRADE_UP', 'PREFERENCE_CHANGE', 'GOAL_CHANGE', 'STATUS_CHANGE', 'INITIAL', 'OTHER');

-- 希望関連
CREATE TYPE teacher_preference_value AS ENUM ('available', 'unavailable');
CREATE TYPE student_preference_value AS ENUM ('preferred', 'unavailable', 'possible');

-- ターム・制約関連
CREATE TYPE term_status AS ENUM ('creating', 'confirmed', 'archived');
CREATE TYPE constraint_target_type AS ENUM ('teacher', 'student', 'classroom');
CREATE TYPE constraint_type AS ENUM ('max_slots', 'min_slots', 'max_consecutive', 'subject_limit', 'day_limit', 'preferred_teacher', 'ng_teacher', 'gender_preference', 'booth_capacity');
CREATE TYPE policy_type AS ENUM ('P001', 'P002', 'P003', 'P004', 'P005', 'P006');

-- 時間割関連
CREATE TYPE schedule_status AS ENUM ('draft', 'confirmed', 'archived');
CREATE TYPE slot_type AS ENUM ('one_to_two', 'one_to_one');
CREATE TYPE slot_status AS ENUM ('scheduled', 'absent', 'substituted');

-- 欠席・振替関連
CREATE TYPE absent_type AS ENUM ('teacher', 'student');
CREATE TYPE substitution_status AS ENUM ('pending', 'completed', 'cancelled');
CREATE TYPE substitution_type AS ENUM ('reschedule', 'substitute');
CREATE TYPE ng_created_by AS ENUM ('teacher', 'student');

-- 通知関連
CREATE TYPE notification_type AS ENUM ('fulfillment_low', 'unanswered_preference', 'term_deadline', 'schedule_conflict');
CREATE TYPE severity AS ENUM ('critical', 'warning', 'info');

-- 科目関連
CREATE TYPE grade_category AS ENUM ('elementary', 'junior_high', 'high_school');
CREATE TYPE subject_category AS ENUM ('english', 'math', 'japanese', 'science', 'social');
```

---

## 6. 科目マスタ（初期データ）

```sql
INSERT INTO subjects (subject_id, subject_name, grade_category, subject_category, is_jhs_exam_target, is_hs_exam_target) VALUES
-- 小学生
('ELE_ENG', '小学英語', 'elementary', 'english', false, false),
('ELE_MATH_PUB', '公立算数', 'elementary', 'math', false, false),
('ELE_MATH_JKN', '中受算数', 'elementary', 'math', true, false),
('ELE_JPN', '小学国語', 'elementary', 'japanese', false, false),
('ELE_ESSAY', '小論', 'elementary', 'japanese', false, false),
('ELE_SCI_PUB', '公立理科', 'elementary', 'science', false, false),
('ELE_SCI_JKN', '中受理科', 'elementary', 'science', true, false),
('ELE_SOC_PUB', '公立社会', 'elementary', 'social', false, false),
('ELE_SOC_JKN', '中受社会', 'elementary', 'social', true, false),
-- 中学生
('JHS_ENG', '中学英語', 'junior_high', 'english', false, true),
('JHS_MATH_PUB', '公立数学', 'junior_high', 'math', false, true),
('JHS_MATH_PRI', '私立数学', 'junior_high', 'math', false, true),
('JHS_JPN', '中学国語', 'junior_high', 'japanese', false, true),
('JHS_SCI', '中学理科', 'junior_high', 'science', false, true),
('JHS_SOC', '中学社会', 'junior_high', 'social', false, true),
-- 高校生
('HS_ENG_12', '高校12英語', 'high_school', 'english', false, false),
('HS_ENG_3', '高3英語', 'high_school', 'english', false, false),
('HS_JPN', '高校国語', 'high_school', 'japanese', false, false),
('HS_MATH_1A', '数1A', 'high_school', 'math', false, false),
('HS_MATH_2B', '数ⅡB', 'high_school', 'math', false, false),
('HS_MATH_3', '数Ⅲ', 'high_school', 'math', false, false),
('HS_BIO', '生物', 'high_school', 'science', false, false),
('HS_CHEM', '化学', 'high_school', 'science', false, false),
('HS_PHYS', '物理', 'high_school', 'science', false, false),
('HS_WHIS', '世界史', 'high_school', 'social', false, false),
('HS_JHIS', '日本史', 'high_school', 'social', false, false),
('HS_GEO', '地理', 'high_school', 'social', false, false);
```

---

## 7. インデックス戦略

### 7.1 インデックス設計方針

| 方針 | 説明 |
|------|------|
| 検索頻度重視 | WHERE/JOIN条件に頻繁に使用されるカラムに付与 |
| 部分インデックス | 論理削除やステータスで絞り込む場合は WHERE 句付きインデックス |
| 複合インデックス | よく組み合わせて使用されるカラムは複合インデックス |
| 書き込み負荷考慮 | audit_logs等の書き込み頻度が高いテーブルはインデックス数を抑制 |

### 7.2 主要インデックス一覧

| テーブル | インデックス名 | カラム | 用途 |
|---------|--------------|--------|------|
| users | idx_users_email | email | ログイン |
| users | idx_users_role | role | 役割別一覧 |
| classrooms | idx_classrooms_area_id | area_id | エリア別教室一覧 |
| teachers | idx_teachers_current | classroom_id, is_current | 現行講師一覧 |
| students | idx_students_current | classroom_id, is_current | 現行生徒一覧 |
| teacher_shift_preferences | idx_teacher_prefs_term | term_id, teacher_id | ターム別希望 |
| student_preferences | idx_student_prefs_term | term_id, student_id | ターム別希望 |
| schedules | idx_schedules_term | term_id, status | ターム別時間割 |
| schedule_slots | idx_schedule_slots_schedule | schedule_id, day_of_week, slot_number | コマ検索 |
| notifications | idx_notifications_user_unread | user_id, is_read | 未読通知 |
| audit_logs | idx_audit_logs_created | created_at DESC | 監査ログ検索 |

---

## 8. 制約・トリガー

### 8.1 CHECK制約

```sql
-- teachers: コマ数の整合性
ALTER TABLE teachers ADD CONSTRAINT chk_teachers_slots
  CHECK (min_slots_per_week <= max_slots_per_week);

ALTER TABLE teachers ADD CONSTRAINT chk_teachers_consecutive
  CHECK (max_consecutive_slots BETWEEN 1 AND 4);

-- students: 連続コマ数の範囲
ALTER TABLE students ADD CONSTRAINT chk_students_consecutive
  CHECK (max_consecutive_slots BETWEEN 1 AND 4);

-- student_subjects: コマ数は1以上
ALTER TABLE student_subjects ADD CONSTRAINT chk_student_subjects_slots
  CHECK (slots_per_week >= 1);

-- schedules: 充足率は0〜100
ALTER TABLE schedules ADD CONSTRAINT chk_schedules_fulfillment
  CHECK (fulfillment_rate IS NULL OR (fulfillment_rate >= 0 AND fulfillment_rate <= 100));
```

### 8.2 トリガー（updated_at自動更新）

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 全テーブルに適用（例: users）
CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

### 8.3 NG関係の相互設定トリガー

```sql
-- NG関係は相互設定不要（同一レコードで管理）
-- ただし、created_by で誰が設定したかを記録
```

---

## 9. マイグレーション方針

### 9.1 マイグレーションツール

| 項目 | 選定 |
|------|------|
| ツール | Alembic（Python/FastAPI） |
| 命名規則 | `YYYYMMDD_HHMMSS_description.py` |
| 管理テーブル | alembic_version |

### 9.2 マイグレーション順序

1. ENUM型の作成
2. 独立テーブル（areas, subjects）
3. 依存テーブル（classrooms → classroom_settings → teachers → ...）
4. 中間テーブル
5. インデックス作成
6. 初期データ投入（subjects）

---

## 10. 非機能要件との整合性

| 要件 | 目標 | DB設計での対応 |
|------|------|--------------|
| レスポンス1秒以内 | ダッシュボード | 適切なインデックス + 充足率キャッシュ |
| 同時100ユーザー | 接続数 | RDS db.t4g.micro（最大100接続）で対応 |
| RPO 1時間 | データ損失 | RDS自動バックアップ（5分間隔） |
| 監査ログ1年保持 | 保持期間 | audit_logs + パーティショニング |
| 論理削除 | データ保護 | deleted_at + 部分インデックス |

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-03-24 | 初版作成（29テーブル、ER図、ENUM定義、インデックス戦略） |
| 2026-03-24 | データ一覧/要件定義書v1との整合性検証に基づく修正: 参照パス修正(data-list/)、constraint_target_typeにclassroom追加、constraint_typeにbooth_capacity追加、preferred_gender ENUM追加、非機能要件整合（ロック30分、リフレッシュトークン7日） |
