import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import json
import os

# ==============================================================================
# --------------------------- IMPORTATION MANAGER ------------------------------
# ==============================================================================
try:
    from .utils import config_manager
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
    except ImportError:
        config_manager = None

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
# Nouveau chemin pour data_snipe : data/public/utilitaires/
DATA_DIR = os.path.join(BASE_PATH, "..", "..", "..", "..", "data", "public", "utilitaires", "data_snipe")

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Création des dossiers nécessaires pour DATA_DIR
        os.makedirs(DATA_DIR, exist_ok=True)
        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.cancel()

    # --- Gestion Fichiers ---
    def _get_server_path(self, guild_id):
        return os.path.join(DATA_DIR, f"{guild_id}.json")

    def _load_data(self, guild_id):
        path = self._get_server_path(guild_id)
        if not os.path.exists(path): return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}

    def _save_data(self, guild_id, data):
        path = self._get_server_path(guild_id)
        if not data:
            if os.path.exists(path): os.remove(path)
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    # --- Boucle de Nettoyage (24h) ---
    @tasks.loop(hours=1)
    async def cleanup_task(self):
        now = datetime.now(timezone.utc)
        for file in os.listdir(DATA_DIR):
            if file.endswith(".json"):
                gid = file.replace(".json", "")
                data = self._load_data(gid)
                to_delete = []
                for cid, msg in data.items():
                    ts = datetime.fromisoformat(msg['timestamp'])
                    if now - ts >= timedelta(hours=24):
                        self._delete_photo(msg.get('image_id'))
                        to_delete.append(cid)
                for cid in to_delete: del data[cid]
                self._save_data(gid, data)

    # --- Capture des événements ---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild: return
        await self._save_event(message, {"type": "del", "content": message.content})

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        await self._save_event(before, {"type": "edit", "old": before.content, "new": after.content})

    async def _save_event(self, msg, extra):
        gid, cid = msg.guild.id, str(msg.channel.id)
        data = self._load_data(gid)

        # RÈGLE : Vérifier et supprimer l'ancien snipe du salon pour ne garder que le DERNIER
        if cid in data:
            pass

        data[cid] = {
            "author_id": msg.author.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra
        }
        self._save_data(gid, data)

    # --- Commande Snipe ---
    @commands.hybrid_command(name="snipe", description="Affiche la dernière activité (suppression/edit) du salon.")
    async def snipe(self, ctx):
        gid = ctx.guild.id
        cid = str(ctx.channel.id)
        data = self._load_data(gid)
        
        # Vérification et nettoyage forcé si rien n'est trouvé
        if cid not in data:
            # On s'assure qu'aucune image orpheline ne traîne pour ce salon par erreur
            await ctx.send("❌ Aucun message récent trouvé dans ce salon.", ephemeral=True)
            return

        msg_data = data[cid]
        is_del = msg_data['type'] == "del"
        
        # Nouveau format d'embed demandé
        ts = int(datetime.fromisoformat(msg_data['timestamp']).timestamp())
        time_relative = f"<t:{ts}:R>"
        author_mention = f"<@{msg_data['author_id']}>"
        deleter_name = ctx.author.display_name
        deleter_avatar = ctx.author.display_avatar.url
        if is_del:
            description = (
                f"Message supprimé de {author_mention}. "
                f"Le message avait été écrit {time_relative}.\n\n"
                f"**Message :**\n{msg_data['content'] or '*Message vide*'}"
            )
            title = "🗑️ Message Supprimé"
        else:
            description = (
                f"Message modifié par {deleter_name}. "
                f"Le message avait été écrit {time_relative}.\n\n"
                f"**Ancien :**\n```\n{msg_data['old'] or 'Vide'}\n```\n"
                f"**Nouveau :**\n```\n{msg_data['new'] or 'Vide'}\n```"
            )
            title = "✏️ Message Modifié"

        # --- Utilisation du Manager Embed ---
        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=ctx.guild,
                user=ctx.author,
                bot=self.bot,
                title=title,
                description=description,
                target_id=gid
            )
            if is_del:
                embed.set_author(name=f"Supprimé par {deleter_name}", icon_url=deleter_avatar)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)
            if is_del:
                embed.set_author(name=f"Supprimé par {deleter_name}", icon_url=deleter_avatar)
            embed.set_footer(text=f"Demandé par {ctx.author.name}")


        # Image : L'image jointe au message original (si elle existe)
        file = None
        # On n'envoie plus jamais de fichiers (image/vidéo/son), mais on continue de les stocker côté serveur
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Snipe(bot))