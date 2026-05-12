import fs from "fs/promises";
import path from "path";

const COGS_PATH = process.env.COGS_TEMPLATE_PATH || "/Partage/Synkrone/templates/cogs";

export interface CatalogCommand {
  id: string;
  name: string;
  category: string;
  module: string;
  priceKr: number;
}

/* ─── Mapping catégories → prix forfaitaires ───
   0  = commandes individuelles (prix par commande)
   >0 = module entier (flatPrice)
   999 = réservé OWNER
*/
const FLAT_PRICES: Record<string, number> = {
  AI: 300,
  AUTOROLES: 40,
  GIVEAWAYS: 40,
  LOGS: 30,
  MUSIC: 200,
  REACTIONS: 30,
  TICKETS: 50,
  WELCOME: 30,
  OWNER: 999,
};

const CMD_PRICES: Record<string, number> = {
  ECONOMY: 10,
  FUN: 5,
  JEUX: 5,
  MODERATION: 10,
  UTILITAIRES: 5,
  INFOS: 5,
  XP: 15,
  STATISTIQUES: 15,
  DIVERS: 5,
  ADDONS: 15,
};

function mapCategory(raw: string): string {
  const m: Record<string, string> = {
    divertissement: "FUN",
    games: "JEUX",
    ia: "AI",
    social: "REACTIONS",
    statistiques: "XP",
    utilitaires: "UTILITAIRES",
    rolemenu: "AUTOROLES",
    logserver: "LOGS",
    ticket: "TICKETS",
    voice: "VOICE",
    secur: "SECURITY",
    update: "UPDATE",
    giveaway: "GIVEAWAYS",
    modération: "MODERATION",
    bot: "INFOS",
    owner: "OWNER",
    perm: "ADDONS",
    prefix: "ADDONS",
    embed_type: "ADDONS",
    economy: "ECONOMY",
    welcome: "WELCOME",
    music: "MUSIC",
    divers: "DIVERS",
    addons: "ADDONS",
    staff: "STAFF",
  };
  return m[raw.toLowerCase()] || raw.toUpperCase();
}

export async function scanCogs(): Promise<CatalogCommand[]> {
  const results: CatalogCommand[] = [];

  try {
    const accessDirs = await fs.readdir(COGS_PATH, { withFileTypes: true });

    for (const accessDir of accessDirs) {
      if (!accessDir.isDirectory()) continue;
      const accessPath = path.join(COGS_PATH, accessDir.name);

      const catDirs = await fs.readdir(accessPath, { withFileTypes: true });
      for (const catDir of catDirs) {
        if (!catDir.isDirectory()) continue;
        const catPath = path.join(accessPath, catDir.name);
        const category = mapCategory(catDir.name);

        const modDirs = await fs.readdir(catPath, { withFileTypes: true });
        for (const modDir of modDirs) {
          if (!modDir.isDirectory()) continue;
          const modPath = path.join(catPath, modDir.name);

          const files = await fs.readdir(modPath);
          const hasPy = files.some((f) => f.endsWith(".py") && f !== "__init__.py");
          if (!hasPy) continue;

          const basePrice = FLAT_PRICES[category] ?? CMD_PRICES[category] ?? 5;
          results.push({
            id: `${accessDir.name}.${catDir.name}.${modDir.name}`,
            name: modDir.name,
            category,
            module: `${accessDir.name}.${catDir.name}.${modDir.name}`,
            priceKr: basePrice,
          });
        }
      }
    }
  } catch {
    /* ignore fs errors (VPS path may differ) */
  }

  return results;
}
