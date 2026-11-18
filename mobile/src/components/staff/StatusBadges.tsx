import { useTranslation } from 'react-i18next';

import type { ExpiryBucket, StockStatus } from '@/api/staff/types';
import { Badge } from '@/components/ui';
import { statusTone } from '@/theme/tokens';

export function StockBadge({ status }: { status: StockStatus }) {
  const { t } = useTranslation();
  return <Badge label={t(`staff.stockStatus.${status}`)} tone={statusTone[status]} />;
}

/** "Expired 2 days ago", "Expires today", "5 days left", "No expiry". */
export function ExpiryBadge({ bucket, days }: { bucket: ExpiryBucket; days: number | null }) {
  const { t } = useTranslation();
  let label: string;
  if (days === null) label = t('staff.expiry.noExpiry');
  else if (days < 0) label = t('staff.expiry.expiredAgo', { count: -days });
  else if (days === 0) label = t('staff.expiry.expiresToday');
  else label = t('staff.expiry.daysLeft', { count: days });
  return <Badge label={label} tone={statusTone[bucket]} />;
}
