export const ROLES = {
  USER: "USER",
  SUPPORT: "SUPPORT",
  DEV_TEST: "DEV_TEST",
  DEV_DEV: "DEV_DEV",
  DEV_ELITE: "DEV_ELITE",
  MANAGER: "MANAGER",
  SUPERVISOR: "SUPERVISOR",
  LEADER: "LEADER",
} as const;

export type Role = keyof typeof ROLES;

// Hiérarchie : plus l'index est élevé, plus le rôle est puissant
export const ROLE_HIERARCHY: Role[] = [
  "USER",
  "SUPPORT",
  "DEV_TEST",
  "DEV_DEV",
  "DEV_ELITE",
  "MANAGER",
  "SUPERVISOR",
  "LEADER",
];

// Mapping Discord ID → rôle interne
export const DISCORD_ROLE_MAP: Record<string, Role> = {
  "1368719335534887023": "LEADER",
  "1368620965403299890": "SUPERVISOR",
  "1500974364114423858": "MANAGER",
  "1500974295134896369": "DEV_ELITE",
  "1369430431212114002": "DEV_DEV",
  "1474871058166448280": "DEV_TEST",
  "1465825778771034236": "SUPPORT",
};

// Retourne true si l'utilisateur a au moins le rôle requis
export function hasRole(userRoles: string[], requiredRole: Role): boolean {
  const requiredIndex = ROLE_HIERARCHY.indexOf(requiredRole);
  return userRoles.some((role) => {
    const userIndex = ROLE_HIERARCHY.indexOf(role as Role);
    return userIndex >= requiredIndex;
  });
}

// Retourne true si l'utilisateur a accès à synkrone.dev
export function hasDevAccess(userRoles: string[]): boolean {
  return hasRole(userRoles, "SUPPORT");
}

// Rôles avec tokens illimités (admin, dev seniors)
export function hasUnlimitedTokens(userRoles: string[]): boolean {
  return hasRole(userRoles, "MANAGER");
}

// Taille de box en Mo par rôle
export const BOX_SIZE_BY_ROLE: Record<Role, number> = {
  USER: 0,
  SUPPORT: 500,
  DEV_TEST: 500,
  DEV_DEV: 1024,
  DEV_ELITE: 3072,
  MANAGER: 5120,
  SUPERVISOR: 10240,
  LEADER: -1, // illimité
};
