import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  sessionId: string | null;
  setAuth: (user: User, token: string, refreshToken: string, sessionId: string) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      sessionId: null,
      setAuth: (user, token, refreshToken, sessionId) => {
        // Debug: log auth set events for tracing in browser console
        try {
          console.debug('[auth] setAuth called', { user, token, refreshToken, sessionId });
        } catch (e) {}
        localStorage.setItem('token', token);
        localStorage.setItem('refresh_token', refreshToken);
        set({ user, token, refreshToken, isAuthenticated: true, sessionId });
      },
      setUser: (user) => {
        try {
          console.debug('[auth] setUser', { user });
        } catch (e) {}
        set({ user });
      },
      clearAuth: () => {
        try {
          console.debug('[auth] clearAuth');
        } catch (e) {}
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        set({ user: null, token: null, refreshToken: null, isAuthenticated: false, sessionId: null });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
