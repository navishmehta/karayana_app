import type { PropsWithChildren } from 'react';
import { KeyboardAvoidingView, Platform, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView, type Edge } from 'react-native-safe-area-context';

import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';

interface ScreenProps extends PropsWithChildren {
  scroll?: boolean;
  edges?: Edge[];
  refreshing?: boolean;
  onRefresh?: () => void;
  center?: boolean;
}

/** Page wrapper: safe areas, theme background, keyboard handling, pull-to-refresh and a max width on web. */
export function Screen({ children, scroll = true, edges = ['top'], refreshing, onRefresh, center }: ScreenProps) {
  const { colors } = useAppTheme();
  const content = <View style={[styles.content, center && styles.center]}>{children}</View>;

  return (
    <SafeAreaView edges={edges} style={[styles.root, { backgroundColor: colors.background }]}>
      <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        {scroll ? (
          <ScrollView
            contentContainerStyle={styles.scroll}
            keyboardShouldPersistTaps="handled"
            refreshControl={
              onRefresh ? (
                <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
              ) : undefined
            }
          >
            {content}
          </ScrollView>
        ) : (
          content
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const MAX_CONTENT_WIDTH = 720;

const styles = StyleSheet.create({
  root: { flex: 1 },
  scroll: { flexGrow: 1 },
  content: {
    flexGrow: 1,
    width: '100%',
    maxWidth: MAX_CONTENT_WIDTH,
    alignSelf: 'center',
    padding: spacing.lg,
    gap: spacing.lg,
  },
  center: { justifyContent: 'center' },
});
