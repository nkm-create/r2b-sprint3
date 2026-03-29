"""
時間割作成APIスキーマ
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# 問題分析 (F080)
class ScaleDetails(BaseModel):
    """問題規模詳細"""
    teacher_count: int
    student_count: int
    weekly_slots: int


class Bottleneck(BaseModel):
    """ボトルネック情報"""
    type: str  # time_slot, subject, teacher
    day_of_week: str | None = None
    slot_number: int | None = None
    subject: str | None = None
    demand: int
    supply: int
    gap: int


class ProblemAnalysis(BaseModel):
    """問題分析結果"""
    scale: str  # small, medium, large
    scale_details: ScaleDetails
    difficulty: str  # low, medium, high
    difficulty_reasons: list[str]
    bottlenecks: list[Bottleneck]


class RecommendedStrategy(BaseModel):
    """推奨戦略"""
    initial_strategy: str  # standard, relaxed, partial
    timeout: int
    reason: str


class AnalyzeResponse(BaseModel):
    """問題分析レスポンス"""
    analysis: ProblemAnalysis
    recommended_strategy: RecommendedStrategy


# 時間割作成ジャーニー
class JourneyStepStatus(BaseModel):
    """ジャーニーステップの状態"""
    is_ready: bool
    message: str


class ScheduleJourneyStatusResponse(BaseModel):
    """時間割作成ジャーニーの状態"""
    is_ready_to_generate: bool
    steps: dict[str, JourneyStepStatus]
    counts: dict[str, int]
    missing_requirements: list[str]


# 時間割生成 (F081)
class GenerateOptions(BaseModel):
    """生成オプション"""
    max_timeout_seconds: int = Field(default=60, ge=10, le=120)
    progress_channel: str | None = None


class GenerateRequest(BaseModel):
    """生成リクエスト"""
    options: GenerateOptions = Field(default_factory=GenerateOptions)


class GenerationResult(BaseModel):
    """生成結果"""
    soft_constraint_rate: Decimal
    one_to_two_rate: Decimal
    unplaced_students: int


class OrchestratorDecision(BaseModel):
    """オーケストレーター判断"""
    time_ms: int
    decision: str  # continue, stop
    current_rate: Decimal
    reason: str


class SolverStats(BaseModel):
    """ソルバー統計"""
    strategy_used: str
    solve_time_ms: int
    solutions_found: int
    optimality_gap: Decimal | None = None
    termination_reason: str


class UnplacedDetail(BaseModel):
    """未配置生徒詳細"""
    student_id: str
    student_name: str
    subject: str
    reason: str


class GenerateSuccessResponse(BaseModel):
    """生成成功レスポンス"""
    schedule_id: UUID
    version: int
    status: str = "draft"
    solution_status: str  # optimal, feasible, partial
    result: GenerationResult
    solver_stats: SolverStats
    orchestrator_decisions: list[OrchestratorDecision]
    next_action: str = "confirm_or_adjust"


class StrategyAttempt(BaseModel):
    """戦略試行"""
    strategy: str
    result: str
    time_ms: int


class GeneratePartialResponse(BaseModel):
    """部分解レスポンス"""
    schedule_id: UUID
    version: int
    status: str = "draft"
    solution_status: str = "partial"
    result: GenerationResult
    unplaced_details: list[UnplacedDetail]
    solver_stats: dict
    next_actions: list[dict]


class ConflictingConstraint(BaseModel):
    """競合制約"""
    constraint_type: str
    description: str
    affected_students: list[str]
    detail: str


class RelaxationSuggestion(BaseModel):
    """緩和提案"""
    suggestion_id: int
    title: str
    constraint_to_relax: str
    impact: str
    affected_count: int


class InfeasibilityAnalysis(BaseModel):
    """実行不可能分析"""
    conflicting_constraints: list[ConflictingConstraint]


class GenerateInfeasibleResponse(BaseModel):
    """実行不可能レスポンス"""
    schedule_id: None = None
    solution_status: str = "infeasible"
    infeasibility_analysis: InfeasibilityAnalysis
    relaxation_suggestions: list[RelaxationSuggestion]
    next_action: str = "select_relaxation"


# 再生成
class RegenerateRequest(BaseModel):
    """再生成リクエスト"""
    relaxations: list[dict] = Field(default_factory=list)
    fixed_slots: list[str] = Field(default_factory=list)

    def to_generate_options(self, progress_channel: str | None = None) -> "GenerateOptions":
        return GenerateOptions(progress_channel=progress_channel)


# 結果説明 (F082)
class ExplanationSummary(BaseModel):
    """説明サマリー"""
    overall: str
    key_points: list[str]


class BottleneckExplanation(BaseModel):
    """ボトルネック説明"""
    main_bottleneck: str
    detail: str
    structural_cause: bool


class TradeOff(BaseModel):
    """トレードオフ"""
    description: str
    pros: list[str]
    cons: list[str]
    recommendation: str


class ExplanationResponse(BaseModel):
    """説明レスポンス"""
    summary: ExplanationSummary
    bottleneck_explanation: BottleneckExplanation
    trade_offs: list[TradeOff]


# What-if分析
class WhatIfRequest(BaseModel):
    """What-ifリクエスト"""
    question: str


class WhatIfImpact(BaseModel):
    """What-if影響"""
    feasible: bool
    impact: dict


class WhatIfResponse(BaseModel):
    """What-ifレスポンス"""
    analysis: WhatIfImpact
    explanation: str


# カレンダービュー (F083)
class ScheduleMetrics(BaseModel):
    """時間割メトリクス"""
    soft_constraint_rate: Decimal
    one_to_two_rate: Decimal
    unplaced_count: int


class PersonInfo(BaseModel):
    """人物情報"""
    id: str
    name: str
    subject: str | None = None


class SlotInfo(BaseModel):
    """コマ情報"""
    slot_id: UUID
    teacher: PersonInfo
    student1: PersonInfo
    student2: PersonInfo | None = None
    slot_type: str
    status: str
    has_issue: bool = False
    issues: list[str] = Field(default_factory=list)


class CellInfo(BaseModel):
    """セル情報"""
    day_of_week: str
    slot_number: int
    slots: list[SlotInfo]
    status: str  # sufficient, warning, critical
    issues: list[str]


class UnplacedStudent(BaseModel):
    """未配置生徒"""
    student_id: str
    student_name: str
    subject: str
    required_slots: int
    reason: str


class CalendarViewResponse(BaseModel):
    """カレンダービューレスポンス"""
    schedule_id: UUID
    status: str
    solution_status: str
    metrics: ScheduleMetrics
    time_slots: dict
    cells: list[CellInfo]
    unplaced_students: list[UnplacedStudent]


# 手動調整 (F085)
class MovableTarget(BaseModel):
    """移動可能先"""
    day_of_week: str
    slot_number: int
    feasibility: str  # allowed, soft_violation, hard_violation
    violations: list[str] = Field(default_factory=list)
    impact: dict = Field(default_factory=dict)


class MovableTargetsResponse(BaseModel):
    """移動可能先レスポンス"""
    targets: list[MovableTarget]


class MoveSlotRequest(BaseModel):
    """コマ移動リクエスト"""
    target_day_of_week: str
    target_slot_number: int
    force: bool = False


class MoveSlotResponse(BaseModel):
    """コマ移動レスポンス"""
    success: bool
    new_slot_id: UUID | None = None
    updated_metrics: ScheduleMetrics | None = None
    error: str | None = None


# 時間割確定 (F086)
class ConfirmRequest(BaseModel):
    """確定リクエスト"""
    force: bool = False


class ConfirmWarning(BaseModel):
    """確定警告"""
    type: str
    current: Decimal | None = None
    target: Decimal | None = None
    message: str


class ConfirmCheckResponse(BaseModel):
    """確定前チェックレスポンス"""
    can_confirm: bool
    warnings: list[ConfirmWarning]
    require_confirmation: bool


class ConfirmResponse(BaseModel):
    """確定レスポンス"""
    schedule_id: UUID
    status: str
    confirmed_at: datetime
    message: str


# PDF/CSV出力 (F087)
class ExportOptions(BaseModel):
    """出力オプション"""
    paper_size: str = "A3"
    orientation: str = "landscape"


class ExportRequest(BaseModel):
    """出力リクエスト"""
    format: str  # pdf, csv
    type: str = "all"  # all, by_teacher, by_student
    options: ExportOptions = Field(default_factory=ExportOptions)


class ExportResponse(BaseModel):
    """出力レスポンス"""
    download_url: str
    expires_at: datetime
    file_name: str


# 時間割一覧
class ScheduleListItem(BaseModel):
    """時間割一覧アイテム"""
    schedule_id: UUID
    version: int
    status: str
    soft_constraint_rate: Decimal | None = None
    one_to_two_rate: Decimal | None = None
    created_at: datetime
    confirmed_at: datetime | None = None


class ScheduleListResponse(BaseModel):
    """時間割一覧レスポンス"""
    data: list[ScheduleListItem]


# WebSocket進捗
class GenerationProgress(BaseModel):
    """生成進捗"""
    type: str  # progress, complete, error
    solutions_found: int | None = None
    current_rate: Decimal | None = None
    elapsed_ms: int | None = None
    strategy: str | None = None
    status: str | None = None
    final_rate: Decimal | None = None
    termination_reason: str | None = None
    error: str | None = None
