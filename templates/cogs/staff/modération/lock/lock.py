import discord
from discord.ext import commands
from pathlib import Path
import json
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class Lock(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_path = Path(__file__).parent / "data"
        self.data_path.mkdir(parents=True, exist_ok=True)

    def load_db(self, gid):
        file = self.data_path / f"{gid}.json"
        if not file.exists(): return {}
        try:
            with open(file, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def save_db(self, gid, data):
        with open(self.data_path / f"{gid}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @commands.hybrid_command(name="lock", description="🔒 Verrouille l'écriture en préservant strictement la visibilité.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        try:
            db = self.load_db(ctx.guild.id)
            cid = str(ctx.channel.id)
            target = ctx.guild.default_role
            
            # 1. ANALYSE PRÉCISE DES PERMISSIONS ACTUELLES
            ov = ctx.channel.overwrites_for(target)
            
            # On stocke TOUT dans le JSON pour le unlock futur
            db[cid] = {
                "send_messages": ov.send_messages,
                "add_reactions": ov.add_reactions,
                "connect": ov.connect,
                "speak": ov.speak,
                "view_channel": ov.view_channel 
            }
            self.save_db(ctx.guild.id, db)

            # 2. LOCK SÉCURISÉ (FORCE LE MAINTIEN DE LA VISIBILITÉ)
            # On réinjecte explicitement la valeur actuelle de view_channel
            # Si ov.view_channel est False (caché), on renvoie False. 
            # Si c'est None (hérité), on renvoie None.
            
            if isinstance(ctx.channel, (discord.TextChannel, discord.ForumChannel)):
                await ctx.channel.set_permissions(
                    target, 
                    send_messages=False, 
                    add_reactions=False,
                    view_channel=ov.view_channel # FORCE la conservation du statut caché/visible
                )
            elif isinstance(ctx.channel, discord.VoiceChannel):
                await ctx.channel.set_permissions(
                    target, 
                    connect=False,
                    view_channel=ov.view_channel # FORCE la conservation du statut caché/visible
                )

            # 3. EMBED
            rank = "Owner" if ctx.author.id == ctx.guild.owner_id else "Administrateur" if ctx.author.guild_permissions.administrator else "Modérateur"
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild,
                    user=ctx.author,
                    bot=self.bot,
                    title="🔒 Salon Verrouillé",
                    description=f"Le salon {ctx.channel.mention} est fermé.",
                    target_id=ctx.guild.id if ctx.guild else None
                )
                embed.add_field(name="Autorité", value=rank)
                embed.color = 0xE74C3C
            else:
                embed = discord.Embed(title="🔒 Salon Verrouillé", description=f"Fermé par {ctx.author.mention}", color=discord.Color.red())
            
            await ctx.channel.send(embed=embed)

        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"❌ Erreur critique : {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Lock(bot))