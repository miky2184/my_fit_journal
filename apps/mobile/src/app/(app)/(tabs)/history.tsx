import { useEffect, useState } from 'react'
import { View, Text, FlatList, ActivityIndicator } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { api } from '@/lib/api'
import type { WorkoutSession } from '@mfj/types'

export default function HistoryScreen() {
  const [sessions, setSessions] = useState<WorkoutSession[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<WorkoutSession[]>('/sessions/history')
      .then(setSessions)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <View className="flex-1 items-center justify-center">
        <ActivityIndicator size="large" color="#16a34a" />
      </View>
    )
  }

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="px-5 pb-4 pt-6">
        <Text className="text-2xl font-bold text-gray-900">Storico</Text>
      </View>
      <FlatList
        data={sessions}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingHorizontal: 20, gap: 10 }}
        renderItem={({ item }) => (
          <View className="rounded-2xl bg-white p-4 shadow-sm">
            <Text className="font-semibold text-gray-900">{item.name}</Text>
            <Text className="mt-0.5 text-sm text-gray-500">
              {new Date(item.startedAt).toLocaleDateString('it-IT')}
              {item.durationMinutes ? ` · ${item.durationMinutes} min` : ''}
              {item.kcalBurned ? ` · ${item.kcalBurned} kcal` : ''}
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <Text className="mt-10 text-center text-gray-400">Nessun allenamento completato.</Text>
        }
      />
    </SafeAreaView>
  )
}
