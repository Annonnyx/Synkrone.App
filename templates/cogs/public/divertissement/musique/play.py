import discord
from discord.ext import commands
from discord import ui
import yt_dlp
import asyncio
import os
import shutil

# --- CONFIGURATION HÉBERGEUR ---
# On utilise "ffmpeg" en direct car les serveurs Linux le gèrent ainsi.
FFMPEG_EXECUTABLE = "ffmpeg" 

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"'
}

# --- 1. MODAL DE SAISIE ---
class MusicModal(ui.Modal, title="Ajouter une musique"):
    url_input = ui.TextInput(
        label="Lien ou recherche",
        placeholder="Artiste, titre ou URL YouTube...",
        required=True
    )

    def __init__(self, cog, ctx):
        super().__init__()
        self.cog, self.ctx = cog, ctx

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.cog.execute_play(self.ctx, self.url_input.value)
        await interaction.followup.send("Requête envoyée !", delete_after=2)

# --- 1.1. MODAL DE GÉNÉRATION DE LISTE ---
class GenerateListModal(ui.Modal, title="Générer une liste de musiques"):
    keyword_input = ui.TextInput(
        label="Mot-clé",
        placeholder="Entrez un mot-clé pour générer 25 musiques...",
        required=True,
        max_length=100
    )

    def __init__(self, cog, ctx):
        super().__init__()
        self.cog, self.ctx = cog, ctx

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.cog.generate_music_list(self.ctx, self.keyword_input.value)
        await interaction.followup.send("Génération de la liste en cours...", delete_after=3)

# --- 2. CONTRÔLES ---
class PlayControls(ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=None)
        self.cog, self.ctx = cog, ctx

    @ui.button(label="Ajouter", style=discord.ButtonStyle.success, emoji="➕")
    async def play_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(MusicModal(self.cog, self.ctx))

    @ui.button(label="Générer une liste", style=discord.ButtonStyle.primary, emoji="🎵")
    async def generate_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(GenerateListModal(self.cog, self.ctx))

    @ui.button(label="Passer", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.ctx.voice_client or not self.ctx.voice_client.is_playing():
            return await interaction.response.send_message("Rien n'est joué !", ephemeral=True)
        self.ctx.voice_client.stop()
        await interaction.response.send_message("⏭️ Musique passée.", delete_after=3)

    @ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.ctx.voice_client: return
        self.cog.queues[self.ctx.guild.id] = []
        self.ctx.voice_client.stop()
        await self.ctx.voice_client.disconnect()
        await interaction.response.send_message("⏹️ Déconnexion.", delete_after=3)

# --- 3. LE COG MUSIQUE ---
class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.current_tracks = {}
        self.interfaces = {} 
        self.skip_votes = {}
        
        # Test de détection au chargement
        if shutil.which(FFMPEG_EXECUTABLE):
            print(f"✅ [MusicBot] FFmpeg a été trouvé avec succès.")
        else:
            print(f"❌ [MusicBot] ATTENTION : FFmpeg est introuvable sur cet hébergeur.")

    def get_data(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
            self.current_tracks[guild_id] = None
            self.interfaces[guild_id] = None
            self.skip_votes[guild_id] = set()

    async def update_display(self, ctx, status_text, force_new_message=False):
        gid = ctx.guild.id
        self.get_data(gid)

        embed = discord.Embed(title=status_text, color=discord.Color.blue())
        track = self.current_tracks[gid]

        if track:
            embed.add_field(name="🎵 En cours", value=f"[{track['title']}]({track['url']})", inline=False)
            if track['thumb']:
                embed.set_thumbnail(url=track['thumb'])

        queue = self.queues[gid]
        if queue:
            q_list = "\n".join([f"**{i+1}.** {t['title']}" for i, t in enumerate(queue[:5])])
            embed.add_field(name=f"📜 File ({len(queue)})", value=q_list, inline=False)

        view = PlayControls(self, ctx)
        if force_new_message:
            self.interfaces[gid] = await ctx.send(embed=embed, view=view)
        else:
            if self.interfaces[gid]:
                try:
                    await self.interfaces[gid].edit(embed=embed, view=view)
                except:
                    self.interfaces[gid] = await ctx.send(embed=embed, view=view)
            else:
                self.interfaces[gid] = await ctx.send(embed=embed, view=view)

    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):
        if not ctx.author.voice:
            return await ctx.send("Vocal requis !")

        if search is None:
            await self.update_display(ctx, "🎙️ Console", force_new_message=True)
        else:
            await self.execute_play(ctx, search)

    async def execute_play(self, ctx, search):
        gid = ctx.guild.id
        self.get_data(gid)
        if not ctx.voice_client: 
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(search, download=False)
                    if 'entries' in info: info = info['entries'][0]
                    data = {
                        'title': info.get('title', 'Musique'),
                        'url': info.get('webpage_url'),
                        'stream': info.get('url'),
                        'thumb': info.get('thumbnail')
                    }

                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    self.queues[gid].append(data)
                    await self.update_display(ctx, "📥 Ajouté")
                else:
                    await self.start_playing(ctx, data)
            except Exception as e:
                await ctx.send(f"❌ Erreur : {e}", delete_after=5)

    async def start_playing(self, ctx, data):
        gid = ctx.guild.id
        self.current_tracks[gid] = data
        
        try:
            # On utilise FFMPEG_EXECUTABLE défini en haut
            source = discord.FFmpegOpusAudio(
                data['stream'], 
                executable=FFMPEG_EXECUTABLE, 
                **FFMPEG_OPTIONS
            )
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await self.update_display(ctx, "▶️ Lecture")
        except Exception as e:
            await ctx.send(f"Erreur technique FFmpeg : {e}")

    async def generate_music_list(self, ctx, keyword):
        """Génère 25 musiques à partir d'un mot-clé et les ajoute à la file"""
        gid = ctx.guild.id
        self.get_data(gid)
        
        if not ctx.voice_client: 
            await ctx.author.voice.channel.connect()
        
        await ctx.send(f"🔍 Recherche de 25 musiques avec le mot-clé : **{keyword}**...")
        
        added_count = 0
        failed_count = 0
        
        # Générer 25 requêtes de recherche différentes basées sur le mot-clé
        search_queries = [
            f"{keyword} music",
            f"{keyword} songs",
            f"best {keyword}",
            f"top {keyword}",
            f"{keyword} playlist",
            f"{keyword} mix",
            f"{keyword} compilation",
            f"{keyword} hits",
            f"{keyword} 2024",
            f"{keyword} 2023",
            f"{keyword} remix",
            f"{keyword} official",
            f"{keyword} audio",
            f"{keyword} track",
            f"{keyword} album",
            f"{keyword} radio",
            f"{keyword} live",
            f"{keyword} acoustic",
            f"{keyword} cover",
            f"{keyword} instrumental",
            f"{keyword} version",
            f"{keyword} edition",
            f"{keyword} collection",
            f"{keyword} greatest"
        ]
        
        async with ctx.typing():
            for i, query in enumerate(search_queries[:25]):  # Limiter à 25
                try:
                    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(query, download=False)
                        if 'entries' in info: 
                            info = info['entries'][0]
                        
                        data = {
                            'title': info.get('title', f'Musique {i+1}'),
                            'url': info.get('webpage_url'),
                            'stream': info.get('url'),
                            'thumb': info.get('thumbnail')
                        }
                        
                        self.queues[gid].append(data)
                        added_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    continue
                
                # Petite pause pour éviter de surcharger les requêtes
                if i % 5 == 0:
                    await asyncio.sleep(0.5)
        
        # Si rien n'est en cours de lecture, démarrer la première musique
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused() and self.queues[gid]:
            first_track = self.queues[gid].pop(0)
            await self.start_playing(ctx, first_track)
        
        await ctx.send(f"✅ **{added_count}** musiques ajoutées à la file !{f' ({failed_count} échecs)' if failed_count > 0 else ''}")
        await self.update_display(ctx, f"📋 Liste générée ({added_count} musiques)")

    async def play_next(self, ctx):
        gid = ctx.guild.id
        if gid in self.queues and self.queues[gid]:
            next_track = self.queues[gid].pop(0)
            await self.start_playing(ctx, next_track)
        else:
            self.current_tracks[gid] = None
            await self.update_display(ctx, "🏁 Terminé")

async def setup(bot):
    await bot.add_cog(MusicBot(bot))