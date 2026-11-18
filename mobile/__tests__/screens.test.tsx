/** Key screens render in every theme × language combination, with the right language showing. */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react-native';

import type { PublicProduct, PublicStore } from '@/api/types';
import CustomerHome from '@/app/(customer)/index';
import ProductScreen from '@/app/product/[slug]';
import LoginScreen from '@/app/login';
import DashboardScreen from '@/app/staff/(tabs)/index';
import { useSession } from '@/auth/session';
import i18n from '@/i18n';
import { ThemeProvider } from '@/theme/ThemeProvider';

jest.mock('expo-router', () => ({
  router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => true },
  useLocalSearchParams: () => ({ slug: 'fresh-milk' }),
  Redirect: () => null,
}));
jest.mock('react-native-safe-area-context', () => {
  const { View } = jest.requireActual('react-native');
  return { SafeAreaView: View, useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) };
});

const store: PublicStore = {
  name: 'Ramesh Karayana Store', tagline: 'Fresh every day', logo_url: null, logo_thumb_url: null, phone: '9876500000',
  whatsapp: '9876500000', address: 'Main Bazaar', hours: '8 AM – 10 PM', offers_enabled: true, currency: 'INR',
};
const milk: PublicProduct = {
  slug: 'fresh-milk', name: 'Fresh Milk 1L', description: 'Full cream', brand: 'Verka',
  category: { slug: 'dairy', name: 'Dairy', name_translations: { pa: 'ਡੇਅਰੀ' } }, unit: 'pcs', price: '65.00',
  selling_price: '68.00', mrp: '70.00', discount_percent: '7.14', on_offer: true, offer_ends_at: '2026-11-21',
  availability: 'low_stock', expiry_date: '2026-11-25', is_featured: true, images: [],
};

jest.mock('@/hooks/useCatalogue', () => {
  const ok = (data: unknown) => ({ data, isPending: false, isError: false, isSuccess: true, isRefetching: false, refetch: jest.fn() });
  return {
    useStoreInfo: () => ok(store),
    useCategories: () => ok([{ ...milk.category, description: null, image_url: null, image_thumb_url: null, products_count: 1 }]),
    useHighlights: () => ok([milk]),
    useProduct: () => ok(milk),
  };
});
jest.mock('@/hooks/useStaff', () => {
  const ok = (data: unknown) => ({ data, isPending: false, isError: false, isRefetching: false, refetch: jest.fn() });
  return {
    useDashboard: () =>
      ok({
        products_total: 12, products_active: 11, categories_total: 10, sellers_total: 2,
        stock: { total_quantity: '230.000', low_stock: 3, out_of_stock: 1 },
        expiry: { expired_batches: 1, expiring_batches: 2, expiring_within_days: 7 },
        value: { purchase_cost: '15000.00', selling_value: '19000.00' },
        stock_by_category: [{ id: 1, name: 'Dairy', products: 4, quantity: '40.000' }],
        movements: [{ day: '2026-11-19', stock_in: '10.000', stock_out: '4.000' }],
        recent_products: [], recent_movements: [],
      }),
    useUnreadCount: () => ok(3),
  };
});

const COMBOS = [
  ['light', 'en'],
  ['dark', 'en'],
  ['light', 'pa'],
  ['dark', 'pa'],
] as const;

const renderIn = async (ui: React.ReactElement, theme: 'light' | 'dark', language: 'en' | 'pa') => {
  await i18n.changeLanguage(language);
  await render(
    <QueryClientProvider client={new QueryClient()}>
      <ThemeProvider initialPreference={theme}>{ui}</ThemeProvider>
    </QueryClientProvider>,
  );
};

afterAll(() => i18n.changeLanguage('en'));

describe.each(COMBOS)('%s theme, %s', (theme, language) => {
  const pa = language === 'pa';

  it('customer home', async () => {
    await renderIn(<CustomerHome />, theme, language);
    expect(screen.getByText('Ramesh Karayana Store')).toBeTruthy(); // store name is shown as entered
    expect(screen.getByText(pa ? 'ਖਾਸ ਆਫ਼ਰ' : 'Special offers')).toBeTruthy();
    expect(screen.getByText(pa ? 'ਡੇਅਰੀ' : 'Dairy')).toBeTruthy(); // category name translated by the admin
  });

  it('product page', async () => {
    await renderIn(<ProductScreen />, theme, language);
    expect(screen.getAllByText('Fresh Milk 1L').length).toBeGreaterThan(0); // product names are never translated
    expect(screen.getByText('₹65.00')).toBeTruthy();
    expect(screen.getByText(pa ? 'ਥੋੜ੍ਹੇ ਹੀ ਬਚੇ ਹਨ' : 'Only a few left')).toBeTruthy();
    expect(screen.getByText('25-11-2026')).toBeTruthy(); // DD-MM-YYYY
  });

  it('login', async () => {
    await renderIn(<LoginScreen />, theme, language);
    expect(screen.getAllByText(pa ? 'ਸਟਾਫ਼ ਲੌਗਇਨ' : 'Staff login').length).toBeGreaterThan(0);
  });

  it('staff dashboard', async () => {
    useSession.setState({
      status: 'staff',
      user: { id: 1, name: 'Ramesh', email: 'a@example.com', phone: null, locale: language, role: 'admin', permissions: [], last_login_at: null },
    });
    await renderIn(<DashboardScreen />, theme, language);
    expect(screen.getByText(pa ? 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ, Ramesh' : 'Hello, Ramesh')).toBeTruthy();
    expect(screen.getByText('₹15,000.00')).toBeTruthy(); // Indian grouping in both languages
    expect(screen.getByText(pa ? 'ਘੱਟ ਸਟਾਕ' : 'Low stock')).toBeTruthy();
  });
});
