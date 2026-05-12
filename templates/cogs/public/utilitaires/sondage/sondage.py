"""
Module de gestion des sondages pour Discord

Ce module permet de créer et gérer des sondages interactifs avec les fonctionnalités suivantes :
- Création de sondages avec options personnalisables
- Support des votes multiples ou uniques
- Interface interactive pour la configuration et la participation
- Stockage persistant des sondages
- Gestion des votes et affichage des résultats
- Nettoyage automatique des anciens sondages
"""

import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from datetime import datetime, timezone

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

# ==============================================================================
# ----------------------------- CLASSE DE DONNÉES ------------------------------
# ==============================================================================

class Survey:
    def __init__(self, **kwargs):
        self.title = kwargs.get("title", "Nouveau Sondage")
        self.options = kwargs.get("options", [])
        self.description = kwargs.get("description", "")
        self.channel_id = kwargs.get("channel_id")
        self.author_id = kwargs.get("author_id")
        self.guild_id = kwargs.get("guild_id")
        self.is_multiple = kwargs.get("is_multiple", False)
        self.votes = kwargs.get("votes", {}) 
        self.message_id = kwargs.get("message_id")
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc).timestamp())
        self.ended_at = kwargs.get("ended_at")

    def to_dict(self):
        return self.__dict__

# ==============================================================================
# -------------------------- MODALES DE CONFIGURATION --------------------------
# ==============================================================================

class SurveyConfigModal(discord.ui.Modal, title="Contenu du Sondage"):
    def __init__(self, setup_view):
        super().__init__()
        self.setup_view = setup_view
        self.survey_title = discord.ui.TextInput(label="Titre", default=setup_view.survey.title, max_length=100)
        self.survey_desc = discord.ui.TextInput(label="Description", default=setup_view.survey.description, style=discord.TextStyle.paragraph, required=False, max_length=1000)
        self.add_item(self.survey_title)
        self.add_item(self.survey_desc)

    async def on_submit(self, it: discord.Interaction):
        self.setup_view.survey.title = self.survey_title.value
        self.setup_view.survey.description = self.survey_desc.value
        await self.setup_view.update_setup_embed(it)

class SurveyOptionModal(discord.ui.Modal, title="Ajouter des Options"):
    def __init__(self, setup_view):
        super().__init__()
        self.setup_view = setup_view
        remaining = 25 - len(setup_view.survey.options)
        count = min(5, remaining)
        self.inputs = [discord.ui.TextInput(label=f"Option {len(setup_view.survey.options)+i+1}", required=False) for i in range(count)]
        for item in self.inputs: self.add_item(item)

    async def on_submit(self, it: discord.Interaction):
        for i in self.inputs:
            if i.value and i.value.strip():
                if len(self.setup_view.survey.options) < 25:
                    self.setup_view.survey.options.append(i.value.strip())
        await self.setup_view.update_setup_embed(it)

# ==============================================================================
# ------------------------- VUE DE PRÉPARATION (ADMIN) -------------------------
# ==============================================================================

class SurveySetupView(discord.ui.View):
    def __init__(self, cog, survey):
        super().__init__(timeout=600)
        self.cog, self.survey = cog, survey

    def update_components(self):
        self.clear_items()
        
        btn_main = discord.ui.Button(label="Titre/Desc", style=discord.ButtonStyle.secondary, emoji="📝", row=0)
        btn_main.callback = self.main_callback
        self.add_item(btn_main)

        btn_opts = discord.ui.Button(label="Ajouter Options", style=discord.ButtonStyle.secondary, emoji="➕", disabled=len(self.survey.options) >= 25, row=0)
        btn_opts.callback = self.opts_callback
        self.add_item(btn_opts)

        mode_label = "MULTIPLE" if self.survey.is_multiple else "SIMPLE"
        btn_mode = discord.ui.Button(label=f"Mode: {mode_label}", style=discord.ButtonStyle.green if self.survey.is_multiple else discord.ButtonStyle.gray, emoji="🔄", row=0)
        btn_mode.callback = self.mode_callback
        self.add_item(btn_mode)

        if self.survey.options:
            select = discord.ui.Select(
                placeholder="🗑️ Supprimer une option...", 
                options=[discord.SelectOption(label=f"{i+1}. {o[:50]}", value=str(i)) for i, o in enumerate(self.survey.options)],
                row=1
            )
            select.callback = self.remove_option_callback
            self.add_item(select)

        btn_launch = discord.ui.Button(label="Lancer le Sondage", style=discord.ButtonStyle.primary, emoji="🚀", row=2)
        btn_launch.callback = self.launch_callback
        self.add_item(btn_launch)

    async def main_callback(self, it): await it.response.send_modal(SurveyConfigModal(self))
    async def opts_callback(self, it): await it.response.send_modal(SurveyOptionModal(self))
    
    async def mode_callback(self, it):
        self.survey.is_multiple = not self.survey.is_multiple
        await self.update_setup_embed(it)

    async def remove_option_callback(self, it: discord.Interaction):
        self.survey.options.pop(int(it.data['values'][0]))
        await self.update_setup_embed(it)

    async def launch_callback(self, it: discord.Interaction):
        if len(self.survey.options) < 2:
            return await it.response.send_message("❌ Il faut au moins 2 options.", ephemeral=True)
        
        self.survey.channel_id = it.channel_id
        embed = await self.cog.create_survey_embed(self.survey)
        
        msg = await it.channel.send(embed=embed)
        self.survey.message_id = msg.id
        
        public_view = SurveyPublicView(self.survey, self.cog)
        await msg.edit(view=public_view)
        
        self.cog.save_survey_data(self.survey)
        await it.response.edit_message(content="✅ Sondage publié !", embed=None, view=None)

    async def update_setup_embed(self, it: discord.Interaction):
        self.update_components()
        title = "⚙️ Préparation du Sondage"
        opts_text = "\n".join([f"`{i+1}`. {o}" for i, o in enumerate(self.survey.options)]) or "*Aucune option*"
        desc = (f"**Titre :** {self.survey.title}\n"
                f"**Description :** {self.survey.description or '*Aucune*'}\n\n"
                f"**Options ({len(self.survey.options)}/25) :**\n{opts_text}")
        
        if config_manager:
            embed = config_manager.get_formatted_embed(it.guild, it.user, it.client, title, desc, it.guild.id)
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
            
        await it.response.edit_message(embed=embed, view=self)

# ==============================================================================
# ----------------------- VUE PUBLIQUE (VOTE ET CLÔTURE) -----------------------
# ==============================================================================

class SurveyPublicView(discord.ui.View):
    def __init__(self, survey, cog):
        super().__init__(timeout=None)
        self.survey, self.cog = survey, cog
        
        opts = [discord.SelectOption(label=f"{i+1}. {o[:90]}", value=str(i)) for i, o in enumerate(self.survey.options)]
        
        # Le sélecteur de vote
        self.add_item(discord.ui.Select(
            placeholder=f"Voter ({'Multi' if self.survey.is_multiple else 'Simple'})",
            options=opts,
            min_values=1,
            max_values=len(opts) if self.survey.is_multiple else 1,
            custom_id=f"sv_vote_{self.survey.message_id}"
        ))
        
        # Le bouton de clôture
        self.add_item(discord.ui.Button(
            label="Terminer", 
            style=discord.ButtonStyle.danger, 
            emoji="🏁", 
            custom_id=f"sv_end_{self.survey.message_id}"
        ))

    async def interaction_check(self, it: discord.Interaction) -> bool:
        custom_id = it.data.get("custom_id")
        
        if custom_id == f"sv_vote_{self.survey.message_id}":
            await self.handle_vote(it)
        elif custom_id == f"sv_end_{self.survey.message_id}":
            # VERIFICATION : Auteur ou Admin uniquement
            is_author = it.user.id == self.survey.author_id
            is_admin = it.user.guild_permissions.administrator
            
            if not (is_author or is_admin):
                await it.response.send_message("❌ Seul l'auteur du sondage ou un administrateur peut utiliser ce bouton.", ephemeral=True)
                return False
                
            await self.handle_end(it)
        return True

    async def handle_vote(self, it: discord.Interaction):
        self.survey.votes[str(it.user.id)] = [int(v) for v in it.data['values']]
        self.cog.save_survey_data(self.survey)
        await self.cog.update_survey_message(self.survey)
        await it.response.send_message("✅ Votre vote a été enregistré.", ephemeral=True)

    async def handle_end(self, it: discord.Interaction):
        await self.cog.close_survey(self.survey)
        await it.response.send_message("🏁 Le sondage a été clôturé manuellement.", ephemeral=True)

# ==============================================================================
# ------------------------------- COG PRINCIPAL --------------------------------
# ==============================================================================

class Sondage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_dir = os.path.join(os.path.dirname(__file__), "data_sondage")
        os.makedirs(self.base_dir, exist_ok=True)
        self.cleanup_loop.start()

    def cog_unload(self):
        self.cleanup_loop.cancel()

    def save_survey_data(self, survey):
        path = os.path.join(self.base_dir, f"{survey.message_id}.json")
        with open(path, "w", encoding='utf-8') as f:
            json.dump(survey.to_dict(), f, indent=4, ensure_ascii=False)

    @tasks.loop(hours=1)
    async def cleanup_loop(self):
        """Vérifie la clôture auto après 30 jours (2592000 secondes)"""
        now = datetime.now(timezone.utc).timestamp()
        for file in os.listdir(self.base_dir):
            if file.endswith(".json"):
                try:
                    p = os.path.join(self.base_dir, file)
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if now - data.get("created_at", 0) >= 2592000:
                        s = Survey(**data)
                        await self.close_survey(s)
                except: continue

    async def close_survey(self, survey):
        """Met à jour l'embed final, retire la vue et supprime le fichier JSON"""
        survey.ended_at = datetime.now(timezone.utc).timestamp()
        chan = self.bot.get_channel(survey.channel_id)
        if chan:
            try:
                msg = await chan.fetch_message(survey.message_id)
                await msg.edit(embed=await self.create_survey_embed(survey), view=None)
            except: pass
        
        path = os.path.join(self.base_dir, f"{survey.message_id}.json")
        if os.path.exists(path):
            os.remove(path)

    async def create_survey_embed(self, survey):
        total_voters = len(survey.votes)
        stats = {i: 0 for i in range(len(survey.options))}
        for user_votes in survey.votes.values():
            for v in user_votes: 
                if v < len(survey.options): stats[v] += 1

        res_text = ""
        for i, opt in enumerate(survey.options):
            cnt = stats[i]
            pct = (cnt / total_voters * 100) if total_voters > 0 else 0
            bar = "🟦" * int(pct/10) + "⬜" * (10 - int(pct/10))
            res_text += f"`{i+1}`. **{opt}**\n{bar} `{pct:.1f}%` ({cnt})\n"

        status_info = f"🔴 **Clôturé**" if survey.ended_at else "🟢 **En cours**"
        description = (f"{survey.description}\n\n" if survey.description else "") + \
                      f"💡 *Mode: {'Multiple' if survey.is_multiple else 'Unique'}*\n" + \
                      f"📊 {status_info}\n\n{res_text}\n" + \
                      f"👥 **{total_voters}** votants"
        
        guild = self.bot.get_guild(survey.guild_id)
        try: author = await self.bot.fetch_user(survey.author_id)
        except: author = None

        if config_manager:
            return config_manager.get_formatted_embed(guild, author, self.bot, f"📊 {survey.title}", description, survey.guild_id)
        
        return discord.Embed(title=f"📊 {survey.title}", description=description, color=0x2b2d31)

    async def update_survey_message(self, survey):
        chan = self.bot.get_channel(survey.channel_id)
        if not chan: return
        try:
            msg = await chan.fetch_message(survey.message_id)
            await msg.edit(embed=await self.create_survey_embed(survey))
        except: pass

    @commands.hybrid_command(name="sondage", description="Permet de créer un sondage public.")
    @commands.has_permissions(administrator=True)
    async def survey_cmd(self, ctx: commands.Context):
        survey = Survey(guild_id=ctx.guild.id, author_id=ctx.author.id)
        view = SurveySetupView(self, survey)
        view.update_components()
        
        title, desc = "⚙️ Préparation du Sondage", "Configurez votre sondage ci-dessous."
        if config_manager:
            embed = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, title, desc, ctx.guild.id)
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
            
        await ctx.send(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    cog = Sondage(bot)
    await bot.add_cog(cog)
    
    # Restauration des vues persistantes au redémarrage
    if os.path.exists(cog.base_dir):
        for file in os.listdir(cog.base_dir):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(cog.base_dir, file), "r", encoding='utf-8') as f:
                        data = json.load(f)
                    s = Survey(**data)
                    if not s.ended_at:
                        bot.add_view(SurveyPublicView(s, cog))
                except: continue