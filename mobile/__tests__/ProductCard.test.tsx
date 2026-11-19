import { fireEvent, render, screen } from '@testing-library/react-native';
import { router } from 'expo-router';

import type { PublicProduct } from '@/api/types';
import { ProductCard } from '@/components/catalogue/ProductCard';
import i18n from '@/i18n';
import { ThemeProvider } from '@/theme/ThemeProvider';

jest.mock('expo-router', () => ({ router: { push: jest.fn() } }));

const product = (overrides: Partial<PublicProduct> = {}): PublicProduct => ({
  slug: 'amul-butter',
  name: 'Amul Butter 500g',
  description: null,
  brand: 'Amul',
  category: { slug: 'dairy', name: 'Dairy', name_translations: {} },
  unit: 'pcs',
  price: '275.00',
  selling_price: '285.00',
  mrp: '290.00',
  discount_percent: '5.17',
  on_offer: true,
  offer_ends_at: null,
  availability: 'in_stock',
  expiry_date: null,
  is_featured: false,
  images: [],
  ...overrides,
});

const renderCard = (p: PublicProduct) =>
  render(
    <ThemeProvider>
      <ProductCard product={p} />
    </ThemeProvider>,
  );

beforeAll(() => i18n.changeLanguage('en'));

it('shows name, brand, price, struck MRP and the discount ribbon', async () => {
  await renderCard(product());
  expect(screen.getByText('Amul Butter 500g')).toBeTruthy();
  expect(screen.getByText('Amul')).toBeTruthy();
  expect(screen.getByText('₹275.00')).toBeTruthy();
  expect(screen.getByText('₹290.00')).toBeTruthy();
  expect(screen.getByText('5.2% off')).toBeTruthy(); // ribbon on the photo (shown once, not repeated under the price)
  expect(screen.queryByText('In stock')).toBeNull(); // only unusual availability is labelled on cards
});

it('labels out-of-stock items and hides MRP when it equals the price', async () => {
  await renderCard(product({ availability: 'out_of_stock', mrp: '275.00', discount_percent: null, on_offer: false }));
  expect(screen.getByText('Out of stock')).toBeTruthy();
  expect(screen.getAllByText('₹275.00')).toHaveLength(1);
});

it('shows an Offer ribbon when the offer has no percentage discount', async () => {
  await renderCard(product({ discount_percent: null }));
  expect(screen.getByText('Offer')).toBeTruthy();
});

it('opens the product page', async () => {
  await renderCard(product());
  await fireEvent.press(screen.getByRole('button', { name: 'Amul Butter 500g' }));
  expect(router.push).toHaveBeenCalledWith({ pathname: '/product/[slug]', params: { slug: 'amul-butter' } });
});

it('shows Punjabi labels', async () => {
  await i18n.changeLanguage('pa');
  await renderCard(product({ availability: 'low_stock' }));
  expect(screen.getByText('ਥੋੜ੍ਹੇ ਹੀ ਬਚੇ ਹਨ')).toBeTruthy();
  expect(screen.getByText('ਪ੍ਰਤੀ pcs')).toBeTruthy();
  await i18n.changeLanguage('en');
});
