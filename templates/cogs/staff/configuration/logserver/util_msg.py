import discord
from discord.ext import commands
import asyncio
from . import logserver

class MsgLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_threads = {} # {message_id: thread_object}

    def get_chan(self, guild):
        main_cog = self.bot.get_cog("LogSystem")
        if not main_cog: 
            print("❌ LogSystem cog non trouvé dans MsgLog.get_chan")
            return None
        config = main_cog.get_config(guild.id)
        channel_id = config.get("log_msg")
        return guild.get_channel(channel_id) if channel_id else None

    async def get_deletion_performer(self, message):
        """Cherche si un modérateur a supprimé le message"""
        await asyncio.sleep(0.8) # Temps pour que le log s'écrive
        try:
            async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                # Vérifie si la cible est l'auteur et si le salon correspond
                if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                    # Vérifie si le log est récent (moins de 10s)
                    if (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                        return entry.user
        except Exception: pass
        return None

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot: return
        chan = self.get_chan(message.guild)
        if not chan: return

        # Recherche du responsable
        performer = await self.get_deletion_performer(message)
        
        # Titre dynamique
        title = "🔨 Message Supprimé (Modération)" if performer else "🗑️ Message Supprimé"
        desc = f"👤 **Auteur :** {message.author.mention}\n📍 **Salon :** {message.channel.mention}"
        
        if performer:
            desc += f"\n👮 **Supprimé par :** {performer.mention}"
            
        # Utilisation de la fonction create_embed de logserver
        from .logserver import create_embed
        color = 0xff4757 if performer else 0x95a5a6
        embed = await create_embed(
            guild=message.guild,
            user=message.author,
            bot=self.bot,
            title=title,
            description=desc,
            color=color
        )
        
        content = message.content[:1000] if message.content else "*Fichier/Embed*"
        embed.add_field(name="Contenu du message", value=f"```\n{content}\n```")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        chan = self.get_chan(before.guild)
        if not chan: return

        # --- CAS 1 : PREMIÈRE MODIFICATION ---
        if before.id not in self.active_threads:
            title = "📝 Message Modifié"
            desc = f"👤 **Auteur :** {before.author.mention}\n📍 **Salon :** {before.channel.mention}\n🔗 [Lien du message]({after.jump_url})"

            # Utilisation de la fonction create_embed de logserver
            from .logserver import create_embed
            embed = await create_embed(
                guild=before.guild,
                user=before.author,
                bot=self.bot,
                title=title,
                description=desc,
                color=0xeaa14e
            )

            # ON N'AFFICHE QUE LE MESSAGE D'ORIGINE DANS LE SALON PRINCIPAL
            embed.add_field(name="Message d'origine", value=f"```\n{before.content[:1000] or 'Vide'}\n```", inline=False)
            embed.set_thumbnail(url=before.author.display_avatar.url)
            embed.set_footer(text="Historique des modifications disponible dans le fil ci-dessous")

            log_msg = await chan.send(embed=embed)
            
            try:
                thread = await log_msg.create_thread(name=f"Modifs - {before.author.name}", auto_archive_duration=60)
                self.active_threads[before.id] = thread
                # Premier message du fil : la version 1 (après modif)
                await thread.send(f"🔄 **1ère modification :**\n```\n{after.content[:1900]}\n```")
            except Exception: pass

        # --- CAS 2 : MODIFICATIONS SUIVANTES ---
        else:
            thread = self.active_threads[before.id]
            try:
                await thread.send(f"🔄 **Nouvelle modification :**\n```\n{after.content[:1900]}\n```")
            except discord.NotFound:
                self.active_threads.pop(before.id, None)

        # Nettoyage auto
        await asyncio.sleep(3600)
        self.active_threads.pop(before.id, None)

async def setup(bot):
    try:
        cog = MsgLog(bot)
        await bot.add_cog(cog)
        # MsgLog chargé silencieusement
        return True
    except Exception as e:
        print(f"❌ Erreur lors du chargement de MsgLog: {str(e)}")
        import traceback
        traceback.print_exc()
        return False