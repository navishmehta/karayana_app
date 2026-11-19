import type { TextStyle } from 'react-native';

/**
 * Design tokens: every colour, size and font used by the app is defined here.
 * Dark mode is its own palette (deep green-black surfaces, softened accents), not just black.
 * Gradients, tints and shadows give the app its premium look; change them here only.
 */

const palette = {
  green50: '#E7F6EE',
  green300: '#4FD192',
  green500: '#16A063',
  green600: '#0F7A4A',
  green700: '#0B5E39',
  green800: '#0A5235',
  greenText: '#12784A', // passes 4.5:1 on every light surface (WCAG AA)
  teal300: '#3CC9B5',
  teal700: '#0E7C6B',
  saffron400: '#FBBF24',
  saffron500: '#F59E0B',
  saffronText: '#C2410C', // deep saffron for text/badges on light surfaces (AA)
  saffronDeep: '#B45309',
  amberText: '#A35207',
  red400: '#F87171',
  redText: '#C81E1E', // passes 4.5:1 on every light surface and under white button text
  blue400: '#60A5FA',
  blue600: '#2563EB',
  mist50: '#F4F7F5',
  mist100: '#EDF2EF',
  mist200: '#E2E9E5',
  grey400: '#9AABA3',
  grey600: '#56665E',
  grey900: '#0F1B15',
  ink950: '#080D0B',
  ink900: '#0E1412',
  ink850: '#111915',
  ink800: '#18221D',
  ink700: '#24302A',
  ink100: '#EAF2EE',
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
  /** Text on the green hero gradients (white in both themes). */
  textOnHero: string;
  primary: string;
  primaryPressed: string;
  primarySoft: string;
  accent: string;
  success: string;
  warning: string;
  danger: string;
  info: string;
  overlay: string;
  /** Tint used for soft shadows. */
  shadow: string;
}

export const colors: Record<ColorScheme, ThemeColors> = {
  light: {
    background: palette.mist50,
    surface: palette.white,
    surfaceAlt: palette.mist100,
    border: palette.mist200,
    text: palette.grey900,
    textMuted: palette.grey600,
    textOnPrimary: palette.white,
    textOnHero: palette.white,
    primary: palette.green600,
    primaryPressed: palette.green700,
    primarySoft: palette.green50,
    accent: palette.saffronText,
    success: palette.greenText,
    warning: palette.amberText,
    danger: palette.redText,
    info: palette.blue600,
    overlay: 'rgba(8, 13, 11, 0.5)',
    shadow: '#0B3D2A',
  },
  dark: {
    background: palette.ink950,
    surface: palette.ink850,
    surfaceAlt: palette.ink800,
    border: palette.ink700,
    text: palette.ink100,
    textMuted: palette.grey400,
    textOnPrimary: palette.ink900,
    textOnHero: palette.white,
    primary: palette.green300,
    primaryPressed: palette.green500,
    primarySoft: '#14301F',
    accent: palette.saffron400,
    success: palette.green300,
    warning: palette.saffron400,
    danger: palette.red400,
    info: palette.blue400,
    overlay: 'rgba(0, 0, 0, 0.65)',
    shadow: '#000000',
  },
};

/** Gradient colour stops (start → end). Text on each must stay readable (checked by the contrast tests). */
export interface ThemeGradients {
  /** Big header areas (customer home, staff dashboard, login). Text: textOnHero. */
  hero: readonly [string, string, ...string[]];
  /** Primary buttons. Text: textOnPrimary. */
  primary: readonly [string, string, ...string[]];
  /** Offer / discount highlights. Text: white. */
  accent: readonly [string, string, ...string[]];
}

export const gradients: Record<ColorScheme, ThemeGradients> = {
  light: {
    hero: [palette.green800, palette.green600, palette.teal700],
    primary: [palette.green600, palette.teal700],
    accent: [palette.saffronText, palette.saffronDeep],
  },
  dark: {
    hero: ['#0B3D2A', '#0F5C40', '#0D5F55'],
    primary: [palette.green300, palette.teal300],
    accent: [palette.saffronText, palette.saffronDeep],
  },
};

/** Soft colour pairs (background, foreground) that give categories and tiles their own look. */
export interface Tint {
  bg: string;
  fg: string;
}

export const tints: Record<ColorScheme, readonly Tint[]> = {
  light: [
    { bg: '#E7F6EE', fg: '#0F7A4A' }, // emerald
    { bg: '#FEF3E2', fg: '#B45309' }, // amber
    { bg: '#FDECEF', fg: '#BE123C' }, // rose
    { bg: '#E8F1FD', fg: '#1D4ED8' }, // sky
    { bg: '#F1ECFD', fg: '#6D28D9' }, // violet
    { bg: '#E4F6F4', fg: '#0F766E' }, // teal
  ],
  dark: [
    { bg: '#12291E', fg: '#4FD192' },
    { bg: '#2E2210', fg: '#FBBF24' },
    { bg: '#2E1419', fg: '#FB7185' },
    { bg: '#11223A', fg: '#60A5FA' },
    { bg: '#221A38', fg: '#A78BFA' },
    { bg: '#0F2A28', fg: '#2DD4BF' },
  ],
};

/** Picks a tint by position, so neighbouring items get different colours. */
export const tintAt = (scheme: ColorScheme, index: number): Tint => tints[scheme][index % tints[scheme].length];

export const spacing = { xxs: 2, xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 } as const;

export const radius = { sm: 10, md: 14, lg: 20, xl: 28, pill: 999 } as const;

/**
 * Text inputs draw their own focus border, so the browser's default focus rectangle is turned off on the web.
 * (`outlineStyle` only matters on the web; native platforms ignore it.)
 */
// React Native's types only list visible outline styles, so the web-only value is cast here, in one place.
export const noWebOutline = { outlineStyle: 'none' } as unknown as TextStyle;

/** Minimum touch target (accessibility). */
export const TOUCH_TARGET = 48;

/** Chips look slimmer than buttons; an invisible margin (hitSlop) still makes them TOUCH_TARGET tall to tap. */
export const CHIP_HEIGHT = 40;
export const CHIP_HIT_SLOP = (TOUCH_TARGET - CHIP_HEIGHT) / 2;

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

/** Shadow depth for cards and floating elements. Light mode: soft green-tinted shadows. Dark mode: borders do the work. */
export const elevation = {
  none: 0,
  low: 1,
  medium: 2,
  high: 3,
} as const;

export type Elevation = keyof typeof elevation;

const SHADOWS = {
  none: { opacity: 0, radius: 0, y: 0, android: 0 },
  low: { opacity: 0.06, radius: 8, y: 2, android: 1 },
  medium: { opacity: 0.09, radius: 18, y: 8, android: 3 },
  high: { opacity: 0.16, radius: 28, y: 14, android: 8 },
} as const;

export function shadow(level: Elevation, color: string, scheme: ColorScheme) {
  const s = SHADOWS[level];
  const strength = scheme === 'dark' ? 2.5 : 1; // dark backgrounds need a stronger shadow to show at all
  return {
    shadowColor: color,
    shadowOpacity: Math.min(s.opacity * strength, 0.5),
    shadowRadius: s.radius,
    shadowOffset: { width: 0, height: s.y },
    elevation: s.android,
  };
}

/** Coloured glow under primary buttons and hero cards. */
export const glow = (color: string) => ({
  shadowColor: color,
  shadowOpacity: 0.32,
  shadowRadius: 14,
  shadowOffset: { width: 0, height: 6 },
  elevation: 4,
});

/** Animation timings (ms) and spring settings, shared by every animated component. */
export const motion = {
  pressScale: 0.97,
  spring: { damping: 18, stiffness: 260, mass: 0.6 },
  enterStaggerMs: 55,
  enterMaxDelayMs: 440,
  pulseMs: 900,
} as const;
