#!/usr/bin/env python3
"""
Template Synkrone Bot — Discord.py
Ce fichier est copié à chaque création de bot. Il lit :
  - .enc        : variables sensibles (TOKEN, PREFIX, BOT_NAME)
  - bot.config.json : cogs activés et configuration
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

# ─── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("synkrone")

# ─── Charger .enc (format KEY=VAL) ────────────────────────────────────
BOT_DIR = Path(__file__).parent.resolve()
ENC_PATH = BOT_DIR / ".enc"
CONFIG_PATH = BOT_DIR / "bot.config.json"

env = {}
if ENC_PATH.exists():
    for line in ENC_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
else:
    logger.error("Fichier .enc introuvable : %s", ENC_PATH)
    sys.exit(1)

BOT_TOKEN = env.get("BOT_TOKEN")
PREFIX = env.get("PREFIX", "!")
BOT_NAME = env.get("BOT_NAME", "SynkroneBot")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN manquant dans .enc")
    sys.exit(1)

# ─── Charger bot.config.json ──────────────────────────────────────────
config = {}
if CONFIG_PATH.exists():
    config = json.loads(CONFIG_PATH.read_text())

COGS = config.get("cogs", [])

# ─── Intents ──────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ─── Bot ──────────────────────────────────────────────────────────────
class SynkroneBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

    async def setup_hook(self):
        logger.info("Chargement des cogs : %s", COGS)
        for cog in COGS:
            try:
                await self.load_extension(f"cogs.{cog}")
                logger.info("Cog chargé : %s", cog)
            except Exception as e:
                logger.warning("Impossible de charger le cog '%s' : %s", cog, e)
        await self.tree.sync()

    async def on_ready(self):
        logger.info("%s connecté en tant que %s (%s)", BOT_NAME, self.user, self.user.id)
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
            await ctx.send("Tu n'as pas la permission d'utiliser cette commande.")
            return
        logger.error("Erreur commande : %s", error)

# ─── Help custom ──────────────────────────────────────────────────────
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
        embed.add_field(
            name="Cogs activés",
            value=", ".join(f"`{c}`" for c in COGS) or "Aucun",
            inline=False,
        )
        await ctx.send(embed=embed)

# ─── Lancement ──────────────────────────────────────────────────────
async def main():
    bot = SynkroneBot()
    await bot.add_cog(HelpCog(bot))
    async with bot:
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
