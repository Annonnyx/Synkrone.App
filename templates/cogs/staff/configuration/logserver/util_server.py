import discord
from discord.ext import commands
import asyncio
from . import logserver

class ServerLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        main_cog = self.bot.get_cog("LogSystem")
        if not main_cog: return None
        config = main_cog.get_config(guild.id)
        channel_id = config.get("log_server")
        return guild.get_channel(channel_id) if channel_id else None

    async def get_responsible(self, guild, action_type, target_id):
        """Cherche le modérateur dans les Audit Logs avec une marge de sécurité"""
        await asyncio.sleep(1.2)
        try:
            async for entry in guild.audit_logs(limit=5, action=action_type):
                if entry.target.id == target_id:
                    return entry.user
        except: pass
        return None

    async def send_server_log(self, guild, title, details, color, target_id=None, action_type=None, user_fixed=None):
        channel = self.get_log_channel(guild)
        if not channel: return

        # 1. Identification du responsable
        performer = user_fixed
        if action_type and target_id and not performer:
            performer = await self.get_responsible(guild, action_type, target_id)

        # 2. Construction du contenu de l'embed
        header = f"# ⚙️ {title}"
        resp_line = f"\n🛡️ **Responsable :** {performer.mention if performer else '`Système / Inconnu`'}"
        full_description = f"{header}\n{details}{resp_line}"

        # Utilisation de la fonction create_embed de logserver
        from .logserver import create_embed
        display_user = performer or self.bot.user
        
        # On extrait le titre de la description (première ligne) pour le passer séparément
        lines = full_description.split('\n', 1)
        title = lines[0].replace('#', '').strip()
        description = lines[1] if len(lines) > 1 else ''
        
        embed = await create_embed(
            guild=guild,
            user=display_user,
            bot=self.bot,
            title=title,
            description=description,
            color=color
        )

        await channel.send(embed=embed)

    # ───────────────── LOGS SALONS ─────────────────

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        cat = channel.category.name if channel.category else "Aucune"
        details = f"📍 **Salon :** {channel.mention}\n📂 **Catégorie :** `{cat}`\n🆔 **ID :** `{channel.id}`\n"
        await self.send_server_log(channel.guild, "Salon Créé", details, 0x2ecc71, channel.id, discord.AuditLogAction.channel_create)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        cat = channel.category.name if channel.category else "Aucune"
        details = f"🗑️ **Nom :** `#{channel.name}`\n📂 **Catégorie :** `{cat}`\n"
        await self.send_server_log(channel.guild, "Salon Supprimé", details, 0xe74c3c, channel.id, discord.AuditLogAction.channel_delete)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"📝 **Nom :** `{before.name}` ➔ `{after.name}`")
        if before.category != after.category:
            changes.append(f"📂 **Catégorie :** `{before.category}` ➔ `{after.category}`")
        if before.topic != after.topic:
            changes.append(f"📖 **Sujet :** `MODIFIÉ`")
        
        if changes:
            details = f"🔧 **Salon :** {after.mention}\n" + "\n".join(changes) + "\n"
            await self.send_server_log(after.guild, "Salon Modifié", details, 0x3498db, after.id, discord.AuditLogAction.channel_update)

    # ───────────────── LOGS RÔLES ─────────────────

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        details = f"✨ **Rôle :** {role.mention}\n🆔 **ID :** `{role.id}`\n"
        await self.send_server_log(role.guild, "Rôle Créé", details, 0x2ecc71, role.id, discord.AuditLogAction.role_create)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        details = f"🗑️ **Nom :** `{role.name}`\n"
        await self.send_server_log(role.guild, "Rôle Supprimé", details, 0xe74c3c, role.id, discord.AuditLogAction.role_delete)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []
        # Changements basiques
        if before.name != after.name: changes.append(f"📝 **Nom :** `{before.name}` ➔ `{after.name}`")
        if before.color != after.color: changes.append(f"🌈 **Couleur :** `{before.color}` ➔ `{after.color}`")
        if before.hoist != after.hoist: changes.append(f"👥 **Affiché séparément :** `{'Oui' if after.hoist else 'Non'}`")
        
        # Permissions
        if before.permissions != after.permissions:
            perms = []
            for perm, value in after.permissions:
                if dict(before.permissions).get(perm) != value:
                    perms.append(f"{'✅' if value else '❌'} `{perm}`")
            if perms:
                changes.append("**Permissions modifiées :**\n" + "\n".join(perms[:10]))

        if changes:
            details = f"🎭 **Rôle :** {after.mention}\n" + "\n".join(changes) + "\n"
            await self.send_server_log(after.guild, "Rôle Modifié", details, 0x3498db, after.id, discord.AuditLogAction.role_update)

    # ───────────────── LOGS SERVEUR ─────────────────

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []
        if before.name != after.name: changes.append(f"📝 **Nom :** `{before.name}` ➔ `{after.name}`")
        if before.icon != after.icon: changes.append("🖼️ **Icône modifiée.**")
        if before.banner != after.banner: changes.append("🚩 **Bannière modifiée.**")
        if before.owner != after.owner: changes.append(f"👑 **Propriétaire :** {after.owner.mention}")
        
        if changes:
            await self.send_server_log(after.guild, "Système - Serveur", "\n".join(changes) + "\n", 0xf1c40f, after.id, discord.AuditLogAction.guild_update)

async def setup(bot):
    await bot.add_cog(ServerLog(bot))