import { useQuery } from '@tanstack/react-query';
import { Users, Activity, BarChart3, MessageSquare, BookOpen, User, Star } from 'lucide-react';
import { adminApi } from '../../services/api';
import { UsersTable } from './UsersTable';
import { ActivityLog } from './ActivityLog';
import { MetricsCharts } from './MetricsCharts';
import { AdminBooks } from './AdminBooks';
import { AdminContacts } from './AdminContacts';
import { EvaluationReport } from './EvaluationReport';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Skeleton } from '../ui/skeleton';

export function AdminDashboard() {
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: adminApi.getUsers,
  });

  const { data: activitiesData, isLoading: activitiesLoading } = useQuery({
    queryKey: ['admin-activities'],
    queryFn: adminApi.getActivities,
  });

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: adminApi.getMetrics,
  });

  const users = usersData?.users || [];
  const activities = activitiesData?.activities || [];

  // Calculate total chats from chat_statistics
  const totalChats = metrics?.chat_statistics?.reduce((sum, stat) => sum + stat.chat_count, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{metrics?.total_users || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Activities</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{metrics?.total_activities || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Chats</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{totalChats}</div>
            )}
          </CardContent>
        </Card>

        <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">User Types</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-2xl font-bold">
                {metrics?.user_statistics?.length || 0} types
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="users" className="space-y-4">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="books">Books</TabsTrigger>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="evaluation">Evaluation</TabsTrigger>
          <TabsTrigger value="activity">Activity Log</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <UsersTable users={users} isLoading={usersLoading} />
        </TabsContent>

        <TabsContent value="books" className="space-y-4">
          <AdminBooks />
        </TabsContent>

        <TabsContent value="contacts" className="space-y-4">
          <AdminContacts />
        </TabsContent>

        <TabsContent value="evaluation" className="space-y-4">
          <EvaluationReport />
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <ActivityLog activities={activities} isLoading={activitiesLoading} />
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <MetricsCharts metrics={metrics} isLoading={metricsLoading} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
