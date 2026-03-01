import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { borrowApi } from '../services/api';
import { BookOpen, Clock, CheckCircle, XCircle, Pickaxe, ArrowLeft, Loader2, Calendar, Bookmark } from 'lucide-react';

const statusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  denied: { label: 'Denied', color: 'bg-red-100 text-red-800', icon: XCircle },
  picked_up: { label: 'Picked Up', color: 'bg-blue-100 text-blue-800', icon: Pickaxe },
  returned: { label: 'Returned', color: 'bg-gray-100 text-gray-800', icon: BookOpen },
};

const reservationStatusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  active: { label: 'Active', color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
  fulfilled: { label: 'Ready for Pickup', color: 'bg-green-100 text-green-800', icon: Pickaxe },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800', icon: XCircle },
  expired: { label: 'Expired', color: 'bg-gray-100 text-gray-800', icon: Calendar },
  pending_ill: { label: 'ILL Request', color: 'bg-purple-100 text-purple-800', icon: BookOpen },
};

export function MyBorrowRequestsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'borrows' | 'reservations'>('borrows');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [reservationFilter, setReservationFilter] = useState<string>('');

  // Borrow requests query
  const { data: borrowData, isLoading: borrowLoading, error: borrowError } = useQuery({
    queryKey: ['myBorrowRequests', statusFilter],
    queryFn: () => borrowApi.getMyRequests(statusFilter || undefined),
    enabled: activeTab === 'borrows',
  });

  // Reservations query
  const { data: reservationData, isLoading: reservationLoading, error: reservationError } = useQuery({
    queryKey: ['myReservations', reservationFilter],
    queryFn: () => borrowApi.getMyReservations(reservationFilter || undefined),
    enabled: activeTab === 'reservations',
  });

  // Cancel reservation mutation
  const cancelReservationMutation = useMutation({
    mutationFn: (reservationId: number) => borrowApi.cancelReservation(reservationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myReservations'] });
    },
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const isLoading = activeTab === 'borrows' ? borrowLoading : reservationLoading;
  const error = activeTab === 'borrows' ? borrowError : reservationError;
  const requests = borrowData?.requests || [];
  const reservations = reservationData?.reservations || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center text-red-600">
        <XCircle className="w-12 h-12 mx-auto mb-4" />
        <p>Failed to load data</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Books</h1>
          <p className="text-muted-foreground">Track your borrow requests and reservations</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('borrows')}
            className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'borrows'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <BookOpen className="w-4 h-4 inline mr-2" />
            Borrow Requests ({requests.length})
          </button>
          <button
            onClick={() => setActiveTab('reservations')}
            className={`px-4 py-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'reservations'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Bookmark className="w-4 h-4 inline mr-2" />
            Reservations ({reservations.length})
          </button>
        </div>
      </div>

      {/* Borrow Requests Tab */}
      {activeTab === 'borrows' && (
        <>
          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setStatusFilter('')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                !statusFilter ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
              }`}
            >
              All ({requests.length})
            </button>
            {Object.entries(statusConfig).map(([status, config]) => {
              const count = requests.filter((r) => r.status === status).length;
              return (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === status ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  {config.label} ({count})
                </button>
              );
            })}
          </div>

          {/* Requests List */}
          {requests.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No borrow requests yet</p>
              <p>Search for books and request to borrow them</p>
            </div>
          ) : (
            <div className="space-y-4">
              {requests.map((request) => {
                const status = statusConfig[request.status];
                const StatusIcon = status.icon;

                return (
                  <div
                    key={request.id}
                    className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg">
                            {request.book?.title || `Book #${request.book_id}`}
                          </h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                            <StatusIcon className="w-3 h-3 inline mr-1" />
                            {status.label}
                          </span>
                        </div>
                        
                        <div className="text-sm text-muted-foreground space-y-1">
                          <p>Author: {request.book?.author || 'N/A'}</p>
                          <p>Requested: {formatDate(request.request_date)}</p>
                          
                          {request.status === 'approved' && request.pickup_deadline && (
                            <p className="text-blue-600 font-medium">
                              Pick up by: {formatDate(request.pickup_deadline)}
                            </p>
                          )}
                          
                          {request.status === 'denied' && request.admin_notes && (
                            <p className="text-red-600">
                              Reason: {request.admin_notes}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Reservations Tab */}
      {activeTab === 'reservations' && (
        <>
          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setReservationFilter('')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                !reservationFilter ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
              }`}
            >
              All ({reservations.length})
            </button>
            {Object.entries(reservationStatusConfig).map(([status, config]) => {
              const count = reservations.filter((r) => r.status === status).length;
              return (
                <button
                  key={status}
                  onClick={() => setReservationFilter(status)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    reservationFilter === status ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  {config.label} ({count})
                </button>
              );
            })}
          </div>

          {/* Reservations List */}
          {reservations.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Bookmark className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No reservations yet</p>
              <p>Search for books and reserve them when unavailable</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reservations.map((reservation) => {
                const status = reservationStatusConfig[reservation.status] || { 
                  label: reservation.status, 
                  color: 'bg-gray-100 text-gray-800', 
                  icon: Clock 
                };
                const StatusIcon = status.icon;

                // Parse OpenLibrary book info from notes if available
                // Get book info from book object (works for both local and external via schema)
                let bookTitle = reservation.book?.title || `Book #${reservation.book_id}`;
                let bookAuthor = reservation.book?.author || 'N/A';
                // Fallback: parse from notes if book data not available (legacy format)
                if (!reservation.book && reservation.notes && reservation.notes.includes('external):')) {
                  const content = reservation.notes.split('external):')[1]?.trim() || '';
                  if (content.includes(' by ')) {
                    const parts = content.split(' by ');
                    bookTitle = parts[0].trim();
                    bookAuthor = parts[1].trim();
                  } else {
                    bookTitle = content;
                  }
                }

                return (
                  <div
                    key={reservation.id}
                    className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg">
                            {bookTitle}
                          </h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                            <StatusIcon className="w-3 h-3 inline mr-1" />
                            {status.label}
                          </span>
                        </div>
                        
                        <div className="text-sm text-muted-foreground space-y-1">
                          <p>Author: {bookAuthor}</p>
                          <p>Reserved: {formatDate(reservation.reserve_date)}</p>
                          <p>Expires: {formatDate(reservation.expiry_date)}</p>
                          
                          {reservation.status === 'fulfilled' && (
                            <p className="text-green-600 font-medium">
                              Your book is ready for pickup! Please visit the library to collect it.
                            </p>
                          )}
                          
                          {reservation.status === 'cancelled' && reservation.admin_notes && (
                            <p className="text-red-600">
                              Reason: {reservation.admin_notes}
                            </p>
                          )}
                          
                          {reservation.notes && (
                            <p className="text-muted-foreground">
                              Notes: {reservation.notes}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      {reservation.status === 'pending' || reservation.status === 'active' || reservation.status === 'pending_ill' ? (
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to cancel this reservation?')) {
                              cancelReservationMutation.mutate(reservation.id);
                            }
                          }}
                          className="px-3 py-1 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50"
                          disabled={cancelReservationMutation.isPending}
                        >
                          Cancel
                        </button>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
