/** Picks the right font family and line height for the current language (Gurmukhi needs taller lines). */
import { useTranslation } from 'react-i18next';

import { type FontWeight, fonts, fontSizes, lineHeightRatio } from '@/theme/tokens';

export function useTypography() {
  const { i18n } = useTranslation();
  const script = i18n.language === 'pa' ? 'gurmukhi' : 'latin';
  return (size: keyof typeof fontSizes, weight: FontWeight = 'regular') => ({
    fontFamily: fonts[script][weight],
    fontSize: fontSizes[size],
    lineHeight: Math.round(fontSizes[size] * lineHeightRatio[script]),
  });
}
