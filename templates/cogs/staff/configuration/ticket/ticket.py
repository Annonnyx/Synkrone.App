import discord
from discord.ext import tasks, commands
import json
import os
import time

# IMPORTATIONS CORRECTES
from .util.embed_launcher import LauncherView
from .util.config_util import get_config
from .util.embed_admin import AdminView, AdminEmbed

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sync_tickets.start()

    def cog_unload(self):
        self.sync_tickets.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        # Charge la vue persistante pour que les boutons marchent après reboot
        for guild in self.bot.guilds:
            cfg = get_config(guild.id)
            if cfg.get("enabled"):
                self.bot.add_view(LauncherView(cfg))
        # Système de tickets prêt silencieusement

    @commands.Cog.listener()
    async def on_message(self, message):
        """Calcule le temps de réponse moyen du support"""
        if message.author.bot or not message.guild: return
        if not hasattr(message.channel, "name") or not message.channel.name or not message.channel.name[0].isdigit(): return

        cfg = get_config(message.guild.id)
        support_role_id = cfg.get("support_role_id")
        
        # Si le message vient du support
        if support_role_id and any(role.id == support_role_id for role in message.author.roles):
            # Si le ticket n'a pas encore de réponse marquée
            if hasattr(message.channel, "topic") and message.channel.topic and "Répondu" not in message.channel.topic:
                wait_time = (message.created_at.timestamp() - message.channel.created_at.timestamp()) / 60
                
                path = f"./data/ticket/{message.guild.id}/attente.json"
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                data = {"total_wait_time": 0, "total_tickets_answered": 0}
                if os.path.exists(path):
                    with open(path, "r") as f: data = json.load(f)
                
                data["total_wait_time"] += wait_time
                data["total_tickets_answered"] += 1
                
                with open(path, "w") as f: json.dump(data, f)
                await message.channel.edit(topic=f"{message.channel.topic} | Répondu")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Ferme le ticket si l'utilisateur quitte le serveur"""
        cfg = get_config(member.guild.id)
        category = member.guild.get_channel(cfg.get("category_id"))
        if category:
            suffix = f"-{member.name.lower().replace(' ', '-')}"
            chan = discord.utils.get(category.text_channels, name__endswith=suffix)
            if chan:
                await chan.delete()

    @tasks.loop(minutes=1.0)
    async def sync_tickets(self):
        for guild in self.bot.guilds:
            cfg = get_config(guild.id)
            if cfg.get("enabled") and cfg.get("channel_id"):
                chan = guild.get_channel(cfg["channel_id"])
                if chan:
                    try:
                        msg = await chan.fetch_message(cfg["msg_id"])
                        await msg.edit(view=LauncherView(cfg))
                    except: pass

    @sync_tickets.before_loop
    async def before_sync(self): await self.bot.wait_until_ready()

    # --- LA COMMANDE !ticket ---
    @commands.hybrid_command(name="ticket", description="Ouvre le panneau de configuration des tickets")
    @commands.has_permissions(administrator=True)
    async def ticket_cmd(self, ctx):
        # On charge la config
        cfg = get_config(ctx.guild.id)
        # On envoie l'embed Admin avec la vue Admin
        await ctx.send(embed=AdminEmbed(ctx.guild, cfg), view=AdminView(self.bot, cfg, ctx.author))

async def setup(bot):
    await bot.add_cog(Ticket(bot))