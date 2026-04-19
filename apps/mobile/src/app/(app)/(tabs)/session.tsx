import { View, Text } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

export default function SessionScreen() {
  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="px-5 pt-6">
        <Text className="text-2xl font-bold text-gray-900">Allenamento attivo</Text>
        <Text className="mt-2 text-gray-500">
          Avvia una sessione dalla scheda "Oggi" per iniziare.
        </Text>
      </View>
    </SafeAreaView>
  )
}
