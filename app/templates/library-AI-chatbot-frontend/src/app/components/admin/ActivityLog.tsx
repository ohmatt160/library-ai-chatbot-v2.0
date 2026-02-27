import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Filter } from 'lucide-react';
import type { Activity } from '../../types';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Skeleton } from '../ui/skeleton';
import { ScrollArea } from '../ui/scroll-area';
import { Button } from '../ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../ui/sheet';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

interface ActivityLogProps {
  activities: Activity[];
  isLoading: boolean;
}

export function ActivityLog({ activities, isLoading }: ActivityLogProps) {
  const [userFilter, setUserFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  const filteredActivities = activities.filter(
    (activity) =>
      (!userFilter || (activity.username && activity.username.toLowerCase().includes(userFilter.toLowerCase()))) &&
      (!actionFilter || activity.activity_type.toLowerCase().includes(actionFilter.toLowerCase()))
  );

  const getActivityDetails = (activity: Activity): string => {
    if (!activity.activity_details) return '';
    if (typeof activity.activity_details === 'string') return activity.activity_details;
    // Format JSON details into readable string
    const details = activity.activity_details;
    if (details.message) return `Message: ${details.message}`;
    if (details.action) return details.action;
    if (details.query) return `Search: ${details.query}`;
    return JSON.stringify(details);
  };

  return (
    <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
      <div className="p-4 border-b border-border flex justify-between items-center">
        <h3>Activity Log</h3>
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Filter Activities</SheetTitle>
              <SheetDescription>
                Filter activities by user or action
              </SheetDescription>
            </SheetHeader>
            <div className="mt-6 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="user-filter">User</Label>
                <Input
                  id="user-filter"
                  placeholder="Filter by username"
                  value={userFilter}
                  onChange={(e) => setUserFilter(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="action-filter">Activity Type</Label>
                <Input
                  id="action-filter"
                  placeholder="Filter by activity type"
                  value={actionFilter}
                  onChange={(e) => setActionFilter(e.target.value)}
                />
              </div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setUserFilter('');
                  setActionFilter('');
                }}
              >
                Clear Filters
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>

      <ScrollArea className="h-[600px]">
        <div className="p-4 space-y-4">
          {isLoading ? (
            Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="flex items-start gap-4 pb-4 border-b border-border last:border-0">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))
          ) : filteredActivities.length > 0 ? (
            filteredActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-4 pb-4 border-b border-border last:border-0"
              >
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-medium">
                    {(activity.username || 'A').charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium truncate">{activity.username || 'Anonymous'}</span>
                    {activity.user_type && (
                      <Badge variant="secondary" className="text-xs">
                        {activity.user_type}
                      </Badge>
                    )}
                    <Badge variant="outline" className="text-xs">
                      {activity.activity_type}
                    </Badge>
                  </div>
                  {getActivityDetails(activity) && (
                    <p className="text-sm text-muted-foreground mb-1">{getActivityDetails(activity)}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-muted-foreground py-12">
              No activities found
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
