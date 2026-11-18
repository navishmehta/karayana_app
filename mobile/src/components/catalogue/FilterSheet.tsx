/** Bottom sheet with sort and filters. Changes apply when the user taps "Show results". */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Pressable, ScrollView, StyleSheet, Switch, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppText, Button, TextField } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { type CatalogueFilters, DEFAULT_FILTERS, SORT_OPTIONS, type SortOption } from '@/utils/catalogue';

interface FilterSheetProps {
  visible: boolean;
  filters: CatalogueFilters;
  offersEnabled: boolean;
  onApply: (filters: CatalogueFilters) => void;
  onClose: () => void;
}

export function FilterSheet({ visible, filters, offersEnabled, onApply, onClose }: FilterSheetProps) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const insets = useSafeAreaInsets();
  const [draft, setDraft] = useState(filters);
  const update = (patch: Partial<CatalogueFilters>) => setDraft((d) => ({ ...d, ...patch }));

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} onShow={() => setDraft(filters)}>
      <Pressable style={[styles.backdrop, { backgroundColor: colors.overlay }]} onPress={onClose} accessibilityLabel={t('common.cancel')} />
      <View style={[styles.sheet, { backgroundColor: colors.surface, paddingBottom: insets.bottom + spacing.lg }]}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <AppText size="title" weight="bold">
            {t('catalogue.filters')}
          </AppText>

          <AppText weight="semibold">{t('catalogue.sortBy')}</AppText>
          <View style={styles.wrap} accessibilityRole="radiogroup">
            {SORT_OPTIONS.map((option: SortOption) => {
              const selected = draft.sort === option;
              return (
                <Pressable
                  key={option}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: selected }}
                  onPress={() => update({ sort: option })}
                  style={[
                    styles.option,
                    { borderColor: selected ? colors.primary : colors.border, backgroundColor: selected ? colors.primarySoft : 'transparent' },
                  ]}
                >
                  <AppText size="small" weight={selected ? 'semibold' : 'regular'} color={selected ? 'primary' : 'text'}>
                    {t(`catalogue.sort.${option}`)}
                  </AppText>
                </Pressable>
              );
            })}
          </View>

          <AppText weight="semibold">{t('catalogue.priceRange')}</AppText>
          <View style={styles.row}>
            <View style={styles.flex}>
              <TextField label={t('catalogue.minPrice')} value={draft.minPrice} onChangeText={(v) => update({ minPrice: v })} keyboardType="decimal-pad" />
            </View>
            <View style={styles.flex}>
              <TextField label={t('catalogue.maxPrice')} value={draft.maxPrice} onChangeText={(v) => update({ maxPrice: v })} keyboardType="decimal-pad" />
            </View>
          </View>

          <ToggleRow label={t('catalogue.inStockOnly')} value={draft.inStock} onChange={(v) => update({ inStock: v })} />
          {offersEnabled && <ToggleRow label={t('catalogue.onOfferOnly')} value={draft.onOffer} onChange={(v) => update({ onOffer: v })} />}
          <ToggleRow label={t('catalogue.featuredOnly')} value={draft.featured} onChange={(v) => update({ featured: v })} />
        </ScrollView>

        <View style={styles.actions}>
          <Button
            title={t('catalogue.reset')}
            variant="ghost"
            onPress={() => setDraft({ ...DEFAULT_FILTERS, search: draft.search, category: draft.category })}
          />
          <View style={styles.flex}>
            <Button title={t('catalogue.showResults')} onPress={() => onApply(draft)} fullWidth />
          </View>
        </View>
      </View>
    </Modal>
  );
}

function ToggleRow({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  const { colors } = useAppTheme();
  return (
    <View style={styles.toggle}>
      <AppText style={styles.flex}>{label}</AppText>
      <Switch
        accessibilityLabel={label}
        value={value}
        onValueChange={onChange}
        trackColor={{ true: colors.primary, false: colors.border }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1 },
  sheet: { maxHeight: '85%', borderTopLeftRadius: radius.xl, borderTopRightRadius: radius.xl },
  content: { padding: spacing.xl, gap: spacing.lg, width: '100%', maxWidth: 720, alignSelf: 'center' },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  option: { borderWidth: 1, borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  row: { flexDirection: 'row', gap: spacing.md },
  flex: { flex: 1 },
  toggle: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  actions: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.xl, width: '100%', maxWidth: 720, alignSelf: 'center' },
});
