import { routeForNotification } from '@/utils/notificationRoutes';
import { columnWidth, EMPTY_REPORT_FILTERS, exportFileName, isNumeric, reportQuery } from '@/utils/reports';

describe('reportQuery', () => {
  it('sends only filters the report supports, with valid dates converted', () => {
    const filters = { categoryId: 4, withinDays: 15, dateFrom: '01-11-2026', dateTo: '31-02-2026' };
    expect(reportQuery(filters, ['category_id', 'within_days'])).toEqual({ category_id: 4, within_days: 15 });
    expect(reportQuery(filters, ['category_id', 'date_from', 'date_to'])).toEqual({ category_id: 4, date_from: '2026-11-01' });
    expect(reportQuery(EMPTY_REPORT_FILTERS, ['category_id', 'within_days'])).toEqual({});
  });
});

it('names exports like the server, with DD-MM-YYYY', () => {
  expect(exportFileName('stock', 'xlsx', new Date(2026, 10, 19))).toBe('stock-19-11-2026.xlsx');
});

it('sizes and aligns table columns by kind', () => {
  expect(columnWidth('text', 'product')).toBeGreaterThan(columnWidth('money', 'selling_price'));
  expect(isNumeric('money')).toBe(true);
  expect(isNumeric('date')).toBe(false);
});

describe('notification taps', () => {
  it('opens the product for stock alerts and the expiry tab for the daily check', () => {
    expect(routeForNotification({ type: 'low_stock', product_id: 12 })).toBe('/staff/product/12');
    expect(routeForNotification({ type: 'expiry_digest' })).toBe('/staff/expiry');
    expect(routeForNotification({ type: 'something_new' })).toBe('/staff/notifications');
    expect(routeForNotification(undefined)).toBeNull();
  });
});
