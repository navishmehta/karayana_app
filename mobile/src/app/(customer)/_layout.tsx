import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { useTypography } from '@/hooks/useTypography';
import { useAppTheme } from '@/theme/ThemeProvider';

/** Customer tabs. Phase 7 adds Categories and Search. */
export default function CustomerTabs() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const typography = useTypography();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
        tabBarLabelStyle: typography('caption', 'medium'),
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t('common.home'),
          tabBarIcon: ({ color, size }) => <Ionicons name="storefront-outline" size={size} color={String(color)} />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t('common.settings'),
          tabBarIcon: ({ color, size }) => <Ionicons name="settings-outline" size={size} color={String(color)} />,
        }}
      />
    </Tabs>
  );
}
