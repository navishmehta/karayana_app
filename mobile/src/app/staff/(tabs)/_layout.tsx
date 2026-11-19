import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { canOpenTab, STAFF_TABS } from '@/auth/staffTabs';
import { useSession } from '@/auth/session';
import { TabIcon, tabHaptics, useTabBarOptions } from '@/components/ui/TabBar';

export default function StaffTabs() {
  const { t } = useTranslation();
  const tabBarOptions = useTabBarOptions();
  const user = useSession((s) => s.user);

  return (
    <Tabs
      screenOptions={tabBarOptions}
      screenListeners={tabHaptics}
    >
      {STAFF_TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: t(tab.titleKey),
            href: canOpenTab(user, tab) ? undefined : null, // hide tabs the user can't use
            tabBarIcon: ({ color, focused }) => <TabIcon icon={tab.icon} focused={focused} color={String(color)} />,
          }}
        />
      ))}
    </Tabs>
  );
}
