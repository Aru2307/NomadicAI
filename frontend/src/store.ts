import { create } from 'zustand'

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface State {
  messages: Message[]
  loading: boolean
  addMessage: (m: Message) => void
  setLoading: (v: boolean) => void
  clear: () => void
}

export const useChatStore = create<State>((set) => ({
  messages: [],
  loading: false,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setLoading: (v) => set({ loading: v }),
  clear: () => set({ messages: [] }),
}))
