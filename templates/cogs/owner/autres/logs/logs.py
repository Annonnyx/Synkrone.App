import discord
from discord.ext import commands
from datetime import datetime
import asyncio

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

LOG_CHANNEL_ID = 1380320307935707278

class LogCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_access_level(self, user, guild):
        """Détermine le rang de l'utilisateur selon ses permissions."""
        if user.id == guild.owner_id: return "Owner"
        if user.guild_permissions.administrator: return "Admin"
        
        p = user.guild_permissions
        mod_perms = [
            p.manage_roles, p.manage_expressions, p.create_expressions,
            p.view_audit_log, p.manage_webhooks, p.manage_guild,
            p.manage_nicknames, p.kick_members, p.ban_members,
            p.moderate_members, p.mention_everyone, p.manage_messages,
            p.manage_threads, p.mute_members, p.deafen_members,
            p.move_members, p.manage_channels
        ]
        
        if any(mod_perms): return "Modérateur"
        return "Utilisateur"

    async def generate_invite(self, channel) -> str:
        try:
            target = channel.parent if isinstance(channel, discord.Thread) else channel
            invite = await target.create_invite(max_age=3600, max_uses=1)
            return invite.url
        except:
            return None

    async def monitor_channel(self, thread, channel, guild):
        """Surveille le salon pendant 30 secondes avec le formatage demandé."""
        def check(m):
            return m.channel.id == channel.id

        end_time = datetime.utcnow().timestamp() + 30
        
        while datetime.utcnow().timestamp() < end_time:
            try:
                timeout = end_time - datetime.utcnow().timestamp()
                if timeout <= 0: break
                
                msg = await self.bot.wait_for("message", check=check, timeout=timeout)
                
                # Détection si c'est une commande ou une réponse de bot
                content_display = msg.content if msg.content else "*(Média/Embed)*"
                
                # Si c'est le bot qui répond à une commande
                if msg.author.id == self.bot.user.id:
                    content_display = "(Voir la commande)"

                # Construction de la description demandée
                desc = f"```{msg.author.id}```\n\n```{content_display}```"

                if config_manager:
                    spy_embed = config_manager.get_formatted_embed(
                        guild=guild, user=msg.author, bot=self.bot,
                        title=f"{msg.author.display_name}",
                        description=desc,
                        target_id=guild.id
                    )
                else:
                    spy_embed = discord.Embed(title=f"{msg.author.display_name}", description=desc, color=discord.Color.blue())

                spy_embed.set_thumbnail(url=msg.author.display_avatar.url)
                
                # On envoie l'embed de vision + les éventuels embeds originaux du message
                to_send = [spy_embed]
                if msg.embeds and msg.author.id != self.bot.user.id:
                    for e in msg.embeds: to_send.append(e)
                
                await thread.send(embeds=to_send)
                
            except asyncio.TimeoutError:
                break
            except Exception:
                break

        await thread.send("───\n🏁 **Fin de la vision** (30s écoulées)")

    async def send_log_embed(self, guild, channel, user, full_command, cmd_type):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel or user.bot: return

        # 1. Analyse réponse immédiate
        await asyncio.sleep(1.2)
        bot_reply = "Aucune réponse"
        async for message in channel.history(limit=3):
            if message.author.id == self.bot.user.id:
                if message.embeds: bot_reply = "Embed reçu"
                elif message.content: bot_reply = message.content
                break

        # 2. Log Principal
        invite_url = await self.generate_invite(channel)
        access = self.get_access_level(user, guild)

        description = (
            f"👤 **Utilisateur :** {user.mention}\n"
            f"🆔 **ID :** `{user.id}`\n"
            f"🔐 **Accès :** `{access}`\n\n"
            f"🕹️ **Type :** `{cmd_type}`\n\n"
            f"⌨️ **Commande :**\n```{full_command}```\n"
            f"💬 **Réponse :**\n```{bot_reply}```\n\n"
            f"📎 **Salon :** {channel.mention}"
        )

        if config_manager:
            embed = config_manager.get_formatted_embed(guild, user, self.bot, guild.name, description, guild.id)
        else:
            embed = discord.Embed(title=guild.name, description=description, color=discord.Color.blue())

        if invite_url: embed.url = invite_url
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        embed.timestamp = datetime.utcnow()

        log_msg = await log_channel.send(embed=embed)
        
        # 3. Création Fil et Vision
        try:
            thread = await log_msg.create_thread(name=f"Vision : {user.name}", auto_archive_duration=60)
            self.bot.loop.create_task(self.monitor_channel(thread, channel, guild))
        except:
            pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command: return
        if not interaction.guild: return
        
        cmd_name = interaction.command.name if interaction.command else "Inconnue"
        args = ""
        if interaction.data and "options" in interaction.data:
            opts = interaction.data.get("options", [])
            args = " ".join([str(o.get("value", "")) for o in opts])
        
        await self.send_log_embed(interaction.guild, interaction.channel, interaction.user, f"/{cmd_name} {args}", "Slash Command")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        
        prefix = await self.bot.get_prefix(message)
        prefixes = [prefix] if isinstance(prefix, str) else prefix
        
        if any(message.content.startswith(p) for p in prefixes):
            await self.send_log_embed(message.guild, message.channel, message.author, message.content, "Prefix Command")

async def setup(bot: commands.Bot):
    await bot.add_cog(LogCog(bot))