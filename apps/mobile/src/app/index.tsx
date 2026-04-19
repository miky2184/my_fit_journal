import { Redirect } from 'expo-router'
import * as SecureStore from 'expo-secure-store'
import { useEffect, useState } from 'react'
import { View, ActivityIndicator } from 'react-native'

export default function Index() {
  const [checking, setChecking] = useState(true)
  const [hasToken, setHasToken] = useState(false)

  useEffect(() => {
    SecureStore.getItemAsync('token').then((token) => {
      setHasToken(!!token)
      setChecking(false)
    })
  }, [])

  if (checking) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#16a34a" />
      </View>
    )
  }

  return <Redirect href={hasToken ? '/(app)/(tabs)/today' : '/(auth)/login'} />
}
