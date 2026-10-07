/**
 * Art direction becomes a runtime theme. The brand system provides
 * constraints; the production's art_direction provides the expression.
 * No permanent house look is hard-coded here.
 */
import type {ThemeProps} from '../runtime/props';

export interface ArtDirectionInput {
  palette_discipline?: {primary?: string; accent_1?: string; accent_2?: string | null; neutral?: string | null};
  typography_personality?: string;
  layout_language?: string;
  texture_language?: string | null;
  transition_language?: string | null;
  motion_intensity?: number;
}

export const DEFAULT_THEME: ThemeProps = {
  background: '#12151C',
  surface: '#1A202C',
  text: '#F8FAFC',
  mutedText: '#94A3B8',
  accent: '#D97736',
  accentSecondary: '#4F709C',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  headlineSize: 64,
  bodySize: 34,
  lineWeight: 2,
  cornerRadius: 12,
  motion: {stiffness: 90, damping: 22, mass: 1},
};

function isHexColor(value: unknown): value is string {
  return typeof value === 'string' && /^#[0-9a-fA-F]{6}$/.test(value);
}

export function artDirectionToTheme(art: ArtDirectionInput): ThemeProps {
  const palette = art.palette_discipline ?? {};
  const intensity = Math.min(10, Math.max(1, art.motion_intensity ?? 6));
  return {
    ...DEFAULT_THEME,
    background: isHexColor(palette.primary) ? palette.primary : DEFAULT_THEME.background,
    accent: isHexColor(palette.accent_1) ? palette.accent_1 : DEFAULT_THEME.accent,
    accentSecondary: isHexColor(palette.accent_2) ? palette.accent_2 : DEFAULT_THEME.accentSecondary,
    mutedText: isHexColor(palette.neutral) ? palette.neutral : DEFAULT_THEME.mutedText,
    motion: {stiffness: 80 + intensity * 8, damping: 22 - intensity, mass: 1},
  };
}

export function validateTheme(theme: ThemeProps): string[] {
  const errors: string[] = [];
  for (const key of ['background', 'surface', 'text', 'accent'] as const) {
    if (!isHexColor(theme[key])) {
      errors.push(`theme.${key} must be a #RRGGBB color`);
    }
  }
  if (!(theme.headlineSize > 0 && theme.bodySize > 0)) {
    errors.push('theme type sizes must be positive');
  }
  return errors;
}
