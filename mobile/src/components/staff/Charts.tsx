/** Lightweight, themeable charts built from Views (no chart library needed). */
import { StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { formatQuantity } from '@/utils/format';

const BAR_HEIGHT = 10;
const COLUMN_AREA_HEIGHT = 96;

/** Horizontal bars: label, bar, value. */
export function BarList({ rows }: { rows: { label: string; value: number; display?: string }[] }) {
  const { colors } = useAppTheme();
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <View style={styles.list}>
      {rows.map((row) => (
        <View key={row.label} style={styles.barRow} accessible accessibilityLabel={`${row.label}: ${row.display ?? row.value}`}>
          <View style={styles.barLabel}>
            <AppText size="small" numberOfLines={1}>
              {row.label}
            </AppText>
            <AppText size="small" weight="semibold">
              {row.display ?? formatQuantity(row.value)}
            </AppText>
          </View>
          <View style={[styles.track, { backgroundColor: colors.surfaceAlt }]}>
            <View style={[styles.fill, { width: `${(row.value / max) * 100}%`, backgroundColor: colors.primary }]} />
          </View>
        </View>
      ))}
    </View>
  );
}

/** Paired daily columns (in vs out) for the stock movement chart. */
export function DailyColumns({
  days,
  inLabel,
  outLabel,
}: {
  days: { label: string; in: number; out: number }[];
  inLabel: string;
  outLabel: string;
}) {
  const { colors } = useAppTheme();
  const max = Math.max(1, ...days.flatMap((d) => [d.in, d.out]));
  const step = Math.ceil(days.length / 7); // label every day for a week, fewer for a month
  return (
    <View style={styles.list}>
      <View style={styles.columns}>
        {days.map((d) => (
          <View key={d.label} style={styles.dayGroup} accessible accessibilityLabel={`${d.label}: ${inLabel} ${d.in}, ${outLabel} ${d.out}`}>
            <View style={[styles.column, { height: (d.in / max) * COLUMN_AREA_HEIGHT, backgroundColor: colors.primary }]} />
            <View style={[styles.column, { height: (d.out / max) * COLUMN_AREA_HEIGHT, backgroundColor: colors.accent }]} />
          </View>
        ))}
      </View>
      <View style={styles.columnLabels}>
        {days.map((d, i) => (
          <AppText key={d.label} size="caption" color="textMuted" style={styles.dayLabel}>
            {i % step === 0 ? d.label : ''}
          </AppText>
        ))}
      </View>
      <View style={styles.legend}>
        <Legend color={colors.primary} label={inLabel} />
        <Legend color={colors.accent} label={outLabel} />
      </View>
    </View>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <View style={styles.legendItem}>
      <View style={[styles.swatch, { backgroundColor: color }]} />
      <AppText size="small" color="textMuted">
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.md },
  barRow: { gap: spacing.xs },
  barLabel: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.md },
  track: { height: BAR_HEIGHT, borderRadius: radius.pill, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: radius.pill },
  columns: { height: COLUMN_AREA_HEIGHT, flexDirection: 'row', alignItems: 'flex-end', gap: spacing.xxs },
  dayGroup: { flex: 1, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'center', gap: 1 },
  column: { flex: 1, maxWidth: 10, minHeight: 1, borderTopLeftRadius: 3, borderTopRightRadius: 3 },
  columnLabels: { flexDirection: 'row', gap: spacing.xxs },
  dayLabel: { flex: 1, textAlign: 'center' },
  legend: { flexDirection: 'row', gap: spacing.lg },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  swatch: { width: 12, height: 12, borderRadius: 3 },
});
