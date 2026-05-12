import discord
from discord.ext import commands
from discord import ui
from pathlib import Path
import json
import math
import traceback

# --- Configuration & Chemins ---
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "DB"
DB_PATH = DB_DIR / "autoping.json"

# --- Import du Config Manager (Design Premium) ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ------------------------------ UTILITAIRES -----------------------------------
# ==============================================================================

def get_embed(guild, author, bot, title, description, color=0x3498db):
    """Génère un embed visuellement cohérent via le config_manager avec un fallback global."""
    if config_manager:
        try:
            return config_manager.get_formatted_embed(guild, author, bot, title, description)
        except Exception:
            pass
    return discord.Embed(title=title, description=description, color=color)

# ==============================================================================
# --------------------------------- VUES UI ------------------------------------
# ==============================================================================

class AutoPingBaseView(ui.View):
    """Vue de base pour appliquer la restriction d'interaction à tous les menus."""
    def __init__(self, ctx, timeout=300):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Sécurité : Seul l'auteur de la commande peut utiliser les boutons/sélecteurs
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Ce menu ne vous est pas destiné. Vous ne pouvez pas interagir avec.", ephemeral=True)
            return False
        return True

class AutoPingAddView(AutoPingBaseView):
    def __init__(self, cog, ctx, main_view):
        super().__init__(ctx, timeout=300)
        self.cog = cog
        self.main_view = main_view
        self.selected_channel_id = None
        
        # 1er Sélecteur : Les salons
        self.chan_select = ui.ChannelSelect(
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            placeholder="1️⃣ Sélectionnez le salon à surveiller...",
            row=0
        )
        self.chan_select.callback = self.on_channel_select
        self.add_item(self.chan_select)

        # Bouton Retour
        self.return_btn = ui.Button(label="Retour", style=discord.ButtonStyle.secondary, emoji="↩️", row=4)
        self.return_btn.callback = self.on_return
        self.add_item(self.return_btn)

    async def get_current_embed(self):
        if not self.selected_channel_id:
            desc = "Veuillez sélectionner le **salon** dans le menu déroulant ci-dessous."
        else:
            desc = f"✅ Salon sélectionné : <#{self.selected_channel_id}>\n\nVeuillez maintenant sélectionner le **rôle** à ping."
        return get_embed(self.ctx.guild, self.ctx.author, self.cog.bot, "➕ Ajouter un Ping Automatique", desc)

    async def on_channel_select(self, interaction: discord.Interaction):
        self.selected_channel_id = str(self.chan_select.values[0].id)
        
        # Transition : On retire le salon, on place le rôle
        self.remove_item(self.chan_select)
        self.role_select = ui.RoleSelect(placeholder="2️⃣ Sélectionnez le rôle à ping...", row=0)
        self.role_select.callback = self.on_role_select
        
        self.remove_item(self.return_btn)
        self.add_item(self.role_select)
        self.add_item(self.return_btn)

        await interaction.response.edit_message(embed=await self.get_current_embed(), view=self)

    async def on_role_select(self, interaction: discord.Interaction):
        role_id = str(self.role_select.values[0].id)
        
        # SAUVEGARDE EN BASE DE DONNÉES (Persistance)
        self.cog.add_config(str(self.ctx.guild.id), self.selected_channel_id, role_id)
        
        self.clear_items()
        self.add_item(self.return_btn)
        
        desc = f"🎉 **Configuration sauvegardée et mémorisée !**\n\n**Salon** : <#{self.selected_channel_id}>\n**Rôle** : <@&{role_id}>"
        embed = get_embed(self.ctx.guild, self.ctx.author, self.cog.bot, "✅ Succès", desc, color=0x2ecc71)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_return(self, interaction: discord.Interaction):
        embed = self.main_view.get_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.main_view)


class AutoPingListView(AutoPingBaseView):
    def __init__(self, cog, ctx, main_view):
        super().__init__(ctx, timeout=300)
        self.cog = cog
        self.main_view = main_view
        self.page = 0
        self.items_per_page = 5
        self.update_components()

    def get_data(self):
        return self.cog.configs.get(str(self.ctx.guild.id), {})

    def get_list_embed(self):
        data = self.get_data()
        if not data:
            desc = "Aucun ping n'est configuré sur ce serveur actuellement."
            return get_embed(self.ctx.guild, self.ctx.author, self.cog.bot, "📋 Liste des Pings", desc)
        
        items = list(data.items())
        max_pages = math.ceil(len(items) / self.items_per_page)
        start = self.page * self.items_per_page
        page_items = items[start : start + self.items_per_page]

        desc = "**Liste des salons surveillés et leurs rôles associés :**\n\n"
        for i, (chan_id, role_id) in enumerate(page_items, start=start+1):
            desc += f"`{i}.` ➡️ **Salon :** <#{chan_id}> | **Ping :** <@&{role_id}>\n"

        embed = get_embed(self.ctx.guild, self.ctx.author, self.cog.bot, "📋 Liste des Pings", desc)
        if config_manager is None:
            embed.set_footer(text=f"Page {self.page+1}/{max_pages}")
        return embed

    def update_components(self):
        self.clear_items()
        data = self.get_data()
        
        if data:
            items = list(data.items())
            max_pages = math.ceil(len(items) / self.items_per_page)
            start = self.page * self.items_per_page
            page_items = items[start : start + self.items_per_page]

            # Sélecteur de suppression de la page actuelle
            options = []
            for i, (chan_id, role_id) in enumerate(page_items, start=start+1):
                chan = self.ctx.guild.get_channel(int(chan_id))
                chan_name = chan.name if chan else "Salon introuvable"
                options.append(discord.SelectOption(
                    label=f"Supprimer la config n°{i}", 
                    description=f"Salon: {chan_name}", 
                    value=chan_id, 
                    emoji="🗑️"
                ))

            if options:
                del_select = ui.Select(placeholder="🗑️ Choisissez une configuration à supprimer...", options=options, row=0)
                del_select.callback = self.on_delete
                self.add_item(del_select)

            # Boutons de Pagination
            if max_pages > 1:
                prev_btn = ui.Button(label="◀", style=discord.ButtonStyle.primary, row=1, disabled=(self.page == 0))
                prev_btn.callback = self.on_prev
                self.add_item(prev_btn)

                next_btn = ui.Button(label="▶", style=discord.ButtonStyle.primary, row=1, disabled=(self.page == max_pages - 1))
                next_btn.callback = self.on_next
                self.add_item(next_btn)

        # Bouton Retour
        ret_btn = ui.Button(label="Retour", style=discord.ButtonStyle.secondary, emoji="↩️", row=2)
        ret_btn.callback = self.on_return
        self.add_item(ret_btn)

    async def on_delete(self, interaction: discord.Interaction):
        select = [x for x in self.children if isinstance(x, ui.Select)][0]
        chan_id_to_delete = select.values[0]
        
        # SUPPRESSION EN BASE DE DONNÉES (Persistance)
        self.cog.remove_config(str(self.ctx.guild.id), chan_id_to_delete)
        
        data = self.get_data()
        max_pages = max(1, math.ceil(len(data) / self.items_per_page))
        if self.page >= max_pages:
            self.page = max_pages - 1

        self.update_components()
        await interaction.response.edit_message(embed=self.get_list_embed(), view=self)

    async def on_prev(self, interaction: discord.Interaction):
        self.page -= 1
        self.update_components()
        await interaction.response.edit_message(embed=self.get_list_embed(), view=self)

    async def on_next(self, interaction: discord.Interaction):
        self.page += 1
        self.update_components()
        await interaction.response.edit_message(embed=self.get_list_embed(), view=self)

    async def on_return(self, interaction: discord.Interaction):
        embed = self.main_view.get_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.main_view)


class AutoPingMainView(AutoPingBaseView):
    def __init__(self, cog, ctx):
        super().__init__(ctx, timeout=300)
        self.cog = cog

    def get_main_embed(self):
        desc = "Bienvenue dans le panneau de gestion des pings automatiques.\n\n" \
               "Ici, vous pouvez automatiser l'envoi d'un ping à un rôle spécifique dès qu'un message " \
               "est publié dans un de vos salons cibles (idéal pour les annonces inter-serveurs)."
        return get_embed(self.ctx.guild, self.ctx.author, self.cog.bot, "🔔 Interface Auto-Ping", desc)

    @ui.button(label="Ajouter / Modifier", style=discord.ButtonStyle.success, emoji="➕", custom_id="ap_add")
    async def add_btn(self, interaction: discord.Interaction, button: ui.Button):
        view = AutoPingAddView(self.cog, self.ctx, self)
        await interaction.response.edit_message(embed=await view.get_current_embed(), view=view)

    @ui.button(label="Gérer les pings", style=discord.ButtonStyle.primary, emoji="📋", custom_id="ap_list")
    async def list_btn(self, interaction: discord.Interaction, button: ui.Button):
        view = AutoPingListView(self.cog, self.ctx, self)
        await interaction.response.edit_message(embed=view.get_list_embed(), view=view)


# ==============================================================================
# ------------------------------ COG PRINCIPAL ---------------------------------
# ==============================================================================

class AutoPing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chargement immédiat des configurations au démarrage
        self.configs = self._load_config()

    def _load_config(self):
        """Récupère les données sauvegardées sur le disque."""
        try:
            if not DB_PATH.exists():
                DB_DIR.mkdir(parents=True, exist_ok=True)
                return {}
            
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur de chargement AutoPing: {e}")
            return {}

    def _save_config(self):
        """Écrit les données sur le disque en temps réel pour qu'il s'en souvienne au redémarrage."""
        try:
            DB_DIR.mkdir(parents=True, exist_ok=True)
            with open(DB_PATH, "w", encoding="utf-8") as f:
                json.dump(self.configs, f, indent=4)
        except Exception as e:
            print(f"Erreur de sauvegarde AutoPing: {e}")

    def add_config(self, guild_id: str, channel_id: str, role_id: str):
        if guild_id not in self.configs:
            self.configs[guild_id] = {}
        self.configs[guild_id][channel_id] = role_id
        self._save_config() # Sauvegarde immédiate !

    def remove_config(self, guild_id: str, channel_id: str):
        if guild_id in self.configs and channel_id in self.configs[guild_id]:
            del self.configs[guild_id][channel_id]
            self._save_config() # Sauvegarde immédiate !

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Sécurité : Ignore les propres messages du bot, mais écoute les autres (incluant les Webhooks)
        if message.author.id == self.bot.user.id or not message.guild:
            return

        guild_id = str(message.guild.id)
        chan_id = str(message.channel.id)

        # Vérifie si la configuration existe dans la "mémoire" du bot
        if guild_id in self.configs and chan_id in self.configs[guild_id]:
            role_id = self.configs[guild_id][chan_id]
            role = message.guild.get_role(int(role_id))
            
            if role:
                try:
                    # Le ping reste de façon permanente dans le salon (suppression du delete_after)
                    await message.channel.send(f"🔔 {role.mention}")
                except discord.Forbidden:
                    # Le bot n'a pas les permissions dans ce salon
                    pass
                except discord.HTTPException:
                    pass

    @commands.hybrid_command(name="autoping", description="Ouvre le panneau de configuration des pings automatiques")
    @commands.has_permissions(administrator=True)
    async def autoping(self, ctx: commands.Context):
        view = AutoPingMainView(self, ctx)
        embed = view.get_main_embed()
        
        try:
            if ctx.interaction:
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=True)
        except Exception as e:
            traceback.print_exc()

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoPing(bot))