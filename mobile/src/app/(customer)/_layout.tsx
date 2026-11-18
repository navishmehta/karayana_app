import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { useTypography } from '@/hooks/useTypography';
import { useAppTheme } from '@/theme/ThemeProvider';

type IconName = keyof typeof Ionicons.glyphMap;

const TABS: { name: string; titleKey: string; icon: IconName }[] = [
  { name: 'index', titleKey: 'common.home', icon: 'storefront-outline' },
  { name: 'categories', titleKey: 'catalogue.categories', icon: 'grid-outline' },
  { name: 'search', titleKey: 'catalogue.search', icon: 'search-outline' },
  { name: 'settings', titleKey: 'common.settings', icon: 'settings-outline' },
];

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
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: t(tab.titleKey),
            tabBarIcon: ({ color, size }) => <Ionicons name={tab.icon} size={size} color={String(color)} />,
          }}
        />
      ))}
    </Tabs>
  );
}
