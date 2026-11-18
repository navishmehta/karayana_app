/**
 * Root: loads fonts, saved language and the saved login, then shows the app.
 * Route access: the customer side is always open; login screens only for guests; /staff only for staff.
 * (This only decides which screens show — the server checks every request itself.)
 */
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold } from '@expo-google-fonts/inter';
import {
  NotoSansGurmukhi_400Regular,
  NotoSansGurmukhi_500Medium,
  NotoSansGurmukhi_600SemiBold,
  NotoSansGurmukhi_700Bold,
} from '@expo-google-fonts/noto-sans-gurmukhi';
import { QueryClientProvider } from '@tanstack/react-query';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { useSession } from '@/auth/session';
import { restoreLanguage } from '@/i18n';
import { queryClient } from '@/lib/queryClient';
import { ThemeProvider, useAppTheme } from '@/theme/ThemeProvider';

void SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
    NotoSansGurmukhi_400Regular,
    NotoSansGurmukhi_500Medium,
    NotoSansGurmukhi_600SemiBold,
    NotoSansGurmukhi_700Bold,
  });
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    void Promise.allSettled([restoreLanguage(), useSession.getState().restore()]).then(() => setRestored(true));
  }, []);

  const ready = restored && (fontsLoaded || !!fontError); // a font failure falls back to system fonts
  useEffect(() => {
    if (ready) void SplashScreen.hideAsync();
  }, [ready]);

  if (!ready) return null;

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RootStack />
        </ThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

function RootStack() {
  const { colors, scheme } = useAppTheme();
  const isStaff = useSession((s) => s.status === 'staff');

  return (
    <>
      <StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }}>
        <Stack.Screen name="(customer)" />
        <Stack.Protected guard={!isStaff} redirectTo="/staff">
          <Stack.Screen name="login" />
          <Stack.Screen name="forgot-password" />
        </Stack.Protected>
        <Stack.Protected guard={isStaff} redirectTo="/login">
          <Stack.Screen name="staff" />
        </Stack.Protected>
      </Stack>
    </>
  );
}
