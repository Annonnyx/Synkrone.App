import discord
from discord.ext import commands
import json
import os
import traceback
from typing import List, Dict, Any, Optional

# Tentative d'import du manager d'embed
try:
    from cogs.addons.embed_type.utils import config_manager
    HAS_MANAGER = True
except ImportError:
    config_manager = None
    HAS_MANAGER = False

# ==============================================================================
# -------------------------- SYSTEME DE PAGINATION -----------------------------
# ==============================================================================

class SetupDropdown(discord.ui.Select):
    def __init__(self, pages_data: List[Dict[str, str]]):
        options = []
        for index, page in enumerate(pages_data):
            title = page.get("title", f"Page {index + 1}")
            title_parts = title.split(" ", 1)
            if len(title_parts) == 2:
                emoji, label = title_parts
            else:
                emoji, label = None, title
            options.append(
                discord.SelectOption(
                    label=label,
                    description="Voir la page de configuration",
                    emoji=emoji,
                    value=str(index)
                )
            )
        super().__init__(placeholder="Sélectionnez une catégorie...", min_values=1, max_values=1, options=options)
        self.pages_data = pages_data

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        page = self.pages_data[index]
        
        if HAS_MANAGER and config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild,
                user=interaction.user,
                bot=interaction.client,
                title=page["title"],
                description=page["content"],
                target_id=interaction.guild.id
            )
        else:
            embed = discord.Embed(title=page["title"], description=page["content"], color=0x2b2d31)
            embed.set_footer(text=f"Page {index + 1}/{len(self.pages_data)} • {interaction.guild.name}")

        await interaction.response.edit_message(embed=embed, view=self.view)

class SetupView(discord.ui.View):
    def __init__(self, pages_data: List[Dict[str, str]], timeout: int = 180):
        super().__init__(timeout=timeout)
        self.add_item(SetupDropdown(pages_data))

class JoinServer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def load_config(self) -> Optional[Dict[str, Any]]:
        """Charge la configuration locale du cog."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'config.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Erreur : 'config.json' absent dans {current_dir}")
            return None
        except Exception as e:
            print(f"❌ Erreur lecture JSON : {e}")
            return None
            
    def get_setup_pages(self) -> List[Dict[str, str]]:
        """Retourne les pages de configuration avec recommandations et emojis."""
        # Charger la configuration
        config = self.load_config()
        if not config or "setup_pages" not in config:
            # Retourner une configuration par défaut si le chargement échoue
            return [
                {
                    "title": "⚠️ Configuration non chargée", 
                    "content": "Impossible de charger la configuration. Vérifiez le fichier config.json"
                }
            ]
        return config["setup_pages"]

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Gère l'arrivée du bot sur un nouveau serveur."""
        # 1. Chargement de la configuration
        config = self.load_config()
        if not config:
            return

        # 2. Configuration des permissions du salon
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True, 
                embed_links=True,
                read_message_history=True
            ),
            guild.owner: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True
            )
        }

        # Ajout des administrateurs
        for role in guild.roles:
            if role.permissions.administrator and not role.is_default():
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        # 3. Création du salon
        channel_name = f"🤖│{self.bot.user.name}"
        try:
            channel = await guild.create_text_channel(
                channel_name, 
                overwrites=overwrites,
                reason="Création automatique du salon de configuration"
            )

            # 4. Recherche de l'inviteur via les logs d'audit
            inviter_mention = await self._find_inviter_mention(guild)

            # 5. Envoi du message de bienvenue avec le menu de configuration
            await self._send_welcome_message(guild, channel, inviter_mention)
            
        except discord.Forbidden:
            print(f"❌ Permissions insuffisantes sur '{guild.name}' pour créer le salon.")
        except Exception as e:
            print(f"❌ Erreur lors de la configuration du serveur {guild.name}: {e}")
            traceback.print_exc()
    
    async def _find_inviter_mention(self, guild: discord.Guild) -> str:
        """Trouve et retourne la mention de l'utilisateur qui a invité le bot."""
        if not guild.me.guild_permissions.view_audit_log:
            return ""
            
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == self.bot.user.id and entry.user.id != guild.owner_id:
                    return f" & {entry.user.mention}"
        except Exception:
            traceback.print_exc()
        return ""
    
    async def _send_welcome_message(self, guild: discord.Guild, channel: discord.TextChannel, inviter_mention: str):
        """Envoie le message de bienvenue avec le menu de configuration."""
        config = self.load_config()
        if not config:
            return

        # Message d'introduction
        intro_desc = (
            "## 🚀 Bienvenue sur le serveur de configuration !\n"
            "Utilisez le menu déroulant ci-dessous pour explorer les différentes catégories de configuration.\n\n"
            "🛡️ **Sécurité & Modération** : Protection et paramètres sensibles\n"
            "⚙️ **Accueil & Communauté** : Bienvenue, invitations et boosts\n"
            "🎟️ **Système de Tickets** : Configuration complète des tickets\n"
            "📊 **Vocaux & Statistiques** : Voix et stats du serveur\n"
            "🎮 **Jeux & Divertissement** : Fonctionnalités ludiques\n"
            "🔊 **Gestion des Salons Vocaux** : Paramétrage vocal avancé\n\n"
            "⚠️ **CONSEIL :** Pour une efficacité maximale, placez le rôle du bot le plus haut possible."
        )

        # Création de l'embed
        if HAS_MANAGER and config_manager:
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=self.bot.user,
                bot=self.bot,
                title=config.get("embed_title", "🔧 Configuration du Bot"),
                description=intro_desc,
                target_id=guild.id
            )
        else:
            embed = discord.Embed(
                title=config.get("embed_title", "🔧 Configuration du Bot"),
                description=intro_desc,
                color=0x2b2d31
            )
            if self.bot.user.display_avatar:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(text=f"ID du serveur : {guild.id}")

        # Ajout des pages de configuration
        pages = self.get_setup_pages()
        view = SetupView(pages)

        # Envoi du message
        content = f"{guild.owner.mention}{inviter_mention}"
        await channel.send(content=content, embed=embed, view=view)
        
        # Envoi des informations supplémentaires si disponibles
        if "welcome_text" in config or "help_notice" in config:
            welcome_text = config.get('welcome_text', '')
            help_notice = config.get('help_notice', '')
            
            if welcome_text or help_notice:
                embed = discord.Embed(
                    title="📋 Informations complémentaires",
                    description=f"{welcome_text}\n\n{help_notice}",
                    color=0x3498db
                )
                await channel.send(embed=embed)

    @commands.hybrid_command(
        name="setup",
        description="Affiche le menu interactif pour configurer le bot."
    )
    @commands.has_permissions(administrator=True)
    async def setup_command(self, ctx: commands.Context):
        """Affiche le menu de configuration interactif."""
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        pages = self.get_setup_pages()
        
        # Message d'accueil / Intro
        intro_desc = (
            "## 🚀 Configuration du Bot\n"
            "Bienvenue dans votre panneau de configuration ! Voici les catégories :\n\n"
            "🛡️ **Sécurité & Modération** : `Indispensable` pour la protection.\n"
            "⚙️ **Accueil & Communauté** : `Utile` pour les messages et l’accueil.\n"
            "🎟️ **Système de Tickets** : `Support` pour vos membres.\n"
            "📊 **Vocaux & Statistiques** : `Suivi` de l’activité.\n"
            "🎮 **Jeux & Divertissement** : `Fun` pour l’animation.\n"
            "🔊 **Gestion des Salons Vocaux** : `Avancé` pour les vocaux.\n\n"
            "⚠️ **CONSEIL :** Pour une efficacité maximale, placez le rôle du bot le plus haut possible."
        )

        if HAS_MANAGER and config_manager:
            embed = config_manager.get_formatted_embed(
                guild=ctx.guild,
                user=ctx.author,
                bot=self.bot,
                title="Panneau de Contrôle",
                description=intro_desc,
                target_id=ctx.guild.id if ctx.guild else None
            )
        else:
            embed = discord.Embed(
                title="Panneau de Contrôle", 
                description=intro_desc, 
                color=0x3498db
            )
            if self.bot.user.display_avatar:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = SetupView(pages)
        
        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.send(embed=embed, view=view, reference=ctx.message)

async def setup(bot: commands.Bot):
    if bot.get_command("setup"):
        bot.remove_command("setup")
    await bot.add_cog(JoinServer(bot))
