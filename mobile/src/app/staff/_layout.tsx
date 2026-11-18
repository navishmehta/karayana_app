import { Stack } from 'expo-router';

import { useAppTheme } from '@/theme/ThemeProvider';

/** Staff area. Phase 8 (admin) and Phase 9 (seller) add their screens here. */
export default function StaffLayout() {
  const { colors } = useAppTheme();
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }} />;
}
