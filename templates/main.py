#!/usr/bin/env python3
"""
Synkrone Bot — Dynamique
Charge uniquement les cogs présents dans cogs/
Lit .env (DISCORD_TOKEN, PREFIX, BOT_NAME)
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

# ─── Configuration ──────────────────────────────────────────────────
BOT_DIR = Path(__file__).parent.resolve()

# Charger .env
env = {}
env_path = BOT_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

TOKEN = env.get("DISCORD_TOKEN")
PREFIX = env.get("PREFIX", "!")
BOT_NAME = env.get("BOT_NAME", "SynkroneBot")

if not TOKEN:
    print("[✗] DISCORD_TOKEN manquant dans .env")
    sys.exit(1)

# ─── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("synkrone")

# ─── Intents ──────────────────────────────────────────────────────────
intents = discord.Intents.all()

# ─── Système de préfixes ────────────────────────────────────────────────
_DEFAULT_PREFIX = PREFIX

def get_prefix(_bot, message):
    return [_DEFAULT_PREFIX]

# ─── Bot ──────────────────────────────────────────────────────────────
class SynkroneBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

    async def setup_hook(self):
        """Charge dynamiquement tous les cogs trouvés dans cogs/"""
        cog_dir = BOT_DIR / "cogs"
        if not cog_dir.exists():
            logger.warning("Dossier cogs/ introuvable")
            return

        loaded = 0
        errors = 0

        for root, dirs, files in os.walk(cog_dir):
            dirs[:] = [d for d in dirs if not d.startswith("__")]
            for filename in files:
                if not filename.endswith(".py") or filename.startswith("__"):
                    continue
                if filename.startswith("util_"):
                    continue

                rel_path = Path(root).relative_to(cog_dir) / filename
                cog_name = str(rel_path.with_suffix("")).replace(os.sep, ".")

                try:
                    await self.load_extension(f"cogs.{cog_name}")
                    loaded += 1
                    logger.info("[✓] Cog chargé : cogs.%s", cog_name)
                except Exception as e:
                    errors += 1
                    logger.warning("[!] Erreur cogs.%s : %s", cog_name, e)

        logger.info("=== %s chargé(s) | %s erreur(s) ===", loaded, errors)

    async def on_ready(self):
        logger.info("🤖 %s connecté en tant que %s (%s)", BOT_NAME, self.user, self.user.id)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{PREFIX}help"
            )
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
            return
        logger.error("Erreur commande : %s", error)

# ─── Help global ──────────────────────────────────────────────────────
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        embed = discord.Embed(
            title=f"{BOT_NAME} — Aide",
            description=f"Préfixe : `{PREFIX}`",
            color=0x5865F2,
        )
        cogs_list = "\n".join(
            f"`{cog.qualified_name}` — {len(cog.get_commands())} commandes"
            for cog in self.bot.cogs.values()
        ) or "Aucun cog chargé"
        embed.add_field(name="Modules chargés", value=cogs_list, inline=False)
        await ctx.send(embed=embed)

# ─── Lancement ──────────────────────────────────────────────────────
async def main():
    bot = SynkroneBot()
    await bot.add_cog(HelpCog(bot))
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error("Erreur fatale : %s", e)
        sys.exit(1)
