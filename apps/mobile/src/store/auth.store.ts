import { create } from 'zustand'
import * as SecureStore from 'expo-secure-store'

interface AuthState {
  token: string | null
  setToken: (token: string) => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: async (token) => {
    await SecureStore.setItemAsync('token', token)
    set({ token })
  },
  logout: async () => {
    await SecureStore.deleteItemAsync('token')
    set({ token: null })
  },
}))
