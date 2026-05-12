import discord
from discord.ext import commands
import json
import os
from datetime import datetime

EMBED_TYPE_ENABLED = True

# --- GESTIONNAIRE DE CONFIGURATION ---
class EmbedConfigManager:
    DATA_DIR = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(__file__)
                )
            )
        ),
        "data",
        "addons",
        "data_embed_type"
    )
    GLOBAL_FILE = "global_config.json"
    DEFAULT_COLOR = 0x660099
    DEFAULT_FOOTER = "{bot_nom} - /help pour découvrir mes commandes."

    def __init__(self):
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR)

    def _get_path(self, guild_id=None):
        return os.path.join(self.DATA_DIR, f"{guild_id}.json" if guild_id else self.GLOBAL_FILE)

    def load_config(self, guild_id=None):
        path = self._get_path(guild_id)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_config(self, data, guild_id=None):
        path = self._get_path(guild_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def delete_config(self, guild_id=None):
        path = self._get_path(guild_id)
        if os.path.exists(path): os.remove(path)

    def get_resolved_values(self, guild_id, force_global=False):
        server_conf = {} if (force_global or guild_id is None) else (self.load_config(guild_id) or {})
        global_conf = self.load_config(None) or {}
        
        return {
            "color": server_conf.get("color") if server_conf.get("color") is not None else (global_conf.get("color") or self.DEFAULT_COLOR),
            "footer": server_conf.get("footer") or global_conf.get("footer") or self.DEFAULT_FOOTER
        }

    def get_formatted_embed(self, guild, user, bot, title=None, description=None, target_id=None, force_global=False):
        vals = self.get_resolved_values(target_id, force_global=force_global)

        def parse(text):
            if not text: return ""
            placeholders = {
                "{pseudo}": user.display_name,
                "{bot_nom}": bot.user.name,
                "{serveur}": guild.name if guild else "Dev",
                "{membres}": str(guild.member_count) if guild else "0",
                "{date}": datetime.now().strftime("%d/%m/%Y"),
                "{heure}": datetime.now().strftime("%H:%M")
            }
            for key, value in placeholders.items():
                text = text.replace(key, value)
            return text

        embed = discord.Embed(title=title, description=description, color=vals['color'])
        # Suppression du set_author
        if vals['footer']:
            embed.set_footer(text=parse(vals['footer']), icon_url=bot.user.display_avatar.url)
        return embed

config_manager = EmbedConfigManager()

# --- VUE DE DOCUMENTATION ---
class DocEmbedView(discord.ui.View):
    def __init__(self, target_id, user, bot, guild, is_server):
        super().__init__(timeout=60)
        self.embed = config_manager.get_formatted_embed(
            guild=guild, user=user, bot=bot, target_id=target_id,
            title="📚 Détails des Variables Disponibles",
            description="Utilisez ces balises pour personnaliser vos textes :",
            force_global=not is_server
        )
        self.embed.add_field(name="👤 Utilisateur", value="`{pseudo}` : Affiche votre nom d'affichage sur le serveur.", inline=False)
        self.embed.add_field(name="🤖 Bot", value="`{bot_nom}` : Affiche le nom actuel du bot.", inline=False)
        self.embed.add_field(name="🏰 Serveur", value="`{serveur}` : Nom du serveur actuel.\n`{membres}` : Nombre total de membres inscrits.", inline=False)
        self.embed.add_field(name="📅 Horodatage", value="`{date}` : Date du jour.\n`{heure}` : Heure de l'exécution.", inline=False)

# --- MODAL DE CONFIGURATION ---
class ConfigModal(discord.ui.Modal):
    def __init__(self, current_values, is_server_config, guild_id, bot):
        title = f"Édition {'Serveur' if is_server_config else 'Globale'}"
        super().__init__(title=title)
        self.guild_id = guild_id
        self.is_server = is_server_config
        self.bot = bot
        
        self.color_input = discord.ui.TextInput(
            label="Code Couleur (Hex)", default=f"#{current_values['color']:06x}", required=False, min_length=6, max_length=7
        )
        self.footer_input = discord.ui.TextInput(
            label="Texte du Bas (Footer)", default=current_values['footer'], required=False, style=discord.TextStyle.long, max_length=80
        )
        for item in [self.color_input, self.footer_input]:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        raw_color = self.color_input.value.strip().lstrip('#')
        try:
            new_color = int(raw_color, 16) if raw_color else config_manager.DEFAULT_COLOR
        except ValueError:
            return await interaction.response.send_message("❌ Code couleur invalide.", ephemeral=True)

        footer_text = self.footer_input.value or ""
        if len(footer_text) > 80:
            return await interaction.response.send_message(f"❌ Le footer ne doit pas dépasser 80 caractères (actuel : {len(footer_text)}).", ephemeral=True)
        data = {"color": new_color, "footer": footer_text}
        config_manager.save_config(data, self.guild_id)
        
        view = EmbedCustomizerView(self.is_server, self.guild_id, self.bot, interaction.user.id)
        await interaction.response.edit_message(embed=view.generate_preview_embed(interaction.user, interaction.guild), view=view)

# --- VUE PRINCIPALE ---
class EmbedCustomizerView(discord.ui.View):
    def __init__(self, is_server_config, target_id, bot, user_id):
        super().__init__(timeout=300)
        self.is_server_config = is_server_config
        self.target_id = target_id
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Vous n'avez pas l'autorisation.", ephemeral=True)
            return False
        return True

    def generate_preview_embed(self, user, guild):
        force_glob = not self.is_server_config
        
        # Ajout du lien vers le site de couleurs dans la description
        desc = (
            "Voici un aperçu de vos réglages actuels.\n\n"
            "🎨 **Trouver une couleur :** [Cliquez ici](https://htmlcolorcodes.com/fr/)\n"
            "📖 *Cliquez sur Documentation pour voir les balises.*"
        )
        
        embed = config_manager.get_formatted_embed(
            guild=guild, user=user, bot=self.bot, target_id=self.target_id,
            description=desc, force_global=force_glob
        )
        embed.title = f"🛠️ {'Configuration Serveur' if self.is_server_config else 'Configuration Globale'}"
        return embed

    @discord.ui.button(label="Modifier", style=discord.ButtonStyle.blurple, emoji="✏️")
    async def customize_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = self.target_id if self.is_server_config else None
        current_vals = config_manager.load_config(gid) or config_manager.get_resolved_values(gid, force_global=not self.is_server_config)
        await interaction.response.send_modal(ConfigModal(current_vals, self.is_server_config, gid, self.bot))

    @discord.ui.button(label="Variables", style=discord.ButtonStyle.gray, emoji="📚")
    async def doc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        doc_view = DocEmbedView(self.target_id, interaction.user, self.bot, interaction.guild, self.is_server_config)
        await interaction.response.send_message(embed=doc_view.embed, ephemeral=True)

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.red, emoji="🗑️")
    async def reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config_manager.delete_config(self.target_id if self.is_server_config else None)
        await interaction.response.edit_message(embed=self.generate_preview_embed(interaction.user, interaction.guild), view=self)