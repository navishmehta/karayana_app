import {
  activeFilterCount,
  DEFAULT_FILTERS,
  gridColumns,
  localizedName,
  toCatalogueQuery,
} from '@/utils/catalogue';

describe('toCatalogueQuery', () => {
  it('sends only what is set', () => {
    expect(toCatalogueQuery(DEFAULT_FILTERS)).toEqual({ sort: 'name_asc' });
  });

  it('maps every filter to the API parameter names', () => {
    const query = toCatalogueQuery({
      ...DEFAULT_FILTERS,
      search: '  amul ',
      category: 'dairy',
      minPrice: '10',
      maxPrice: '1,000',
      inStock: true,
      onOffer: true,
      featured: true,
      sort: 'price_asc',
    });
    expect(query).toEqual({
      search: 'amul',
      category: 'dairy',
      min_price: 10,
      max_price: 1000,
      in_stock: true,
      on_offer: true,
      featured: true,
      sort: 'price_asc',
    });
  });

  it('ignores invalid prices and never sends max below min', () => {
    expect(toCatalogueQuery({ ...DEFAULT_FILTERS, minPrice: 'abc', maxPrice: '-5' })).toEqual({ sort: 'name_asc' });
    expect(toCatalogueQuery({ ...DEFAULT_FILTERS, minPrice: '100', maxPrice: '50' })).toMatchObject({
      min_price: 100,
      max_price: 100,
    });
  });
});

it('counts active filters for the Filter button', () => {
  expect(activeFilterCount(DEFAULT_FILTERS)).toBe(0);
  expect(activeFilterCount({ ...DEFAULT_FILTERS, search: 'x', inStock: true, sort: 'newest' })).toBe(2);
});

it('chooses 2 columns on phones and more on wide screens', () => {
  expect(gridColumns(360)).toBe(2);
  expect(gridColumns(700)).toBe(4);
  expect(gridColumns(2000)).toBe(5);
});

it('uses the Punjabi category name when the admin entered one', () => {
  const dairy = { name: 'Dairy', name_translations: { pa: 'ਡੇਅਰੀ' } };
  expect(localizedName(dairy, 'pa')).toBe('ਡੇਅਰੀ');
  expect(localizedName(dairy, 'en')).toBe('Dairy');
  expect(localizedName({ name: 'Snacks', name_translations: {} }, 'pa')).toBe('Snacks');
});
