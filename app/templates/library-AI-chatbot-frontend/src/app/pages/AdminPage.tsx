import { Navigate } from 'react-router';
import { useAuthStore } from '../store/auth';
import { AdminDashboard } from '../components/admin/AdminDashboard';
import { ShieldAlert } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';

export function AdminPage() {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (!(user?.user_type === 'Admin' || user?.user_type === 'admin')) {
    return (
      <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
        <CardContent className="p-12 text-center">
          <ShieldAlert className="h-12 w-12 mx-auto mb-4 text-destructive" />
          <h2 className="mb-2">Access Denied</h2>
          <p className="text-muted-foreground">
            You don't have permission to access this page.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1>Admin Dashboard</h1>
        <p className="text-muted-foreground">
          Manage users, view activity logs, and monitor system metrics
        </p>
      </div>
      <AdminDashboard />
    </div>
  );
}
