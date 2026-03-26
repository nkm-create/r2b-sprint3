'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useAuth } from '@/hooks/use-auth';
import { GuestGuard } from '@/components/auth/auth-guard';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoginPending } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ email, password });
  };

  return (
    <GuestGuard>
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary/5 to-primary/10">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <div className="flex items-center gap-2 text-primary">
                <Calendar className="h-10 w-10" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold">ログイン</CardTitle>
            <CardDescription>学習塾時間割最適化システム</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">メールアドレス</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="admin@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoginPending}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">パスワード</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoginPending}
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-4">
              <Button type="submit" className="w-full" disabled={isLoginPending}>
                {isLoginPending ? 'ログイン中...' : 'ログイン'}
              </Button>
              <Button
                type="button"
                variant="link"
                className="text-sm text-muted-foreground"
                onClick={() => router.push('/password/reset')}
              >
                パスワードをお忘れですか？
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </GuestGuard>
  );
}
