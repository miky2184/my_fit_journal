import { Tabs } from 'expo-router'
import { Dumbbell, CalendarDays, History } from 'lucide-react-native'

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#16a34a',
        tabBarInactiveTintColor: '#9ca3af',
        tabBarStyle: { borderTopColor: '#e5e7eb' },
      }}
    >
      <Tabs.Screen
        name="today"
        options={{
          title: "Oggi",
          tabBarIcon: ({ color, size }) => <CalendarDays color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="session"
        options={{
          title: 'Allenamento',
          tabBarIcon: ({ color, size }) => <Dumbbell color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'Storico',
          tabBarIcon: ({ color, size }) => <History color={color} size={size} />,
        }}
      />
    </Tabs>
  )
}
