import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';

export function SystemHealth() {
  const [isOnline, setIsOnline] = useState(true);
  const [responseTime, setResponseTime] = useState<number | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      const start = Date.now();
      try {
        const response = await fetch('http://localhost:5000/api/session', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          },
        });
        const end = Date.now();
        setIsOnline(response.ok || response.status === 401); // 401 means server is up but not authenticated
        setResponseTime(end - start);
      } catch (error) {
        setIsOnline(false);
        setResponseTime(null);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className="cursor-pointer"
          >
            <Activity className={`h-3 w-3 mr-1 ${isOnline ? 'text-green-500' : 'text-red-500'}`} />
            {isOnline ? 'Online' : 'Offline'}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>
            Server Status: {isOnline ? 'Connected' : 'Disconnected'}
            {responseTime && isOnline && (
              <span className="block text-xs text-muted-foreground">
                Response time: {responseTime}ms
              </span>
            )}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
