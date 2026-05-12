import discord
from discord.ext import commands
from discord import ui
import datetime
from typing import Optional, List, Dict, Any
import traceback
import json
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ----------------------------- UI / VIEWS -------------------------------------
# ==============================================================================

class GuildInviteView(ui.View):
    """Vue pour générer ou récupérer une invitation de serveur (Check Serveur)"""
    def __init__(self, bot: commands.Bot, guild: discord.Guild, author: discord.User, cog: commands.Cog):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.guild = guild
        self.author = author
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Vous n'êtes pas autorisé à utiliser ce bouton.", ephemeral=True)
            return False
        return True

    @ui.button(label="Rejoindre", style=discord.ButtonStyle.success, emoji="🔗")
    async def generate_invite(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        invite_info = None
        try:
            # 1. Chercher une invitation valide existante (> 10 minutes ou infinie)
            invites = await self.guild.invites()
            for inv in invites:
                if inv.max_age == 0 or inv.max_age > 600:
                    invite_info = f"✅ **Lien existant trouvé :**\n{inv.url}"
                    break
            
            # 2. S'il n'y en a pas, on en crée une éphémère (10 min, 1 usage)
            if not invite_info:
                for channel in self.guild.text_channels:
                    if channel.permissions_for(self.guild.me).create_instant_invite:
                        new_invite = await channel.create_invite(max_age=600, max_uses=1, reason="Owner requested check")
                        invite_info = f"✨ **Nouveau lien généré** *(Usage unique, expire dans 10m)* :\n{new_invite.url}"
                        break

        except discord.Forbidden:
            invite_info = "❌ Permissions insuffisantes pour voir ou créer une invitation sur ce serveur."
        except Exception as e:
            invite_info = f"❌ Erreur: {str(e)}"

        if not invite_info:
            invite_info = "❌ Aucun salon textuel disponible ou permission manquante."

        original_message = interaction.message
        embed = original_message.embeds[0]
        
        if "### 🔗 Accès au Serveur" in embed.description:
            parts = embed.description.split("### 🔗 Accès au Serveur")
            embed.description = parts[0] + f"### 🔗 Accès au Serveur\n{invite_info}"
        else:
            embed.description += f"\n\n### 🔗 Accès au Serveur\n{invite_info}"

        await interaction.edit_original_response(embed=embed, view=self)


class UserPaginationView(ui.View):
    """Vue avec pagination pour afficher les serveurs en commun (Check Utilisateur)"""
    def __init__(self, cog: commands.Cog, target_user: discord.User, author: discord.User, 
                 status_str: str, voice_str: str, guilds_list: List[str]):
        super().__init__(timeout=300.0)
        self.cog = cog
        self.target_user = target_user
        self.author = author
        self.status_str = status_str
        self.voice_str = voice_str
        self.guilds_list = guilds_list
        self.current_page = 0
        self.per_page = 5
        self.max_pages = max(1, (len(self.guilds_list) + self.per_page - 1) // self.per_page)
        
        self._update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Ce menu ne vous appartient pas.", ephemeral=True)
            return False
        return True

    def _update_buttons(self):
        self.btn_prev.disabled = self.current_page == 0
        self.btn_next.disabled = self.current_page >= self.max_pages - 1
        self.btn_counter.label = f"Page {self.current_page + 1}/{self.max_pages}"

    def build_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        current_guilds = self.guilds_list[start_idx:end_idx]

        if not current_guilds:
            shared_guilds_str = "*Aucun serveur en commun trouvé.*"
        else:
            shared_guilds_str = "\n".join(current_guilds)

        # Emoji d'état devant le pseudo
        pseudo = f"{self.status_str} {self.target_user.display_name}"

        desc = ""
        if self.voice_str:
            desc += f"**Vocal** : {self.voice_str}\n"
        desc += f"\n### 🌐 Serveurs en commun : `{len(self.guilds_list)}`\n{shared_guilds_str}"

        # Embed sans titre, pseudo dans l'auteur avec avatar
        embed = self.cog.create_custom_embed(None, self.author, None, desc)
        embed.remove_author()
        embed.set_author(name=pseudo, icon_url=self.target_user.display_avatar.url)
        if self.target_user.avatar:
            embed.set_thumbnail(url=self.target_user.avatar.url)
        if self.target_user.banner:
            embed.set_image(url=self.target_user.banner.url)
        return embed

    @ui.button(label="◀", style=discord.ButtonStyle.secondary, custom_id="btn_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True, custom_id="btn_counter")
    async def btn_counter(self, interaction: discord.Interaction, button: ui.Button):
        pass # Bouton indicatif

    @ui.button(label="▶", style=discord.ButtonStyle.secondary, custom_id="btn_next")
    async def btn_next(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


# ==============================================================================
# ----------------------------- COG CHECK INFO ---------------------------------
# ==============================================================================

class OwnerCheck(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # --- Système de Tracker de Commandes ---
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.last_cmd_file = self.data_dir / "last_commands.json"
        self.last_commands: Dict[str, Dict[str, Any]] = self._load_last_commands()

    # --- Gestion JSON Last Commands ---
    def _load_last_commands(self) -> dict:
        if self.last_cmd_file.exists():
            try:
                with open(self.last_cmd_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_last_commands(self):
        try:
            with open(self.last_cmd_file, "w", encoding="utf-8") as f:
                json.dump(self.last_commands, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CheckInfo] Erreur sauvegarde last_commands.json : {e}")

    def _update_last_command(self, guild_id: int, cmd_name: str, user: discord.User):
        """Met à jour le fichier de log pour la dernière commande du serveur."""
        now = datetime.datetime.now().strftime("[%d/%m/%y] %H:%M")
        self.last_commands[str(guild_id)] = {
            "time": now,
            "cmd": cmd_name,
            "user_id": user.id,
            "user_name": user.display_name
        }
        self._save_last_commands()

    # --- Écouteurs pour traquer les commandes ---
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Traque les commandes prefixées."""
        if ctx.guild:
            self._update_last_command(ctx.guild.id, f"/{ctx.command.name}", ctx.author)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        """Traque les commandes Slash."""
        if interaction.guild:
            self._update_last_command(interaction.guild.id, f"/{command.name}", interaction.user)

    # --- Utilitaires ---
    def create_custom_embed(self, guild: Optional[discord.Guild], user: discord.User, title: str, description: str) -> discord.Embed:
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title=title,
                description=description
            )
        embed = discord.Embed(title=title, description=description, color=0x2b2d31)
        return embed

    def get_status_format(self, status: discord.Status) -> str:
        """Retourne uniquement l'emoji du statut Discord."""
        if status == discord.Status.online:
            return "🟢"
        elif status == discord.Status.idle:
            return "🟠"
        elif status == discord.Status.dnd:
            return "🔴"
        else:
            return "⚫"

    # --- Commande Principale ---
    @commands.hybrid_command(
        name="check", 
        description="[Owner] Inspecte un ID pour obtenir des informations détaillées (Serveur ou Utilisateur)."
    )
    @commands.is_owner()
    @discord.app_commands.describe(target_id="L'ID du serveur ou de l'utilisateur à inspecter")
    async def check(self, ctx: commands.Context, target_id: str):
        print("[CHECK] Commande check appelée avec:", target_id)
        await ctx.defer(ephemeral=False)

        if not target_id.isdigit():
            print("[CHECK] ID non numérique")
            return await ctx.send("❌ L'ID fourni n'est pas valide (chiffres uniquement).", ephemeral=True)
            
        obj_id = int(target_id)
        
        # 1. EST-CE UN SERVEUR ?
        guild = self.bot.get_guild(obj_id)
        if guild:
            print(f"[CHECK] ID {obj_id} correspond à un serveur : {guild.name}")
            return await self._handle_guild_check(ctx, guild)

        # 2. EST-CE UN UTILISATEUR ?
        try:
            print(f"[CHECK] Tentative de récupération utilisateur pour ID {obj_id}")
            user = await self.bot.fetch_user(obj_id)
            print(f"[CHECK] Utilisateur fetch_user : {user}")
            if user:
                return await self._handle_user_check(ctx, user)
        except discord.NotFound:
            print(f"[CHECK] Utilisateur non trouvé pour ID {obj_id}")
        except discord.HTTPException as e:
            print(f"[CHECK] HTTPException lors du fetch_user : {e}")

        print(f"[CHECK] Aucun serveur ou utilisateur trouvé pour ID {obj_id}")
        await ctx.send("❌ Impossible de trouver un Serveur ou un Utilisateur correspondant à cet ID.")

    async def _handle_guild_check(self, ctx: commands.Context, guild: discord.Guild):
        """Traitement Check Serveur"""
        humans = [m for m in guild.members if not m.bot]
        bots = [m for m in guild.members if m.bot]
        
        humans_online = [m for m in humans if m.status != discord.Status.offline]
        bots_online = [m for m in bots if m.status != discord.Status.offline]
        total_online = len(humans_online) + len(bots_online)

        if guild.me.joined_at:
            joined_days = (discord.utils.utcnow() - guild.me.joined_at).days
            joined_date_str = guild.me.joined_at.strftime("%d/%m/%y")
            bot_presence = f"[{joined_date_str}] - Rejoint il y a {joined_days} jours"
        else:
            bot_presence = "Date inconnue"

        owner_mention = f"<@{guild.owner_id}>" if guild.owner_id else "Inconnu"
        owner_name = guild.owner.display_name if guild.owner else "Inconnu"

        # Récupération de la dernière commande depuis le JSON

        last_cmd_data = self.last_commands.get(str(guild.id))
        if last_cmd_data:
            last_cmd_str = (
                f"**Dernière commande** : {last_cmd_data['time']} | `{last_cmd_data['cmd']}`\n"
                f"-> {last_cmd_data['user_name']} - `{last_cmd_data['user_id']}`"
            )
        else:
            last_cmd_str = ""

        desc = (
    f"**Serveur** : {guild.name}\n"
    f"-> `{guild.id}`\n\n"
    f"**Owner** : {owner_mention}\n"
    f"-> `{guild.owner_id}`\n\n"
    f"👥 Membres Total : `{guild.member_count}`\n"
    f"› 👤 Humains : `{len(humans)}`\n"
    f"› 🤖 Bots : `{len(bots)}`\n\n"
    f"🟢 Membres Connectés : `{total_online}`\n"
    f"› 👤 Humains : `{len(humans_online)}`\n"
    f"› 🤖 Bots : `{len(bots_online)}`\n\n"
    f"{last_cmd_str}"
)

        # Supprimer le saut de ligne final si pas de commande
        desc = desc.rstrip("\n")

        # Ligne de présence du bot tout en bas, formatée
        if guild.me.joined_at:
            joined_days = (discord.utils.utcnow() - guild.me.joined_at).days
            joined_date_str = guild.me.joined_at.strftime("%d/%m/%y")
            presence_line = f"\n\n📅 *[{joined_date_str}] - Rejoint il y a **{joined_days}** jours*"
        else:
            presence_line = ""
        desc += presence_line

        embed = self.create_custom_embed(ctx.guild, ctx.author, guild.name, desc)
        
        if guild.owner:
            embed.set_author(name=f"Géré par {owner_name}", icon_url=guild.owner.display_avatar.url)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        view = GuildInviteView(self.bot, guild, ctx.author, self)
        
        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)

    async def _handle_user_check(self, ctx: commands.Context, user: discord.User):
        print(f"[CHECK] _handle_user_check appelé pour user : {user} ({user.id})")
        """Traitement Check Utilisateur"""
        raw_guilds = []
        voice_str = ""
        highest_status = discord.Status.offline

        # Récupération des données brutes
        for guild in self.bot.guilds:
            member = guild.get_member(user.id)
            if member:
                print(f"[CHECK] Utilisateur trouvé dans le serveur : {guild.name}")
                # Évaluation de l'importance (Tier 1 = Owner, 4 = Membre)
                tier = 4
                emoji = "👤"
                if member.guild.owner_id == member.id:
                    tier = 1; emoji = "👑"
                elif member.guild_permissions.administrator:
                    tier = 2; emoji = "🛠️"
                elif member.guild_permissions.manage_guild or member.guild_permissions.manage_messages:
                    tier = 3; emoji = "🛡️"
                
                raw_guilds.append({
                    "tier": tier,
                    "emoji": emoji,
                    "count": guild.member_count,
                    "name": guild.name,
                    "id": guild.id
                })

                # Garder le statut le plus "actif"
                if member.status != discord.Status.offline and highest_status == discord.Status.offline:
                    highest_status = member.status
                elif member.status == discord.Status.online:
                    highest_status = member.status # Priorité max
                
                # Assigner le vocal si trouvé (écrase le précédent si plusieurs, suffisant pour l'owner check)
                if member.voice and member.voice.channel:
                    voice_str = f"🎙️ **{guild.name}**\n-> `{member.voice.channel.id}`"

        # Tri de la liste des serveurs : Tier en premier (1 asc), puis par nombre de membres (desc)
        raw_guilds.sort(key=lambda x: (x["tier"], -x["count"]))

        # Formatage des strings selon la nouvelle demande
        guilds_list_str = []
        for g in raw_guilds:
            formatted = f"{g['emoji']} | {g['name']} `{g['id']}`"
            guilds_list_str.append(formatted)

        status_str = self.get_status_format(highest_status)

        # Création et envoi avec Pagination
        print(f"[CHECK] Serveurs trouvés : {len(guilds_list_str)}")
        view = UserPaginationView(self, user, ctx.author, status_str, voice_str, guilds_list_str)
        embed = view.build_embed()

        if ctx.interaction:
            print("[CHECK] Envoi via interaction.followup.send")
            await ctx.interaction.followup.send(embed=embed, view=view if view.max_pages > 1 else discord.utils.MISSING)
        else:
            print("[CHECK] Envoi via ctx.send")
            await ctx.send(embed=embed, view=view if view.max_pages > 1 else discord.utils.MISSING)


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCheck(bot))