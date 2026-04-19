import { useEffect, useState } from 'react'
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { router } from 'expo-router'
import { api } from '@/lib/api'
import type { WorkoutPlan } from '@mfj/types'

export default function TodayScreen() {
  const [workouts, setWorkouts] = useState<WorkoutPlan[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<WorkoutPlan[]>('/workouts')
      .then(setWorkouts)
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
        <Text className="text-2xl font-bold text-gray-900">Le tue schede</Text>
        <Text className="mt-1 text-sm text-gray-500">Seleziona una scheda per iniziare</Text>
      </View>

      <FlatList
        data={workouts}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingHorizontal: 20, gap: 12 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            className="rounded-2xl bg-white p-5 shadow-sm"
            onPress={() =>
              router.push({
                pathname: '/(app)/workout/[id]',
                params: { id: item.id },
              })
            }
          >
            <View className="flex-row items-center justify-between">
              <Text className="text-base font-semibold text-gray-900">{item.name}</Text>
              <CategoryBadge category={item.category} />
            </View>
            <Text className="mt-1 text-sm text-gray-500">
              {item.estimatedMinutes} min · {item.exercises.length} esercizi
            </Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <Text className="mt-10 text-center text-gray-400">
            Nessuna scheda. Creane una dal desktop.
          </Text>
        }
      />
    </SafeAreaView>
  )
}

function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    gym: 'bg-blue-100 text-blue-700',
    swimming: 'bg-cyan-100 text-cyan-700',
    running: 'bg-orange-100 text-orange-700',
    cycling: 'bg-yellow-100 text-yellow-700',
    other: 'bg-gray-100 text-gray-600',
  }
  return (
    <View className={`rounded-full px-2 py-0.5 ${colors[category] ?? colors['other']}`}>
      <Text className="text-xs font-medium capitalize">{category}</Text>
    </View>
  )
}
