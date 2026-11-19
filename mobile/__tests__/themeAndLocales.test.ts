import en from '@/i18n/locales/en.json';
import pa from '@/i18n/locales/pa.json';
import { colors, gradients, tints, type ThemeColors } from '@/theme/tokens';

// --- WCAG contrast ------------------------------------------------------------------------------

const luminance = (hex: string) => {
  const [r, g, b] = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

const AA_TEXT = 4.5;
const TEXT_ON: (keyof ThemeColors)[] = ['background', 'surface', 'surfaceAlt'];
const TEXT_COLOURS: (keyof ThemeColors)[] = ['text', 'textMuted', 'primary', 'success', 'warning', 'danger', 'info', 'accent'];

describe.each(['light', 'dark'] as const)('%s theme meets WCAG AA', (scheme) => {
  const c = colors[scheme];
  it.each(TEXT_COLOURS)('%s text is readable on every surface', (fg) => {
    for (const bg of TEXT_ON) expect(contrast(c[fg], c[bg])).toBeGreaterThanOrEqual(AA_TEXT);
  });
  it('button text is readable on primary and danger buttons', () => {
    expect(contrast(c.textOnPrimary, c.primary)).toBeGreaterThanOrEqual(AA_TEXT);
    expect(contrast(c.textOnPrimary, c.danger)).toBeGreaterThanOrEqual(AA_TEXT);
  });
  it('selected chips (primary on primarySoft) are readable', () => {
    expect(contrast(c.primary, c.primarySoft)).toBeGreaterThanOrEqual(AA_TEXT);
  });
  it('text is readable on every stop of every gradient', () => {
    const g = gradients[scheme];
    for (const stop of g.hero) expect(contrast(c.textOnHero, stop)).toBeGreaterThanOrEqual(AA_TEXT);
    for (const stop of g.primary) expect(contrast(c.textOnPrimary, stop)).toBeGreaterThanOrEqual(AA_TEXT);
    for (const stop of g.accent) expect(contrast('#FFFFFF', stop)).toBeGreaterThanOrEqual(AA_TEXT);
  });
  it('category tints keep their text readable', () => {
    for (const tint of tints[scheme]) expect(contrast(tint.fg, tint.bg)).toBeGreaterThanOrEqual(AA_TEXT);
  });
});

// --- Translations ---------------------------------------------------------------------------------

type Tree = { [key: string]: string | Tree };
const flatten = (tree: Tree, prefix = ''): Record<string, string> =>
  Object.entries(tree).reduce<Record<string, string>>((all, [key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return typeof value === 'string' ? { ...all, [path]: value } : { ...all, ...flatten(value, path) };
  }, {});

const enKeys = flatten(en as Tree);
const paKeys = flatten(pa as Tree);
const placeholders = (text: string) => [...text.matchAll(/{{(\w+)}}/g)].map((m) => m[1]).sort();

describe('translations', () => {
  it('English and Punjabi have exactly the same keys', () => {
    expect(Object.keys(paKeys).sort()).toEqual(Object.keys(enKeys).sort());
  });
  it('no translation is empty', () => {
    for (const [key, value] of [...Object.entries(enKeys), ...Object.entries(paKeys)]) {
      expect(`${key}=${value.trim()}`).not.toMatch(/=$/);
    }
  });
  it('placeholders like {{name}} match in both languages', () => {
    for (const [key, value] of Object.entries(enKeys)) {
      expect([key, placeholders(paKeys[key])]).toEqual([key, placeholders(value)]);
    }
  });
  it('Punjabi text is really in Gurmukhi (not left in English by mistake)', () => {
    const gurmukhi = /[਀-੿]/;
    const untranslated = Object.entries(paKeys).filter(
      ([key, value]) => !gurmukhi.test(value) && value === enKeys[key] && /[a-z]{4,}/i.test(value),
    );
    // Allowed: brand / technical words kept in English on purpose.
    const allowed = new Set(['settings.version', 'staff.common.dateHint', 'catalogue.mrpLabel']); // MRP is printed on packs
    expect(untranslated.map(([key]) => key).filter((k) => !allowed.has(k))).toEqual([]);
  });
});
