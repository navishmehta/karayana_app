import { Text, type TextProps } from 'react-native';

import { useTypography } from '@/hooks/useTypography';
import { useAppTheme } from '@/theme/ThemeProvider';
import type { FontWeight, fontSizes, ThemeColors } from '@/theme/tokens';

export interface AppTextProps extends TextProps {
  size?: keyof typeof fontSizes;
  weight?: FontWeight;
  color?: keyof ThemeColors;
  align?: 'left' | 'center' | 'right';
}

/** All text in the app goes through this, so fonts, colours and line heights stay consistent. */
export function AppText({ size = 'body', weight = 'regular', color = 'text', align, style, ...rest }: AppTextProps) {
  const { colors } = useAppTheme();
  const typography = useTypography();
  return <Text style={[typography(size, weight), { color: colors[color], textAlign: align }, style]} {...rest} />;
}
