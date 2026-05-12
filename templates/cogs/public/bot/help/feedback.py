import discord
from discord.ext import commands
from discord import ui
from pathlib import Path
import json
import os

# ==============================================================================
# --------------------------- CONFIGURATION & UTILS ----------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

LOG_CHANNEL_ID = int(os.getenv("FEEDBACK_LOG_CHANNEL_ID", "0")) or None
ADMIN_ROLE_ID = int(os.getenv("FEEDBACK_ADMIN_ROLE_ID", "0")) or None

DATA_PATH = Path(__file__).parent / "feedback_data.json"
CONFIG_PATH = Path(__file__).parent / "feedback_config.json"

def get_feedback_data():
    if not DATA_PATH.exists(): return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f: return json.load(f)

def save_feedback_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

def get_next_id():
    count = 1
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f: data = json.load(f)
        count = data.get("count", 0) + 1
    with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump({"count": count}, f)
    return count

# ==============================================================================
# --------------------------- VOTE & ADMIN SYSTEM ------------------------------
# ==============================================================================

class FeedbackVoteView(ui.View):
    def __init__(self, f_id: str, author_id: str):
        super().__init__(timeout=None)
        self.f_id, self.author_id = f_id, author_id

    @ui.button(label="Feedback", emoji="➕", style=discord.ButtonStyle.primary, custom_id="v_create") # PREMIER & BLEU
    async def v_create(self, it, bt):
        cat_path = Path(__file__).parent / "catégorie"
        data = {f.stem: json.load(open(f, "r", encoding="utf-8")) for f in cat_path.glob("*.json")} if cat_path.exists() else {}
        view = FeedbackCreationView(it.user, it.client, data)
        await view.step_type_lite()
        await it.response.send_message(embed=view.get_embed("📝 Nouveau Feedback", "Choisissez une option :"), view=view, ephemeral=True)

    @ui.button(emoji="👍", style=discord.ButtonStyle.success, custom_id="v_up")
    async def v_up(self, it, bt): await self.process_vote(it, "up")

    @ui.button(emoji="➖", style=discord.ButtonStyle.primary, custom_id="v_neu") # BLEU
    async def v_neu(self, it, bt): await self.process_vote(it, "neutral")

    @ui.button(emoji="👎", style=discord.ButtonStyle.danger, custom_id="v_dow")
    async def v_dow(self, it, bt): await self.process_vote(it, "down")

    @ui.button(emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="v_admin") # EMOJI SEUL
    async def v_admin(self, it, bt):
        if not it.user.get_role(ADMIN_ROLE_ID): return await it.response.send_message("❌ Staff uniquement.", ephemeral=True)
        view = ui.View()
        options = [
            discord.SelectOption(label="Prochaine MAJ", value="🚀 Prochaine MAJ", emoji="🚀"),
            discord.SelectOption(label="En recherche", value="🛠️ En recherche", emoji="🔍"),
            discord.SelectOption(label="Besoin d'infos", value="🗣️ Précisions requises", emoji="❓"),
            discord.SelectOption(label="Intégré", value="✅ Intégré", emoji="✔️"),
            discord.SelectOption(label="Doublon", value="📂 Doublon", emoji="👥"),
            discord.SelectOption(label="Refusé", value="❌ Refusé", emoji="✖️")
        ]
        select = ui.Select(placeholder="🎯 Modifier l'état...", options=options)
        async def cb(i):
            s = i.data['values'][0]
            if "Refusé" in s: await i.response.send_modal(RefusalReasonModal(self.f_id, self.author_id, s))
            else: await update_feedback_state(i, self.f_id, self.author_id, s)
        select.callback = cb; view.add_item(select)
        await it.user.send(f"🛠️ **Gestion Feedback n°{self.f_id}**", view=view)
        await it.response.send_message("📥 Menu admin envoyé en MP.", ephemeral=True)

    async def process_vote(self, it, vote_type):
        data = get_feedback_data()
        fid = str(self.f_id); data.setdefault(fid, {"votes": {}, "author_id": self.author_id})
        data[fid]["votes"][str(it.user.id)] = vote_type
        save_feedback_data(data)
        v = data[fid]["votes"]; t = len(v)
        up, n, d = list(v.values()).count("up"), list(v.values()).count("neutral"), list(v.values()).count("down")
        embed = it.message.embeds[0]
        # Index 1 car État est passé en Index 0
        embed.set_field_at(1, name="📊 Statistiques des votes", 
                          value=f"Total : **{t}** vote(s)\n🟢 Positifs : **{up/max(1,t)*100:.0f}% ({up})**\n🔵 Neutres : **{n/max(1,t)*100:.0f}% ({n})**\n🔴 Négatifs : **{d/max(1,t)*100:.0f}% ({d})**", 
                          inline=False)
        await it.response.edit_message(embed=embed)

# ==============================================================================
# --------------------------- CREATION PROCESS (SALON -> MP) -------------------
# ==============================================================================

class FeedbackCreationView(ui.View):
    def __init__(self, author, bot, categories_data):
        super().__init__(timeout=600)
        self.author, self.bot, self.categories_data = author, bot, categories_data
        self.type = self.category = self.command = self.rating = self.short_desc = self.user_message = self.cmd_name = None

    def get_embed(self, title, description):
        if config_manager:
            return config_manager.get_formatted_embed(guild=None, user=self.author, bot=self.bot, title=title, description=description)
        return discord.Embed(title=title, description=description, color=0x3498db)

    async def send_final(self, it):
        f_id = get_next_id()
        cmd_f = self.cmd_name if self.type == "Ajout" else self.command
        cat_f = f"📂 {self.category}" if self.category else "✨ Nouveau concept"
        
        log_embed = self.get_embed(f"Feedback n°{f_id}", f"# {cmd_f}\n-# {cat_f}")
        log_embed.set_thumbnail(url=self.author.display_avatar.url)
        
        # RÉORGANISATION : État en premier
        log_embed.add_field(name="⚙️ État du feedback", value="**👀 En attente de lecture**", inline=False)
        log_embed.add_field(name="📊 Statistiques des votes", value="⌛ En attente...", inline=False)
        log_embed.add_field(name="📌 Résumé", value=f"```{self.short_desc}```", inline=False)
        log_embed.add_field(name="💬 Retour complet", value=f"```{self.user_message}```", inline=False)
        
        if self.rating: log_embed.set_footer(text=f"Note : {self.rating}/5 ⭐ | Auteur : {self.author.name}")

        chan = self.bot.get_channel(LOG_CHANNEL_ID)
        if chan:
            msg = await chan.send(embed=log_embed, view=FeedbackVoteView(str(f_id), str(self.author.id)))
            data = get_feedback_data(); data[str(f_id)] = {"message_id": msg.id, "author_id": str(self.author.id), "votes": {}}; save_feedback_data(data)
            try: await msg.create_thread(name=f"💬 Discussion Feedback n°{f_id}")
            except: pass
        await it.response.edit_message(content="🎉 **Feedback envoyé !**", embed=None, view=None)

    async def step_type_lite(self):
        self.clear_items()
        select = ui.Select(placeholder="✨ Choisissez le type...", options=[
            discord.SelectOption(label="Ajout", emoji="✨"),
            discord.SelectOption(label="Amélioration", emoji="📈"),
            discord.SelectOption(label="Bug", emoji="🐛")
        ])
        async def cb(i):
            self.type = i.data['values'][0]
            if self.type == "Ajout": await i.response.send_modal(AddModal(self))
            else: await self.step_cat(i)
        select.callback = cb; self.add_item(select)

    async def step_cat(self, it):
        self.clear_items()
        opts = [discord.SelectOption(label=d.get("category_name", fid), value=fid, emoji=d.get("emoji", "📂")) for fid, d in self.categories_data.items()]
        select = ui.Select(placeholder="📂 Catégorie...", options=opts)
        async def cb(i): self.category = i.data['values'][0]; await self.step_cmd(i)
        select.callback = cb; self.add_item(select); self.add_back(self.step_type_lite_with_edit)
        await it.response.edit_message(embed=self.get_embed("📝 Création", f"🎯 Type : **{self.type}**"), view=self)

    async def step_type_lite_with_edit(self, it):
        await self.step_type_lite()
        await it.response.edit_message(embed=self.get_embed("📝 Nouveau Feedback", "Choisissez une option :"), view=self)

    async def step_cmd(self, it):
        self.clear_items()
        cmds = [c for s in self.categories_data[self.category]["sections"].values() for c in s.keys()]
        opts = [discord.SelectOption(label=c.replace('`',''), value=c, emoji="⌨️") for c in cmds[:25]]
        select = ui.Select(placeholder="⌨️ Quelle commande ?", options=opts)
        async def cb(i): self.command = i.data['values'][0]; await self.step_rate(i)
        select.callback = cb; self.add_item(select); self.add_back(self.step_cat)
        await it.response.edit_message(view=self)

    async def step_rate(self, it):
        self.clear_items()
        select = ui.Select(placeholder="⭐ Note...", options=[discord.SelectOption(label=f"{i}/5 ⭐", value=str(i)) for i in range(5, -1, -1)])
        async def cb(i): self.rating = i.data['values'][0]; await i.response.send_modal(DetailsModal(self))
        select.callback = cb; self.add_item(select); self.add_back(self.step_cmd)
        await it.response.edit_message(view=self)

    def add_back(self, func):
        btn = ui.Button(label="Retour", emoji="⬅️", style=discord.ButtonStyle.secondary)
        async def cb(i): await func(i)
        btn.callback = cb; self.add_item(btn)

# --- Modals ---
class AddModal(ui.Modal, title="✨ Proposition d'Ajout"):
    n = ui.TextInput(label="Nom"); s = ui.TextInput(label="Résumé"); d = ui.TextInput(label="Détails", style=discord.TextStyle.paragraph)
    def __init__(self, p): super().__init__(); self.p = p
    async def on_submit(self, i): self.p.cmd_name, self.p.short_desc, self.p.user_message = self.n.value, self.s.value, self.d.value; await self.p.send_final(i)

class DetailsModal(ui.Modal, title="📝 Détails du retour"):
    s = ui.TextInput(label="Sujet"); c = ui.TextInput(label="Détails", style=discord.TextStyle.paragraph)
    def __init__(self, p): super().__init__(); self.p = p
    async def on_submit(self, i): self.p.short_desc, self.p.user_message = self.s.value, self.c.value; await self.p.send_final(i)

# --- Admin Utils ---
async def update_feedback_state(interaction, f_id, user_id, state, reason=None):
    data = get_feedback_data(); msg_id = data.get(str(f_id), {}).get("message_id")
    channel = interaction.client.get_channel(LOG_CHANNEL_ID)
    if msg_id and channel:
        try:
            msg = await channel.fetch_message(msg_id)
            embed = msg.embeds[0]
            val = f"**{state}**" + (f"\n> 📝 **Raison :** {reason}" if reason else "")
            embed.set_field_at(0, name="⚙️ État du feedback", value=val, inline=False) # Index 0 mis à jour
            await msg.edit(embed=embed)
            user = await interaction.client.fetch_user(int(user_id))
            await user.send(content=f"✨ **Mise à jour de votre retour n°{f_id}**", embed=embed.copy())
        except: pass
    await interaction.response.edit_message(content=f"✅ État mis à jour : **{state}**", view=None)

class RefusalReasonModal(ui.Modal, title="❌ Justification"):
    reason = ui.TextInput(label="Raison", style=discord.TextStyle.paragraph, min_length=10)
    def __init__(self, f_id, u_id, state): super().__init__(); self.f_id, self.u_id, self.state = f_id, u_id, state
    async def on_submit(self, interaction): await update_feedback_state(interaction, self.f_id, self.u_id, self.state, self.reason.value)

# ==============================================================================
# --------------------------- INITIAL COMMAND ----------------------------------
# ==============================================================================

class Feedback(commands.Cog):
    def __init__(self, bot): self.bot = bot
    @commands.Cog.listener()
    async def on_ready(self): self.bot.add_view(FeedbackVoteView("0", "0"))

    @commands.hybrid_command(name="feedback")
    async def feedback(self, ctx):
        cat_path = Path(__file__).parent / "catégorie"
        data = {f.stem: json.load(open(f, "r", encoding="utf-8")) for f in cat_path.glob("*.json")} if cat_path.exists() else {}
        view = FeedbackCreationView(ctx.author, self.bot, data)
        await view.step_type_lite()
        await ctx.send(embed=view.get_embed("📝 Nouveau Feedback", "Choisissez une option :"), view=view)

async def setup(bot): await bot.add_cog(Feedback(bot))