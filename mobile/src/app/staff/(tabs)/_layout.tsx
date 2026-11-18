import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { canOpenTab, STAFF_TABS } from '@/auth/staffTabs';
import { useSession } from '@/auth/session';
import { useTypography } from '@/hooks/useTypography';
import { useAppTheme } from '@/theme/ThemeProvider';

export default function StaffTabs() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const typography = useTypography();
  const user = useSession((s) => s.user);

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
      {STAFF_TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: t(tab.titleKey),
            href: canOpenTab(user, tab) ? undefined : null, // hide tabs the user can't use
            tabBarIcon: ({ color, size }) => <Ionicons name={tab.icon} size={size} color={String(color)} />,
          }}
        />
      ))}
    </Tabs>
  );
}
