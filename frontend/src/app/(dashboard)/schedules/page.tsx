'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Play, Check, AlertTriangle, Download, Calendar, Info, Sparkles, Move, Bot, Upload } from 'lucide-react';
import { useClassrooms } from '@/hooks/use-classroom';
import { useTeachers } from '@/hooks/use-teacher';
import {
  useTerms,
  usePolicies,
  useUpdatePolicies,
  useConstraints,
  useCreateConstraints,
  useMasterStatus,
} from '@/hooks/use-condition';
import { useImportPreferences } from '@/hooks/use-preference';
import {
  useScheduleJourneyStatus,
  useScheduleList,
  useAnalyzeSchedule,
  useGenerateSchedule,
  useCalendarView,
  useExplanation,
  useConfirmSchedule,
  useExportSchedule,
  useMoveSlot,
  useWhatIfAnalysis,
} from '@/hooks/use-schedule';
import {
  createGenerationProgressSocket,
  getMovableTargets,
  type CellInfo,
  type GenerationProgressEvent,
  type MovableTarget,
  type SlotInfo,
} from '@/lib/api/schedule';
import { getErrorMessage } from '@/lib/api/client';
import type { ConstraintValue } from '@/lib/api/condition';

const DAYS = [
  { key: 'mon', label: '月' },
  { key: 'tue', label: '火' },
  { key: 'wed', label: '水' },
  { key: 'thu', label: '木' },
  { key: 'fri', label: '金' },
  { key: 'sat', label: '土' },
];

// 曜日選択用（T002）
const DAY_OPTIONS = [
  { key: 'mon', label: '月曜日' },
  { key: 'tue', label: '火曜日' },
  { key: 'wed', label: '水曜日' },
  { key: 'thu', label: '木曜日' },
  { key: 'fri', label: '金曜日' },
  { key: 'sat', label: '土曜日' },
];

// 科目選択用（T001）
const SUBJECT_OPTIONS = [
  { key: 'JHS_ENG', label: '中学英語' },
  { key: 'JHS_MATH_PUB', label: '中学数学（公立）' },
  { key: 'JHS_MATH_PRI', label: '中学数学（私立）' },
  { key: 'JHS_JPN', label: '中学国語' },
  { key: 'JHS_SCI', label: '中学理科' },
  { key: 'JHS_SOC', label: '中学社会' },
  { key: 'HS_ENG', label: '高校英語' },
  { key: 'HS_MATH_1A', label: '高校数学ⅠA' },
  { key: 'HS_MATH_2B', label: '高校数学ⅡB' },
  { key: 'HS_MATH_3', label: '高校数学Ⅲ' },
  { key: 'HS_JPN_MOD', label: '高校現代文' },
  { key: 'HS_JPN_CLS', label: '高校古文・漢文' },
  { key: 'HS_PHY', label: '高校物理' },
  { key: 'HS_CHM', label: '高校化学' },
  { key: 'HS_BIO', label: '高校生物' },
  { key: 'HS_JHIS', label: '高校日本史' },
  { key: 'HS_WHIS', label: '高校世界史' },
  { key: 'ES_ENG', label: '小学英語' },
  { key: 'ES_MATH', label: '小学算数' },
  { key: 'ES_JPN', label: '小学国語' },
];

const SLOT_TIMES = [
  { slot: 1, time: '16:00-17:20' },
  { slot: 2, time: '17:30-18:50' },
  { slot: 3, time: '19:00-20:20' },
  { slot: 4, time: '20:30-21:50' },
];

const HARD_CONSTRAINTS = [
  { id: 'H001', name: '科目適合', description: '講師の指導可能科目に生徒の受講科目が含まれること' },
  { id: 'H002', name: '学年適合', description: '講師の指導可能学年に生徒の学年が含まれること' },
  { id: 'H003', name: '講師出勤可能時間', description: '講師シフト希望で可の時間帯のみ配置' },
  { id: 'H004', name: '生徒通塾可能時間', description: '生徒受講希望で可/可能の時間帯のみ配置' },
  { id: 'H005', name: 'NG組合せ禁止', description: '生徒NG講師・講師NG生徒の組合せを禁止（常時適用）' },
];

export default function SchedulesPage() {
  type TeacherConstraintDraft = {
    draftId: string;
    teacherId: string;
    selectedValues: string[];
  };

  const [selectedClassroomId, setSelectedClassroomId] = useState<string>('');
  const [selectedTermId, setSelectedTermId] = useState<string>('');
  const [selectedScheduleId, setSelectedScheduleId] = useState<string>('');
  const [maxTimeoutSeconds, setMaxTimeoutSeconds] = useState<number>(60);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationStatusText, setGenerationStatusText] = useState('');
  const [journeyMessage, setJourneyMessage] = useState('');
  const [workflowTab, setWorkflowTab] = useState('term');
  const [activeTab, setActiveTab] = useState('calendar');
  const [teacherFileName, setTeacherFileName] = useState('');
  const [studentFileName, setStudentFileName] = useState('');
  const [constraintDrafts, setConstraintDrafts] = useState({
    boothCapacity: 8,
  });
  const [subjectLimitDrafts, setSubjectLimitDrafts] = useState<TeacherConstraintDraft[]>([
    { draftId: 'subject-1', teacherId: '', selectedValues: [] },
  ]);
  const [dayLimitDrafts, setDayLimitDrafts] = useState<TeacherConstraintDraft[]>([
    { draftId: 'day-1', teacherId: '', selectedValues: [] },
  ]);
  const [constraintSaveMessage, setConstraintSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [draggingSlot, setDraggingSlot] = useState<SlotInfo | null>(null);
  const [movableTargets, setMovableTargets] = useState<Record<string, MovableTarget>>({});
  const [selectedIssue, setSelectedIssue] = useState<{ slot: SlotInfo; cell: CellInfo } | null>(null);
  const [guideTargets, setGuideTargets] = useState<MovableTarget[]>([]);
  const [whatIfQuestion, setWhatIfQuestion] = useState('');
  const [whatIfAnswer, setWhatIfAnswer] = useState('');
  const progressSocketRef = useRef<WebSocket | null>(null);

  // データ取得
  const { data: classrooms } = useClassrooms();
  const { data: terms } = useTerms(selectedClassroomId || undefined);
  const { data: teachersData, refetch: refetchTeachers } = useTeachers(
    selectedClassroomId || undefined
  );
  const { data: journeyStatus, refetch: refetchJourneyStatus } = useScheduleJourneyStatus(
    selectedClassroomId || undefined,
    selectedTermId || undefined
  );
  const { data: masterStatus } = useMasterStatus(
    selectedClassroomId || undefined,
    selectedTermId || undefined
  );
  const { data: constraintsData, refetch: refetchConstraints } = useConstraints(
    selectedClassroomId || undefined,
    selectedTermId || undefined
  );
  const { data: policiesData } = usePolicies(
    selectedClassroomId || undefined,
    selectedTermId || undefined
  );
  const { data: scheduleList, refetch: refetchSchedules } = useScheduleList(
    selectedClassroomId || undefined,
    selectedTermId || undefined
  );
  const { data: calendarView, refetch: refetchCalendar } = useCalendarView(
    selectedScheduleId || undefined
  );
  const { data: explanation } = useExplanation(selectedScheduleId || undefined);

  // ミューテーション
  const analyzeMutation = useAnalyzeSchedule(selectedClassroomId, selectedTermId);
  const generateMutation = useGenerateSchedule(selectedClassroomId, selectedTermId);
  const importPreferencesMutation = useImportPreferences(
    selectedClassroomId || '',
    selectedTermId || ''
  );
  const createConstraintsMutation = useCreateConstraints(
    selectedClassroomId || '',
    selectedTermId || ''
  );
  const updatePoliciesMutation = useUpdatePolicies(
    selectedClassroomId || '',
    selectedTermId || ''
  );
  const confirmMutation = useConfirmSchedule(selectedScheduleId);
  const exportMutation = useExportSchedule(selectedScheduleId);
  const moveMutation = useMoveSlot(selectedScheduleId);
  const whatIfMutation = useWhatIfAnalysis(selectedScheduleId);

  const effectivePolicies = useMemo(() => {
    if (!policiesData?.data) return [];
    return policiesData.data;
  }, [policiesData]);

  useEffect(() => {
    return () => {
      progressSocketRef.current?.close();
    };
  }, []);

  useEffect(() => {
    setSelectedTermId('');
    setSelectedScheduleId('');
    setTeacherFileName('');
    setStudentFileName('');
    setConstraintDrafts({
      boothCapacity: 8,
    });
    setSubjectLimitDrafts([{ draftId: 'subject-1', teacherId: '', selectedValues: [] }]);
    setDayLimitDrafts([{ draftId: 'day-1', teacherId: '', selectedValues: [] }]);
    setConstraintSaveMessage(null);
  }, [selectedClassroomId]);

  useEffect(() => {
    setSelectedScheduleId('');
    setTeacherFileName('');
    setStudentFileName('');
    setJourneyMessage('');
    setConstraintDrafts({
      boothCapacity: 8,
    });
    setSubjectLimitDrafts([{ draftId: 'subject-1', teacherId: '', selectedValues: [] }]);
    setDayLimitDrafts([{ draftId: 'day-1', teacherId: '', selectedValues: [] }]);
    setConstraintSaveMessage(null);
  }, [selectedTermId]);

  // 時間割生成
  const handleGenerate = async () => {
    if (!selectedClassroomId || !selectedTermId) return;
    if (!journeyStatus?.is_ready_to_generate) {
      setJourneyMessage(
        journeyStatus?.missing_requirements.join(' / ') || '生成前の準備が不足しています'
      );
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);

    try {
      const progressChannel = `${selectedClassroomId}-${selectedTermId}`;
      progressSocketRef.current?.close();
      const socket = createGenerationProgressSocket(progressChannel);
      progressSocketRef.current = socket;
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as GenerationProgressEvent;
        if (payload.type === 'progress') {
          setGenerationStatusText(
            `探索中... 解${payload.solutions_found ?? 0}個 / 充足率${Number(
              payload.current_rate ?? 0
            ).toFixed(1)}%`
          );
          setGenerationProgress(Math.min(95, Math.max(10, Number(payload.current_rate ?? 0))));
        } else if (payload.type === 'complete') {
          setGenerationStatusText(
            `完了: ${payload.status ?? 'unknown'} / 最終充足率 ${Number(
              payload.final_rate ?? 0
            ).toFixed(1)}%`
          );
          setGenerationProgress(100);
        } else if (payload.type === 'error') {
          setGenerationStatusText(payload.error ?? '生成エラー');
        }
      };

      // 問題分析
      await analyzeMutation.mutateAsync();
      setGenerationProgress(20);
      setGenerationStatusText('問題分析が完了しました');

      // 生成実行
      const result = await generateMutation.mutateAsync({
        options: {
          max_timeout_seconds: maxTimeoutSeconds,
          progress_channel: progressChannel,
        },
      });
      setGenerationProgress(100);
      setGenerationStatusText('最適化が完了しました');

      // 生成された時間割を選択
      setSelectedScheduleId(result.schedule_id);
      await refetchSchedules();
      await refetchJourneyStatus();
    } catch (error) {
      setGenerationStatusText(getErrorMessage(error));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleImportPreference = async (
    type: 'teacher' | 'student',
    file: File | null
  ) => {
    if (!file || !selectedClassroomId || !selectedTermId) return;
    try {
      const result = await importPreferencesMutation.mutateAsync({ type, file });
      if (type === 'teacher') {
        setTeacherFileName(file.name);
      } else {
        setStudentFileName(file.name);
      }
      setJourneyMessage(result.message);
      await refetchJourneyStatus();
    } catch (error) {
      setJourneyMessage(getErrorMessage(error));
    }
  };

  const applyConstraint = async (key: string) => {
    if (!selectedClassroomId || !selectedTermId) return;
    setConstraintSaveMessage(null);
    let payload: { target_type: 'teacher' | 'student' | 'classroom'; target_id: string; constraints: ConstraintValue[] } | null = null;
    if (key === 'booth_capacity') {
      payload = {
        target_type: 'classroom',
        target_id: 'classroom',
        constraints: [
          { constraint_type: 'booth_capacity', value: { value: Number(constraintDrafts.boothCapacity || 0) } },
        ],
      };
    }

    if (!payload) return;

    try {
      await createConstraintsMutation.mutateAsync(payload);
      setConstraintSaveMessage({
        type: 'success',
        text: `✓ S007（ブース上限）を ${constraintDrafts.boothCapacity} に設定しました`,
      });
      await refetchConstraints();
      await refetchJourneyStatus();
    } catch (error) {
      setConstraintSaveMessage({ type: 'error', text: getErrorMessage(error) });
    }
  };

  const updateTeacherDraft = (
    type: 'subject' | 'day',
    draftId: string,
    patch: Partial<{ teacherId: string; selectedValues: string[] }>
  ) => {
    const updater = (prev: TeacherConstraintDraft[]) =>
      prev.map((item) => (item.draftId === draftId ? { ...item, ...patch } : item));
    if (type === 'subject') {
      setSubjectLimitDrafts(updater);
      return;
    }
    setDayLimitDrafts(updater);
  };

  const toggleTeacherDraftValue = (
    type: 'subject' | 'day',
    draftId: string,
    valueKey: string
  ) => {
    const drafts = type === 'subject' ? subjectLimitDrafts : dayLimitDrafts;
    const draft = drafts.find((d) => d.draftId === draftId);
    if (!draft) return;

    const newValues = draft.selectedValues.includes(valueKey)
      ? draft.selectedValues.filter((v) => v !== valueKey)
      : [...draft.selectedValues, valueKey];

    updateTeacherDraft(type, draftId, { selectedValues: newValues });
  };

  const addTeacherDraft = (type: 'subject' | 'day') => {
    const nextId = `${type}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
    const nextItem: TeacherConstraintDraft = { draftId: nextId, teacherId: '', selectedValues: [] };
    if (type === 'subject') {
      setSubjectLimitDrafts((prev) => [...prev, nextItem]);
      return;
    }
    setDayLimitDrafts((prev) => [...prev, nextItem]);
  };

  const removeTeacherDraft = (type: 'subject' | 'day', draftId: string) => {
    if (type === 'subject') {
      setSubjectLimitDrafts((prev) => (prev.length > 1 ? prev.filter((item) => item.draftId !== draftId) : prev));
      return;
    }
    setDayLimitDrafts((prev) => (prev.length > 1 ? prev.filter((item) => item.draftId !== draftId) : prev));
  };

  const applyTeacherDrafts = async (type: 'subject' | 'day') => {
    if (!selectedClassroomId || !selectedTermId) return;
    setConstraintSaveMessage(null);
    const drafts = type === 'subject' ? subjectLimitDrafts : dayLimitDrafts;
    if (teacherMasterItems.length === 0) {
      setConstraintSaveMessage({ type: 'error', text: '講師一覧を取得できていません。講師マスタを確認してください' });
      await refetchTeachers();
      return;
    }
    const invalid = drafts.find((item) => !item.teacherId || item.selectedValues.length === 0);
    if (invalid) {
      setConstraintSaveMessage({ type: 'error', text: '講師と選択肢をすべて設定してください' });
      return;
    }

    try {
      setConstraintSaveMessage({ type: 'success', text: '保存中です...' });
      for (const item of drafts) {
        await createConstraintsMutation.mutateAsync({
          target_type: 'teacher',
          target_id: item.teacherId,
          constraints: [
            type === 'subject'
              ? { constraint_type: 'subject_limit', value: { subject_ids: item.selectedValues } }
              : { constraint_type: 'day_limit', value: { days: item.selectedValues } },
          ],
        });
      }
      const teacherNames = drafts.map((d) => {
        const t = teacherMasterItems.find((t) => t.teacher_id === d.teacherId);
        return t?.name ?? d.teacherId;
      }).join('、');
      setConstraintSaveMessage({
        type: 'success',
        text: type === 'subject'
          ? `✓ T001（担当科目限定）を保存しました: ${teacherNames}`
          : `✓ T002（担当曜日限定）を保存しました: ${teacherNames}`,
      });
      await refetchConstraints();
      await refetchJourneyStatus();
      await refetchTeachers();
    } catch (error) {
      setConstraintSaveMessage({ type: 'error', text: getErrorMessage(error) });
    }
  };

  const handlePreferencePolicyToggle = async (
    key: 'enable_preferred_teacher' | 'enable_gender_preference',
    checked: boolean
  ) => {
    if (!selectedClassroomId || !selectedTermId) return;
    const base = effectivePolicies.find((policy) => policy.policy_type === 'P004');
    const currentParameters = base?.parameters ?? {
      enable_preferred_teacher: true,
      enable_gender_preference: true,
    };
    try {
      await updatePoliciesMutation.mutateAsync({
        policies: [
          {
            policy_type: 'P004',
            is_enabled: true,
            parameters: {
              ...currentParameters,
              [key]: checked,
            },
          },
        ],
      });
      setJourneyMessage('希望データ反映設定を更新しました');
      await refetchJourneyStatus();
    } catch (error) {
      setJourneyMessage(getErrorMessage(error));
    }
  };


  // 確定
  const handleConfirm = async () => {
    if (!selectedScheduleId) return;

    try {
      await confirmMutation.mutateAsync({ force: false });
      await refetchSchedules();
    } catch (error) {
      const message = getErrorMessage(error);
      if (window.confirm(`${message}\n強制確定しますか？`)) {
        await confirmMutation.mutateAsync({ force: true });
        await refetchSchedules();
      }
    }
  };

  // エクスポート
  const handleExport = async (format: 'pdf' | 'csv') => {
    if (!selectedScheduleId) return;

    try {
      const result = await exportMutation.mutateAsync({
        format,
        type: 'all',
      });
      // 相対URLはAPIサーバーの絶対URLに変換
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const downloadUrl = result.download_url.startsWith('http')
        ? result.download_url
        : `${apiUrl}${result.download_url}`;
      window.open(downloadUrl, '_blank');
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  // セルをグループ化
  const cellsByDaySlot = calendarView?.cells.reduce(
    (acc, cell) => {
      const key = `${cell.day_of_week}-${cell.slot_number}`;
      acc[key] = cell;
      return acc;
    },
    {} as Record<string, typeof calendarView.cells[0]>
  );

  const formatRate = (value: number | string | undefined) =>
    Number(value ?? 0).toFixed(1);

  const journeySteps = [
    {
      id: 'term',
      title: '1. ターム選択',
      ready: Boolean(selectedClassroomId && selectedTermId),
      message: selectedTermId ? 'ターム選択済み' : '教室とタームを選択してください',
    },
    {
      id: 'preferences',
      title: '2. 希望データ',
      ready: Boolean(journeyStatus?.steps.preferences?.is_ready),
      message: journeyStatus?.steps.preferences?.message ?? '希望データをアップロードしてください',
    },
    {
      id: 'conditions',
      title: '3. 条件設定',
      ready: Boolean(journeyStatus?.steps.conditions?.is_ready),
      message: journeyStatus?.steps.conditions?.message ?? 'ポリシーを設定してください',
    },
    {
      id: 'generate',
      title: '4. 時間割作成',
      ready: Boolean(journeyStatus?.is_ready_to_generate),
      message: journeyStatus?.steps.generate?.message ?? '準備完了後に生成できます',
    },
  ];

  const p004Policy = effectivePolicies.find((policy) => policy.policy_type === 'P004');
  const teacherMasterItems = useMemo(() => {
    const fromMaster = masterStatus?.teachers?.items ?? [];
    if (fromMaster.length > 0) {
      return fromMaster;
    }
    const fromTeachersApi = teachersData?.data ?? [];
    return fromTeachersApi.map((teacher) => ({
      teacher_id: teacher.teacher_id,
      name: teacher.name,
      min_slots: teacher.min_slots_per_week,
      max_slots: teacher.max_slots_per_week,
      max_consecutive: teacher.max_consecutive_slots,
      has_term_adjustment: false,
    }));
  }, [masterStatus, teachersData]);

  const handleDragStart = async (slot: SlotInfo) => {
    if (!selectedScheduleId || calendarView?.status !== 'draft') return;
    setDraggingSlot(slot);
    try {
      const targets = await getMovableTargets(selectedScheduleId, slot.slot_id);
      const map: Record<string, MovableTarget> = {};
      targets.targets.forEach((t) => {
        map[`${t.day_of_week}-${t.slot_number}`] = t;
      });
      setMovableTargets(map);
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  const handleDrop = async (day: string, slotNumber: number) => {
    if (!draggingSlot || !selectedScheduleId || calendarView?.status !== 'draft') return;
    const target = movableTargets[`${day}-${slotNumber}`];
    if (!target) return;
    const force =
      target.feasibility === 'soft_violation'
        ? window.confirm(
            `この移動はソフト制約違反を含みます:\n${target.violations.join(
              '\n'
            )}\n移動しますか？`
          )
        : false;
    if (target.feasibility === 'hard_violation') {
      alert(`ハード制約違反のため移動できません:\n${target.violations.join('\n')}`);
      return;
    }

    try {
      await moveMutation.mutateAsync({
        slotId: draggingSlot.slot_id,
        data: {
          target_day_of_week: day,
          target_slot_number: slotNumber,
          force,
        },
      });
      await refetchCalendar();
      setDraggingSlot(null);
      setMovableTargets({});
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  const loadGuideTargets = async (slot: SlotInfo) => {
    if (!selectedScheduleId) return;
    try {
      const targets = await getMovableTargets(selectedScheduleId, slot.slot_id);
      setGuideTargets(targets.targets.filter((t) => t.feasibility !== 'hard_violation').slice(0, 8));
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  const runWhatIf = async () => {
    if (!whatIfQuestion || !selectedScheduleId) return;
    try {
      const result = await whatIfMutation.mutateAsync({ question: whatIfQuestion });
      setWhatIfAnswer(result.explanation);
    } catch (error) {
      setWhatIfAnswer(getErrorMessage(error));
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">時間割作成</h1>
          <p className="text-muted-foreground">
            AIソルバーによる最適な時間割を自動生成
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">時間割作成ワークフロー</CardTitle>
          <CardDescription>
            フェーズタブを移動しながら設定を完了してください
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-4">
            {journeySteps.map((step) => (
              <div key={step.id} className={`rounded border p-3 ${step.ready ? 'border-green-500' : 'border-muted'}`}>
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{step.title}</p>
                  <Badge variant={step.ready ? 'default' : 'secondary'}>
                    {step.ready ? '完了' : '未完了'}
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">{step.message}</p>
              </div>
            ))}
          </div>

          <Tabs value={workflowTab} onValueChange={setWorkflowTab}>
            <TabsList>
              <TabsTrigger value="term">1.ターム選択</TabsTrigger>
              <TabsTrigger value="preferences">2.希望データ</TabsTrigger>
              <TabsTrigger value="conditions">3.条件設定</TabsTrigger>
              <TabsTrigger value="generate">4.時間割作成</TabsTrigger>
            </TabsList>

            <TabsContent value="term" className="mt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">教室</label>
                  <Select value={selectedClassroomId} onValueChange={setSelectedClassroomId}>
                    <SelectTrigger>
                      <SelectValue placeholder="教室を選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {classrooms?.data.map((c) => (
                        <SelectItem key={c.classroom_id} value={c.classroom_id}>
                          {c.classroom_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">ターム</label>
                  <Select
                    value={selectedTermId}
                    onValueChange={setSelectedTermId}
                    disabled={!selectedClassroomId}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="タームを選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {terms?.data.map((t) => (
                        <SelectItem key={t.term_id} value={t.term_id}>
                          {t.term_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">時間割バージョン</label>
                  <Select
                    value={selectedScheduleId}
                    onValueChange={setSelectedScheduleId}
                    disabled={!selectedTermId || !scheduleList?.data.length}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="バージョンを選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {scheduleList?.data.map((s) => (
                        <SelectItem key={s.schedule_id} value={s.schedule_id}>
                          v{s.version} ({s.status}) - 達成率: {formatRate(s.soft_constraint_rate)}%
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="preferences" className="mt-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded border p-4 space-y-3">
                  <Label>講師希望データ</Label>
                  <Input
                    type="file"
                    accept=".xlsx"
                    disabled={!selectedClassroomId || !selectedTermId || importPreferencesMutation.isPending}
                    onChange={(e) =>
                      void handleImportPreference('teacher', e.target.files?.[0] ?? null)
                    }
                  />
                  <p className="text-xs text-muted-foreground">{teacherFileName || '未アップロード'}</p>
                </div>
                <div className="rounded border p-4 space-y-3">
                  <Label>生徒希望データ</Label>
                  <Input
                    type="file"
                    accept=".xlsx"
                    disabled={!selectedClassroomId || !selectedTermId || importPreferencesMutation.isPending}
                    onChange={(e) =>
                      void handleImportPreference('student', e.target.files?.[0] ?? null)
                    }
                  />
                  <p className="text-xs text-muted-foreground">{studentFileName || '未アップロード'}</p>
                </div>
              </div>
              <div className="mt-4 flex gap-2 text-xs text-muted-foreground">
                <Upload className="h-4 w-4" />
                <span>
                  登録件数: 講師 {journeyStatus?.counts.teacher_preferences ?? 0} / 生徒 {journeyStatus?.counts.student_preferences ?? 0}
                </span>
              </div>
            </TabsContent>

            <TabsContent value="conditions" className="mt-4 space-y-4">
              <div className="rounded border p-4 space-y-3">
                <p className="text-sm font-semibold">必須制約（ハード制約）</p>
                <p className="text-xs text-muted-foreground">
                  ここは自動適用され、変更できません
                </p>
                <div className="space-y-2">
                  {HARD_CONSTRAINTS.map((item) => (
                    <div key={item.id} className="flex items-start justify-between rounded border p-2">
                      <div>
                        <p className="text-sm font-medium">{item.id} {item.name}</p>
                        <p className="text-xs text-muted-foreground">{item.description}</p>
                      </div>
                      <Badge variant="secondary">固定ON</Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded border p-4 space-y-3">
                <p className="text-sm font-semibold">調整可能制約（ターム限定）</p>
                <p className="text-xs text-muted-foreground">
                  マスタの基本値に対して、このタームだけ上書きできます
                </p>
                <p className="text-xs text-muted-foreground">
                  ※個人ごとの設定は T001/T002 のみです。講師選択は各カード内で行います。
                </p>

                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded border p-3 gap-3">
                    <p className="text-sm font-medium min-w-[260px]">S007 同時授業数（ブース上限）</p>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={constraintDrafts.boothCapacity}
                        onChange={(e) =>
                          setConstraintDrafts((prev) => ({ ...prev, boothCapacity: Number(e.target.value || 0) }))
                        }
                        className="w-24"
                      />
                      <Button type="button" size="sm" onClick={() => void applyConstraint('booth_capacity')}>
                        適用
                      </Button>
                    </div>
                  </div>

                  <div className="rounded border p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">T001 講師の担当科目限定（ターム限定）</p>
                        <p className="text-xs text-muted-foreground">このタームで担当可能な科目を制限します</p>
                      </div>
                      <Button type="button" variant="outline" size="sm" onClick={() => addTeacherDraft('subject')}>
                        講師を追加
                      </Button>
                    </div>
                    {teacherMasterItems.length === 0 && (
                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          講師候補が読み込めていません。ターム選択後に再読み込みしてください。
                        </AlertDescription>
                      </Alert>
                    )}
                    {subjectLimitDrafts.map((draft) => (
                      <div key={draft.draftId} className="rounded border p-3 space-y-2 bg-muted/30">
                        <div className="flex items-center gap-2">
                          <Select
                            value={draft.teacherId}
                            onValueChange={(value) => updateTeacherDraft('subject', draft.draftId, { teacherId: value })}
                          >
                            <SelectTrigger className="w-64">
                              <SelectValue placeholder="講師を選択してください" />
                            </SelectTrigger>
                            <SelectContent>
                              {teacherMasterItems.map((teacher) => (
                                <SelectItem key={teacher.teacher_id} value={teacher.teacher_id}>
                                  {teacher.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeTeacherDraft('subject', draft.draftId)}
                          >
                            削除
                          </Button>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                          {SUBJECT_OPTIONS.map((subject) => (
                            <label
                              key={subject.key}
                              className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 p-1 rounded"
                            >
                              <Checkbox
                                checked={draft.selectedValues.includes(subject.key)}
                                onCheckedChange={() => toggleTeacherDraftValue('subject', draft.draftId, subject.key)}
                              />
                              {subject.label}
                            </label>
                          ))}
                        </div>
                        {draft.selectedValues.length > 0 && (
                          <p className="text-xs text-muted-foreground">
                            選択中: {draft.selectedValues.map((k) => SUBJECT_OPTIONS.find((s) => s.key === k)?.label ?? k).join('、')}
                          </p>
                        )}
                      </div>
                    ))}
                    <Button type="button" size="sm" onClick={() => void applyTeacherDrafts('subject')}>
                      T001を保存
                    </Button>
                  </div>

                  <div className="rounded border p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">T002 講師の担当曜日限定（ターム限定）</p>
                        <p className="text-xs text-muted-foreground">このタームで出勤可能な曜日を制限します</p>
                      </div>
                      <Button type="button" variant="outline" size="sm" onClick={() => addTeacherDraft('day')}>
                        講師を追加
                      </Button>
                    </div>
                    {dayLimitDrafts.map((draft) => (
                      <div key={draft.draftId} className="rounded border p-3 space-y-2 bg-muted/30">
                        <div className="flex items-center gap-2">
                          <Select
                            value={draft.teacherId}
                            onValueChange={(value) => updateTeacherDraft('day', draft.draftId, { teacherId: value })}
                          >
                            <SelectTrigger className="w-64">
                              <SelectValue placeholder="講師を選択してください" />
                            </SelectTrigger>
                            <SelectContent>
                              {teacherMasterItems.map((teacher) => (
                                <SelectItem key={teacher.teacher_id} value={teacher.teacher_id}>
                                  {teacher.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeTeacherDraft('day', draft.draftId)}
                          >
                            削除
                          </Button>
                        </div>
                        <div className="flex flex-wrap gap-3">
                          {DAY_OPTIONS.map((day) => (
                            <label
                              key={day.key}
                              className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 p-1 rounded"
                            >
                              <Checkbox
                                checked={draft.selectedValues.includes(day.key)}
                                onCheckedChange={() => toggleTeacherDraftValue('day', draft.draftId, day.key)}
                              />
                              {day.label}
                            </label>
                          ))}
                        </div>
                        {draft.selectedValues.length > 0 && (
                          <p className="text-xs text-muted-foreground">
                            選択中: {draft.selectedValues.map((k) => DAY_OPTIONS.find((d) => d.key === k)?.label ?? k).join('、')}
                          </p>
                        )}
                      </div>
                    ))}
                    <Button type="button" size="sm" onClick={() => void applyTeacherDrafts('day')}>
                      T002を保存
                    </Button>
                  </div>

                  <div className="flex items-center justify-between rounded border p-3 gap-3">
                    <div className="min-w-[260px]">
                      <p className="text-sm font-medium">希望講師の反映</p>
                      <p className="text-xs text-muted-foreground">Excel希望データ内の「希望講師」を最適化で使う</p>
                    </div>
                    <Checkbox
                      checked={Boolean(p004Policy?.parameters.enable_preferred_teacher ?? true)}
                      onCheckedChange={(checked) =>
                        void handlePreferencePolicyToggle('enable_preferred_teacher', Boolean(checked))
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between rounded border p-3 gap-3">
                    <div className="min-w-[260px]">
                      <p className="text-sm font-medium">講師性別希望の反映</p>
                      <p className="text-xs text-muted-foreground">Excel希望データ内の「講師性別希望」を最適化で使う</p>
                    </div>
                    <Checkbox
                      checked={Boolean(p004Policy?.parameters.enable_gender_preference ?? true)}
                      onCheckedChange={(checked) =>
                        void handlePreferencePolicyToggle('enable_gender_preference', Boolean(checked))
                      }
                    />
                  </div>
                </div>

                {/* 保存結果のフィードバック */}
                {constraintSaveMessage && (
                  <Alert variant={constraintSaveMessage.type === 'error' ? 'destructive' : 'default'} className="mt-3">
                    {constraintSaveMessage.type === 'error' ? (
                      <AlertTriangle className="h-4 w-4" />
                    ) : (
                      <Check className="h-4 w-4" />
                    )}
                    <AlertDescription>{constraintSaveMessage.text}</AlertDescription>
                  </Alert>
                )}

                {/* 登録済み制約の詳細表示 */}
                <div className="mt-4 rounded border p-3 space-y-2 bg-muted/20">
                  <p className="text-sm font-medium">登録済みの制約一覧</p>
                  {(!constraintsData?.data || constraintsData.data.length === 0) ? (
                    <p className="text-xs text-muted-foreground">まだ制約が登録されていません</p>
                  ) : (
                    <div className="space-y-1">
                      {constraintsData.data.map((constraint, idx) => {
                        const teacherName = teacherMasterItems.find((t) => t.teacher_id === constraint.target_id)?.name;
                        let displayValue = '';
                        if (constraint.constraint_type === 'subject_limit') {
                          const subjectIds = (constraint.constraint_value as { subject_ids?: string[] })?.subject_ids ?? [];
                          displayValue = subjectIds.map((k) => SUBJECT_OPTIONS.find((s) => s.key === k)?.label ?? k).join('、');
                        } else if (constraint.constraint_type === 'day_limit') {
                          const days = (constraint.constraint_value as { days?: string[] })?.days ?? [];
                          displayValue = days.map((k) => DAY_OPTIONS.find((d) => d.key === k)?.label ?? k).join('、');
                        } else if (constraint.constraint_type === 'booth_capacity') {
                          displayValue = `${(constraint.constraint_value as { value?: number })?.value ?? 0} ブース`;
                        }
                        return (
                          <div key={idx} className="flex items-center gap-2 text-xs bg-background rounded p-2 border">
                            <Badge variant="outline" className="text-xs">
                              {constraint.constraint_type === 'subject_limit' && 'T001'}
                              {constraint.constraint_type === 'day_limit' && 'T002'}
                              {constraint.constraint_type === 'booth_capacity' && 'S007'}
                            </Badge>
                            {constraint.target_type === 'teacher' && (
                              <span className="font-medium">{teacherName ?? constraint.target_id}</span>
                            )}
                            {constraint.target_type === 'classroom' && (
                              <span className="font-medium">教室全体</span>
                            )}
                            <span className="text-muted-foreground">→</span>
                            <span>{displayValue}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="generate" className="mt-4">
              <div className="space-y-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="timeout">探索時間上限 (秒)</Label>
                    <p className="text-sm text-muted-foreground">
                      Orchestratorが自動的に戦略を切り替えます (standard → relaxed → partial)
                    </p>
                    <Input
                      id="timeout"
                      type="number"
                      min={10}
                      max={120}
                      value={maxTimeoutSeconds}
                      onChange={(e) => setMaxTimeoutSeconds(Number(e.target.value || 60))}
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-4">
                  <Button
                    onClick={handleGenerate}
                    disabled={!selectedClassroomId || !selectedTermId || isGenerating || !journeyStatus?.is_ready_to_generate}
                    className="gap-2"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        生成中...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        時間割を生成
                      </>
                    )}
                  </Button>

                  {selectedScheduleId && calendarView?.status === 'draft' && (
                    <Button
                      variant="default"
                      onClick={handleConfirm}
                      disabled={confirmMutation.isPending}
                      className="gap-2"
                    >
                      <Check className="h-4 w-4" />
                      確定する
                    </Button>
                  )}

                  {selectedScheduleId && (
                    <>
                      <Button
                        variant="outline"
                        onClick={() => handleExport('pdf')}
                        disabled={exportMutation.isPending}
                        className="gap-2"
                      >
                        <Download className="h-4 w-4" />
                        PDF出力
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleExport('csv')}
                        disabled={exportMutation.isPending}
                        className="gap-2"
                      >
                        <Download className="h-4 w-4" />
                        CSV出力
                      </Button>
                    </>
                  )}
                </div>

                {!journeyStatus?.is_ready_to_generate && selectedTermId && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>生成前チェック</AlertTitle>
                    <AlertDescription>
                      {(journeyStatus?.missing_requirements ?? []).join(' / ') || '前ステップを完了してください'}
                    </AlertDescription>
                  </Alert>
                )}

                {isGenerating && (
                  <div className="mt-4">
                    <Progress value={generationProgress} className="h-2" />
                    <p className="text-sm text-muted-foreground mt-2">
                      {generationStatusText || '最適解を探索中...'}
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>

          {journeyMessage && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>{journeyMessage}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* メトリクス */}
      {calendarView && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>ソフト制約達成率</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatRate(calendarView.metrics.soft_constraint_rate)}%
              </div>
              <Progress
                value={Number(calendarView.metrics.soft_constraint_rate)}
                className="h-2 mt-2"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>1対2率</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatRate(calendarView.metrics.one_to_two_rate)}%
              </div>
              <Progress
                value={Number(calendarView.metrics.one_to_two_rate)}
                className="h-2 mt-2"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>ステータス</CardDescription>
            </CardHeader>
            <CardContent>
              <Badge
                variant={
                  calendarView.status === 'confirmed'
                    ? 'default'
                    : calendarView.status === 'draft'
                      ? 'secondary'
                      : 'outline'
                }
              >
                {calendarView.status === 'confirmed'
                  ? '確定済み'
                  : calendarView.status === 'draft'
                    ? '下書き'
                    : calendarView.status}
              </Badge>
              <p className="text-sm text-muted-foreground mt-2">
                未配置: {calendarView.metrics.unplaced_count}名
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* タブコンテンツ */}
      {selectedScheduleId && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="calendar" className="gap-2">
              <Calendar className="h-4 w-4" />
              カレンダー
            </TabsTrigger>
            <TabsTrigger value="explanation" className="gap-2">
              <Info className="h-4 w-4" />
              結果説明
            </TabsTrigger>
            <TabsTrigger value="guide" className="gap-2">
              <Bot className="h-4 w-4" />
              ガイド付き解決
            </TabsTrigger>
          </TabsList>

          <TabsContent value="calendar" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>時間割カレンダー</CardTitle>
                <CardDescription>
                  ドラッグ&ドロップでコマを移動できます（下書き時のみ）
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <th className="border p-2 bg-muted w-24">時限</th>
                        {DAYS.map((day) => (
                          <th key={day.key} className="border p-2 bg-muted min-w-[150px]">
                            {day.label}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {SLOT_TIMES.map((slot) => (
                        <tr key={slot.slot}>
                          <td className="border p-2 text-center bg-muted/50">
                            <div className="font-medium">{slot.slot}限</div>
                            <div className="text-xs text-muted-foreground">{slot.time}</div>
                          </td>
                          {DAYS.map((day) => {
                            const cell = cellsByDaySlot?.[`${day.key}-${slot.slot}`];
                            return (
                              <td
                                key={`${day.key}-${slot.slot}`}
                                className="border p-1 align-top"
                                onDragOver={(e) => {
                                  if (calendarView?.status === 'draft') {
                                    e.preventDefault();
                                  }
                                }}
                                onDrop={(e) => {
                                  e.preventDefault();
                                  void handleDrop(day.key, slot.slot);
                                }}
                              >
                                {cell?.slots.map((slotInfo) => (
                                  <div
                                    key={slotInfo.slot_id}
                                    className={`p-2 mb-1 rounded text-xs ${
                                      slotInfo.slot_type === 'one_to_two'
                                        ? 'bg-blue-50 border border-blue-200'
                                        : 'bg-green-50 border border-green-200'
                                    } ${slotInfo.has_issue ? 'border-red-500' : ''} ${
                                      calendarView?.status === 'draft' ? 'cursor-move' : ''
                                    }`}
                                    draggable={calendarView?.status === 'draft'}
                                    onDragStart={() => void handleDragStart(slotInfo)}
                                    onDragEnd={() => {
                                      setDraggingSlot(null);
                                      setMovableTargets({});
                                    }}
                                    onClick={() => {
                                      if (slotInfo.has_issue) {
                                        setSelectedIssue({ slot: slotInfo, cell });
                                        void loadGuideTargets(slotInfo);
                                        setActiveTab('guide');
                                      }
                                    }}
                                  >
                                    <div className="font-medium">{slotInfo.teacher.name}</div>
                                    <div className="text-muted-foreground">
                                      {slotInfo.student1.name}
                                      {slotInfo.student1.subject && (
                                        <span className="ml-1">({slotInfo.student1.subject})</span>
                                      )}
                                    </div>
                                    {slotInfo.student2 && (
                                      <div className="text-muted-foreground">
                                        {slotInfo.student2.name}
                                        {slotInfo.student2.subject && (
                                          <span className="ml-1">({slotInfo.student2.subject})</span>
                                        )}
                                      </div>
                                    )}
                                    <Badge
                                      variant="outline"
                                      className="mt-1 text-[10px]"
                                    >
                                      {slotInfo.slot_type === 'one_to_two' ? '1対2' : '1対1'}
                                    </Badge>
                                    {slotInfo.has_issue && (
                                      <div className="mt-1 text-[10px] text-red-600">
                                        {slotInfo.issues?.[0] ?? '制約違反の可能性'}
                                      </div>
                                    )}
                                  </div>
                                ))}
                                {(!cell || cell.slots.length === 0) && (
                                  <div className="h-16 flex items-center justify-center text-muted-foreground text-xs">
                                    -
                                  </div>
                                )}
                                {draggingSlot && movableTargets[`${day.key}-${slot.slot}`] && (
                                  <div
                                    className={`mt-1 rounded px-1 py-0.5 text-[10px] ${
                                      movableTargets[`${day.key}-${slot.slot}`].feasibility === 'allowed'
                                        ? 'bg-green-100 text-green-800'
                                        : movableTargets[`${day.key}-${slot.slot}`].feasibility === 'soft_violation'
                                          ? 'bg-yellow-100 text-yellow-800'
                                          : 'bg-red-100 text-red-800'
                                    }`}
                                  >
                                    {movableTargets[`${day.key}-${slot.slot}`].feasibility}
                                  </div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="explanation" className="mt-4">
            {explanation && (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>結果サマリー</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-lg">{explanation.summary.overall}</p>
                    <ul className="mt-4 space-y-2">
                      {explanation.summary.key_points.map((point, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <Check className="h-4 w-4 mt-1 text-green-500" />
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>ボトルネック分析</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertTitle>{explanation.bottleneck_explanation.main_bottleneck}</AlertTitle>
                      <AlertDescription>
                        {explanation.bottleneck_explanation.detail}
                      </AlertDescription>
                    </Alert>
                    {explanation.bottleneck_explanation.structural_cause && (
                      <p className="mt-2 text-sm text-muted-foreground">
                        これは構造的な原因によるものです。
                      </p>
                    )}
                  </CardContent>
                </Card>

                {explanation.trade_offs.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>トレードオフ</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {explanation.trade_offs.map((tradeoff, i) => (
                          <div key={i} className="border rounded-lg p-4">
                            <p className="font-medium">{tradeoff.description}</p>
                            <div className="grid grid-cols-2 gap-4 mt-2">
                              <div>
                                <p className="text-sm font-medium text-green-600">メリット</p>
                                <ul className="text-sm">
                                  {tradeoff.pros.map((pro, j) => (
                                    <li key={j}>+ {pro}</li>
                                  ))}
                                </ul>
                              </div>
                              <div>
                                <p className="text-sm font-medium text-red-600">デメリット</p>
                                <ul className="text-sm">
                                  {tradeoff.cons.map((con, j) => (
                                    <li key={j}>- {con}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                            <Badge variant="outline" className="mt-2">
                              {tradeoff.recommendation}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="guide" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>問題箇所ハイライト・ガイド付き解決</CardTitle>
                <CardDescription>
                  問題のあるコマをクリックすると、推奨移動先と影響を表示します。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!selectedIssue && (
                  <Alert>
                    <Move className="h-4 w-4" />
                    <AlertTitle>対象コマを選択してください</AlertTitle>
                    <AlertDescription>
                      カレンダー内の赤枠コマをクリックすると、解決候補を表示します。
                    </AlertDescription>
                  </Alert>
                )}

                {selectedIssue && (
                  <div className="space-y-3">
                    <div className="rounded border p-3">
                      <p className="font-medium">
                        {selectedIssue.cell.day_of_week.toUpperCase()} {selectedIssue.cell.slot_number}限 /{' '}
                        {selectedIssue.slot.teacher.name}
                      </p>
                      <ul className="mt-2 text-sm text-red-600 list-disc pl-5">
                        {(selectedIssue.slot.issues ?? []).map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded border p-3">
                      <p className="font-medium mb-2">推奨移動先</p>
                      <div className="grid gap-2 md:grid-cols-2">
                        {guideTargets.map((target, idx) => (
                          <button
                            key={`${target.day_of_week}-${target.slot_number}-${idx}`}
                            className="rounded border p-2 text-left hover:bg-muted"
                            onClick={() =>
                              void handleDrop(target.day_of_week, target.slot_number)
                            }
                          >
                            <p className="font-medium">
                              {target.day_of_week.toUpperCase()} {target.slot_number}限
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {target.feasibility} / 新規違反 {String(target.impact.new_violations ?? 0)}
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="rounded border p-3 space-y-2">
                      <p className="font-medium">What-if 質問</p>
                      <textarea
                        className="w-full rounded border p-2 text-sm"
                        rows={3}
                        placeholder="例: 山田太郎を土曜1限に固定したらどうなりますか？"
                        value={whatIfQuestion}
                        onChange={(e) => setWhatIfQuestion(e.target.value)}
                      />
                      <Button onClick={runWhatIf} disabled={whatIfMutation.isPending}>
                        分析する
                      </Button>
                      {whatIfAnswer && (
                        <Alert>
                          <Info className="h-4 w-4" />
                          <AlertDescription>{whatIfAnswer}</AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* 選択ガイド */}
      {!selectedScheduleId && selectedTermId && (
        <Alert>
          <Play className="h-4 w-4" />
          <AlertTitle>時間割を生成してください</AlertTitle>
          <AlertDescription>
            「時間割を生成」ボタンをクリックすると、AIソルバーが最適な時間割を自動生成します。
            通常30秒〜1分で完了します。
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
