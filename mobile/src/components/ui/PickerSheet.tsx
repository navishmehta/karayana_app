/** Searchable list in a bottom sheet for choosing one item (category, brand, unit, product…). */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, FlatList, Modal, Pressable, StyleSheet, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTypography } from '@/hooks/useTypography';
import { useAppTheme } from '@/theme/ThemeProvider';
import { noWebOutline, radius, spacing, TOUCH_TARGET } from '@/theme/tokens';

import { AppText } from './AppText';
import { Button } from './Button';

export interface PickerItem {
  id: number;
  label: string;
  hint?: string;
}

interface PickerSheetProps {
  visible: boolean;
  title: string;
  items: PickerItem[];
  loading?: boolean;
  selectedId?: number | null;
  onSelect: (item: PickerItem) => void;
  onClose: () => void;
  /** Server-side search: called as the user types. Without it, items are filtered locally. */
  onSearch?: (text: string) => void;
  /** Offer to create a new item with the typed text (e.g. a new brand). */
  onCreate?: (text: string) => void;
  createLabel?: (text: string) => string;
}

export function PickerSheet(props: PickerSheetProps) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const insets = useSafeAreaInsets();
  const typography = useTypography();
  const [text, setText] = useState('');
  const query = text.trim().toLowerCase();
  const items = props.onSearch || !query ? props.items : props.items.filter((i) => i.label.toLowerCase().includes(query));
  const canCreate = props.onCreate && text.trim() && !items.some((i) => i.label.toLowerCase() === query);

  return (
    <Modal visible={props.visible} transparent animationType="slide" onRequestClose={props.onClose} onShow={() => setText('')}>
      <Pressable style={[styles.backdrop, { backgroundColor: colors.overlay }]} onPress={props.onClose} />
      <View style={[styles.sheet, { backgroundColor: colors.surface, paddingBottom: insets.bottom + spacing.md }]}>
        <AppText size="subtitle" weight="bold">
          {props.title}
        </AppText>
        <View style={[styles.search, { borderColor: colors.border }]}>
          <Ionicons name="search" size={18} color={colors.textMuted} />
          <TextInput
            value={text}
            onChangeText={(v) => {
              setText(v);
              props.onSearch?.(v);
            }}
            placeholder={t('staff.common.search')}
            placeholderTextColor={colors.textMuted}
            accessibilityLabel={t('staff.common.search')}
            style={[styles.input, noWebOutline, typography('body'), { color: colors.text }]}
            autoCorrect={false}
          />
        </View>
        {canCreate && <Button title={props.createLabel?.(text.trim()) ?? text} variant="secondary" onPress={() => props.onCreate?.(text.trim())} />}
        {props.loading ? (
          <ActivityIndicator color={colors.primary} style={styles.loading} />
        ) : (
          <FlatList
            data={items}
            keyExtractor={(i) => String(i.id)}
            keyboardShouldPersistTaps="handled"
            ListEmptyComponent={
              <AppText color="textMuted" align="center" style={styles.loading}>
                {t('staff.common.nothingFound')}
              </AppText>
            }
            renderItem={({ item }) => {
              const selected = item.id === props.selectedId;
              return (
                <Pressable
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  onPress={() => props.onSelect(item)}
                  style={[styles.item, { borderBottomColor: colors.border }]}
                >
                  <View style={styles.flex}>
                    <AppText weight={selected ? 'semibold' : 'regular'} color={selected ? 'primary' : 'text'}>
                      {item.label}
                    </AppText>
                    {item.hint && (
                      <AppText size="small" color="textMuted">
                        {item.hint}
                      </AppText>
                    )}
                  </View>
                  {selected && <Ionicons name="checkmark" size={20} color={colors.primary} />}
                </Pressable>
              );
            }}
          />
        )}
      </View>
    </Modal>
  );
}

/** A form field that opens a PickerSheet. */
export function PickerField({ label, value, placeholder, error, onPress, disabled }: {
  label: string;
  value?: string;
  placeholder: string;
  error?: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  const { colors } = useAppTheme();
  return (
    <View style={styles.field}>
      <AppText size="small" weight="medium" color="textMuted">
        {label}
      </AppText>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={label}
        onPress={onPress}
        disabled={disabled}
        style={[styles.box, { borderColor: error ? colors.danger : colors.border, backgroundColor: colors.surface, opacity: disabled ? 0.6 : 1 }]}
      >
        <AppText color={value ? 'text' : 'textMuted'} style={styles.flex} numberOfLines={1}>
          {value || placeholder}
        </AppText>
        <Ionicons name="chevron-down" size={18} color={colors.textMuted} />
      </Pressable>
      {error && (
        <AppText size="small" color="danger">
          {error}
        </AppText>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1 },
  sheet: {
    height: '75%',
    borderTopLeftRadius: radius.xl,
    borderTopRightRadius: radius.xl,
    padding: spacing.lg,
    gap: spacing.md,
    width: '100%',
    maxWidth: 720,
    alignSelf: 'center',
  },
  search: { minHeight: TOUCH_TARGET, flexDirection: 'row', alignItems: 'center', gap: spacing.sm, borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md },
  input: { flex: 1 },
  item: { minHeight: TOUCH_TARGET, flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, borderBottomWidth: StyleSheet.hairlineWidth },
  flex: { flex: 1 },
  loading: { padding: spacing.xl },
  field: { gap: spacing.xs },
  box: { minHeight: TOUCH_TARGET, flexDirection: 'row', alignItems: 'center', gap: spacing.sm, borderWidth: 1.5, borderRadius: radius.md, paddingHorizontal: spacing.md },
});
