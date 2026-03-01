import { BookOpen, MapPin, CheckCircle2, XCircle, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import type { Book } from '../../types';
import { useAuthStore } from '../../store/auth';
import { borrowApi } from '../../services/api';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { cn } from '../ui/utils';
import { useMutation } from '@tanstack/react-query';

interface BookCardProps {
  book: Book;
  viewMode: 'grid' | 'list';
  onBookClick?: (book: Book) => void;
}

export function BookCard({ book, viewMode, onBookClick }: BookCardProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isAvailable = book.copies_available > 0;

  // Borrow mutation for available books
  const borrowMutation = useMutation({
    mutationFn: (bookId: number) => borrowApi.createRequest(bookId),
    onSuccess: (data) => {
      toast.success(data.message || 'Borrow request submitted successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to submit borrow request');
    },
  });

  // Reserve mutation for unavailable books
  const reserveMutation = useMutation({
    mutationFn: (bookId: number) => borrowApi.createReservation(bookId),
    onSuccess: (data) => {
      toast.success(data.message || 'Reservation submitted successfully!');
    },
    onError: (error: any) => {
      console.error('Reservation error:', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to create reservation';
      toast.error(errorMsg);
    },
  });

  const handleBorrow = () => {
    if (!isAuthenticated) {
      toast.error('Please login to borrow books');
      return;
    }
    borrowMutation.mutate(book.id);
  };

  const handleReserve = () => {
    if (!isAuthenticated) {
      toast.error('Please login to reserve books');
      return;
    }
    reserveMutation.mutate(book.id);
  };

  const handleBookClick = () => {
    if (onBookClick) {
      onBookClick(book);
    } else if (book.preview_url || book.source === 'openlibrary') {
      // Open preview in new tab if available
      const url = book.preview_url || (book.openlibrary_key ? `https://openlibrary.org${book.openlibrary_key}` : null);
      if (url) {
        window.open(url, '_blank');
      }
    }
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
          <div 
            className="w-24 h-32 bg-muted rounded flex items-center justify-center flex-shrink-0 overflow-hidden cursor-pointer relative group"
            onClick={handleBookClick}
          >
            {book.cover_url ? (
              <>
                <img
                  src={book.cover_url}
                  alt={book.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <ExternalLink className="h-4 w-4 text-white" />
                </div>
              </>
            ) : (
              <BookOpen className="h-8 w-8 text-muted-foreground" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {book.source === 'openlibrary' && (
                <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800">
                  OpenLibrary
                </Badge>
              )}
              {book.cover_url && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleBookClick();
                  }}
                >
                  <ExternalLink className="h-3 w-3 mr-1" />
                  Preview
                </Button>
              )}
            </div>
            <h3 className="truncate mb-1 cursor-pointer hover:text-primary" onClick={handleBookClick}>{book.title}</h3>
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
            {isAvailable ? (
              <Button
                onClick={handleBorrow}
                disabled={borrowMutation.isPending}
                size="sm"
              >
                {borrowMutation.isPending ? 'Processing...' : 'Borrow'}
              </Button>
            ) : (
              <Button
                onClick={handleReserve}
                disabled={reserveMutation.isPending}
                size="sm"
                variant="outline"
              >
                {reserveMutation.isPending ? 'Reserving...' : 'Reserve'}
              </Button>
            )}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="backdrop-blur-sm bg-card/80 border border-border/50 hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="w-full h-48 bg-muted rounded mb-4 flex items-center justify-center overflow-hidden relative group cursor-pointer" onClick={handleBookClick}>
          {book.cover_url ? (
            <>
              <img
                src={book.cover_url}
                alt={book.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback to icon if image fails
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
              {/* Overlay with preview button on hover */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleBookClick();
                  }}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Preview
                </Button>
              </div>
            </>
          ) : (
            <BookOpen className="h-12 w-12 text-muted-foreground" />
          )}
        </div>
        <CardTitle className="line-clamp-2 cursor-pointer hover:text-primary transition-colors" onClick={handleBookClick}>
          {book.title}
        </CardTitle>
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
        <div className="flex items-center gap-2">
          <Badge className={cn('flex items-center gap-1', getAvailabilityColor())}>
            {getAvailabilityIcon()}
            {getAvailabilityText()}
          </Badge>
          {book.source === 'openlibrary' && (
            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800">
              OpenLibrary
            </Badge>
          )}
        </div>
        {isAvailable ? (
          <Button
            onClick={handleBorrow}
            disabled={borrowMutation.isPending}
            size="sm"
          >
            {borrowMutation.isPending ? 'Processing...' : 'Borrow'}
          </Button>
        ) : (
          <Button
            onClick={handleReserve}
            disabled={reserveMutation.isPending}
            size="sm"
            variant="outline"
          >
            {reserveMutation.isPending ? 'Reserving...' : 'Reserve'}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
