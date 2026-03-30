'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Calendar,
  Users,
  GraduationCap,
  BookOpen,
  Building2,
  Settings,
  LayoutDashboard,
  ClipboardList,
  Bell,
  CalendarRange,
  UserCog,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Separator } from '@/components/ui/separator';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const mainNavItems: NavItem[] = [
  {
    title: 'ダッシュボード',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: '時間割作成',
    href: '/schedules',
    icon: Calendar,
  },
];

const managementNavItems: NavItem[] = [
  {
    title: '教室管理',
    href: '/classrooms',
    icon: Building2,
  },
  {
    title: '講師管理',
    href: '/teachers',
    icon: Users,
  },
  {
    title: '生徒管理',
    href: '/students',
    icon: GraduationCap,
  },
  {
    title: '科目管理',
    href: '/subjects',
    icon: BookOpen,
  },
  {
    title: '期間設定',
    href: '/terms',
    icon: CalendarRange,
  },
];

const systemNavItems: NavItem[] = [
  {
    title: '通知管理',
    href: '/notifications',
    icon: Bell,
  },
  {
    title: 'ユーザー管理',
    href: '/users',
    icon: UserCog,
  },
  {
    title: 'システム設定',
    href: '/settings',
    icon: Settings,
  },
];

function NavSection({
  title,
  items,
}: {
  title?: string;
  items: NavItem[];
}) {
  const pathname = usePathname();

  return (
    <div className="space-y-1">
      {title && (
        <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </h3>
      )}
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <Icon className="h-4 w-4" />
            {item.title}
          </Link>
        );
      })}
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-background">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center border-b px-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <Calendar className="h-6 w-6 text-primary" />
            <span className="font-semibold">時間割システム</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-6 overflow-y-auto p-4">
          <NavSection items={mainNavItems} />
          <Separator />
          <NavSection title="マスタ管理" items={managementNavItems} />
          <Separator />
          <NavSection title="システム" items={systemNavItems} />
        </nav>
      </div>
    </aside>
  );
}
