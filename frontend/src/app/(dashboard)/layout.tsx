'use client';

import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { AuthGuard } from '@/components/auth/auth-guard';
import { useAuthStore } from '@/stores/auth';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuthStore();

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div className="ml-64">
          <Header
            user={
              user
                ? {
                    name: user.name,
                    email: user.email,
                    role: user.role,
                  }
                : undefined
            }
          />
          <main className="p-6">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}
