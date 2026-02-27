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
