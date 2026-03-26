'use client';

import { useAuthStore } from '@/stores/auth';
import { useDashboard, useMarkNotificationAsRead } from '@/hooks/use-dashboard';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Calendar,
  Users,
  GraduationCap,
  AlertCircle,
  TrendingUp,
  ArrowRight,
  Bell,
  CheckCircle,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  HeatmapCell,
  SubjectCoverage,
  SupplyDemandBalance,
  NotificationItem,
  TermInfo,
} from '@/lib/api/dashboard';

// 曜日表示用マッピング
const dayLabels: Record<string, string> = {
  mon: '月',
  tue: '火',
  wed: '水',
  thu: '木',
  fri: '金',
  sat: '土',
};

// ヒートマップセルの色
const heatmapColors: Record<string, string> = {
  surplus: 'bg-green-500',
  balanced: 'bg-lime-400',
  tight: 'bg-yellow-400',
  shortage: 'bg-red-500',
};

// カバー率ステータスの色
const coverageColors: Record<string, string> = {
  sufficient: 'bg-green-500',
  partial: 'bg-yellow-400',
  insufficient: 'bg-red-500',
};

// 通知の重要度アイコン
const severityIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  critical: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const severityColors: Record<string, string> = {
  critical: 'text-red-500',
  warning: 'text-yellow-500',
  info: 'text-blue-500',
};

// 統計カードコンポーネント
function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
}: {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: number;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <div className="text-2xl font-bold">{value}</div>
          {trend !== undefined && (
            <span
              className={cn(
                'text-xs',
                trend >= 0 ? 'text-green-600' : 'text-red-600'
              )}
            >
              {trend >= 0 ? '+' : ''}
              {trend}%
            </span>
          )}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

// 充足率円グラフコンポーネント
function FulfillmentChart({ rate }: { rate: number }) {
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (rate / 100) * circumference;

  return (
    <div className="relative flex h-32 w-32 items-center justify-center">
      <svg className="h-32 w-32 -rotate-90 transform">
        <circle
          cx="64"
          cy="64"
          r="40"
          stroke="currentColor"
          strokeWidth="8"
          fill="transparent"
          className="text-muted"
        />
        <circle
          cx="64"
          cy="64"
          r="40"
          stroke="currentColor"
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className={cn(
            rate >= 85 ? 'text-green-500' : rate >= 70 ? 'text-yellow-500' : 'text-red-500'
          )}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-bold">{rate.toFixed(1)}%</span>
        <span className="text-xs text-muted-foreground">充足率</span>
      </div>
    </div>
  );
}

// ヒートマップコンポーネント
function HeatmapGrid({ cells }: { cells: HeatmapCell[] }) {
  const days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
  const slots = [0, 1, 2, 3, 4];

  const getCellData = (day: string, slot: number) => {
    return cells.find((c) => c.day_of_week === day && c.slot_number === slot);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="p-2"></th>
            {days.map((day) => (
              <th key={day} className="p-2 text-center font-medium">
                {dayLabels[day]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {slots.map((slot) => (
            <tr key={slot}>
              <td className="p-2 text-center font-medium">{slot}限</td>
              {days.map((day) => {
                // 平日の0限はスキップ
                if (slot === 0 && day !== 'sat') {
                  return <td key={day} className="p-1"></td>;
                }
                const cell = getCellData(day, slot);
                if (!cell) {
                  return <td key={day} className="p-1"></td>;
                }
                return (
                  <td key={day} className="p-1">
                    <div
                      className={cn(
                        'flex h-10 w-full items-center justify-center rounded text-xs font-medium text-white',
                        heatmapColors[cell.status]
                      )}
                      title={`供給: ${cell.supply} / 需要: ${cell.demand} / 差: ${cell.balance}`}
                    >
                      {cell.balance >= 0 ? `+${cell.balance}` : cell.balance}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-2 flex items-center justify-center gap-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded bg-green-500" />
          <span>余裕</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded bg-lime-400" />
          <span>適正</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded bg-yellow-400" />
          <span>ギリギリ</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded bg-red-500" />
          <span>不足</span>
        </div>
      </div>
    </div>
  );
}

// 科目別カバー率コンポーネント
function SubjectCoverageList({ items }: { items: SubjectCoverage[] }) {
  const categoryLabels: Record<string, string> = {
    elementary: '小学生',
    junior_high: '中学生',
    high_school: '高校生',
  };

  // カテゴリでグループ化
  const grouped = items.reduce(
    (acc, item) => {
      const category = item.grade_category;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(item);
      return acc;
    },
    {} as Record<string, SubjectCoverage[]>
  );

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([category, subjects]) => (
        <div key={category}>
          <h4 className="mb-2 text-sm font-medium">{categoryLabels[category]}</h4>
          <div className="space-y-2">
            {subjects.slice(0, 3).map((subject) => (
              <div key={subject.subject_id} className="flex items-center gap-2">
                <span className="w-20 truncate text-sm">{subject.subject_name}</span>
                <div className="flex-1">
                  <div className="h-2 rounded-full bg-muted">
                    <div
                      className={cn(
                        'h-2 rounded-full',
                        coverageColors[subject.status]
                      )}
                      style={{ width: `${Math.min(100, subject.coverage_rate)}%` }}
                    />
                  </div>
                </div>
                <span className="w-12 text-right text-sm">
                  {subject.coverage_rate.toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// 需給バランスコンポーネント
function SupplyDemandChart({ items }: { items: SupplyDemandBalance[] }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.category} className="flex items-center gap-4">
          <span className="w-16 text-sm font-medium">{item.category}</span>
          <div className="flex flex-1 items-center gap-2">
            <div className="flex-1">
              <div className="flex h-6 items-center">
                <div
                  className="h-4 rounded-l bg-blue-500"
                  style={{
                    width: `${(item.supply / Math.max(item.supply, item.demand)) * 100}%`,
                  }}
                />
              </div>
              <div className="flex h-6 items-center">
                <div
                  className="h-4 rounded-l bg-orange-500"
                  style={{
                    width: `${(item.demand / Math.max(item.supply, item.demand)) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-blue-600">供給: {item.supply}</div>
            <div className="text-xs text-orange-600">需要: {item.demand}</div>
          </div>
          <div
            className={cn(
              'w-16 text-right text-sm font-medium',
              item.difference >= 0 ? 'text-green-600' : 'text-red-600'
            )}
          >
            {item.difference >= 0 ? '+' : ''}
            {item.difference}
          </div>
        </div>
      ))}
    </div>
  );
}

// ターム情報カード
function TermCard({ term, label }: { term: TermInfo | null; label: string }) {
  if (!term) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{label}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">未設定</p>
        </CardContent>
      </Card>
    );
  }

  const statusLabels: Record<string, string> = {
    creating: '作成中',
    confirmed: '確定',
    archived: 'アーカイブ',
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="font-medium">{term.term_name}</p>
        <p className="text-sm text-muted-foreground">
          {term.start_date} 〜 {term.end_date}
        </p>
        <span
          className={cn(
            'mt-1 inline-block rounded px-2 py-0.5 text-xs',
            term.status === 'confirmed'
              ? 'bg-green-100 text-green-800'
              : term.status === 'creating'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-800'
          )}
        >
          {statusLabels[term.status] || term.status}
        </span>
      </CardContent>
    </Card>
  );
}

// 通知リストコンポーネント
function NotificationList({
  items,
  onMarkAsRead,
}: {
  items: NotificationItem[];
  onMarkAsRead: (id: string) => void;
}) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <CheckCircle className="mb-2 h-8 w-8" />
        <p>通知はありません</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const Icon = severityIcons[item.severity] || Info;
        return (
          <div
            key={item.notification_id}
            className={cn(
              'flex items-start gap-3 rounded-lg border p-3 transition-colors',
              item.is_read ? 'bg-muted/30' : 'bg-background'
            )}
          >
            <Icon className={cn('mt-0.5 h-5 w-5', severityColors[item.severity])} />
            <div className="flex-1">
              <p className="text-sm font-medium">{item.title}</p>
              <p className="text-xs text-muted-foreground">{item.message}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {new Date(item.created_at).toLocaleString('ja-JP')}
              </p>
            </div>
            {!item.is_read && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onMarkAsRead(item.notification_id)}
              >
                既読
              </Button>
            )}
          </div>
        );
      })}
    </div>
  );
}

// メインダッシュボードページ
export default function DashboardPage() {
  const { user } = useAuthStore();

  // TODO: ユーザーの所属教室IDを取得する仕組みを実装
  // 現在は仮のIDを使用（実際の実装ではユーザー情報から取得）
  const classroomId = user?.classroom_ids?.[0];

  const { data: dashboard, isLoading, error } = useDashboard(classroomId);
  const { mutate: markAsRead } = useMarkNotificationAsRead(classroomId ?? '');

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-muted-foreground">読み込み中...</div>
      </div>
    );
  }

  if (error || !dashboard) {
    // データがない場合はデモ表示
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">ダッシュボード</h1>
          <p className="text-muted-foreground">
            時間割作成状況と教室の概要を確認できます
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="1対2充足率"
            value="--"
            description="データがありません"
            icon={TrendingUp}
          />
          <StatCard
            title="登録講師数"
            value="--"
            description="アクティブな講師"
            icon={Users}
          />
          <StatCard
            title="登録生徒数"
            value="--"
            description="今期の受講生徒"
            icon={GraduationCap}
          />
          <StatCard
            title="要対応アラート"
            value="--"
            description="確認が必要な項目"
            icon={Bell}
          />
        </div>

        <Card>
          <CardContent className="py-8">
            <div className="text-center text-muted-foreground">
              <p>教室が選択されていないか、データがありません。</p>
              <p className="mt-2">教室を選択してください。</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ページタイトル */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {dashboard.classroom_name}
          </h1>
          <p className="text-muted-foreground">
            時間割作成状況と教室の概要を確認できます
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            時間割作成
          </Button>
          <Button>
            振替対応
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="1対2充足率"
          value={`${dashboard.fulfillment.fulfillment_rate}%`}
          description={`${dashboard.fulfillment.one_to_two_slots}コマ / ${dashboard.fulfillment.total_slots}コマ`}
          icon={TrendingUp}
        />
        <StatCard
          title="コマ数サマリー"
          value={dashboard.fulfillment.total_slots}
          description={`1対2: ${dashboard.fulfillment.one_to_two_slots} / 1対1: ${dashboard.fulfillment.one_to_one_slots}`}
          icon={Calendar}
        />
        <StatCard
          title="登録講師数"
          value={dashboard.personnel.teacher_count}
          description="アクティブな講師"
          icon={Users}
        />
        <StatCard
          title="登録生徒数"
          value={dashboard.personnel.student_count}
          description="今期の受講生徒"
          icon={GraduationCap}
        />
      </div>

      {/* メインコンテンツ */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* 充足率チャート */}
        <Card>
          <CardHeader>
            <CardTitle>充足率サマリー</CardTitle>
            <CardDescription>1対2形式の授業充足状況</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
            <FulfillmentChart rate={Number(dashboard.fulfillment.fulfillment_rate)} />
          </CardContent>
        </Card>

        {/* 人員状況ヒートマップ */}
        <Card>
          <CardHeader>
            <CardTitle>人員状況ヒートマップ</CardTitle>
            <CardDescription>曜日×時間帯の需給バランス</CardDescription>
          </CardHeader>
          <CardContent>
            <HeatmapGrid cells={dashboard.heatmap.cells} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* 科目別カバー率 */}
        <Card>
          <CardHeader>
            <CardTitle>科目別カバー率</CardTitle>
            <CardDescription>科目ごとの講師充足状況</CardDescription>
          </CardHeader>
          <CardContent>
            <SubjectCoverageList items={dashboard.subject_coverage.items} />
          </CardContent>
        </Card>

        {/* 需給バランス */}
        <Card>
          <CardHeader>
            <CardTitle>需給バランス</CardTitle>
            <CardDescription>学年カテゴリ別の需給差分</CardDescription>
          </CardHeader>
          <CardContent>
            <SupplyDemandChart items={dashboard.supply_demand.items} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* ターム情報 */}
        <TermCard term={dashboard.current_term} label="現在のターム" />
        <TermCard term={dashboard.next_term} label="次回ターム" />

        {/* 通知・アラート */}
        <Card className="lg:row-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>通知・アラート</CardTitle>
              <CardDescription>
                {dashboard.notifications.unread_count > 0
                  ? `${dashboard.notifications.unread_count}件の未読`
                  : '全て既読'}
              </CardDescription>
            </div>
            <Bell className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <NotificationList
              items={dashboard.notifications.items}
              onMarkAsRead={markAsRead}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
