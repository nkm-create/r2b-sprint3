"""
制約定義モジュール

ハード制約（H001-H005）とソフト制約（S001-S007）を定義
"""
from ortools.sat.python import cp_model

from .models import SolverInput, TeacherData, StudentData, PolicyData


class ConstraintBuilder:
    """制約構築クラス"""

    def __init__(
        self,
        model: cp_model.CpModel,
        solver_input: SolverInput,
        assignment_vars: dict,
        teacher_idx: dict,
        student_idx: dict,
        slot_idx: dict,
    ):
        self.model = model
        self.input = solver_input
        self.vars = assignment_vars
        self.teacher_idx = teacher_idx
        self.student_idx = student_idx
        self.slot_idx = slot_idx

        # ポリシー設定を辞書化
        self.policies = {p.policy_type: p for p in solver_input.policies}

    def add_hard_constraints(self) -> None:
        """ハード制約を追加"""
        self._add_h001_student_one_slot_per_time()
        self._add_h002_teacher_one_slot_per_time()
        self._add_h003_teacher_availability()
        self._add_h004_subject_capability()
        self._add_h005_ng_relations()
        self._add_h006_no_same_student_double_assign()

    def add_soft_constraints(self) -> list:
        """ソフト制約を追加し、ペナルティ変数を返す"""
        penalties = []
        penalties.extend(self._add_s001_student_preference())
        penalties.extend(self._add_s002_teacher_consecutive())
        penalties.extend(self._add_s003_student_consecutive())
        penalties.extend(self._add_s004_teacher_slots_balance())
        penalties.extend(self._add_s005_one_to_two_optimization())
        if self._is_preferred_teacher_enabled():
            penalties.extend(self._add_s006_preferred_teacher())
        if self._is_gender_preference_enabled():
            penalties.extend(self._add_s007_gender_preference())
        return penalties

    def _is_preferred_teacher_enabled(self) -> bool:
        p004 = self.policies.get("P004")
        if not p004 or not p004.is_enabled:
            return False
        return bool(p004.parameters.get("enable_preferred_teacher", True))

    def _is_gender_preference_enabled(self) -> bool:
        p004 = self.policies.get("P004")
        if not p004 or not p004.is_enabled:
            return False
        return bool(p004.parameters.get("enable_gender_preference", True))

    # ====== ハード制約 ======

    def _add_h001_student_one_slot_per_time(self) -> None:
        """H001: 生徒は同一時間帯に1コマのみ"""
        for student in self.input.students:
            s_idx = self.student_idx[student.student_id]
            for slot in self.input.time_slots:
                slot_key = (slot.day_of_week, slot.slot_number)
                # この生徒がこの時間帯に配置されるブースは最大1つ
                booth_vars = []
                for booth in range(1, slot.booth_count + 1):
                    for t_idx in range(len(self.input.teachers)):
                        # student1として配置
                        var_key = (slot_key, booth, t_idx, s_idx, 1)
                        if var_key in self.vars:
                            booth_vars.append(self.vars[var_key])
                        # student2として配置
                        var_key = (slot_key, booth, t_idx, s_idx, 2)
                        if var_key in self.vars:
                            booth_vars.append(self.vars[var_key])

                if booth_vars:
                    self.model.Add(sum(booth_vars) <= 1)

    def _add_h002_teacher_one_slot_per_time(self) -> None:
        """H002: 講師は同一時間帯に1コマのみ"""
        for teacher in self.input.teachers:
            t_idx = self.teacher_idx[teacher.teacher_id]
            for slot in self.input.time_slots:
                slot_key = (slot.day_of_week, slot.slot_number)
                # この講師がこの時間帯に担当するブースは最大1つ
                booth_vars = []
                for booth in range(1, slot.booth_count + 1):
                    for s_idx in range(len(self.input.students)):
                        var_key = (slot_key, booth, t_idx, s_idx, 1)
                        if var_key in self.vars:
                            booth_vars.append(self.vars[var_key])

                if booth_vars:
                    self.model.Add(sum(booth_vars) <= 1)

    def _add_h003_teacher_availability(self) -> None:
        """H003: 講師はシフト希望「不可」の時間帯に配置不可"""
        from .models import PreferenceValue

        for teacher in self.input.teachers:
            t_idx = self.teacher_idx[teacher.teacher_id]
            for slot in self.input.time_slots:
                slot_key = (slot.day_of_week, slot.slot_number)
                pref = teacher.preferences.get(slot_key)

                if pref == PreferenceValue.UNAVAILABLE:
                    # この時間帯への配置を禁止
                    for booth in range(1, slot.booth_count + 1):
                        for s_idx in range(len(self.input.students)):
                            var_key = (slot_key, booth, t_idx, s_idx, 1)
                            if var_key in self.vars:
                                self.model.Add(self.vars[var_key] == 0)

    def _add_h004_subject_capability(self) -> None:
        """H004: 講師は担当可能科目のみ担当可能"""
        # 変数作成時にフィルタリング済み（担当不可の組み合わせは変数を作らない）
        pass

    def _add_h005_ng_relations(self) -> None:
        """H005: NG関係の講師と生徒は組み合わせ不可"""
        # 変数作成時にフィルタリング済み
        pass

    def _add_h006_no_same_student_double_assign(self) -> None:
        """H006: 同じ(時間帯, ブース, 講師)で同じ生徒がstudent1とstudent2の両方にならない"""
        for slot in self.input.time_slots:
            slot_key = (slot.day_of_week, slot.slot_number)
            for booth in range(1, slot.booth_count + 1):
                for t_idx in range(len(self.input.teachers)):
                    for s_idx in range(len(self.input.students)):
                        var1_key = (slot_key, booth, t_idx, s_idx, 1)
                        var2_key = (slot_key, booth, t_idx, s_idx, 2)
                        var1 = self.vars.get(var1_key)
                        var2 = self.vars.get(var2_key)
                        if var1 is not None and var2 is not None:
                            # 同じ生徒がstudent1かstudent2のどちらか一方のみ
                            self.model.Add(var1 + var2 <= 1)

    # ====== ソフト制約 ======

    def _add_s001_student_preference(self) -> list:
        """S001: 生徒の希望時間帯優先"""
        from .models import PreferenceValue

        penalties = []
        for student in self.input.students:
            s_idx = self.student_idx[student.student_id]
            for slot in self.input.time_slots:
                slot_key = (slot.day_of_week, slot.slot_number)
                pref = student.preferences.get(slot_key)

                if pref == PreferenceValue.UNAVAILABLE:
                    # 不可時間帯への配置にペナルティ
                    for booth in range(1, slot.booth_count + 1):
                        for t_idx in range(len(self.input.teachers)):
                            var_key = (slot_key, booth, t_idx, s_idx, 1)
                            if var_key in self.vars:
                                penalty = self.model.NewBoolVar(
                                    f"penalty_s001_{s_idx}_{slot_key}_{booth}"
                                )
                                self.model.Add(penalty == self.vars[var_key])
                                penalties.append((penalty, 10))  # 重みつきペナルティ

        return penalties

    def _add_s002_teacher_consecutive(self) -> list:
        """S002: 講師の連続コマ数上限"""
        penalties = []
        days = sorted(set(s.day_of_week for s in self.input.time_slots))

        for teacher in self.input.teachers:
            t_idx = self.teacher_idx[teacher.teacher_id]
            max_consecutive = teacher.max_consecutive_slots

            for day in days:
                day_slots = sorted(
                    [s for s in self.input.time_slots if s.day_of_week == day],
                    key=lambda x: x.slot_number
                )

                # 連続(max_consecutive + 1)コマを検出
                if len(day_slots) > max_consecutive:
                    for start in range(len(day_slots) - max_consecutive):
                        window_slots = day_slots[start:start + max_consecutive + 1]
                        window_vars = []

                        for slot in window_slots:
                            slot_key = (slot.day_of_week, slot.slot_number)
                            for booth in range(1, slot.booth_count + 1):
                                for s_idx in range(len(self.input.students)):
                                    var_key = (slot_key, booth, t_idx, s_idx, 1)
                                    if var_key in self.vars:
                                        window_vars.append(self.vars[var_key])

                        if window_vars:
                            # 連続超過にペナルティ
                            excess = self.model.NewIntVar(
                                0, len(window_vars),
                                f"excess_s002_{t_idx}_{day}_{start}"
                            )
                            self.model.Add(
                                excess >= sum(window_vars) - max_consecutive
                            )
                            penalties.append((excess, 5))

        return penalties

    def _add_s003_student_consecutive(self) -> list:
        """S003: 生徒の連続コマ数上限"""
        penalties = []
        days = sorted(set(s.day_of_week for s in self.input.time_slots))

        for student in self.input.students:
            s_idx = self.student_idx[student.student_id]
            max_consecutive = student.max_consecutive_slots

            for day in days:
                day_slots = sorted(
                    [s for s in self.input.time_slots if s.day_of_week == day],
                    key=lambda x: x.slot_number
                )

                if len(day_slots) > max_consecutive:
                    for start in range(len(day_slots) - max_consecutive):
                        window_slots = day_slots[start:start + max_consecutive + 1]
                        window_vars = []

                        for slot in window_slots:
                            slot_key = (slot.day_of_week, slot.slot_number)
                            for booth in range(1, slot.booth_count + 1):
                                for t_idx in range(len(self.input.teachers)):
                                    var_key = (slot_key, booth, t_idx, s_idx, 1)
                                    if var_key in self.vars:
                                        window_vars.append(self.vars[var_key])
                                    var_key = (slot_key, booth, t_idx, s_idx, 2)
                                    if var_key in self.vars:
                                        window_vars.append(self.vars[var_key])

                        if window_vars:
                            excess = self.model.NewIntVar(
                                0, len(window_vars),
                                f"excess_s003_{s_idx}_{day}_{start}"
                            )
                            self.model.Add(
                                excess >= sum(window_vars) - max_consecutive
                            )
                            penalties.append((excess, 5))

        return penalties

    def _add_s004_teacher_slots_balance(self) -> list:
        """S004: 講師の週コマ数バランス"""
        penalties = []

        for teacher in self.input.teachers:
            t_idx = self.teacher_idx[teacher.teacher_id]
            min_slots = teacher.min_slots_per_week
            max_slots = teacher.max_slots_per_week

            # この講師の全配置変数
            teacher_vars = []
            for slot in self.input.time_slots:
                slot_key = (slot.day_of_week, slot.slot_number)
                for booth in range(1, slot.booth_count + 1):
                    for s_idx in range(len(self.input.students)):
                        var_key = (slot_key, booth, t_idx, s_idx, 1)
                        if var_key in self.vars:
                            teacher_vars.append(self.vars[var_key])

            if teacher_vars:
                total = self.model.NewIntVar(
                    0, len(teacher_vars), f"total_slots_{t_idx}"
                )
                self.model.Add(total == sum(teacher_vars))

                # 最小・最大からの乖離にペナルティ
                under = self.model.NewIntVar(0, min_slots, f"under_{t_idx}")
                over = self.model.NewIntVar(0, max_slots, f"over_{t_idx}")
                self.model.Add(under >= min_slots - total)
                self.model.Add(over >= total - max_slots)

                penalties.append((under, 3))
                penalties.append((over, 3))

        return penalties

    def _add_s005_one_to_two_optimization(self) -> list:
        """S005: 1対2コマの最大化（目標充足率85%）"""
        penalties = []
        p005 = self.policies.get("P005")
        target_rate = 85
        if p005 and p005.is_enabled:
            target_rate = int(p005.parameters.get("target_rate", 85))
        # 目標値が高いほど 1対1 へのペナルティを強くする
        one_to_one_penalty_weight = max(1, min(10, target_rate // 10))

        # 1対1になるコマにペナルティ（1対2を促進）
        for slot in self.input.time_slots:
            slot_key = (slot.day_of_week, slot.slot_number)
            for booth in range(1, slot.booth_count + 1):
                for t_idx in range(len(self.input.teachers)):
                    # student1のみで、student2がいない場合にペナルティ
                    student1_vars = []
                    for s_idx in range(len(self.input.students)):
                        var_key = (slot_key, booth, t_idx, s_idx, 1)
                        if var_key in self.vars:
                            student1_vars.append(self.vars[var_key])

                    student2_vars = []
                    for s_idx in range(len(self.input.students)):
                        var_key = (slot_key, booth, t_idx, s_idx, 2)
                        if var_key in self.vars:
                            student2_vars.append(self.vars[var_key])

                    if student1_vars and student2_vars:
                        # 1対1（student2がいない）にペナルティ
                        has_s1 = self.model.NewBoolVar(f"has_s1_{slot_key}_{booth}_{t_idx}")
                        has_s2 = self.model.NewBoolVar(f"has_s2_{slot_key}_{booth}_{t_idx}")

                        self.model.Add(sum(student1_vars) >= 1).OnlyEnforceIf(has_s1)
                        self.model.Add(sum(student1_vars) == 0).OnlyEnforceIf(has_s1.Not())
                        self.model.Add(sum(student2_vars) >= 1).OnlyEnforceIf(has_s2)
                        self.model.Add(sum(student2_vars) == 0).OnlyEnforceIf(has_s2.Not())

                        # s1はいるがs2がいない = 1対1
                        is_one_to_one = self.model.NewBoolVar(
                            f"one_to_one_{slot_key}_{booth}_{t_idx}"
                        )
                        self.model.AddBoolAnd([has_s1, has_s2.Not()]).OnlyEnforceIf(
                            is_one_to_one
                        )
                        self.model.AddBoolOr([has_s1.Not(), has_s2]).OnlyEnforceIf(
                            is_one_to_one.Not()
                        )

                        penalties.append((is_one_to_one, one_to_one_penalty_weight))

        return penalties

    def _add_s006_preferred_teacher(self) -> list:
        """S006: 生徒の担当講師希望"""
        penalties = []

        for student in self.input.students:
            if not student.preferred_teacher_id:
                continue

            s_idx = self.student_idx[student.student_id]
            pref_t_idx = self.teacher_idx.get(student.preferred_teacher_id)

            if pref_t_idx is None:
                continue

            # 希望講師以外への配置にペナルティ
            for slot in self.input.time_slots:
                slot_key = (slot.day_of_week, slot.slot_number)
                for booth in range(1, slot.booth_count + 1):
                    for t_idx in range(len(self.input.teachers)):
                        if t_idx == pref_t_idx:
                            continue  # 希望講師はOK

                        var_key = (slot_key, booth, t_idx, s_idx, 1)
                        if var_key in self.vars:
                            penalty = self.model.NewBoolVar(
                                f"penalty_s006_{s_idx}_{slot_key}_{t_idx}"
                            )
                            self.model.Add(penalty == self.vars[var_key])
                            penalties.append((penalty, 1))

        return penalties

    def _add_s007_gender_preference(self) -> list:
        """S007: 生徒の講師性別希望"""
        penalties = []

        for student in self.input.students:
            if not student.preferred_teacher_gender or student.preferred_teacher_gender == "none":
                continue

            s_idx = self.student_idx[student.student_id]

            # 希望性別以外の講師への配置にペナルティ
            for t_idx, teacher in enumerate(self.input.teachers):
                # 講師にgender属性がある前提
                teacher_gender = getattr(teacher, 'gender', None)
                if teacher_gender == student.preferred_teacher_gender:
                    continue  # 希望性別

                for slot in self.input.time_slots:
                    slot_key = (slot.day_of_week, slot.slot_number)
                    for booth in range(1, slot.booth_count + 1):
                        var_key = (slot_key, booth, t_idx, s_idx, 1)
                        if var_key in self.vars:
                            penalty = self.model.NewBoolVar(
                                f"penalty_s007_{s_idx}_{slot_key}_{t_idx}"
                            )
                            self.model.Add(penalty == self.vars[var_key])
                            penalties.append((penalty, 1))

        return penalties
