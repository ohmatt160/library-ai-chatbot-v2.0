import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../services/api';
import type { Book, CreateBookRequest, BulkBooksRequest } from '../../types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { Skeleton } from '../ui/skeleton';
import { toast } from 'sonner';
import { Plus, Trash2, Edit, Upload, BookOpen, Search, X } from 'lucide-react';

export function AdminBooks() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isBulkDialogOpen, setIsBulkDialogOpen] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [bookForm, setBookForm] = useState<CreateBookRequest>({
    title: '',
    author: '',
    isbn: '',
    topic: '',
    copies_available: 1,
    location: '',
    summary: '',
  });
  const [bulkJson, setBulkJson] = useState('');

  const { data: booksData, isLoading } = useQuery({
    queryKey: ['admin-books', search],
    queryFn: () => adminApi.getBooks(1, 50, search),
  });

  const createMutation = useMutation({
    mutationFn: adminApi.createBook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-books'] });
      setIsAddDialogOpen(false);
      resetForm();
      toast.success('Book added successfully');
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Failed to add book';
      toast.error(errorMsg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateBookRequest }) =>
      adminApi.updateBook(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-books'] });
      setEditingBook(null);
      resetForm();
      toast.success('Book updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update book');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteBook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-books'] });
      toast.success('Book deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to delete book');
    },
  });

  const bulkMutation = useMutation({
    mutationFn: (data: BulkBooksRequest) => adminApi.bulkCreateBooks(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-books'] });
      setIsBulkDialogOpen(false);
      setBulkJson('');
      toast.success(`Imported ${result.imported} books. Failed: ${result.failed}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to import books');
    },
  });

  const resetForm = () => {
    setBookForm({
      title: '',
      author: '',
      isbn: '',
      topic: '',
      copies_available: 1,
      location: '',
      summary: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitting book form:', bookForm);
    if (!bookForm.title || !bookForm.author) {
      toast.error('Title and author are required');
      return;
    }
    if (bookForm.copies_available < 1) {
      toast.error('Copies available must be at least 1');
      return;
    }
    if (editingBook) {
      updateMutation.mutate({ id: editingBook.id, data: bookForm });
    } else {
      createMutation.mutate(bookForm);
    }
  };

  const handleBulkImport = () => {
    try {
      const parsed = JSON.parse(bulkJson);
      if (!parsed.books || !Array.isArray(parsed.books)) {
        toast.error('Invalid format. Expected { "books": [...] }');
        return;
      }
      bulkMutation.mutate(parsed);
    } catch {
      toast.error('Invalid JSON format');
    }
  };

  const openEdit = (book: Book) => {
    setEditingBook(book);
    setBookForm({
      title: book.title,
      author: book.author,
      isbn: book.isbn,
      topic: book.topic || '',
      copies_available: book.copies_available,
      location: book.location,
      summary: book.summary || '',
    });
  };

  const books = booksData?.books || [];

  return (
    <div className="space-y-4">
      {/* Actions Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search books..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          <Dialog open={isBulkDialogOpen} onOpenChange={setIsBulkDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Bulk Import
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Bulk Import Books</DialogTitle>
                <DialogDescription>
                  Paste a JSON array of books to import multiple books at once.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Textarea
                  placeholder='{"books": [{"title": "Book 1", "author": "Author 1"}, ...]}'
                  value={bulkJson}
                  onChange={(e) => setBulkJson(e.target.value)}
                  className="min-h-[200px] font-mono text-sm"
                />
                <Button onClick={handleBulkImport} disabled={bulkMutation.isPending}>
                  {bulkMutation.isPending ? 'Importing...' : 'Import Books'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Button onClick={() => { resetForm(); setEditingBook(null); setIsAddDialogOpen(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Book
              </Button>
              <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingBook ? 'Edit Book' : 'Add New Book'}</DialogTitle>
                <DialogDescription>
                  Fill in the book details. Title and author are required.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title *</Label>
                    <Input
                      id="title"
                      value={bookForm.title}
                      onChange={(e) => setBookForm({ ...bookForm, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="author">Author *</Label>
                    <Input
                      id="author"
                      value={bookForm.author}
                      onChange={(e) => setBookForm({ ...bookForm, author: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="isbn">ISBN *</Label>
                    <Input
                      id="isbn"
                      value={bookForm.isbn}
                      onChange={(e) => setBookForm({ ...bookForm, isbn: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="topic">Topic</Label>
                    <Input
                      id="topic"
                      value={bookForm.topic}
                      onChange={(e) => setBookForm({ ...bookForm, topic: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="copies">Copies Available *</Label>
                    <Input
                      id="copies"
                      type="number"
                      min="0"
                      value={bookForm.copies_available}
                      onChange={(e) => setBookForm({ ...bookForm, copies_available: parseInt(e.target.value) || 0 })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location *</Label>
                    <Input
                      id="location"
                      value={bookForm.location}
                      onChange={(e) => setBookForm({ ...bookForm, location: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="summary">Summary</Label>
                  <Textarea
                    id="summary"
                    value={bookForm.summary}
                    onChange={(e) => setBookForm({ ...bookForm, summary: e.target.value })}
                  />
                </div>
                <Button type="submit" className="w-full" disabled={createMutation.isPending || updateMutation.isPending}>
                  {createMutation.isPending || updateMutation.isPending ? 'Saving...' : (editingBook ? 'Update Book' : 'Add Book')}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Books Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Books ({booksData?.total || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : books.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No books found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Author</TableHead>
                  <TableHead>ISBN</TableHead>
                  <TableHead>Topic</TableHead>
                  <TableHead>Copies</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {books.map((book) => (
                  <TableRow key={book.id}>
                    <TableCell className="font-medium">{book.title}</TableCell>
                    <TableCell>{book.author}</TableCell>
                    <TableCell className="font-mono text-sm">{book.isbn}</TableCell>
                    <TableCell>
                      {book.topic && <Badge variant="outline">{book.topic}</Badge>}
                    </TableCell>
                    <TableCell>
                      <Badge variant={book.copies_available > 0 ? 'default' : 'destructive'}>
                        {book.copies_available}
                      </Badge>
                    </TableCell>
                    <TableCell>{book.location}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="icon" onClick={() => openEdit(book)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            if (confirm('Are you sure you want to delete this book?')) {
                              deleteMutation.mutate(book.id);
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
