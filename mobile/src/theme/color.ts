/** Small colour helpers. */

/** `#RRGGBB` + opacity (0–1) → `#RRGGBBAA`. Used for soft tinted backgrounds from a theme colour. */
export function withAlpha(hex: string, opacity: number): string {
  const alpha = Math.round(Math.min(Math.max(opacity, 0), 1) * 255)
    .toString(16)
    .padStart(2, '0');
  return `${hex.slice(0, 7)}${alpha}`;
}
