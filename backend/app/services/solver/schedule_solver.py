"""
時間割最適化ソルバー

OR-Tools CP-SATを使用した制約充足問題の求解
"""
import time
from decimal import Decimal
from typing import Callable
from uuid import UUID

from ortools.sat.python import cp_model

from .constraints import ConstraintBuilder
from .models import (
    PreferenceValue,
    SlotAssignment,
    SlotType,
    SolverConfig,
    SolverInput,
    SolverOutput,
    SolverStats,
    UnplacedStudent,
)


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    """解発見時のコールバック"""

    def __init__(
        self,
        assignment_vars: dict,
        progress_callback: Callable | None = None,
    ):
        super().__init__()
        self.vars = assignment_vars
        self.progress_callback = progress_callback
        self.solutions_found = 0
        self.best_objective = float('inf')
        self.start_time = time.time()

    def on_solution_callback(self):
        self.solutions_found += 1
        current_obj = self.ObjectiveValue()

        if current_obj < self.best_objective:
            self.best_objective = current_obj

        if self.progress_callback:
            elapsed_ms = int((time.time() - self.start_time) * 1000)
            self.progress_callback({
                "type": "progress",
                "solutions_found": self.solutions_found,
                "current_objective": current_obj,
                "elapsed_ms": elapsed_ms,
            })


class ScheduleSolver:
    """時間割ソルバー"""

    def __init__(self, config: SolverConfig | None = None):
        self.config = config or SolverConfig()

    def solve(
        self,
        solver_input: SolverInput,
        progress_callback: Callable | None = None,
    ) -> SolverOutput:
        """時間割を最適化"""
        start_time = time.time()

        # モデル作成
        model = cp_model.CpModel()

        # インデックスマッピング
        teacher_idx = {t.teacher_id: i for i, t in enumerate(solver_input.teachers)}
        student_idx = {s.student_id: i for i, s in enumerate(solver_input.students)}
        slot_idx = {
            (s.day_of_week, s.slot_number): i
            for i, s in enumerate(solver_input.time_slots)
        }

        # 決定変数の作成
        # vars[(slot_key, booth, t_idx, s_idx, position)] = BoolVar
        # position: 1 = student1, 2 = student2
        assignment_vars = self._create_variables(
            model, solver_input, teacher_idx, student_idx
        )

        if not assignment_vars:
            return SolverOutput(
                status="infeasible",
                stats=SolverStats(
                    solve_time_ms=int((time.time() - start_time) * 1000),
                    solutions_found=0,
                    optimality_gap=Decimal("1.0"),
                    strategy_used=self.config.strategy,
                    termination_reason="no_variables",
                ),
            )

        # 制約の追加
        constraint_builder = ConstraintBuilder(
            model, solver_input, assignment_vars, teacher_idx, student_idx, slot_idx
        )
        constraint_builder.add_hard_constraints()

        # 生徒のコマ数要求を満たす
        self._add_student_demand_constraints(
            model, solver_input, assignment_vars, student_idx
        )

        # ソフト制約とペナルティ
        penalties = []
        penalty_max_possible = 0
        if self.config.enable_soft_constraints:
            penalties = constraint_builder.add_soft_constraints()
            # 理論上の最大ペナルティを計算（各ペナルティ変数が1の場合）
            penalty_max_possible = sum(weight for _, weight in penalties)

        # 目的関数: ペナルティ最小化 + 配置最大化
        if penalties:
            total_penalty = sum(var * weight for var, weight in penalties)
            model.Minimize(total_penalty)

        # ソルバー実行
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.max_timeout_seconds
        solver.parameters.num_workers = 4  # 並列処理

        callback = SolutionCallback(assignment_vars, progress_callback)
        status = solver.Solve(model, callback)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 結果の解釈
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignments = self._extract_assignments(
                solver, assignment_vars, solver_input, teacher_idx, student_idx
            )
            unplaced = self._find_unplaced_students(
                assignments, solver_input
            )
            fulfillment, one_to_two_rate = self._calculate_rates(
                assignments, solver_input
            )
            # ソフト制約達成率を実際のペナルティから計算
            soft_rate = self._calculate_soft_constraint_rate(
                solver, penalties, penalty_max_possible
            )

            return SolverOutput(
                status="optimal" if status == cp_model.OPTIMAL else "feasible",
                assignments=assignments,
                unplaced_students=unplaced,
                fulfillment_rate=fulfillment,
                soft_constraint_rate=soft_rate,
                one_to_two_rate=one_to_two_rate,
                stats=SolverStats(
                    solve_time_ms=elapsed_ms,
                    solutions_found=callback.solutions_found,
                    optimality_gap=Decimal(str(
                        solver.BestObjectiveBound() / max(solver.ObjectiveValue(), 1)
                        if solver.ObjectiveValue() > 0 else 0
                    )),
                    strategy_used=self.config.strategy,
                    termination_reason="optimal" if status == cp_model.OPTIMAL else "feasible",
                ),
            )
        else:
            return SolverOutput(
                status="infeasible",
                stats=SolverStats(
                    solve_time_ms=elapsed_ms,
                    solutions_found=callback.solutions_found,
                    optimality_gap=Decimal("1.0"),
                    strategy_used=self.config.strategy,
                    termination_reason="infeasible" if status == cp_model.INFEASIBLE else "timeout",
                ),
            )

    def _create_variables(
        self,
        model: cp_model.CpModel,
        solver_input: SolverInput,
        teacher_idx: dict,
        student_idx: dict,
    ) -> dict:
        """決定変数を作成"""
        vars_dict = {}

        for slot in solver_input.time_slots:
            slot_key = (slot.day_of_week, slot.slot_number)

            for booth in range(1, slot.booth_count + 1):
                for t_idx, teacher in enumerate(solver_input.teachers):
                    # 講師がこの時間帯に勤務可能か確認
                    pref = teacher.preferences.get(slot_key)
                    if pref == PreferenceValue.UNAVAILABLE:
                        continue

                    for s_idx, student in enumerate(solver_input.students):
                        # NG関係チェック
                        if student.student_id in teacher.ng_student_ids:
                            continue
                        if teacher.teacher_id in student.ng_teacher_ids:
                            continue

                        # 科目適合チェック
                        student_subjects = [subj["subject_id"] for subj in student.subjects]
                        matching_subjects = set(teacher.subject_ids) & set(student_subjects)
                        if not matching_subjects:
                            continue

                        # student1として配置
                        var_name = f"assign_{slot_key}_{booth}_{t_idx}_{s_idx}_1"
                        vars_dict[(slot_key, booth, t_idx, s_idx, 1)] = model.NewBoolVar(var_name)

                        # student2として配置（1対2用）
                        var_name = f"assign_{slot_key}_{booth}_{t_idx}_{s_idx}_2"
                        vars_dict[(slot_key, booth, t_idx, s_idx, 2)] = model.NewBoolVar(var_name)

        return vars_dict

    def _add_student_demand_constraints(
        self,
        model: cp_model.CpModel,
        solver_input: SolverInput,
        assignment_vars: dict,
        student_idx: dict,
    ) -> None:
        """生徒のコマ数要求を満たす制約"""
        for student in solver_input.students:
            s_idx = student_idx[student.student_id]

            # 生徒の必要総コマ数
            total_required = sum(subj["slots_per_week"] for subj in student.subjects)

            # この生徒の全配置変数
            student_vars = []
            for key, var in assignment_vars.items():
                slot_key, booth, t_idx, student_i, pos = key
                if student_i == s_idx:
                    student_vars.append(var)

            if student_vars:
                # 必要コマ数以上を配置
                model.Add(sum(student_vars) >= total_required)

    def _extract_assignments(
        self,
        solver: cp_model.CpSolver,
        assignment_vars: dict,
        solver_input: SolverInput,
        teacher_idx: dict,
        student_idx: dict,
    ) -> list[SlotAssignment]:
        """ソルバーの結果からコマ割り当てを抽出"""
        # (slot_key, booth, t_idx) -> {s1: s_idx, s2: s_idx or None}
        slot_assignments = {}

        for key, var in assignment_vars.items():
            if solver.Value(var) == 1:
                slot_key, booth, t_idx, s_idx, position = key
                assign_key = (slot_key, booth, t_idx)

                if assign_key not in slot_assignments:
                    slot_assignments[assign_key] = {"s1": None, "s2": None}

                if position == 1:
                    slot_assignments[assign_key]["s1"] = s_idx
                else:
                    slot_assignments[assign_key]["s2"] = s_idx

        # SlotAssignmentに変換
        assignments = []
        idx_to_teacher = {i: t.teacher_id for i, t in enumerate(solver_input.teachers)}
        idx_to_student = {i: s for i, s in enumerate(solver_input.students)}

        for (slot_key, booth, t_idx), students in slot_assignments.items():
            s1_idx = students["s1"]
            s2_idx = students["s2"]

            if s1_idx is None:
                continue

            s1 = idx_to_student[s1_idx]
            s2 = idx_to_student.get(s2_idx) if s2_idx is not None else None

            # 科目を決定（生徒の受講科目から）
            subject_id = s1.subjects[0]["subject_id"] if s1.subjects else "UNKNOWN"

            assignments.append(SlotAssignment(
                day_of_week=slot_key[0],
                slot_number=slot_key[1],
                booth_number=booth,
                teacher_id=idx_to_teacher[t_idx],
                student1_id=s1.student_id,
                student2_id=s2.student_id if s2 else None,
                subject_id=subject_id,
                slot_type=SlotType.ONE_TO_TWO if s2 else SlotType.ONE_TO_ONE,
            ))

        return assignments

    def _find_unplaced_students(
        self,
        assignments: list[SlotAssignment],
        solver_input: SolverInput,
    ) -> list[UnplacedStudent]:
        """未配置の生徒を検出"""
        # 配置された生徒のコマ数をカウント
        placed_counts = {}
        for assignment in assignments:
            placed_counts[assignment.student1_id] = placed_counts.get(
                assignment.student1_id, 0
            ) + 1
            if assignment.student2_id:
                placed_counts[assignment.student2_id] = placed_counts.get(
                    assignment.student2_id, 0
                ) + 1

        unplaced = []
        for student in solver_input.students:
            required = sum(subj["slots_per_week"] for subj in student.subjects)
            placed = placed_counts.get(student.student_id, 0)

            if placed < required:
                for subj in student.subjects:
                    unplaced.append(UnplacedStudent(
                        student_id=student.student_id,
                        student_name=student.student_name,
                        subject_id=subj["subject_id"],
                        reason=f"必要{required}コマに対して{placed}コマのみ配置",
                    ))
                    break  # 1生徒1エントリ

        return unplaced

    def _calculate_rates(
        self,
        assignments: list[SlotAssignment],
        solver_input: SolverInput,
    ) -> tuple[Decimal, Decimal]:
        """充足率と1対2率を計算"""
        if not assignments:
            return Decimal("0"), Decimal("0")

        # 1対2率
        one_to_two_count = sum(
            1 for a in assignments if a.slot_type == SlotType.ONE_TO_TWO
        )
        total_slots = len(assignments)
        one_to_two_rate = Decimal(one_to_two_count) / Decimal(total_slots) * 100

        # 充足率（配置された生徒コマ数 / 必要生徒コマ数）
        total_required = sum(
            sum(subj["slots_per_week"] for subj in s.subjects)
            for s in solver_input.students
        )
        total_placed = sum(
            1 + (1 if a.student2_id else 0) for a in assignments
        )
        fulfillment_rate = (
            Decimal(total_placed) / Decimal(total_required) * 100
            if total_required > 0 else Decimal("0")
        )

        return (
            fulfillment_rate.quantize(Decimal("0.01")),
            one_to_two_rate.quantize(Decimal("0.01")),
        )

    def _calculate_soft_constraint_rate(
        self,
        solver: cp_model.CpSolver,
        penalties: list[tuple],
        max_possible: int,
    ) -> Decimal:
        """ソフト制約達成率を実際のペナルティから計算

        達成率 = (1 - 発生ペナルティ / 最大可能ペナルティ) * 100
        """
        if not penalties or max_possible == 0:
            return Decimal("100.00")

        # 実際に発生したペナルティを計算
        actual_penalty = sum(
            solver.Value(var) * weight for var, weight in penalties
        )

        # 達成率を計算
        rate = (1 - actual_penalty / max_possible) * 100
        rate = max(0, min(100, rate))  # 0-100の範囲にクランプ

        return Decimal(str(rate)).quantize(Decimal("0.01"))
