/** Where tapping a notification takes the user (pure, unit-tested). */
export function routeForNotification(data: Record<string, unknown> | undefined): string | null {
  if (!data) return null;
  if (data.type === 'expiry_digest') return '/staff/expiry';
  if (typeof data.product_id === 'number') return `/staff/product/${data.product_id}`;
  return '/staff/notifications';
}
