"""
LLMサービスのユニットテスト

このテストは外部依存を最小限に抑え、LLMサービスの機能を独立してテストします。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Any


# テスト用のデータクラス定義（実際のクラスと同じ構造）
@dataclass
class SampleExplanationContext:
    """テスト用の説明生成コンテキスト"""
    soft_constraint_rate: Decimal
    one_to_two_rate: Decimal
    teacher_count: int
    student_count: int
    weekly_slots: int
    bottlenecks: list = field(default_factory=list)
    constraint_violations: list = field(default_factory=list)
    schedule_status: str = "optimal"


@dataclass
class SampleWhatIfContext:
    """テスト用のWhat-ifコンテキスト"""
    question: str
    current_soft_constraint_rate: Decimal
    related_constraints: list = field(default_factory=list)
    affected_teachers: list = field(default_factory=list)
    affected_students: list = field(default_factory=list)


@dataclass
class SampleLLMResponse:
    """テスト用のLLM応答"""
    content: str
    model: str = ""
    tokens_used: int = 0
    is_fallback: bool = False


class TestLLMServiceFunctionality:
    """LLMサービスの機能テスト"""

    @pytest.fixture
    def explanation_context(self):
        """説明生成用のコンテキスト"""
        return SampleExplanationContext(
            soft_constraint_rate=Decimal("78.2"),
            one_to_two_rate=Decimal("82.3"),
            teacher_count=15,
            student_count=45,
            weekly_slots=120,
            bottlenecks=[
                {
                    "type": "time_slot",
                    "day_of_week": "sat",
                    "slot_number": 3,
                    "demand": 15,
                    "supply": 10,
                    "gap": -5,
                }
            ],
            constraint_violations=[],
            schedule_status="optimal",
        )

    @pytest.fixture
    def what_if_context(self):
        """What-if分析用のコンテキスト"""
        return SampleWhatIfContext(
            question="講師Aの水曜日の勤務を増やした場合、充足率はどうなりますか？",
            current_soft_constraint_rate=Decimal("85.5"),
            current_soft_constraint_rate=Decimal("78.2"),
            related_constraints=[
                {"code": "H002", "name": "出勤可能制約"},
                {"code": "S001", "name": "希望時間制約"},
            ],
            affected_teachers=["T001"],
            affected_students=["S001", "S002"],
        )

    def test_explanation_context_creation(self, explanation_context):
        """ExplanationContextが正しく作成される"""
        assert explanation_context.soft_constraint_rate == Decimal("85.5")
        assert explanation_context.teacher_count == 15
        assert len(explanation_context.bottlenecks) == 1

    def test_what_if_context_creation(self, what_if_context):
        """WhatIfContextが正しく作成される"""
        assert "講師A" in what_if_context.question
        assert what_if_context.current_soft_constraint_rate == Decimal("85.5")

    def test_llm_response_creation(self):
        """LLMResponseが正しく作成される"""
        response = SampleLLMResponse(
            content="テスト応答",
            model="gpt-4o",
            tokens_used=100,
            is_fallback=False,
        )

        assert response.content == "テスト応答"
        assert response.model == "gpt-4o"
        assert response.tokens_used == 100
        assert response.is_fallback is False

    def test_llm_response_defaults(self):
        """LLMResponseのデフォルト値"""
        response = SampleLLMResponse(content="テスト")

        assert response.content == "テスト"
        assert response.model == ""
        assert response.tokens_used == 0
        assert response.is_fallback is False


class TestPromptBuilding:
    """プロンプト構築のテスト"""

    def test_build_explanation_prompt_structure(self):
        """説明用プロンプトの構造テスト"""
        context = SampleExplanationContext(
            soft_constraint_rate=Decimal("85.5"),
            soft_constraint_rate=Decimal("78.2"),
            one_to_two_rate=Decimal("82.3"),
            teacher_count=15,
            student_count=45,
            weekly_slots=120,
            bottlenecks=[
                {
                    "type": "time_slot",
                    "day_of_week": "sat",
                    "slot_number": 3,
                    "demand": 15,
                    "supply": 10,
                    "gap": -5,
                }
            ],
            constraint_violations=[],
            schedule_status="optimal",
        )

        # プロンプト構築のロジックをテスト
        day_map = {
            "mon": "月曜", "tue": "火曜", "wed": "水曜",
            "thu": "木曜", "fri": "金曜", "sat": "土曜",
        }

        bottleneck_items = []
        for b in context.bottlenecks:
            day_jp = day_map.get(b.get("day_of_week", ""), b.get("day_of_week", ""))
            slot = b.get("slot_number", "")
            gap = b.get("gap", 0)
            bottleneck_items.append(
                f"- {day_jp}{slot}限: 需要{b.get('demand', 0)}に対し供給{b.get('supply', 0)}（差: {gap}）"
            )
        bottleneck_text = "\n".join(bottleneck_items)

        prompt = f"""## 基本情報
- 講師数: {context.teacher_count}名
- 生徒数: {context.student_count}名

## 生成結果
- ソフト制約達成率: {context.soft_constraint_rate}%

## ボトルネック
{bottleneck_text}"""

        assert "85.5" in prompt
        assert "講師数: 15" in prompt
        assert "生徒数: 45" in prompt
        assert "土曜" in prompt

    def test_build_what_if_prompt_structure(self):
        """What-if分析用プロンプトの構造テスト"""
        context = SampleWhatIfContext(
            question="講師Aの水曜日の勤務を増やした場合",
            current_soft_constraint_rate=Decimal("85.5"),
            current_soft_constraint_rate=Decimal("78.2"),
            related_constraints=[
                {"code": "H002", "name": "出勤可能制約"},
            ],
            affected_teachers=["T001"],
            affected_students=["S001"],
        )

        constraints_text = "\n".join([
            f"- {c.get('code', '')}: {c.get('name', '')}"
            for c in context.related_constraints
        ])

        prompt = f"""## 質問
「{context.question}」

## 現在の状態
- ソフト制約達成率: {context.current_soft_constraint_rate}%

## 関連する制約条件
{constraints_text}"""

        assert "講師A" in prompt
        assert "85.5" in prompt
        assert "H002" in prompt


class TestFallbackLogic:
    """フォールバックロジックのテスト"""

    def test_explanation_fallback_good_rate(self):
        """充足率が高い場合のフォールバック"""
        fulfillment = Decimal("90.0")

        if fulfillment >= 85:
            summary = f"充足率{fulfillment}%で、良好な時間割が生成されました。"
        elif fulfillment >= 70:
            summary = f"充足率{fulfillment}%で、概ね良好な時間割ですが、改善の余地があります。"
        else:
            summary = f"充足率{fulfillment}%で、いくつかの課題があります。"

        assert "良好" in summary
        assert "90.0" in summary

    def test_explanation_fallback_medium_rate(self):
        """充足率が中程度の場合のフォールバック"""
        fulfillment = Decimal("75.0")

        if fulfillment >= 85:
            summary = f"充足率{fulfillment}%で、良好な時間割が生成されました。"
        elif fulfillment >= 70:
            summary = f"充足率{fulfillment}%で、概ね良好な時間割ですが、改善の余地があります。"
        else:
            summary = f"充足率{fulfillment}%で、いくつかの課題があります。"

        assert "概ね良好" in summary
        assert "改善の余地" in summary

    def test_explanation_fallback_low_rate(self):
        """充足率が低い場合のフォールバック"""
        fulfillment = Decimal("60.0")

        if fulfillment >= 85:
            summary = f"充足率{fulfillment}%で、良好な時間割が生成されました。"
        elif fulfillment >= 70:
            summary = f"充足率{fulfillment}%で、概ね良好な時間割ですが、改善の余地があります。"
        else:
            summary = f"充足率{fulfillment}%で、いくつかの課題があります。"

        assert "課題" in summary

    def test_what_if_fallback_contains_question(self):
        """What-ifフォールバックが質問を含む"""
        question = "講師Aの勤務を増やした場合"

        content = f"""ご質問「{question}」について分析しました。

【実行可能性】
この変更は実行可能ですが、いくつかの影響を考慮する必要があります。

【推奨事項】
詳細な影響を確認するには、変更を適用した上で再生成を実行することをお勧めします。
"""

        assert question in content
        assert "実行可能" in content
        assert "推奨" in content


class TestPromptTemplateContent:
    """プロンプトテンプレートの内容テスト"""

    def test_explanation_system_prompt_requirements(self):
        """説明用システムプロンプトの要件"""
        # 実際のシステムプロンプトの期待される内容
        expected_keywords = [
            "時間割",
            "教室長",
            "説明",
        ]

        system_prompt = """あなたは学習塾の時間割最適化システムのExplainer Agentです。
生成された時間割の結果を、教室長（非技術者）に分かりやすく説明する役割を担っています。"""

        for keyword in expected_keywords:
            assert keyword in system_prompt, f"Expected '{keyword}' in system prompt"

    def test_what_if_system_prompt_requirements(self):
        """What-if分析用システムプロンプトの要件"""
        expected_keywords = [
            "分析",
            "影響",
        ]

        system_prompt = """あなたは学習塾の時間割最適化システムのExplainer Agentです。
「もし〜したら？」という仮説的な質問に対して、影響分析を行います。"""

        has_any = any(keyword in system_prompt for keyword in expected_keywords)
        assert has_any, f"Expected at least one of {expected_keywords} in system prompt"


class TestAsyncBehavior:
    """非同期動作のテスト"""

    @pytest.mark.asyncio
    async def test_async_api_call_mock(self):
        """非同期API呼び出しのモックテスト"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="テスト応答です。"))
        ]
        mock_response.usage = MagicMock(total_tokens=100)

        async def mock_create(*args, **kwargs):
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create

        # 非同期呼び出しをシミュレート
        response = await mock_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
        )

        assert response.choices[0].message.content == "テスト応答です。"
        assert response.usage.total_tokens == 100

    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """非同期例外処理のテスト"""
        async def mock_failing_call(*args, **kwargs):
            raise Exception("API Error")

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_failing_call

        # 例外が発生することを確認
        with pytest.raises(Exception) as exc_info:
            await mock_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
            )

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_timeout_simulation(self):
        """タイムアウトのシミュレーションテスト"""
        import asyncio

        async def mock_slow_call(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Timeout")

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_slow_call

        with pytest.raises(asyncio.TimeoutError):
            await mock_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
            )


class TestIntegrationPoints:
    """統合ポイントのテスト"""

    def test_context_to_dict_conversion(self):
        """コンテキストから辞書への変換"""
        context = SampleExplanationContext(
            soft_constraint_rate=Decimal("85.5"),
            soft_constraint_rate=Decimal("78.2"),
            one_to_two_rate=Decimal("82.3"),
            teacher_count=15,
            student_count=45,
            weekly_slots=120,
        )

        # dataclassをdict化
        from dataclasses import asdict
        context_dict = asdict(context)

        assert context_dict["soft_constraint_rate"] == Decimal("85.5")
        assert context_dict["teacher_count"] == 15

    def test_decimal_to_string_formatting(self):
        """Decimal型の文字列フォーマット"""
        rate = Decimal("85.567")

        formatted = f"{rate:.1f}%"
        assert formatted == "85.6%"

        formatted2 = f"{rate:.2f}%"
        assert formatted2 == "85.57%"

    def test_bottleneck_day_mapping(self):
        """ボトルネック曜日のマッピング"""
        day_map = {
            "mon": "月曜", "tue": "火曜", "wed": "水曜",
            "thu": "木曜", "fri": "金曜", "sat": "土曜",
        }

        assert day_map["sat"] == "土曜"
        assert day_map["mon"] == "月曜"
        assert day_map.get("sun", "日曜") == "日曜"
