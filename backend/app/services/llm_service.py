"""
LLMサービス - OpenAI APIを使用した自然言語生成

Explainer Agentとして、時間割の結果説明とWhat-if分析を提供する。
"""
import asyncio
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings


# システムプロンプト定義
EXPLANATION_SYSTEM_PROMPT = """あなたは学習塾の時間割最適化システムのExplainer Agentです。
生成された時間割の結果を、教室長（非技術者）に分かりやすく説明する役割を担っています。

以下の点を心がけてください：
1. 専門用語を避け、平易な日本語で説明する
2. 充足率、1対2率などの指標の意味を補足する
3. ボトルネックがある場合は、その原因と改善の方向性を示す
4. 肯定的な点も言及し、バランスの取れた説明を心がける

出力形式:
- 全体サマリー（2-3文）
- 主要なポイント（箇条書き3-5項目）
- ボトルネックの説明（該当する場合）
- 改善の可能性（該当する場合）
"""

WHAT_IF_SYSTEM_PROMPT = """あなたは学習塾の時間割最適化システムのExplainer Agentです。
「もし〜したら？」という仮説的な質問に対して、影響分析を行います。

以下の点を心がけてください：
1. 質問の意図を正確に理解する
2. 変更による影響を具体的に説明する
3. メリット・デメリットを両方示す
4. 実行可能性についても言及する
5. 必要に応じて代替案を提案する

出力形式:
- 変更の実行可能性（可能/注意が必要/困難）
- 予想される影響
- メリット
- デメリットまたは注意点
- 推奨事項
"""


@dataclass
class ExplanationContext:
    """説明生成用のコンテキスト"""
    soft_constraint_rate: Decimal
    one_to_two_rate: Decimal
    teacher_count: int
    student_count: int
    weekly_slots: int
    bottlenecks: list[dict] = field(default_factory=list)
    constraint_violations: list[dict] = field(default_factory=list)
    schedule_status: str = "optimal"


@dataclass
class WhatIfContext:
    """What-if分析用のコンテキスト"""
    question: str
    current_soft_constraint_rate: Decimal
    related_constraints: list[dict] = field(default_factory=list)
    affected_teachers: list[str] = field(default_factory=list)
    affected_students: list[str] = field(default_factory=list)


@dataclass
class LLMResponse:
    """LLM応答"""
    content: str
    model: str = ""
    tokens_used: int = 0
    is_fallback: bool = False


class LLMService:
    """LLMサービス - OpenAI APIラッパー"""

    def __init__(self, timeout: float = 30.0):
        """
        初期化

        Args:
            timeout: API呼び出しのタイムアウト（秒）
        """
        self.timeout = timeout
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI | None:
        """OpenAIクライアントを取得"""
        if not settings.OPENAI_API_KEY:
            return None

        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=self.timeout,
            )
        return self._client

    async def generate_explanation(
        self, context: ExplanationContext
    ) -> LLMResponse:
        """
        時間割の結果説明を生成

        Args:
            context: 説明生成用のコンテキスト

        Returns:
            LLMResponse: 生成された説明
        """
        try:
            client = self._get_client()
            if client is None:
                return self._generate_explanation_fallback(context)

            prompt = self._build_explanation_prompt(context)
            return await self._call_openai(
                system_prompt=EXPLANATION_SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        except asyncio.TimeoutError:
            return self._generate_explanation_fallback(context)
        except Exception:
            return self._generate_explanation_fallback(context)

    async def generate_what_if_analysis(
        self, context: WhatIfContext
    ) -> LLMResponse:
        """
        What-if分析を生成

        Args:
            context: What-if分析用のコンテキスト

        Returns:
            LLMResponse: 生成された分析
        """
        try:
            client = self._get_client()
            if client is None:
                return self._generate_what_if_fallback(context)

            prompt = self._build_what_if_prompt(context)
            return await self._call_openai(
                system_prompt=WHAT_IF_SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        except asyncio.TimeoutError:
            return self._generate_what_if_fallback(context)
        except Exception:
            return self._generate_what_if_fallback(context)

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        """
        OpenAI APIを呼び出す

        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザープロンプト

        Returns:
            LLMResponse: API応答
        """
        client = self._get_client()
        if client is None:
            raise ValueError("OpenAI client is not available")

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0

        return LLMResponse(
            content=content,
            model=settings.OPENAI_MODEL,
            tokens_used=tokens_used,
            is_fallback=False,
        )

    def _build_explanation_prompt(self, context: ExplanationContext) -> str:
        """説明生成用のプロンプトを構築"""
        bottleneck_text = ""
        if context.bottlenecks:
            bottleneck_items = []
            day_map = {
                "mon": "月曜", "tue": "火曜", "wed": "水曜",
                "thu": "木曜", "fri": "金曜", "sat": "土曜",
            }
            for b in context.bottlenecks:
                day_jp = day_map.get(b.get("day_of_week", ""), b.get("day_of_week", ""))
                slot = b.get("slot_number", "")
                gap = b.get("gap", 0)
                bottleneck_items.append(
                    f"- {day_jp}{slot}限: 需要{b.get('demand', 0)}に対し供給{b.get('supply', 0)}（差: {gap}）"
                )
            bottleneck_text = "\n".join(bottleneck_items)

        violations_text = ""
        if context.constraint_violations:
            violation_items = [
                f"- {v.get('constraint_name', '')}: {v.get('description', '')}"
                for v in context.constraint_violations
            ]
            violations_text = "\n".join(violation_items)

        prompt = f"""以下の時間割生成結果について、教室長向けに分かりやすく説明してください。

## 基本情報
- 講師数: {context.teacher_count}名
- 生徒数: {context.student_count}名
- 週間コマ数: {context.weekly_slots}コマ

## 生成結果
- ソフト制約達成率: {context.soft_constraint_rate}%
- 1対2率: {context.one_to_two_rate}%
- 求解ステータス: {context.schedule_status}

## ボトルネック
{bottleneck_text if bottleneck_text else "特に顕著なボトルネックは検出されませんでした。"}

## 制約違反
{violations_text if violations_text else "ハード制約違反はありません。"}

上記の情報を踏まえて、以下の構成で説明を作成してください：
1. 全体サマリー
2. 良い点
3. 改善が必要な点（もしあれば）
4. 今後の推奨アクション
"""
        return prompt

    def _build_what_if_prompt(self, context: WhatIfContext) -> str:
        """What-if分析用のプロンプトを構築"""
        constraints_text = ""
        if context.related_constraints:
            constraint_items = [
                f"- {c.get('code', '')}: {c.get('name', '')}"
                for c in context.related_constraints
            ]
            constraints_text = "\n".join(constraint_items)

        prompt = f"""以下の「もし〜したら？」という質問に対して、影響分析を行ってください。

## 質問
「{context.question}」

## 現在の状態
- ソフト制約達成率: {context.current_soft_constraint_rate}%

## 関連する制約条件
{constraints_text if constraints_text else "特定の関連制約なし"}

## 影響を受ける可能性のある対象
- 講師: {', '.join(context.affected_teachers) if context.affected_teachers else 'なし'}
- 生徒: {', '.join(context.affected_students) if context.affected_students else 'なし'}

上記の情報を踏まえて、以下の構成で分析結果を作成してください：
1. 変更の実行可能性
2. 予想される影響（充足率への影響など）
3. メリット
4. デメリットまたは注意点
5. 推奨事項
"""
        return prompt

    def _generate_explanation_fallback(
        self, context: ExplanationContext
    ) -> LLMResponse:
        """説明生成のフォールバック"""
        soft_rate = context.soft_constraint_rate
        one_to_two = context.one_to_two_rate

        # ステータスに応じたサマリー
        if soft_rate >= 85:
            summary = f"ソフト制約達成率{soft_rate}%で、良好な時間割が生成されました。"
        elif soft_rate >= 70:
            summary = f"ソフト制約達成率{soft_rate}%で、概ね良好な時間割ですが、改善の余地があります。"
        else:
            summary = f"ソフト制約達成率{soft_rate}%で、いくつかの課題があります。"

        # ボトルネック説明
        bottleneck_desc = ""
        if context.bottlenecks:
            b = context.bottlenecks[0]
            day_map = {
                "mon": "月曜", "tue": "火曜", "wed": "水曜",
                "thu": "木曜", "fri": "金曜", "sat": "土曜",
            }
            day_jp = day_map.get(b.get("day_of_week", ""), "")
            slot = b.get("slot_number", "")
            gap = abs(b.get("gap", 0))
            bottleneck_desc = f"\n\n主なボトルネック: {day_jp}{slot}限で講師供給が需要を{gap}コマ下回っています。"

        content = f"""{summary}

【主要ポイント】
- ソフト制約達成率: {soft_rate}%
- 1対2授業率: {one_to_two}%
- 講師数: {context.teacher_count}名、生徒数: {context.student_count}名
{bottleneck_desc}

【改善の方向性】
ボトルネックとなっている時間帯の講師シフトを見直すことで、ソフト制約達成率の向上が期待できます。
"""

        return LLMResponse(
            content=content,
            model="fallback",
            tokens_used=0,
            is_fallback=True,
        )

    def _generate_what_if_fallback(self, context: WhatIfContext) -> LLMResponse:
        """What-if分析のフォールバック"""
        content = f"""ご質問「{context.question}」について分析しました。

【実行可能性】
この変更は実行可能ですが、いくつかの影響を考慮する必要があります。

【予想される影響】
- ソフト制約達成率への影響: 変更内容により1-3%程度の変動が予想されます
- 現在のソフト制約達成率: {context.current_soft_constraint_rate}%

【メリット】
- より柔軟なスケジュール調整が可能になります

【注意点】
- 関連する制約条件との整合性を確認してください
- 影響を受ける講師・生徒への連絡が必要です

【推奨事項】
詳細な影響を確認するには、変更を適用した上で再生成を実行することをお勧めします。
"""

        return LLMResponse(
            content=content,
            model="fallback",
            tokens_used=0,
            is_fallback=True,
        )
