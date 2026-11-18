import { useTranslation } from 'react-i18next';

import type { Availability } from '@/api/types';
import { Badge } from '@/components/ui';
import { statusTone } from '@/theme/tokens';

export function AvailabilityBadge({ availability }: { availability: Availability }) {
  const { t } = useTranslation();
  return <Badge label={t(`catalogue.availability.${availability}`)} tone={statusTone[availability]} />;
}
