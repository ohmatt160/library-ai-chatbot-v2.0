import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Grid, List, Filter } from 'lucide-react';
import { searchApi } from '../../services/api';
import type { BookSearchParams } from '../../types';
import { BookCard } from './BookCard';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Card } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../ui/sheet';

export function BookSearch() {
  const [searchParams, setSearchParams] = useState<BookSearchParams>({ q: '' });
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const { data, isLoading } = useQuery({
    queryKey: ['books', searchParams],
    queryFn: () => searchApi.searchBooks(searchParams),
    enabled: !!searchParams.q || !!searchParams.author || !!searchParams.subject,
  });

  const books = data?.results || [];

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <Card className="p-6 backdrop-blur-sm bg-card/80 border border-border/50">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search for books..."
                value={searchParams.q || ''}
                onChange={(e) =>
                  setSearchParams((prev) => ({ ...prev, q: e.target.value }))
                }
                className="pl-10"
              />
            </div>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                  <Filter className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>Filters</SheetTitle>
                  <SheetDescription>
                    Refine your search with filters
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6 space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="author">Author</Label>
                    <Input
                      id="author"
                      placeholder="Author name"
                      value={searchParams.author || ''}
                      onChange={(e) =>
                        setSearchParams((prev) => ({ ...prev, author: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subject">Subject</Label>
                    <Input
                      id="subject"
                      placeholder="Subject"
                      value={searchParams.subject || ''}
                      onChange={(e) =>
                        setSearchParams((prev) => ({ ...prev, subject: e.target.value }))
                      }
                    />
                  </div>
                </div>
              </SheetContent>
            </Sheet>

            <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'grid' | 'list')}>
              <TabsList>
                <TabsTrigger value="grid">
                  <Grid className="h-4 w-4" />
                </TabsTrigger>
                <TabsTrigger value="list">
                  <List className="h-4 w-4" />
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </form>

        {data && (
          <p className="text-sm text-muted-foreground mt-2">
            Found {data.count} result{data.count !== 1 ? 's' : ''} for "{data.query}"
          </p>
        )}
      </Card>

      {/* Results */}
      <div>
        {isLoading ? (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-4'}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="p-4">
                <Skeleton className="h-48 w-full mb-4" />
                <Skeleton className="h-4 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </Card>
            ))}
          </div>
        ) : books.length > 0 ? (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-4'}>
            {books.map((book) => (
              <BookCard key={book.id} book={book} viewMode={viewMode} />
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center backdrop-blur-sm bg-card/80 border border-border/50">
            <p className="text-muted-foreground">
              {searchParams.q || searchParams.author || searchParams.subject
                ? 'No books found. Try a different search.'
                : 'Enter a search query to find books.'}
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
