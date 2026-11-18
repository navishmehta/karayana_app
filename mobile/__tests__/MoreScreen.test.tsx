import { render, screen } from '@testing-library/react-native';

import type { AuthUser } from '@/api/types';
import MoreScreen from '@/app/staff/(tabs)/more';
import { useSession } from '@/auth/session';
import { PERMISSIONS as P, type Permission } from '@/constants/permissions';
import i18n from '@/i18n';
import { ThemeProvider } from '@/theme/ThemeProvider';

jest.mock('expo-router', () => ({ router: { push: jest.fn(), replace: jest.fn() } }));
jest.mock('react-native-safe-area-context', () => {
  const { View } = jest.requireActual('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) };
});

const user = (role: 'admin' | 'seller', permissions: Permission[] = []): AuthUser => ({
  id: 1, name: 'Raju', email: 'raju@example.com', phone: null, locale: 'en', role, permissions, last_login_at: null,
});

const renderAs = async (u: AuthUser) => {
  useSession.setState({ status: 'staff', user: u });
  await render(
    <ThemeProvider>
      <MoreScreen />
    </ThemeProvider>,
  );
};

beforeAll(() => i18n.changeLanguage('en'));

it('a seller with no permissions sees how to get access, and no admin links', async () => {
  await renderAs(user('seller'));
  expect(screen.getByText('No access yet')).toBeTruthy();
  expect(screen.getByText('Ask the store admin to give you permissions.')).toBeTruthy();
  expect(screen.queryByText('Sellers')).toBeNull();
  expect(screen.queryByText('Categories')).toBeNull();
});

it('a seller sees what they can do, and only the links they may open', async () => {
  await renderAs(user('seller', [P.productsView, P.categoriesView, P.stockView]));
  expect(screen.getByText('What you can do')).toBeTruthy();
  expect(screen.getByText('View stock')).toBeTruthy();
  expect(screen.getByText('Categories')).toBeTruthy();
  expect(screen.queryByText('Store settings')).toBeNull();
});

it('the admin sees the admin tools', async () => {
  await renderAs(user('admin'));
  for (const label of ['Sellers', 'Activity log', 'Store settings', 'Categories']) expect(screen.getByText(label)).toBeTruthy();
  expect(screen.queryByText('What you can do')).toBeNull();
});
