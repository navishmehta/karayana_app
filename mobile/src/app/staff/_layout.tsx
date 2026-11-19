import { Stack } from 'expo-router';

import { useFreshPermissions } from '@/hooks/useFreshPermissions';
import { useOfflineSync } from '@/hooks/useOfflineSync';
import { usePushSetup } from '@/hooks/usePushSetup';
import { useAppTheme } from '@/theme/ThemeProvider';

/** Staff area: tabs, plus detail and form screens opened on top of them. */
export default function StaffLayout() {
  const { colors } = useAppTheme();
  useFreshPermissions();
  usePushSetup();
  useOfflineSync();
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }} />;
}
