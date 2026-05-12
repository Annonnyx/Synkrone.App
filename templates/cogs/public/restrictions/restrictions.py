import discord
from discord.ext import commands, tasks
import json
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

log = logging.getLogger("restrictions")

# ─── Configuration ──────────────────────────────────────────────────
BOT_DIR = Path(__file__).parent.parent.parent.resolve()
CONFIG_PATH = BOT_DIR / "bot.config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


class RestrictionsCog(commands.Cog):
    """
    Cog de restrictions :
    - Limite le nombre de serveurs (maxGuilds)
    - Quitte les serveurs excédentaires
    - Vérifie périodiquement si le bot doit rester en ligne
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()
        self.max_guilds = self.config.get("maxGuilds", 5)
        self._check_loop.start()

    def cog_unload(self):
        self._check_loop.cancel()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Quand le bot rejoint un serveur, vérifier la limite."""
        await self._enforce_guild_limit(guild)

    async def _enforce_guild_limit(self, trigger_guild: discord.Guild = None):
        """Si le bot dépasse maxGuilds, quitte les serveurs en excès."""
        guilds = list(self.bot.guilds)
        if len(guilds) <= self.max_guilds:
            return

        # Trier par date d'ajout (les plus récents en premier à quitter)
        # On ne peut pas savoir exactement, donc on garde les plus grands
        guilds_sorted = sorted(guilds, key=lambda g: g.member_count or 0, reverse=True)
        to_keep = guilds_sorted[:self.max_guilds]
        to_leave = guilds_sorted[self.max_guilds:]

        for guild in to_leave:
            try:
                await guild.leave()
                log.info("[RESTRICTIONS] Bot a quitté '%s' (id:%s) — limite %s serveurs",
                         guild.name, guild.id, self.max_guilds)
                # Envoyer un message dans le système de log si possible
            except Exception as e:
                log.warning("[RESTRICTIONS] Impossible de quitter '%s': %s", guild.name, e)

        if trigger_guild and trigger_guild in to_leave:
            # On a quitté le serveur qui a déclenché l'event
            pass

    @tasks.loop(minutes=60)
    async def _check_loop(self):
        """Vérifie périodiquement les restrictions."""
        self.config = load_config()
        self.max_guilds = self.config.get("maxGuilds", 5)
        await self._enforce_guild_limit()

    @_check_loop.before_loop
    async def before_check_loop(self):
        await self.bot.wait_until_ready()

    @commands.command(name="limits")
    async def limits_cmd(self, ctx: commands.Context):
        """Affiche les limites actuelles du bot."""
        guild_count = len(self.bot.guilds)
        embed = discord.Embed(
            title="Limites du bot",
            color=0x5865F2,
        )
        embed.add_field(name="Serveurs actuels", value=f"{guild_count}", inline=True)
        embed.add_field(name="Max serveurs", value=f"{self.max_guilds}", inline=True)
        embed.add_field(
            name="Statut",
            value="✅ Opérationnel" if guild_count <= self.max_guilds else "⚠️ Limite dépassée",
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RestrictionsCog(bot))
