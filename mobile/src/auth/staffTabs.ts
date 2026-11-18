/** Staff tabs and the permission each needs. Tabs a user can't use are hidden (the server enforces access anyway). */
import type Ionicons from '@expo/vector-icons/Ionicons';

import type { AuthUser } from '@/api/types';
import { type Permission, PERMISSIONS } from '@/constants/permissions';

import { can } from './permissions';

export interface StaffTab {
  name: 'index' | 'products' | 'stock' | 'expiry' | 'more';
  href: '/staff' | '/staff/products' | '/staff/stock' | '/staff/expiry' | '/staff/more';
  titleKey: string;
  icon: keyof typeof Ionicons.glyphMap;
  permission: Permission | null;
}

export const STAFF_TABS: StaffTab[] = [
  { name: 'index', href: '/staff', titleKey: 'staff.tabs.dashboard', icon: 'speedometer-outline', permission: PERMISSIONS.dashboardView },
  { name: 'products', href: '/staff/products', titleKey: 'staff.tabs.products', icon: 'cube-outline', permission: PERMISSIONS.productsView },
  { name: 'stock', href: '/staff/stock', titleKey: 'staff.tabs.stock', icon: 'swap-vertical-outline', permission: PERMISSIONS.stockView },
  { name: 'expiry', href: '/staff/expiry', titleKey: 'staff.tabs.expiry', icon: 'hourglass-outline', permission: PERMISSIONS.expiryView },
  { name: 'more', href: '/staff/more', titleKey: 'staff.tabs.more', icon: 'menu-outline', permission: null },
];

export const canOpenTab = (user: AuthUser | null, tab: StaffTab) => !tab.permission || can(user, tab.permission);

/** Where a staff member lands: the first tab they may use (More is always available). */
export const firstAllowedTab = (user: AuthUser | null): StaffTab =>
  STAFF_TABS.find((tab) => canOpenTab(user, tab)) ?? STAFF_TABS[STAFF_TABS.length - 1];
