import { useState } from 'react'
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert } from 'react-native'
import { router } from 'expo-router'
import { LoginSchema } from '@mfj/validators'
import { useAuthStore } from '@/store/auth.store'
import { api } from '@/lib/api'

export default function LoginScreen() {
  const { setToken } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin() {
    const parsed = LoginSchema.safeParse({ email, password })
    if (!parsed.success) {
      Alert.alert('Errore', parsed.error.issues[0]?.message ?? 'Input non valido')
      return
    }
    setLoading(true)
    try {
      const { accessToken } = await api.post<{ accessToken: string }>(
        '/auth/login',
        parsed.data,
      )
      await setToken(accessToken)
      router.replace('/(app)/(tabs)/today')
    } catch (err) {
      Alert.alert('Errore', err instanceof Error ? err.message : 'Login fallito')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View className="flex-1 justify-center bg-white px-6">
      <Text className="mb-2 text-3xl font-bold text-green-700">MyFit Journal</Text>
      <Text className="mb-8 text-gray-500">Accedi al tuo profilo</Text>

      <TextInput
        className="mb-4 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-base"
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TextInput
        className="mb-6 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-base"
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      <TouchableOpacity
        onPress={handleLogin}
        disabled={loading}
        className="items-center rounded-xl bg-green-600 py-3.5"
      >
        {loading ? (
          <ActivityIndicator color="white" />
        ) : (
          <Text className="text-base font-semibold text-white">Accedi</Text>
        )}
      </TouchableOpacity>
    </View>
  )
}
