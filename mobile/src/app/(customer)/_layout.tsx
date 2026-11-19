import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { TabIcon, tabHaptics, useTabBarOptions } from '@/components/ui/TabBar';

type IconName = keyof typeof Ionicons.glyphMap;

const TABS: { name: string; titleKey: string; icon: IconName }[] = [
  { name: 'index', titleKey: 'common.home', icon: 'storefront-outline' },
  { name: 'categories', titleKey: 'catalogue.categories', icon: 'grid-outline' },
  { name: 'search', titleKey: 'catalogue.search', icon: 'search-outline' },
  { name: 'settings', titleKey: 'common.settings', icon: 'settings-outline' },
];

export default function CustomerTabs() {
  const { t } = useTranslation();
  const tabBarOptions = useTabBarOptions();

  return (
    <Tabs
      screenOptions={tabBarOptions}
      screenListeners={tabHaptics}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: t(tab.titleKey),
            tabBarIcon: ({ color, focused }) => <TabIcon icon={tab.icon} focused={focused} color={String(color)} />,
          }}
        />
      ))}
    </Tabs>
  );
}
