import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { borrowApi } from '../services/api';
import {
  BookOpen, Clock, CheckCircle, XCircle, Pickaxe, Loader2,
  TrendingUp, Users, Book, AlertCircle, Bookmark, Calendar
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '../components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';

const statusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  denied: { label: 'Denied', color: 'bg-red-100 text-red-800', icon: XCircle },
  picked_up: { label: 'Picked Up', color: 'bg-blue-100 text-blue-800', icon: Pickaxe },
  returned: { label: 'Returned', color: 'bg-gray-100 text-gray-800', icon: BookOpen },
};

const reservationStatusConfig = {
  active: { label: 'Active', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  fulfilled: { label: 'Ready', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800', icon: XCircle },
  expired: { label: 'Expired', color: 'bg-gray-100 text-gray-800', icon: Calendar },
  pending_ill: { label: 'ILL Request', color: 'bg-purple-100 text-purple-800', icon: BookOpen },
};

export function AdminBorrowPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'borrows' | 'reservations'>('borrows');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [reservationFilter, setReservationFilter] = useState<string>('');
  const [selectedRequest, setSelectedRequest] = useState<any>(null);
  const [selectedReservation, setSelectedReservation] = useState<any>(null);
  const [denyDialogOpen, setDenyDialogOpen] = useState(false);
  const [cancelReservationDialogOpen, setCancelReservationDialogOpen] = useState(false);
  const [denyReason, setDenyReason] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [daysFilter, setDaysFilter] = useState(30);

  // Borrow requests query
  const { data: requestsData, isLoading: borrowLoading } = useQuery({
    queryKey: ['adminBorrowRequests', statusFilter],
    queryFn: () => borrowApi.getAllRequests(statusFilter || undefined),
    enabled: activeTab === 'borrows',
  });

  // Reservations query
  const { data: reservationsData, isLoading: reservationLoading } = useQuery({
    queryKey: ['adminReservations', reservationFilter],
    queryFn: () => borrowApi.getAllReservations(reservationFilter || undefined),
    enabled: activeTab === 'reservations',
  });

  const { data: analyticsData } = useQuery({
    queryKey: ['borrowAnalytics', daysFilter],
    queryFn: () => borrowApi.getAnalytics(daysFilter),
  });

  const { data: reservationAnalyticsData } = useQuery({
    queryKey: ['reservationAnalytics', daysFilter],
    queryFn: () => borrowApi.getReservationAnalytics(daysFilter),
  });

  // Borrow mutations
  const approveMutation = useMutation({
    mutationFn: ({ id, pickupDays }: { id: number; pickupDays: number }) =>
      borrowApi.approveRequest(id, pickupDays),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminBorrowRequests'] });
      queryClient.invalidateQueries({ queryKey: ['borrowAnalytics'] });
      setSelectedRequest(null);
    },
  });

  const denyMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      borrowApi.denyRequest(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminBorrowRequests'] });
      queryClient.invalidateQueries({ queryKey: ['borrowAnalytics'] });
      setDenyDialogOpen(false);
      setDenyReason('');
      setSelectedRequest(null);
    },
  });

  const pickedUpMutation = useMutation({
    mutationFn: (id: number) => borrowApi.markPickedUp(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminBorrowRequests'] });
      queryClient.invalidateQueries({ queryKey: ['borrowAnalytics'] });
    },
  });

  const returnedMutation = useMutation({
    mutationFn: (id: number) => borrowApi.markReturned(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminBorrowRequests'] });
      queryClient.invalidateQueries({ queryKey: ['borrowAnalytics'] });
    },
  });

  // Reservation mutations
  const fulfillReservationMutation = useMutation({
    mutationFn: (id: number) => borrowApi.fulfillReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminReservations'] });
      queryClient.invalidateQueries({ queryKey: ['reservationAnalytics'] });
    },
  });

  const cancelReservationMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      borrowApi.adminCancelReservation(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminReservations'] });
      queryClient.invalidateQueries({ queryKey: ['reservationAnalytics'] });
      setCancelReservationDialogOpen(false);
      setCancelReason('');
      setSelectedReservation(null);
    },
  });

  const expireReservationMutation = useMutation({
    mutationFn: (id: number) => borrowApi.expireReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminReservations'] });
      queryClient.invalidateQueries({ queryKey: ['reservationAnalytics'] });
    },
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const analytics = analyticsData?.analytics;
  const reservationAnalytics = reservationAnalyticsData?.analytics;
  const isLoading = activeTab === 'borrows' ? borrowLoading : reservationLoading;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Borrow Management</h1>
          <p className="text-muted-foreground">Manage book borrowing requests and reservations</p>
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
            Borrow Requests
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
            Reservations
          </button>
        </div>
      </div>

      {/* Borrow Requests Tab */}
      {activeTab === 'borrows' && (
        <>
          {/* Analytics Cards */}
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">Total Requests</span>
                </div>
                <p className="text-3xl font-bold">{analytics.total_requests}</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-5 h-5 text-yellow-600" />
                  <span className="text-sm font-medium">Pending</span>
                </div>
                <p className="text-3xl font-bold">{analytics.requests_by_status?.pending || 0}</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium">Approval Rate</span>
                </div>
                <p className="text-3xl font-bold">{analytics.approval_rate}%</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium">Avg. Approval Time</span>
                </div>
                <p className="text-3xl font-bold">{analytics.average_approval_hours}h</p>
              </div>
            </div>
          )}

          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setStatusFilter('')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                !statusFilter ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
              }`}
            >
              All ({requestsData?.requests?.length || 0})
            </button>
            {Object.entries(statusConfig).map(([status, config]) => {
              const count = requestsData?.requests?.filter((r) => r.status === status).length || 0;
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

          {/* Requests Table */}
          {borrowLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Student</TableHead>
                    <TableHead>Book</TableHead>
                    <TableHead>Request Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requestsData?.requests?.map((request) => {
                    const status = statusConfig[request.status];
                    return (
                      <TableRow key={request.id}>
                        <TableCell className="font-medium">#{request.id}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">
                              {request.user?.first_name} {request.user?.last_name}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              @{request.user?.username}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{request.book?.title}</p>
                            <p className="text-sm text-muted-foreground">
                              {request.book?.author}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(request.request_date)}</TableCell>
                        <TableCell>
                          <Badge className={status.color}>
                            {status.label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            {request.status === 'pending' && (
                              <>
                                <Button
                                  size="sm"
                                  onClick={() => approveMutation.mutate({ id: request.id, pickupDays: 3 })}
                                  disabled={approveMutation.isPending}
                                >
                                  <CheckCircle className="w-4 h-4 mr-1" />
                                  Approve
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => {
                                    setSelectedRequest(request);
                                    setDenyDialogOpen(true);
                                  }}
                                  disabled={denyMutation.isPending}
                                >
                                  <XCircle className="w-4 h-4 mr-1" />
                                  Deny
                                </Button>
                              </>
                            )}
                            {request.status === 'approved' && (
                              <Button
                                size="sm"
                                onClick={() => pickedUpMutation.mutate(request.id)}
                                disabled={pickedUpMutation.isPending}
                              >
                                <Pickaxe className="w-4 h-4 mr-1" />
                                Mark Picked Up
                              </Button>
                            )}
                            {request.status === 'picked_up' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => returnedMutation.mutate(request.id)}
                                disabled={returnedMutation.isPending}
                              >
                                <BookOpen className="w-4 h-4 mr-1" />
                                Mark Returned
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Deny Dialog */}
          <Dialog open={denyDialogOpen} onOpenChange={setDenyDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Deny Borrow Request</DialogTitle>
              </DialogHeader>
              <div className="py-4">
                <label className="block text-sm font-medium mb-2">
                  Reason for denial
                </label>
                <textarea
                  className="w-full p-3 border rounded-lg"
                  rows={3}
                  value={denyReason}
                  onChange={(e) => setDenyReason(e.target.value)}
                  placeholder="Enter reason for denial..."
                />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDenyDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    if (selectedRequest) {
                      denyMutation.mutate({ id: selectedRequest.id, reason: denyReason });
                    }
                  }}
                  disabled={!denyReason || denyMutation.isPending}
                >
                  {denyMutation.isPending ? 'Denying...' : 'Deny Request'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}

      {/* Reservations Tab */}
      {activeTab === 'reservations' && (
        <>
          {/* Analytics Cards */}
          {reservationAnalytics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Bookmark className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">Total Reservations</span>
                </div>
                <p className="text-3xl font-bold">
                  {Object.values(reservationAnalytics.reservations_by_status || {}).reduce((a: any, b: any) => a + b, 0)}
                </p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-5 h-5 text-yellow-600" />
                  <span className="text-sm font-medium">Pending</span>
                </div>
                <p className="text-3xl font-bold">{reservationAnalytics.reservations_by_status?.pending || 0}</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium">Ready for Pickup</span>
                </div>
                <p className="text-3xl font-bold">{reservationAnalytics.reservations_by_status?.fulfilled || 0}</p>
              </div>
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium">Avg. Fulfillment</span>
                </div>
                <p className="text-3xl font-bold">{reservationAnalytics.average_fulfillment_hours}h</p>
              </div>
            </div>
          )}

          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setReservationFilter('')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                !reservationFilter ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
              }`}
            >
              All ({reservationsData?.reservations?.length || 0})
            </button>
            {Object.entries(reservationStatusConfig).map(([status, config]) => {
              const count = reservationsData?.reservations?.filter((r) => r.status === status).length || 0;
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

          {/* Reservations Table */}
          {reservationLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Student</TableHead>
                    <TableHead>Book</TableHead>
                    <TableHead>Reserved Date</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reservationsData?.reservations?.map((reservation) => {
                    const status = reservationStatusConfig[reservation.status] || { 
                      label: reservation.status, 
                      color: 'bg-gray-100 text-gray-800' 
                    };
                    
                    // Parse OpenLibrary book info from notes if available
                    let bookTitle = reservation.book?.title || 'N/A';
                    let bookAuthor = reservation.book?.author || 'N/A';
                    if (reservation.notes && !reservation.book) {
                      try {
                        const notesData = JSON.parse(reservation.notes);
                        bookTitle = notesData.title || bookTitle;
                        bookAuthor = notesData.author || bookAuthor;
                      } catch (e) {
                        // Use default values
                      }
                    }
                    
                    return (
                      <TableRow key={reservation.id}>
                        <TableCell className="font-medium">#{reservation.id}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">
                              {reservation.user?.first_name} {reservation.user?.last_name}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              @{reservation.user?.username}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{bookTitle}</p>
                            <p className="text-sm text-muted-foreground">
                              {bookAuthor}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(reservation.reserve_date)}</TableCell>
                        <TableCell>{formatDate(reservation.expiry_date)}</TableCell>
                        <TableCell>
                          <Badge className={status.color}>
                            {status.label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            {(reservation.status === 'active' || reservation.status === 'pending_ill') && (
                              <>
                                <Button
                                  size="sm"
                                  onClick={() => fulfillReservationMutation.mutate(reservation.id)}
                                  disabled={fulfillReservationMutation.isPending}
                                >
                                  <CheckCircle className="w-4 h-4 mr-1" />
                                  Mark Ready
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => {
                                    setSelectedReservation(reservation);
                                    setCancelReservationDialogOpen(true);
                                  }}
                                  disabled={cancelReservationMutation.isPending}
                                >
                                  <XCircle className="w-4 h-4 mr-1" />
                                  Cancel
                                </Button>
                              </>
                            )}
                            {reservation.status === 'fulfilled' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  if (confirm('Mark this reservation as expired?')) {
                                    expireReservationMutation.mutate(reservation.id);
                                  }
                                }}
                                disabled={expireReservationMutation.isPending}
                              >
                                <Calendar className="w-4 h-4 mr-1" />
                                Expire
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Cancel Reservation Dialog */}
          <Dialog open={cancelReservationDialogOpen} onOpenChange={setCancelReservationDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Cancel Reservation</DialogTitle>
              </DialogHeader>
              <div className="py-4">
                <label className="block text-sm font-medium mb-2">
                  Reason for cancellation
                </label>
                <textarea
                  className="w-full p-3 border rounded-lg"
                  rows={3}
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="Enter reason for cancellation..."
                />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCancelReservationDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    if (selectedReservation) {
                      cancelReservationMutation.mutate({ id: selectedReservation.id, reason: cancelReason });
                    }
                  }}
                  disabled={!cancelReason || cancelReservationMutation.isPending}
                >
                  {cancelReservationMutation.isPending ? 'Cancelling...' : 'Cancel Reservation'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
}
