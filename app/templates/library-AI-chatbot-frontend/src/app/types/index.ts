// Type definitions for the Library AI Chatbot
// Aligned with backend models and API responses

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'Student' | 'Staff' | 'Faculty' | 'Guest' | 'Admin';
  created_at: string;
  last_login: string | null;
  is_active: boolean;
}

export interface AuthResponse {
  status: string;
  access_token: string;
  refresh_token: string;
  user: User;
  session_id: string;
}

export interface RegisterResponse {
  status: string;
  message: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  user_type?: 'Student' | 'Staff' | 'Faculty' | 'Guest';
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: string;
  feedback?: 'thumbs_up' | 'thumbs_down';
  suggestedFollowUps?: string[];
  confidence?: number;
  processingMethod?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  response_time_ms: number;
  confidence: number;
  processing_method: string;
  suggested_follow_ups: string[];
  timestamp: string;
  user_authenticated: boolean;
  user_type: string;
}

export interface FeedbackRequest {
  message_id: string;
  rating: 'thumbs_up' | 'thumbs_down' | 'neutral';
  comment?: string;
  corrected_response?: string;
}

export interface FeedbackResponse {
  status: string;
  feedback_id: string;
  message: string;
}

export interface Book {
  id: number;
  title: string;
  author: string;
  isbn: string;
  topic?: string;
  copies_available: number;
  location: string;
  summary?: string;
}

export interface BookSearchParams {
  q: string;
  author?: string;
  subject?: string;
}

export interface BookSearchResponse {
  query: string;
  count: number;
  results: Book[];
  source: string;
}

export interface Activity {
  id: number;
  activity_type: string;
  activity_details: Record<string, any> | null;
  timestamp: string;
  ip_address: string;
  // Added by admin endpoint
  username?: string;
  user_type?: string;
}

export interface ActivityResponse {
  activities: Activity[];
  total: number;
  page: number;
  per_page: number;
  total_pages?: number;
}

export interface AdminMetrics {
  user_statistics: Array<{ user_type: string; count: number; date: string }>;
  activity_statistics: Array<{ activity_type: string; count: number; date: string }>;
  chat_statistics: Array<{ date: string; chat_count: number }>;
  system_metrics: Record<string, any>;
  total_users: number;
  total_activities: number;
}

export interface AdminUsersResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
}

export interface SessionInfo {
  session_id: string;
  user_authenticated: boolean;
}

export interface Contact {
  id: number;
  name: string;
  email: string;
  phone?: string;
  subject?: string;
  message: string;
  created_at: string;
  status?: string;
}

export interface AdminBooksResponse {
  books: Book[];
  total: number;
  page: number;
  per_page: number;
}

export interface AdminContactsResponse {
  contacts: Contact[];
  total: number;
  page: number;
  per_page: number;
}

export interface CreateBookRequest {
  title: string;
  author: string;
  isbn: string;
  topic?: string;
  copies_available: number;
  location: string;
  summary?: string;
}

export interface BulkBooksRequest {
  books: CreateBookRequest[];
}

export interface CreateContactRequest {
  name: string;
  email: string;
  phone?: string;
  subject?: string;
  message: string;
}
