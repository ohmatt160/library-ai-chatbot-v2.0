import axios from 'axios';
import type {
  AuthResponse,
  RegisterResponse,
  LoginCredentials,
  RegisterData,
  User,
  ChatRequest,
  ChatResponse,
  FeedbackRequest,
  FeedbackResponse,
  BookSearchParams,
  BookSearchResponse,
  Activity,
  AdminMetrics,
  AdminUsersResponse,
  ActivityResponse,
  SessionInfo,
  AdminBooksResponse,
  AdminContactsResponse,
  CreateBookRequest,
  BulkBooksRequest,
  CreateContactRequest,
  Book,
  Contact,
  BorrowRequest,
  BorrowRequestsResponse,
  Notification,
  NotificationsResponse,
  BorrowAnalytics,
  ReserveRequest,
  ReservationsResponse,
  ReservationAnalytics,
} from '../types';

const BASE_URL = 'http://localhost:5000/api';

// Create axios instance
export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses (expired/invalid token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const errorCode = error.response?.data?.code;
      if (errorCode === 'token_expired' || errorCode === 'invalid_token') {
        // Clear auth state on token expiry
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('auth-storage');
        // Optionally redirect to login
        window.dispatchEvent(new CustomEvent('auth:expired'));
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (data: RegisterData): Promise<RegisterResponse> => {
    const response = await api.post('/register', data);
    return response.data;
  },

  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/login', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/logout');
  },

  getProfile: async (): Promise<User> => {
    const response = await api.get('/profile');
    return response.data;
  },

  getSession: async (): Promise<SessionInfo> => {
    const response = await api.get('/session');
    return response.data;
  },
};

// Chat API
export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat', request);
    return response.data;
  },

  sendFeedback: async (feedback: FeedbackRequest): Promise<FeedbackResponse> => {
    const response = await api.post('/feedback', feedback);
    return response.data;
  },

  getActivity: async (): Promise<ActivityResponse> => {
    const response = await api.get('/activity');
    return response.data;
  },
};

// Search API
export const searchApi = {
  searchBooks: async (params: BookSearchParams): Promise<BookSearchResponse> => {
    const response = await api.get('/search/books', { params });
    return response.data;
  },
};

// Admin API
export const adminApi = {
  getUsers: async (): Promise<AdminUsersResponse> => {
    const response = await api.get('/admin/users');
    return response.data;
  },

  getActivities: async (): Promise<ActivityResponse> => {
    const response = await api.get('/admin/activities');
    return response.data;
  },

  getMetrics: async (): Promise<AdminMetrics> => {
    const response = await api.get('/admin/metrics');
    return response.data;
  },

  // Books Management
  getBooks: async (page = 1, perPage = 20, search = ''): Promise<AdminBooksResponse> => {
    const response = await api.get('/admin/books', { params: { page, per_page: perPage, q: search } });
    return response.data;
  },

  getBook: async (id: number): Promise<Book> => {
    const response = await api.get(`/admin/books/${id}`);
    return response.data;
  },

  createBook: async (data: CreateBookRequest): Promise<Book> => {
    const response = await api.post('/admin/books', data);
    return response.data;
  },

  updateBook: async (id: number, data: CreateBookRequest): Promise<Book> => {
    const response = await api.put(`/admin/books/${id}`, data);
    return response.data;
  },

  deleteBook: async (id: number): Promise<void> => {
    await api.delete(`/admin/books/${id}`);
  },

  bulkCreateBooks: async (data: BulkBooksRequest): Promise<{ imported: number; failed: number; errors: string[] }> => {
    const response = await api.post('/admin/books/bulk', data);
    return response.data;
  },

  // Contacts Management
  getContacts: async (page = 1, perPage = 20, search = ''): Promise<AdminContactsResponse> => {
    const response = await api.get('/admin/contacts', { params: { page, per_page: perPage, q: search } });
    return response.data;
  },

  getContact: async (id: number): Promise<Contact> => {
    const response = await api.get(`/admin/contacts/${id}`);
    return response.data;
  },

  createContact: async (data: CreateContactRequest): Promise<Contact> => {
    const response = await api.post('/admin/contacts', data);
    return response.data;
  },

  updateContact: async (id: number, data: CreateContactRequest): Promise<Contact> => {
    const response = await api.put(`/admin/contacts/${id}`, data);
    return response.data;
  },

  deleteContact: async (id: number): Promise<void> => {
    await api.delete(`/admin/contacts/${id}`);
  },
};

// ====================== BORROW API ======================

export const borrowApi = {
  // User endpoints
  createRequest: async (bookId: number): Promise<{ status: string; message: string; request: BorrowRequest }> => {
    const response = await api.post('/borrow/request', { book_id: bookId });
    return response.data;
  },

  getMyRequests: async (status?: string): Promise<BorrowRequestsResponse> => {
    const params = status ? { status } : {};
    const response = await api.get('/borrow/my-requests', { params });
    return response.data;
  },

  getRequestDetails: async (requestId: number): Promise<{ request: BorrowRequest; history: any[] }> => {
    const response = await api.get(`/borrow/request/${requestId}`);
    return response.data;
  },

  // Notifications
  getNotifications: async (unreadOnly = false): Promise<NotificationsResponse> => {
    const response = await api.get('/borrow/notifications', { params: { unread: unreadOnly } });
    return response.data;
  },

  markNotificationRead: async (notificationId: number): Promise<void> => {
    await api.post(`/borrow/notifications/${notificationId}/read`);
  },

  markAllNotificationsRead: async (): Promise<void> => {
    await api.post('/borrow/notifications/read-all');
  },

  // Admin endpoints
  getAllRequests: async (status?: string, userId?: string, limit = 50): Promise<BorrowRequestsResponse> => {
    const params: Record<string, any> = { limit };
    if (status) params.status = status;
    if (userId) params.user_id = userId;
    const response = await api.get('/admin/borrow/requests', { params });
    return response.data;
  },

  getPendingRequests: async (): Promise<BorrowRequestsResponse> => {
    const response = await api.get('/admin/borrow/requests/pending');
    return response.data;
  },

  approveRequest: async (requestId: number, pickupDays = 3, notes = ''): Promise<{ status: string; request: BorrowRequest }> => {
    const response = await api.post(`/admin/borrow/approve/${requestId}`, { pickup_days: pickupDays, notes });
    return response.data;
  },

  denyRequest: async (requestId: number, reason: string): Promise<{ status: string; request: BorrowRequest }> => {
    const response = await api.post(`/admin/borrow/deny/${requestId}`, { reason });
    return response.data;
  },

  markPickedUp: async (requestId: number): Promise<{ status: string; request: BorrowRequest }> => {
    const response = await api.post(`/admin/borrow/mark-picked/${requestId}`);
    return response.data;
  },

  markReturned: async (requestId: number): Promise<{ status: string; request: BorrowRequest }> => {
    const response = await api.post(`/admin/borrow/mark-returned/${requestId}`);
    return response.data;
  },

  // Analytics
  getAnalytics: async (days = 30): Promise<{ status: string; analytics: BorrowAnalytics; period_days: number }> => {
    const response = await api.get('/admin/borrow/analytics', { params: { days } });
    return response.data;
  },

  // Bulk operations
  bulkApprove: async (requestIds: number[], pickupDays = 3): Promise<{ status: string; approved_count: number }> => {
    const response = await api.post('/admin/borrow/bulk-approve', { request_ids: requestIds, pickup_days: pickupDays });
    return response.data;
  },

  bulkDeny: async (requestIds: number[], reason: string): Promise<{ status: string; denied_count: number }> => {
    const response = await api.post('/admin/borrow/bulk-deny', { request_ids: requestIds, reason });
    return response.data;
  },

  // ====================== RESERVATION API ======================
  
  // User reservation endpoints
  createReservation: async (bookId: number, notes = ''): Promise<{ status: string; message: string; reservation: ReserveRequest }> => {
    const response = await api.post('/borrow/reserve', { book_id: bookId, notes });
    return response.data;
  },

  getMyReservations: async (status?: string): Promise<ReservationsResponse> => {
    const params = status ? { status } : {};
    const response = await api.get('/borrow/my-reservations', { params });
    return response.data;
  },

  getReservationDetails: async (reservationId: number): Promise<{ reservation: ReserveRequest }> => {
    const response = await api.get(`/borrow/reservations/${reservationId}`);
    return response.data;
  },

  cancelReservation: async (reservationId: number): Promise<{ status: string; message: string }> => {
    const response = await api.delete(`/borrow/reservations/${reservationId}`);
    return response.data;
  },

  // Admin reservation endpoints
  getAllReservations: async (status?: string, page = 1, perPage = 20): Promise<ReservationsResponse> => {
    const params: Record<string, any> = { page, per_page: perPage };
    if (status) params.status = status;
    const response = await api.get('/admin/borrow/reservations', { params });
    return response.data;
  },

  fulfillReservation: async (reservationId: number): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/admin/borrow/reservations/${reservationId}/fulfill`);
    return response.data;
  },

  adminCancelReservation: async (reservationId: number, reason: string): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/admin/borrow/reservations/${reservationId}/cancel`, { reason });
    return response.data;
  },

  expireReservation: async (reservationId: number): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/admin/borrow/reservations/${reservationId}/expire`);
    return response.data;
  },

  getReservationAnalytics: async (days = 30): Promise<{ status: string; analytics: ReservationAnalytics }> => {
    const response = await api.get('/admin/borrow/reservations/analytics', { params: { days } });
    return response.data;
  },
};
