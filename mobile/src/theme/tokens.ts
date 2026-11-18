/**
 * Design tokens: every colour, size and font used by the app is defined here.
 * Dark mode is its own palette (soft slate-green surfaces, softened accents), not just black.
 */

const palette = {
  green50: '#E8F5EE',
  green100: '#C9E9D7',
  green500: '#16A063',
  green600: '#0F7A4A',
  green700: '#0B5E39',
  greenText: '#12784A', // passes 4.5:1 on every light surface (WCAG AA)
  green300: '#4FD192',
  saffron400: '#FBBF24',
  saffron500: '#F59E0B',
  saffron600: '#D97706',
  saffronText: '#C2410C', // deep saffron for text/badges on light surfaces (AA)
  amberText: '#A35207',
  red400: '#F87171',
  red600: '#DC2626',
  redText: '#C81E1E', // passes 4.5:1 on every light surface and under white button text
  blue400: '#60A5FA',
  blue600: '#2563EB',
  grey50: '#F7F8F6',
  grey100: '#EEF1EE',
  grey200: '#E3E8E4',
  grey400: '#9AABA3',
  grey600: '#5B6B63',
  grey900: '#14211B',
  ink900: '#0E1412',
  ink800: '#161E1B',
  ink700: '#1E2824',
  ink600: '#2A3631',
  ink100: '#E8F0EC',
  white: '#FFFFFF',
} as const;

export type ColorScheme = 'light' | 'dark';

export interface ThemeColors {
  background: string;
  surface: string;
  surfaceAlt: string;
  border: string;
  text: string;
  textMuted: string;
  textOnPrimary: string;
  primary: string;
  primaryPressed: string;
  primarySoft: string;
  accent: string;
  success: string;
  warning: string;
  danger: string;
  info: string;
  overlay: string;
}

export const colors: Record<ColorScheme, ThemeColors> = {
  light: {
    background: palette.grey50,
    surface: palette.white,
    surfaceAlt: palette.grey100,
    border: palette.grey200,
    text: palette.grey900,
    textMuted: palette.grey600,
    textOnPrimary: palette.white,
    primary: palette.green600,
    primaryPressed: palette.green700,
    primarySoft: palette.green50,
    accent: palette.saffronText,
    success: palette.greenText,
    warning: palette.amberText,
    danger: palette.redText,
    info: palette.blue600,
    overlay: 'rgba(14, 20, 18, 0.45)',
  },
  dark: {
    background: palette.ink900,
    surface: palette.ink800,
    surfaceAlt: palette.ink700,
    border: palette.ink600,
    text: palette.ink100,
    textMuted: palette.grey400,
    textOnPrimary: palette.ink900,
    primary: palette.green300,
    primaryPressed: palette.green500,
    primarySoft: '#173326',
    accent: palette.saffron400,
    success: palette.green300,
    warning: palette.saffron400,
    danger: palette.red400,
    info: palette.blue400,
    overlay: 'rgba(0, 0, 0, 0.6)',
  },
};

export const spacing = { xxs: 2, xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 } as const;

export const radius = { sm: 8, md: 12, lg: 16, xl: 24, pill: 999 } as const;

/** Minimum touch target (accessibility). */
export const TOUCH_TARGET = 48;

export const fontSizes = { caption: 12, small: 14, body: 16, subtitle: 18, title: 22, heading: 28, display: 34 } as const;

export type FontWeight = 'regular' | 'medium' | 'semibold' | 'bold';

/** Loaded font family names, per script. Gurmukhi needs taller lines than Latin. */
export const fonts = {
  latin: {
    regular: 'Inter_400Regular',
    medium: 'Inter_500Medium',
    semibold: 'Inter_600SemiBold',
    bold: 'Inter_700Bold',
  },
  gurmukhi: {
    regular: 'NotoSansGurmukhi_400Regular',
    medium: 'NotoSansGurmukhi_500Medium',
    semibold: 'NotoSansGurmukhi_600SemiBold',
    bold: 'NotoSansGurmukhi_700Bold',
  },
} as const satisfies Record<string, Record<FontWeight, string>>;

export const lineHeightRatio = { latin: 1.35, gurmukhi: 1.6 } as const;

/** Colours for stock / expiry states, used by badges. */
export const statusTone = {
  in_stock: 'success',
  low_stock: 'warning',
  out_of_stock: 'danger',
  expired: 'danger',
  critical: 'danger',
  warning: 'warning',
  notice: 'info',
  safe: 'success',
  no_expiry: 'textMuted',
} as const satisfies Record<string, keyof ThemeColors>;
