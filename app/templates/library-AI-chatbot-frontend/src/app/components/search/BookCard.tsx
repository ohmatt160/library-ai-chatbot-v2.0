import { BookOpen, MapPin, CheckCircle2, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import type { Book } from '../../types';
import { useAuthStore } from '../../store/auth';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { cn } from '../ui/utils';

interface BookCardProps {
  book: Book;
  viewMode: 'grid' | 'list';
}

export function BookCard({ book, viewMode }: BookCardProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const isAvailable = book.copies_available > 0;

  const handleReserve = () => {
    if (!isAuthenticated) {
      toast.error('Please login to reserve books');
      return;
    }
    toast.success(`Reserved: ${book.title}`);
  };

  const getAvailabilityIcon = () => {
    return isAvailable
      ? <CheckCircle2 className="h-4 w-4 text-green-500" />
      : <XCircle className="h-4 w-4 text-red-500" />;
  };

  const getAvailabilityColor = () => {
    return isAvailable
      ? 'bg-green-500/10 text-green-700 dark:text-green-400'
      : 'bg-red-500/10 text-red-700 dark:text-red-400';
  };

  const getAvailabilityText = () => {
    if (isAvailable) {
      return `${book.copies_available} available`;
    }
    return 'Unavailable';
  };

  if (viewMode === 'list') {
    return (
      <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
        <div className="flex items-center gap-4 p-4">
          <div className="w-24 h-32 bg-muted rounded flex items-center justify-center flex-shrink-0">
            <BookOpen className="h-8 w-8 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="truncate mb-1">{book.title}</h3>
            <p className="text-sm text-muted-foreground mb-2">{book.author}</p>
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {book.isbn && <span>ISBN: {book.isbn}</span>}
              {book.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {book.location}
                </span>
              )}
              {book.topic && <span>Topic: {book.topic}</span>}
            </div>
            {book.summary && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{book.summary}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <Badge className={cn('flex items-center gap-1', getAvailabilityColor())}>
              {getAvailabilityIcon()}
              {getAvailabilityText()}
            </Badge>
            <Button
              onClick={handleReserve}
              disabled={!isAvailable}
              size="sm"
            >
              Reserve
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="backdrop-blur-sm bg-card/80 border border-border/50 hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="w-full h-48 bg-muted rounded mb-4 flex items-center justify-center overflow-hidden">
          <BookOpen className="h-12 w-12 text-muted-foreground" />
        </div>
        <CardTitle className="line-clamp-2">{book.title}</CardTitle>
        <p className="text-sm text-muted-foreground">{book.author}</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-muted-foreground">
          {book.isbn && <p>ISBN: {book.isbn}</p>}
          {book.location && (
            <p className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {book.location}
            </p>
          )}
          {book.topic && <p>Topic: {book.topic}</p>}
          {book.summary && (
            <p className="line-clamp-3">{book.summary}</p>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between items-center">
        <Badge className={cn('flex items-center gap-1', getAvailabilityColor())}>
          {getAvailabilityIcon()}
          {getAvailabilityText()}
        </Badge>
        <Button
          onClick={handleReserve}
          disabled={!isAvailable}
          size="sm"
        >
          Reserve
        </Button>
      </CardFooter>
    </Card>
  );
}
