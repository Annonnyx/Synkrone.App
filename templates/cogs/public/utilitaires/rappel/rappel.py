import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import datetime
import re
from pathlib import Path

try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None


# --- NOUVEL EMPLACEMENT DATA ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent.parent.parent.parent / "data" / "public" / "utilitaires" / "data_rappel"
SERVEURS_DIR = DATA_DIR / "serveurs"
USERS_DIR = DATA_DIR / "users"

# Création des dossiers s'ils n'existent pas
DATA_DIR.mkdir(parents=True, exist_ok=True)
SERVEURS_DIR.mkdir(parents=True, exist_ok=True)
USERS_DIR.mkdir(parents=True, exist_ok=True)

def save_json(id_key, data, folder):
    """Sauvegarde les données dans un fichier JSON"""
    if folder == "serveurs":
        file_path = SERVEURS_DIR / f"{id_key}.json"
    else:  # users
        file_path = USERS_DIR / f"{id_key}.json"
    
    # Si c'est un utilisateur et qu'il n'y a plus de rappels, on supprime le fichier
    if not data.get("rappels") and folder == "users":
        if file_path.exists():
            file_path.unlink()
        return
    
    # Sauvegarde des données
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_json(id_key, folder):
    """Charge les données depuis un fichier JSON"""
    if folder == "serveurs":
        file_path = SERVEURS_DIR / f"{id_key}.json"
    else:  # users
        file_path = USERS_DIR / f"{id_key}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Retourne une structure vide si le fichier n'existe pas
    return {"rappels": [], "config": {}}

def parse_time_to_seconds(time_str):
    if not time_str: return None
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if match:
        val, unit = match.groups()
        return int(val) * units[unit]
    return None

# --- MODALS ---

class TimerModal(discord.ui.Modal, title="⏱️ Lancer une Minuterie"):
    def __init__(self):
        super().__init__()
        self.t = discord.ui.TextInput(label="Titre", placeholder="Ex: Cuisson des pâtes", max_length=50)
        self.d = discord.ui.TextInput(label="Durée (ex: 5m, 10s)", placeholder="5m", max_length=10)
        self.add_item(self.t); self.add_item(self.d)

    async def on_submit(self, interaction: discord.Interaction):
        secs = parse_time_to_seconds(self.d.value)
        if not secs: return await interaction.response.send_message("❌ Durée invalide.", ephemeral=True)
        
        data = load_json(interaction.user.id, "users")
        now = datetime.datetime.now().timestamp()
        new_timer = {
            "id": f"timer_{now}",
            "title": f"⏱️ {self.t.value}",
            "time": now + secs,
            "date_str": "Minuterie",
            "relance": 15, # Relance auto toutes les 15s
            "relance_str": "15s",
            "author_id": interaction.user.id,
            "folder": "users"
        }
        data["rappels"].append(new_timer)
        save_json(interaction.user.id, data, "users")
        await interaction.response.send_message(f"✅ Minuterie lancée : **{self.t.value}**", ephemeral=True)

class ServerConfigModal(discord.ui.Modal, title="📍 Configuration Envoi"):
    def __init__(self, folder, id_key, rappel, parent_view):
        super().__init__()
        self.folder, self.id_key, self.rappel, self.parent_view = folder, id_key, rappel, parent_view
        self.chan_id = discord.ui.TextInput(label="ID du Salon Textuel", default=str(rappel.get('chan_id') or ''))
        self.role_id = discord.ui.TextInput(label="ID du Rôle à Ping (Optionnel)", default=str(rappel.get('role_id') or ''), required=False)
        self.add_item(self.chan_id); self.add_item(self.role_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            data = load_json(self.id_key, self.folder)
            for r in data["rappels"]:
                if r['id'] == self.rappel['id']:
                    r['chan_id'] = int(self.chan_id.value)
                    r['role_id'] = int(self.role_id.value) if self.role_id.value else None
                    self.rappel = r
                    break
            save_json(self.id_key, data, self.folder)
            await self.parent_view.refresh_detail(interaction, self.rappel)
        except: await interaction.response.send_message("❌ IDs invalides.", ephemeral=True)

class CreateReminderModal(discord.ui.Modal, title="➕ Nouveau Rappel"):
    def __init__(self, folder, id_key, parent_view):
        super().__init__()
        self.folder, self.id_key, self.parent_view = folder, id_key, parent_view
        self.t = discord.ui.TextInput(label="Titre", placeholder="Ex: Réunion staff", max_length=50)
        self.dt = discord.ui.TextInput(label="Date (JJ/MM/AAAA HH:MM)", default=datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
        self.add_item(self.t); self.add_item(self.dt)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ts = datetime.datetime.strptime(self.dt.value, "%d/%m/%Y %H:%M").timestamp()
            data = load_json(self.id_key, self.folder)
            data["rappels"].append({
                "id": f"r_{ts}_{interaction.user.id}", 
                "title": self.t.value, "time": ts, "date_str": self.dt.value, 
                "relance": 30, "relance_str": "30s", 
                "author_id": interaction.user.id,
                "chan_id": interaction.channel.id if self.folder == "serveurs" else None
            })
            save_json(self.id_key, data, self.folder)
            await self.parent_view.refresh(interaction)
        except: await interaction.response.send_message("❌ Format de date invalide.", ephemeral=True)

class AdvancedConfigModal(discord.ui.Modal, title="📝 Modifier le Rappel"):
    def __init__(self, folder, id_key, rappel, parent_view):
        super().__init__()
        self.folder, self.id_key, self.rappel, self.parent_view = folder, id_key, rappel, parent_view
        self.t = discord.ui.TextInput(label="Titre", default=rappel['title'])
        self.dt = discord.ui.TextInput(label="Date (JJ/MM/AAAA HH:MM)", default=rappel['date_str'])
        self.rep = discord.ui.TextInput(label="Répétition (ex: 24h, 1d)", default=str(rappel.get('repeat') or ''), required=False)
        self.rel = discord.ui.TextInput(label="Relance (ex: 30s)", default=rappel.get('relance_str', '30s'))
        self.add_item(self.t); self.add_item(self.dt); self.add_item(self.rep); self.add_item(self.rel)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ts = datetime.datetime.strptime(self.dt.value, "%d/%m/%Y %H:%M").timestamp()
            data = load_json(self.id_key, self.folder)
            for r in data["rappels"]:
                if r['id'] == self.rappel['id']:
                    r.update({
                        "title": self.t.value, "date_str": self.dt.value, "time": ts, 
                        "repeat": self.rep.value or None, "repeat_secs": parse_time_to_seconds(self.rep.value), 
                        "relance_str": self.rel.value, "relance": parse_time_to_seconds(self.rel.value) or 30
                    })
                    self.rappel = r
                    break
            save_json(self.id_key, data, self.folder)
            await self.parent_view.refresh_detail(interaction, self.rappel)
        except: await interaction.response.send_message("❌ Erreur de format.", ephemeral=True)

# --- VIEWS ---

class ReminderDetailView(discord.ui.View):
    def __init__(self, folder, id_key, rappel, bot, parent_list_view):
        super().__init__(timeout=180)
        self.folder, self.id_key, self.rappel, self.bot, self.parent_list_view = folder, id_key, rappel, bot, parent_list_view
        self.setup_buttons()

    def setup_buttons(self):
        self.clear_items()
        btn_mod = discord.ui.Button(label="Modifier", emoji="📝", style=discord.ButtonStyle.secondary)
        btn_mod.callback = lambda i: i.response.send_modal(AdvancedConfigModal(self.folder, self.id_key, self.rappel, self))
        self.add_item(btn_mod)

        if self.folder == "serveurs":
            btn_cfg = discord.ui.Button(label="Salon / Rôle", emoji="⚙️", style=discord.ButtonStyle.secondary)
            btn_cfg.callback = lambda i: i.response.send_modal(ServerConfigModal(self.folder, self.id_key, self.rappel, self))
            self.add_item(btn_cfg)

        btn_del = discord.ui.Button(label="Supprimer", emoji="🗑️", style=discord.ButtonStyle.danger)
        btn_del.callback = self.delete_cb; self.add_item(btn_del)
        
        btn_back = discord.ui.Button(label="Retour", emoji="⬅️", style=discord.ButtonStyle.gray)
        btn_back.callback = lambda i: self.parent_list_view.refresh(i); self.add_item(btn_back)

    async def delete_cb(self, i):
        data = load_json(self.id_key, self.folder)
        data["rappels"] = [r for r in data["rappels"] if r['id'] != self.rappel['id']]
        save_json(self.id_key, data, self.folder)
        await self.parent_list_view.refresh(i)

    async def refresh_detail(self, interaction, rappel):
        data = load_json(self.id_key, self.folder)
        r = next((item for item in data["rappels"] if item['id'] == rappel['id']), rappel)
        is_priv = self.folder == "users"
        title = f"{'👤 Privé' if is_priv else '🏢 Serveur'} : {r['title']}"
        content = (f"🔔 **Prévu :** <t:{int(r['time'])}:F>\n"
                   f"⌛ **Envoi :** <t:{int(r['time'])}:R>\n\n"
                   f"┣ 🔁 Répétition : `{r.get('repeat') or 'Aucune'}`\n"
                   f"┗ ⚡ Relance : `{r.get('relance_str', '30s')}`")
        if not is_priv:
            content += f"\n\n📍 Salon : <#{r.get('chan_id') or '?'}>\n👥 Rôle : <@&{r.get('role_id')}>" if r.get('role_id') else "\n👥 Rôle : `Auteur`"
        
        emb = config_manager.get_formatted_embed(interaction.guild, interaction.user, self.bot, title, content, interaction.guild_id)
        await (interaction.edit_original_response if interaction.response.is_done() else interaction.response.edit_message)(embed=emb, view=self)

class ReminderListView(discord.ui.View):
    def __init__(self, folder, id_key, bot, ctx):
        super().__init__(timeout=180)
        self.folder, self.id_key, self.bot, self.ctx = folder, id_key, bot, ctx
        self.setup_ui()

    def setup_ui(self):
        self.clear_items()
        data = load_json(self.id_key, self.folder)
        
        if data["rappels"]:
            options = [discord.SelectOption(label=r['title'][:25], value=r['id'], description=f"Le {r['date_str']}") for r in data["rappels"][:25]]
            select = discord.ui.Select(placeholder="🔍 Gérer un rappel...", options=options)
            async def select_cb(i):
                # Correction du chargement ici : on utilise self.id_key
                fresh_data = load_json(self.id_key, self.folder)
                rappel = next((item for item in fresh_data["rappels"] if item['id'] == select.values[0]), None)
                if rappel: await ReminderDetailView(self.folder, self.id_key, rappel, self.bot, self).refresh_detail(i, rappel)
            select.callback = select_cb; self.add_item(select)
            
        b_add = discord.ui.Button(label="Ajouter", emoji="➕", style=discord.ButtonStyle.success)
        b_add.callback = lambda i: i.response.send_modal(CreateReminderModal(self.folder, self.id_key, self)); self.add_item(b_add)
        
        b_back = discord.ui.Button(label="Accueil", emoji="🏠", style=discord.ButtonStyle.gray)
        b_back.callback = self.back_home_cb; self.add_item(b_back)

    async def back_home_cb(self, i):
        emb, view = self.bot.get_cog("RappelCog").get_main_menu(self.ctx)
        await i.response.edit_message(embed=emb, view=view)

    async def refresh(self, interaction: discord.Interaction):
        self.setup_ui()
        data = load_json(self.id_key, self.folder)
        is_priv = self.folder == "users"
        title = f"{'👤' if is_priv else '🏢'} Liste des Rappels {'Privés' if is_priv else 'Serveur'}"
        r_list = "\n".join([f"**•** {r['title']} (<t:{int(r['time'])}:R>)" for r in data["rappels"][:25]]) or "_Aucun rappel actif._"
        emb = config_manager.get_formatted_embed(interaction.guild, interaction.user, self.bot, title, r_list, interaction.guild_id)
        await (interaction.edit_original_response if interaction.response.is_done() else interaction.response.edit_message)(embed=emb, view=self)

# --- COG PRINCIPAL ---

class RappelCog(commands.Cog):
    def __init__(self, bot):
        self.bot, self.active_alerts = bot, {}
        self.check_loop.start()

    def get_main_menu(self, ctx):
        view = discord.ui.View()
        b_tmr = discord.ui.Button(label="Minuterie", emoji="⏱️", style=discord.ButtonStyle.blurple)
        b_tmr.callback = lambda i: i.response.send_modal(TimerModal())
        
        async def open_list(i, folder, id_key, title):
            data = load_json(id_key, folder)
            r_list = "\n".join([f"**•** {r['title']} (<t:{int(r['time'])}:R>)" for r in data["rappels"][:25]]) or "_Aucun rappel._"
            emb = config_manager.get_formatted_embed(ctx.guild, i.user, self.bot, title, r_list, ctx.guild.id if ctx.guild else None)
            await i.response.send_message(embed=emb, view=ReminderListView(folder, id_key, self.bot, ctx), ephemeral=True)

        b_priv = discord.ui.Button(label="Rappels Privés", emoji="👤", style=discord.ButtonStyle.green)
        b_priv.callback = lambda i: open_list(i, "users", i.user.id, "👤 Mes Rappels Privés")
        
        b_serv = discord.ui.Button(label="Rappels Serveur", emoji="🏢", style=discord.ButtonStyle.secondary)
        b_serv.callback = lambda i: open_list(i, "serveurs", i.guild.id, "🏢 Rappels du Serveur") if i.user.guild_permissions.administrator else i.response.send_message("❌ Admin requis.", ephemeral=True)

        for b in [b_tmr, b_priv, b_serv]: view.add_item(b)
        emb = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, "⏰ Centre de Rappels", "Gérez vos alertes.", ctx.guild.id if ctx.guild else None)
        return emb, view

    @tasks.loop(seconds=15)
    async def check_loop(self):
        now = datetime.datetime.now().timestamp()
        for folder in ["users", "serveurs"]:
            path = str(DATA_DIR / folder)
            if not os.path.exists(path):
                continue
            for f in os.listdir(path):
                id_k = f.replace(".json", "")
                data = load_json(id_k, folder)
                upd, changed = [], False
                for r in data["rappels"]:
                    if now >= r["time"] and r["id"] not in self.active_alerts:
                        self.active_alerts[r["id"]] = True
                        asyncio.create_task(self.alert_task(r, folder, id_k))
                        if r.get("repeat_secs"):
                            r["time"] = now + r["repeat_secs"]
                            r["date_str"] = datetime.datetime.fromtimestamp(r["time"]).strftime("%d/%m/%Y %H:%M")
                            upd.append(r); changed = True
                    else: upd.append(r)
                if changed or len(upd) != len(data["rappels"]): save_json(id_k, {"rappels": upd}, folder)

    async def alert_task(self, r, folder, id_k):
        relance = r.get("relance", 30)
        while r["id"] in self.active_alerts:
            curr_data = load_json(id_k, folder)
            if not any(item['id'] == r['id'] for item in curr_data['rappels']) and not r['id'].startswith("timer"):
                if r["id"] in self.active_alerts: del self.active_alerts[r["id"]]
                break

            view = discord.ui.View(timeout=None)
            btn = discord.ui.Button(label="Arrêter l'alerte", style=discord.ButtonStyle.success, emoji="✅")
            async def close_cb(i):
                if r["id"] in self.active_alerts: del self.active_alerts[r["id"]]
                await i.response.edit_message(content="✅ Terminé.", view=None, embed=None)
            btn.callback = close_cb; view.add_item(btn)

            try:
                emb = config_manager.get_formatted_embed(None, self.bot.get_user(r['author_id']), self.bot, f"🚨 {r['title']}", "C'est l'heure !", None)
                if folder == "users":
                    u = self.bot.get_user(int(id_k))
                    if u: await u.send(embed=emb, view=view)
                else:
                    chan = self.bot.get_channel(r.get('chan_id'))
                    ping = f"<@&{r['role_id']}>" if r.get('role_id') else f"<@{r['author_id']}>"
                    if chan: await chan.send(content=ping, embed=emb, view=view)
            except: break
            await asyncio.sleep(relance)

    @commands.hybrid_command(name="rappel", description="Gérez vos rappels et minuteries personnels ou ceux du serveur")
    async def rappel(self, ctx):
        """Affiche le menu principal des rappels pour gérer les minuteries et rappels personnels ou serveur"""
        emb, view = self.get_main_menu(ctx); await ctx.send(embed=emb, view=view)

async def setup(bot): await bot.add_cog(RappelCog(bot))