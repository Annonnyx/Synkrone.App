import discord
import json
import os
import logging
from discord import app_commands, ui
from discord.ext import commands

# Gestionnaire d'importation
logger = logging.getLogger('UpdateClient')

try:
    from .utils import config_manager
    HAS_CUSTOM_EMBED = True
    logger.debug("Utils importés depuis le module local")
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
        HAS_CUSTOM_EMBED = True
        logger.debug("Utils importés depuis developpeur.commands.embed_type")
    except ImportError:
        config_manager = None
        HAS_CUSTOM_EMBED = False
        logger.warning("Aucun config_manager trouvé, utilisation des embeds par défaut")

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UpdateClient')

# --- CONSTANTES ---
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
_BOT_NAME = os.getenv("BOT_NAME", "SynkroneBot")
CHANNEL_NAME = f"🌀│{_BOT_NAME}-Update"
ROLE_NAME = f"🌀│{_BOT_NAME}-Update"
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/p768u2Pgp3")
SUPPORT_TITLE = os.getenv("SUPPORT_TITLE", "Synkrone Support")

# --- UTILITAIRES ---
def get_config_path(guild_id):
    if not os.path.exists(DATA_DIR):
        logger.info(f"Création du dossier data: {DATA_DIR}")
        os.makedirs(DATA_DIR)
    path = os.path.join(DATA_DIR, f"{guild_id}.json")
    logger.debug(f"Chemin de config pour guild {guild_id}: {path}")
    return path

def load_config(guild_id):
    path = get_config_path(guild_id)
    logger.debug(f"Chargement de la config pour guild {guild_id} depuis: {path}")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.debug(f"Config chargée pour guild {guild_id}: {config}")
                return config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la config pour guild {guild_id}: {e}")
            return {"channel_id": None, "role_id": None}
    else:
        logger.debug(f"Fichier de config non trouvé pour guild {guild_id}, utilisation des valeurs par défaut")
        return {"channel_id": None, "role_id": None}

def save_config(guild_id, data):
    path = get_config_path(guild_id)
    logger.debug(f"Sauvegarde de la config pour guild {guild_id}: {data}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.debug(f"Config sauvegardée avec succès pour guild {guild_id}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la config pour guild {guild_id}: {e}")
        raise

async def get_themed_embed(bot, guild, user, description):
    """Génère l'embed avec titre et URL forcés"""
    logger.debug(f"Génération d'un themed embed pour guild {guild.id} par user {user.id}")
    
    # Titre et URL imposés par la demande
    title = SUPPORT_TITLE
    url = SUPPORT_URL
    logger.debug(f"Titre: {title}, URL: {url}")

    if config_manager:
        logger.debug("Utilisation du config_manager pour l'embed")
        try:
            embed = config_manager.get_formatted_embed(guild, user, bot, title, description, guild.id)
            # On force ces valeurs même si le config_manager en met d'autres
            embed.title = title
            embed.url = url
            embed.set_thumbnail(url=bot.user.display_avatar.url)
            logger.debug("Embed custom généré avec succès")
            return embed
        except Exception as e:
            logger.error(f"Erreur avec le config_manager: {e}")
            logger.debug("Utilisation de l'embed par défaut en fallback")
    
    logger.debug("Utilisation de l'embed par défaut")
    embed = discord.Embed(title=title, url=url, description=description, color=0x2ecc71)
    embed.set_footer(text=f"Configuration Update • {guild.name}", icon_url=guild.icon.url if guild.icon else None)
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    return embed

# --- MODAL CHANGEMENT ID ---
class ChangeChannelIDModal(ui.Modal, title="Modifier les IDs"):
    def __init__(self, view_instance):
        super().__init__()
        self.view_instance = view_instance
        
        # Récupérer la config actuelle
        config = load_config(view_instance.guild_id)
        current_channel_id = config.get("channel_id")
        current_role_id = config.get("role_id")
        
        # Créer les champs avec les IDs actuels en placeholder
        self.channel_id_input = ui.TextInput(
            label="ID du Salon (laisser vide si non modifié)", 
            placeholder=f"Actuel: {current_channel_id if current_channel_id else 'Non configuré'}", 
            required=False, 
            max_length=20
        )
        self.role_id_input = ui.TextInput(
            label="ID du Rôle (laisser vide si non modifié)", 
            placeholder=f"Actuel: {current_role_id if current_role_id else 'Non configuré'}", 
            required=False, 
            max_length=20
        )
        
        # Ajouter les champs au modal
        self.add_item(self.channel_id_input)
        self.add_item(self.role_id_input)

    async def on_submit(self, interaction: discord.Interaction):
        logger.debug(f"Modal changement IDs soumis par {interaction.user.id}")
        try:
            guild = interaction.guild
            config = load_config(guild.id)
            logger.debug(f"Config avant modification: {config}")
            
            changes_made = []
            deletions_made = []
            
            # Traitement du salon
            if self.channel_id_input.value.strip():
                new_channel_id = int(self.channel_id_input.value)
                logger.debug(f"Changement salon ID: {new_channel_id}")
                
                channel = guild.get_channel(new_channel_id)
                logger.debug(f"Channel trouvé: {channel.name if channel else 'Non trouvé'}")
                
                if not channel:
                    logger.warning(f"Channel {new_channel_id} introuvable")
                    return await interaction.response.send_message("❌ Salon introuvable avec cet ID.", ephemeral=True)
                
                # Supprimer l'ancien salon s'il existe et s'il a été créé par le bot
                old_channel_id = config.get("channel_id")
                if old_channel_id:
                    old_channel = guild.get_channel(old_channel_id)
                    if old_channel and old_channel.name == CHANNEL_NAME:
                        try:
                            await old_channel.delete(reason="Remplacement par salon manuel")
                            deletions_made.append(f"Ancien salon '{old_channel.name}' supprimé")
                            logger.debug(f"Ancien salon {old_channel.name} supprimé")
                        except discord.Forbidden:
                            logger.warning("Permission refusée pour supprimer l'ancien salon")
                        except Exception as e:
                            logger.error(f"Erreur suppression ancien salon: {e}")
                
                config["channel_id"] = new_channel_id
                changes_made.append(f"Salon: {channel.mention}")
                logger.debug(f"Channel ID mis à jour: {new_channel_id}")
            
            # Traitement du rôle
            if self.role_id_input.value.strip():
                new_role_id = int(self.role_id_input.value)
                logger.debug(f"Changement rôle ID: {new_role_id}")
                
                role = guild.get_role(new_role_id)
                logger.debug(f"Rôle trouvé: {role.name if role else 'Non trouvé'}")
                
                if not role:
                    logger.warning(f"Rôle {new_role_id} introuvable")
                    return await interaction.response.send_message("❌ Rôle introuvable avec cet ID.", ephemeral=True)
                
                # Supprimer l'ancien rôle s'il existe et s'il a été créé par le bot
                old_role_id = config.get("role_id")
                if old_role_id:
                    old_role = guild.get_role(old_role_id)
                    if old_role and old_role.name == ROLE_NAME:
                        try:
                            await old_role.delete(reason="Remplacement par rôle manuel")
                            deletions_made.append(f"Ancien rôle '{old_role.name}' supprimé")
                            logger.debug(f"Ancien rôle {old_role.name} supprimé")
                        except discord.Forbidden:
                            logger.warning("Permission refusée pour supprimer l'ancien rôle")
                        except Exception as e:
                            logger.error(f"Erreur suppression ancien rôle: {e}")
                
                config["role_id"] = new_role_id
                changes_made.append(f"Rôle: {role.mention}")
                logger.debug(f"Role ID mis à jour: {new_role_id}")
            
            if not changes_made:
                return await interaction.response.send_message("❌ Aucun changement effectué.", ephemeral=True)
            
            save_config(guild.id, config)
            logger.debug(f"Config sauvegardée: {config}")
            
            await self.view_instance.update_display(interaction)
            
            # Message de confirmation avec les suppressions
            message = "✅ IDs mis à jour:\n" + "\n".join(changes_made)
            if deletions_made:
                message += "\n\n🗑️ Nettoyage automatique:\n" + "\n".join(deletions_made)
            
            await interaction.followup.send(message, ephemeral=True)
            logger.debug("Modal changement IDs traité avec succès")
            
        except ValueError:
            logger.error(f"Erreur de conversion ID")
            await interaction.response.send_message("❌ ID invalide.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur dans on_submit modal IDs: {e}")
            await interaction.followup.send("❌ Erreur lors de la mise à jour", ephemeral=True)

# --- VUE DE CONFIGURATION ---
class UpdateConfigView(ui.View):
    def __init__(self, bot, guild_id):
        logger.debug(f"Initialisation de UpdateConfigView pour guild {guild_id}")
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.config = load_config(guild_id)
        logger.debug(f"Config initiale: {self.config}")
        self.update_buttons()

    def update_buttons(self):
        logger.debug(f"Mise à jour des boutons avec config: {self.config}")
        
        # Bouton Salon
        has_channel = self.config.get("channel_id") is not None
        self.toggle_channel_btn.style = discord.ButtonStyle.success if has_channel else discord.ButtonStyle.danger
        self.toggle_channel_btn.emoji = "✅" if has_channel else "🔴"
        self.toggle_channel_btn.label = "Salon Update (Activé)" if has_channel else "Salon Update (Désactivé)"
        logger.debug(f"Bouton salon: {self.toggle_channel_btn.label}")
        
        # Bouton Rôle
        has_role = self.config.get("role_id") is not None
        self.toggle_role_btn.style = discord.ButtonStyle.success if has_role else discord.ButtonStyle.danger
        self.toggle_role_btn.emoji = "✅" if has_role else "🔴"
        self.toggle_role_btn.label = "Rôle Notif (Activé)" if has_role else "Rôle Notif (Désactivé)"
        logger.debug(f"Bouton rôle: {self.toggle_role_btn.label}")

    async def update_display(self, interaction):
        """Met à jour l'embed et la vue"""
        # Gérer le cas où c'est un Context au lieu d'une Interaction
        user = interaction.user if hasattr(interaction, 'user') else interaction.author
        guild = interaction.guild if hasattr(interaction, 'guild') else interaction.author.guild
        
        logger.debug(f"Mise à jour de l'affichage pour guild {self.guild_id} par {user.id}")
        try:
            self.config = load_config(self.guild_id) # Reload config
            logger.debug(f"Config rechargée: {self.config}")
            self.update_buttons()
            
            channel = guild.get_channel(self.config.get("channel_id")) if self.config.get("channel_id") else None
            role = guild.get_role(self.config.get("role_id")) if self.config.get("role_id") else None
            
            logger.debug(f"Channel: {channel.name if channel else 'None'}, Role: {role.name if role else 'None'}")

            # Correction de l'affichage du salon pour éviter les doublons
            channel_display = channel.mention if channel else "`❌ Non configuré`"
            role_display = role.mention if role else "`❌ Non configuré`"

            desc = (
                f"### 📢 Configuration des Updates\n"
                f"Gérez ici le salon où seront publiées les nouveautés du bot.\n\n"
                f"**📺 Salon d'Update :** {channel_display}\n"
                f"> *{channel.jump_url if channel else 'Aucun lien'}*\n"
                f"Note : Vous pouvez renommer le salon comme vous le souhaitez.\n\n"
                f"**🔔 Rôle de Notification :** {role_display}\n"
                f"> Ce rôle permet de notifier les membres lors d'une update et donne la visibilité sur le salon."
            )
            
            embed = await get_themed_embed(self.bot, guild, user, desc)
            
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                logger.debug("Response pas encore faite, utilisation de response.edit_message")
                await interaction.response.edit_message(embed=embed, view=self)
            elif hasattr(interaction, 'edit_original_response'):
                logger.debug("Response déjà faite, utilisation de edit_original_response")
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                # Cas pour les commandes textuelles classiques
                logger.debug("Envoi d'un nouveau message pour commande textuelle")
                await interaction.send(embed=embed, view=self)
            
            logger.debug("Affichage mis à jour avec succès")
        except Exception as e:
            logger.error(f"Erreur dans update_display: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    @ui.button(custom_id="conf_up_channel")
    async def toggle_channel_btn(self, interaction: discord.Interaction, button: ui.Button):
        logger.debug(f"Bouton salon cliqué par {interaction.user.id}")
        guild = interaction.guild
        config = load_config(guild.id)
        current_id = config.get("channel_id")
        logger.debug(f"Channel ID actuel: {current_id}")

        if current_id:
            logger.debug("Désactivation et suppression du salon")
            # --- DÉSACTIVATION ET SUPPRESSION ---
            channel = guild.get_channel(current_id)
            logger.debug(f"Channel à supprimer: {channel.name if channel else 'Non trouvé'}")
            
            if channel:
                try:
                    await channel.delete(reason="Désactivation Update par l'admin")
                    logger.debug(f"Channel {channel.name} supprimé avec succès")
                except discord.NotFound:
                    logger.warning("Channel déjà supprimé manuellement")
                    pass # Déjà supprimé manuellement
                except discord.Forbidden:
                    logger.error("Permission refusée pour supprimer le channel")
                    return await interaction.response.send_message("❌ Je n'ai pas la permission de supprimer le salon.", ephemeral=True)
            
            config["channel_id"] = None
            
            # Désactiver automatiquement le rôle si le salon est désactivé
            role_id = config.get("role_id")
            if role_id:
                logger.debug("Désactivation automatique du rôle car le salon est désactivé")
                role = guild.get_role(role_id)
                if role:
                    try:
                        await role.delete(reason="Désactivation automatique (salon supprimé)")
                        logger.debug(f"Rôle {role.name} supprimé automatiquement")
                    except discord.NotFound:
                        logger.warning("Rôle déjà supprimé manuellement")
                    except discord.Forbidden:
                        logger.warning("Permission refusée pour supprimer le rôle automatiquement")
                config["role_id"] = None
                logger.debug("Rôle désactivé automatiquement")
            
            save_config(guild.id, config)
            logger.debug("Channel et rôle désactivés")
            
            # Message informatif
            await interaction.response.send_message(
                "✅ Salon d'update désactivé.\n🔔 Le rôle de notification a été automatiquement désactivé car il n'a pas de salon associé.", 
                ephemeral=True
            )

        else:
            logger.debug("Activation et création du salon")
            # --- ACTIVATION ET CRÉATION ---
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True),
            }
            logger.debug(f"Overwrites de base créés")
            
            # Si un rôle est déjà configuré, on lui donne la vue
            if config.get("role_id"):
                role_obj = guild.get_role(config["role_id"])
                if role_obj:
                    overwrites[role_obj] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    logger.debug(f"Permissions ajoutées pour le rôle {role_obj.name}")

            try:
                channel = await guild.create_text_channel(CHANNEL_NAME, overwrites=overwrites, reason="Config Update Bot")
                config["channel_id"] = channel.id
                save_config(guild.id, config)
                logger.debug(f"Channel {channel.name} créé avec ID: {channel.id}")
            except discord.Forbidden:
                logger.error("Permission refusée pour créer le channel")
                return await interaction.response.send_message("❌ Je n'ai pas la permission de gérer les salons.", ephemeral=True)
            except Exception as e:
                logger.error(f"Erreur lors de la création du channel: {e}")
                return await interaction.response.send_message("❌ Erreur lors de la création du salon.", ephemeral=True)

        await self.update_display(interaction)

    @ui.button(custom_id="conf_up_role")
    async def toggle_role_btn(self, interaction: discord.Interaction, button: ui.Button):
        logger.debug(f"Bouton rôle cliqué par {interaction.user.id}")
        guild = interaction.guild
        config = load_config(guild.id)
        current_id = config.get("role_id")
        logger.debug(f"Role ID actuel: {current_id}")

        if current_id:
            logger.debug("Désactivation et suppression du rôle")
            # --- DÉSACTIVATION ET SUPPRESSION DU RÔLE ---
            role = guild.get_role(current_id)
            logger.debug(f"Rôle à supprimer: {role.name if role else 'Non trouvé'}")
            
            if role:
                try:
                    await role.delete(reason="Désactivation Update par l'admin")
                    logger.debug(f"Rôle {role.name} supprimé avec succès")
                except discord.NotFound:
                    logger.warning("Rôle déjà supprimé manuellement")
                    pass
                except discord.Forbidden:
                    logger.error("Permission refusée pour supprimer le rôle")
                    return await interaction.response.send_message("❌ Je n'ai pas la permission de supprimer le rôle.", ephemeral=True)
            
            config["role_id"] = None
            save_config(guild.id, config)
            logger.debug("Role ID désactivé")

            # On retire aussi la perm du salon si le salon existe encore
            if config.get("channel_id"):
                chan = guild.get_channel(config["channel_id"])
                if chan:
                    logger.debug("Nettoyage des permissions du salon")
                    # On remet les perms par défaut pour le role (qui n'existe plus de toute façon, mais on nettoie l'overwrite si l'objet restait en cache)
                    pass 

        else:
            logger.debug("Activation et création du rôle")
            # --- ACTIVATION ET CRÉATION DU RÔLE ---
            try:
                role = await guild.create_role(name=ROLE_NAME, mentionable=True, reason="Config Update Bot")
                config["role_id"] = role.id
                save_config(guild.id, config)
                logger.debug(f"Rôle {role.name} créé avec ID: {role.id}")

                # Mise à jour des perms du salon si existant
                if config.get("channel_id"):
                    chan = guild.get_channel(config["channel_id"])
                    if chan:
                        await chan.set_permissions(role, read_messages=True, send_messages=False)
                        logger.debug(f"Permissions du rôle mises à jour pour le salon {chan.name}")
                
                await interaction.channel.send(
                    f"💡 **Conseil :**\n"
                    f"- Attribuez le rôle {role.mention} à votre équipe staff.\n"
                    f"- Utilisez `!embed`, `!rolemenu` ou l'autorôle Discord pour permettre aux membres de choisir ce rôle."
                , delete_after=60)
                logger.debug("Message de conseil envoyé")

            except discord.Forbidden:
                logger.error("Permission refusée pour créer le rôle")
                return await interaction.response.send_message("❌ Permission manquante pour créer le rôle.", ephemeral=True)
            except Exception as e:
                logger.error(f"Erreur lors de la création du rôle: {e}")
                return await interaction.response.send_message("❌ Erreur lors de la création du rôle.", ephemeral=True)

        await self.update_display(interaction)

    @ui.button(label="Changer IDs", style=discord.ButtonStyle.secondary, emoji="⚙️", custom_id="conf_up_change_id")
    async def change_id_btn(self, interaction: discord.Interaction, button: ui.Button):
        logger.debug(f"Bouton changer IDs cliqué par {interaction.user.id}")
        try:
            await interaction.response.send_modal(ChangeChannelIDModal(self))
            logger.debug("Modal changement IDs envoyé")
        except Exception as e:
            logger.error(f"Erreur dans change_id_btn: {e}")

# --- COG ---
class UpdateClient(commands.Cog):
    def __init__(self, bot):
        logger.debug("Initialisation du cog UpdateClient")
        self.bot = bot

    @commands.hybrid_command(name="update", description="Configurer le salon des mises à jour")
    @commands.has_permissions(administrator=True)
    async def update_cmd(self, ctx):
        logger.info(f"Commande update utilisée par {ctx.author.id} dans {ctx.guild.id}/{ctx.channel.id}")
        
        try:
            view = UpdateConfigView(self.bot, ctx.guild.id)
            logger.debug("Vue créée, mise à jour de l'affichage")
            # Force refresh display logic to create initial embed
            await view.update_display(ctx.interaction if ctx.interaction else ctx)
            logger.debug("Commande update traitée avec succès")
        except Exception as e:
            logger.error(f"Erreur dans la commande update: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await ctx.send("❌ Erreur lors de l'initialisation de la configuration", ephemeral=True)

async def setup(bot):
    logger.debug("Setup du cog UpdateClient")
    try:
        await bot.add_cog(UpdateClient(bot))
        logger.debug("Cog UpdateClient ajouté avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du setup du cog UpdateClient: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise