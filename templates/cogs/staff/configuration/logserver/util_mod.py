import discord
from discord.ext import commands
import asyncio
from . import logserver

class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_chan(self, guild):
        main_cog = self.bot.get_cog("LogSystem")
        if not main_cog: 
            print("❌ LogSystem cog non trouvé dans util_mod.get_chan")
            return None
        config = main_cog.get_config(guild.id)
        channel_id = config.get("log_mod")
        return guild.get_channel(channel_id) if channel_id else None

    # ──────────────────────────────────────────────
    # MÉTHODE À APPELER DANS TES COMMANDES (!ban, !warn, etc.)
    # ──────────────────────────────────────────────
    async def log_action(self, guild, user, performer, action_name, reason="Aucune raison", duration=None):
        """Appelée manuellement depuis tes fichiers de commandes"""
        chan = self.get_chan(guild)
        if not chan: return

        colors = {
            "Ban": 0xff4757,   # Rouge
            "Kick": 0xff9f43,  # Orange
            "Mute": 0xe84118,  # Rouge foncé
            "Warn": 0xfeca57,  # Jaune
            "Unban": 0x2ed573  # Vert
        }
        
        title = f"🔨 Commande - {action_name}"
        embed = await self.create_mod_embed(guild, title, colors.get(action_name, 0x54a0ff), user, performer, reason)
        
        if duration:
            embed.add_field(name="⏱️ Durée", value=duration, inline=True)
            
        await chan.send(embed=embed)

    # ──────────────────────────────────────────────
    # LISTENERS AUTOMATIQUES (Audit Logs)
    # ──────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Détecte les Bans manuels (Clic-droit)"""
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                # Évite le double log si l'action vient d'une commande du bot
                if entry.user.id == self.bot.user.id: return 
                
                embed = await self.create_mod_embed(guild, "🚫 Ban Manuel", 0xff4757, user, entry.user, entry.reason)
                chan = self.get_chan(guild)
                if chan: await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Détecte les Kicks manuels"""
        await asyncio.sleep(1)
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_kick):
            if entry.target.id == member.id:
                # Vérifie la récence pour ne pas log un vieux kick
                if (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                    if entry.user.id == self.bot.user.id: return
                    
                    embed = await self.create_mod_embed(member.guild, "👢 Kick Manuel", 0xff9f43, member, entry.user, entry.reason)
                    chan = self.get_chan(member.guild)
                    if chan: await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Détecte les Exclusions (Timeout) manuelles"""
        if before.timed_out_until != after.timed_out_until and after.timed_out_until:
            await asyncio.sleep(1)
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    # On vérifie si c'est un timeout (le log indique une modif de membre)
                    if entry.user.id == self.bot.user.id: return
                    
                    embed = await self.create_mod_embed(after.guild, "⏳ Exclusion Manuelle", 0xe84118, after, entry.user, entry.reason)
                    chan = self.get_chan(after.guild)
                    if chan: await chan.send(embed=embed)

    # ──────────────────────────────────────────────
    # GÉNÉRATEUR D'EMBED (Synchronisé avec logserver)
    # ──────────────────────────────────────────────
    async def create_mod_embed(self, guild, title, color, target, performer, reason=None):
        # On s'assure que target et performer sont des chaînes lisibles si l'objet est perdu
        target_mention = target.mention if hasattr(target, 'mention') else f"Utilisateur ({target.id})"
        perf_mention = performer.mention if hasattr(performer, 'mention') else f"{performer}"

        desc = f"👤 **Cible :** {target_mention}\n"
        desc += f"👮 **Modérateur :** {perf_mention}\n"
        desc += f"📝 **Raison :** {reason or 'Non spécifiée'}"
        
        # Utilisation de la fonction create_embed de logserver
        from .logserver import create_embed
        embed = await create_embed(
            guild=guild,
            user=target,
            bot=self.bot,
            title=title,
            description=desc,
            color=color
        )
        
        # Ajout de la miniature avec l'avatar de la cible si disponible
        if hasattr(target, 'display_avatar') and target.display_avatar:
            embed.set_thumbnail(url=target.display_avatar.url)
            
        return embed

async def setup(bot):
    try:
        cog = ModLog(bot)
        await bot.add_cog(cog)
        # ModLog chargé silencieusement
        return True
    except Exception as e:
        print(f"❌ Erreur lors du chargement de ModLog: {str(e)}")
        import traceback
        traceback.print_exc()
        return False