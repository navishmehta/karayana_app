/**
 * Permission checks for showing or hiding UI. The server enforces every permission on its own —
 * hiding a button is only for a clean interface, never for security.
 */
import type { AuthUser } from '@/api/types';
import { ROLES } from '@/constants/app';
import type { Permission } from '@/constants/permissions';

import { useSession } from './session';

export const isAdmin = (user: AuthUser | null): boolean => user?.role === ROLES.admin;

export function can(user: AuthUser | null, ...required: Permission[]): boolean {
  if (!user) return false;
  if (isAdmin(user)) return true;
  return required.every((p) => user.permissions.includes(p));
}

export function useCan(...required: Permission[]): boolean {
  const user = useSession((s) => s.user);
  return can(user, ...required);
}
