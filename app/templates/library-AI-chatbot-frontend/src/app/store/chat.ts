import { create } from 'zustand';

interface ChatState {
  sessionId: string | null;
  setSessionId: (sessionId: string) => void;
  clearSession: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  setSessionId: (sessionId) => set({ sessionId }),
  clearSession: () => set({ sessionId: null }),
}));
