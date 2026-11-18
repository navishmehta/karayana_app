/** Grouped permission checkboxes with dependencies handled automatically, plus quick presets. */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';

import type { PermissionGroup } from '@/api/staff/types';
import { AppText, Button } from '@/components/ui';
import type { Permission } from '@/constants/permissions';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing, TOUCH_TARGET } from '@/theme/tokens';
import { type DependencyMap, PERMISSION_PRESETS, togglePermission } from '@/utils/permissionEditor';

export function PermissionEditor({
  groups,
  value,
  onChange,
}: {
  groups: PermissionGroup[];
  value: Permission[];
  onChange: (next: Permission[]) => void;
}) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const deps: DependencyMap = Object.fromEntries(groups.flatMap((g) => g.permissions.map((p) => [p.key, p.depends_on])));

  return (
    <View style={styles.wrap}>
      <AppText size="small" color="textMuted">
        {t('staff.sellers.presetHint')}
      </AppText>
      <View style={styles.presets}>
        {(Object.keys(PERMISSION_PRESETS) as (keyof typeof PERMISSION_PRESETS)[]).map((preset) => (
          <Button key={preset} title={t(`staff.sellers.presets.${preset}`)} variant="ghost" onPress={() => onChange(PERMISSION_PRESETS[preset])} />
        ))}
        <Button title={t('staff.sellers.presets.none')} variant="ghost" onPress={() => onChange([])} />
      </View>
      {groups.map((group) => (
        <View key={group.key} style={[styles.group, { borderColor: colors.border }]}>
          <AppText weight="semibold">{group.label}</AppText>
          {group.permissions.map((p) => {
            const checked = value.includes(p.key);
            return (
              <Pressable
                key={p.key}
                accessibilityRole="checkbox"
                accessibilityState={{ checked }}
                onPress={() => onChange(togglePermission(value, p.key, deps))}
                style={styles.item}
              >
                <Ionicons name={checked ? 'checkbox' : 'square-outline'} size={24} color={checked ? colors.primary : colors.textMuted} />
                <AppText style={styles.flex}>{p.label}</AppText>
              </Pressable>
            );
          })}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.md },
  presets: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  group: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: spacing.sm, gap: spacing.xxs },
  item: { minHeight: TOUCH_TARGET - spacing.sm, flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  flex: { flex: 1 },
});
