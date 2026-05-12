import discord
from discord.ext import commands
from discord import app_commands, SelectOption
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# --------------------------- CONFIGURATION & DATA -----------------------------
# ==============================================================================
# Chemin local : crée un dossier 'data/securite' relatif au fichier
DATA_DIR = Path("./data/securite")
DATA_DIR.mkdir(parents=True, exist_ok=True)

PAGE_EMOJIS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "⏸️", "⏭️"]

MODULES_DATA = {
    "ban": {"emoji": "🔨", "desc": "Contrôle des bannissements et débannissements massifs.", "def": {"actif": False, "seuil": 5, "temps": 60, "action": "Dérank"}},
    "bot": {"emoji": "🤖", "desc": "Blocage des bots non-autorisés (Anti-Token).", "def": {"actif": False, "action_bot": "Kick", "action_user": "Dérank"}},
    "channel": {"emoji": "📁", "desc": "Protection contre la création/suppression de salons.", "def": {"actif": False, "seuil": 3, "temps": 10, "action": "Dérank"}},
    "deco": {"emoji": "🚪", "desc": "Alerte en cas de départs massifs (Anti-Leaver).", "def": {"actif": False, "seuil": 5, "temps": 60, "action": "Alerte"}},
    "everyone": {"emoji": "📢", "desc": "Limitation des mentions @everyone et @here.", "def": {"actif": False, "seuil": 2, "temps": 60, "action": "Dérank"}},
    "link": {"emoji": "🔗", "desc": "Suppression automatique des liens publicitaires.", "def": {"actif": False, "seuil": 3, "temps": 10, "action": "Mute"}},
    "massmention": {"emoji": "👥", "desc": "Contrôle du nombre de mentions par message.", "def": {"actif": False, "seuil": 5, "action": "Supprimer"}},
    "anti_mention": {"emoji": "🏷️", "desc": "Protection contre le spam de tags rôles/users.", "def": {"actif": False, "seuil": 4, "temps": 5, "action": "Mute"}},
    "role": {"emoji": "🛡️", "desc": "Surveillance des modifications de rôles.", "def": {"actif": False, "seuil": 3, "temps": 10, "action": "Dérank"}},
    "update": {"emoji": "📝", "desc": "Protection des paramètres du serveur.", "def": {"actif": False, "action": "Dérank"}},
    "webhook": {"emoji": "⚓", "desc": "Interdiction de création de webhooks.", "def": {"actif": False, "action": "Dérank"}}
}

PAGES_ORDER = ["main"] + list(MODULES_DATA.keys()) + ["whitelist"]

def load_db(guild_id: int) -> dict:
    path = DATA_DIR / f"{guild_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "whitelist": []}

def save_db(guild_id: int, data: dict):
    with open(DATA_DIR / f"{guild_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==============================================================================
# --------------------------- INTERFACE UTILISATEUR ----------------------------
# ==============================================================================

class SecurView(discord.ui.View):
    def __init__(self, guild: discord.Guild, cog, current_page="main"):
        super().__init__(timeout=None)
        self.guild, self.cog, self.current_page = guild, cog, current_page
        self.db = load_db(guild.id)
        self.page_idx = PAGES_ORDER.index(current_page)
        
        self.setup_ui()

    def setup_ui(self):
        self.clear_items()
        
        # 1. Navigation Flèches
        self.add_item(NavButton(emoji="⬅️", target="prev"))
        page_emoji = PAGE_EMOJIS[self.page_idx] if self.page_idx < len(PAGE_EMOJIS) else "🔢"
        self.add_item(discord.ui.Button(label=f"Page {self.page_idx}", emoji=page_emoji, disabled=True))
        self.add_item(NavButton(emoji="➡️", target="next"))

        # 2. Sélecteur de modules
        options = []
        for i, p in enumerate(PAGES_ORDER):
            num = PAGE_EMOJIS[i] if i < len(PAGE_EMOJIS) else ""
            if p == "main": options.append(SelectOption(label=f"{num} Sommaire", value="main", emoji="🏠"))
            elif p == "whitelist": options.append(SelectOption(label=f"{num} Whitelist", value="whitelist", emoji="⭐"))
            else:
                on = self.db["config"].get(p, {}).get("actif", False)
                options.append(SelectOption(label=f"{num} {p.capitalize()}", value=p, emoji="🟢" if on else "🔴", description=MODULES_DATA[p]["desc"]))
        
        sel = discord.ui.Select(placeholder="🔎 Aller vers un module...", options=options, row=1)
        sel.callback = self.select_nav
        self.add_item(sel)

        # 3. Contrôles de module
        if self.current_page not in ["main", "whitelist"]:
            m_conf = self.db["config"].get(self.current_page, MODULES_DATA[self.current_page]["def"])
            # Toggle Actif
            t_btn = discord.ui.Button(label="Désactiver" if m_conf["actif"] else "Activer", 
                                      style=discord.ButtonStyle.danger if m_conf["actif"] else discord.ButtonStyle.success, row=2)
            t_btn.callback = self.toggle_module
            self.add_item(t_btn)
            
            # Modal Seuil
            if "seuil" in m_conf:
                s_btn = discord.ui.Button(label="Paramétrer Seuils", style=discord.ButtonStyle.secondary, emoji="⏳", row=2)
                s_btn.callback = self.open_modal
                self.add_item(s_btn)

            # Sélecteurs d'action
            if self.current_page == "bot":
                self.add_bot_selectors(m_conf)
            else:
                self.add_generic_selector(m_conf)

    def add_bot_selectors(self, conf):
        s_b = discord.ui.Select(placeholder=f"Punition Bot : {conf.get('action_bot', 'Kick')}", row=3)
        for a in ["Kick", "Ban"]: s_b.add_option(label=a, value=f"bot_{a}")
        s_b.callback = self.bot_punish_callback
        self.add_item(s_b)

        s_u = discord.ui.Select(placeholder=f"Punition User : {conf.get('action_user', 'Dérank')}", row=4)
        for a in ["Dérank", "Kick", "Ban"]: s_u.add_option(label=a, value=f"user_{a}")
        s_u.callback = self.bot_punish_callback
        self.add_item(s_u)

    def add_generic_selector(self, conf):
        choices = ["Dérank", "Kick", "Ban"]
        if self.current_page in ["link", "anti_mention"]: choices.append("Mute")
        if self.current_page == "deco": choices.append("Alerte")
        
        sel = discord.ui.Select(placeholder=f"Action : {conf.get('action', 'Dérank')}", row=3)
        for c in choices: sel.add_option(label=c, value=c)
        sel.callback = self.action_callback
        self.add_item(sel)

    # --- Callbacks ---
    async def select_nav(self, inter):
        await self.cog.refresh(inter, inter.data['values'][0])

    async def toggle_module(self, inter):
        if inter.user.id != self.guild.owner_id: return
        self.db["config"].setdefault(self.current_page, MODULES_DATA[self.current_page]["def"].copy())
        self.db["config"][self.current_page]["actif"] = not self.db["config"][self.current_page]["actif"]
        save_db(self.guild.id, self.db)
        await self.cog.refresh(inter, self.current_page)

    async def action_callback(self, inter):
        if inter.user.id != self.guild.owner_id: return
        self.db["config"][self.current_page]["action"] = inter.data['values'][0]
        save_db(self.guild.id, self.db)
        await self.cog.refresh(inter, self.current_page)

    async def bot_punish_callback(self, inter):
        if inter.user.id != self.guild.owner_id: return
        v = inter.data['values'][0]
        self.db["config"].setdefault("bot", MODULES_DATA["bot"]["def"].copy())
        if "bot_" in v: self.db["config"]["bot"]["action_bot"] = v.replace("bot_", "")
        else: self.db["config"]["bot"]["action_user"] = v.replace("user_", "")
        save_db(self.guild.id, self.db)
        await self.cog.refresh(inter, "bot")

    async def open_modal(self, inter):
        if inter.user.id != self.guild.owner_id: return
        await inter.response.send_modal(SeuilModal(self.guild.id, self.current_page, self.cog))

class NavButton(discord.ui.Button):
    def __init__(self, emoji, target):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary, row=0)
        self.target = target

    async def callback(self, inter):
        view = self.view
        idx = view.page_idx
        new_idx = (idx + 1) % len(PAGES_ORDER) if self.target == "next" else (idx - 1) % len(PAGES_ORDER)
        await view.cog.refresh(inter, PAGES_ORDER[new_idx])

# ==============================================================================
# --------------------------- WHITELIST INTERFACE ------------------------------
# ==============================================================================

class ManualIDModal(discord.ui.Modal, title="Gestion Manuelle par ID"):
    """Modal pour ajouter ou retirer un ID (Membre, Bot ou Rôle) manuellement."""
    target_id = discord.ui.TextInput(
        label="ID de l'entité",
        placeholder="Collez l'ID ici (ex: 123456789012345678)...",
        min_length=17,
        max_length=20,
        required=True
    )

    def __init__(self, guild_id, cog):
        super().__init__()
        self.guild_id = guild_id
        self.cog = cog

    async def on_submit(self, inter: discord.Interaction):
        if inter.user.id != inter.guild.owner_id:
            return await inter.response.send_message("❌ Seul le propriétaire peut faire ça.", ephemeral=True)
        
        try:
            id_to_manage = int(self.target_id.value)
        except ValueError:
            return await inter.response.send_message("❌ ID invalide. Nombres uniquement.", ephemeral=True)

        db = load_db(self.guild_id)
        existing_ids = [x['id'] for x in db["whitelist"]]

        if id_to_manage in existing_ids:
            db["whitelist"] = [x for x in db["whitelist"] if x['id'] != id_to_manage]
            action = "retiré"
        else:
            # Détection automatique du type
            t_type = "ID Manuel"
            if inter.guild.get_role(id_to_manage): t_type = "Rôle"
            elif inter.guild.get_member(id_to_manage): t_type = "Membre/Bot"
            
            db["whitelist"].append({"id": id_to_manage, "type": t_type})
            action = "ajouté"

        save_db(self.guild_id, db)
        await self.cog.refresh(inter, "whitelist")
        await inter.followup.send(f"✅ ID `{id_to_manage}` {action}.", ephemeral=True)


class WhitelistView(SecurView):
    """Vue dédiée à la Whitelist avec sélecteurs et bouton ID."""
    def __init__(self, guild, cog):
        super().__init__(guild, cog, "whitelist")

    def setup_ui(self):
        super().setup_ui() # Conserve la navigation fléchée

        # Sélecteur Membres/Bots
        u_sel = discord.ui.UserSelect(placeholder="👤 Ajouter/Retirer un Membre ou Bot", row=2)
        u_sel.callback = self.on_user_select
        self.add_item(u_sel)

        # Sélecteur Rôles
        r_sel = discord.ui.RoleSelect(placeholder="🎭 Ajouter/Retirer un Rôle", row=3)
        r_sel.callback = self.on_role_select
        self.add_item(r_sel)

        # Bouton Manuel ID
        btn_m = discord.ui.Button(label="Ajouter/Retirer par ID", style=discord.ButtonStyle.primary, emoji="🆔", row=4)
        btn_m.callback = self.on_manual_click
        self.add_item(btn_m)

        # Bouton Vider
        btn_c = discord.ui.Button(label="Vider la liste", style=discord.ButtonStyle.danger, emoji="🗑️", row=4)
        btn_c.callback = self.clear_wl
        self.add_item(btn_c)

    async def on_user_select(self, inter):
        if inter.user.id != self.guild.owner_id: return
        t_id = int(inter.data['values'][0])
        user = inter.guild.get_member(t_id) or await self.cog.bot.fetch_user(t_id)
        self.toggle_id(t_id, "Bot" if user.bot else "Membre")
        await self.cog.refresh(inter, "whitelist")

    async def on_role_select(self, inter):
        if inter.user.id != self.guild.owner_id: return
        t_id = int(inter.data['values'][0])
        self.toggle_id(t_id, "Rôle")
        await self.cog.refresh(inter, "whitelist")

    async def on_manual_click(self, inter):
        await inter.response.send_modal(ManualIDModal(self.guild.id, self.cog))

    async def clear_wl(self, inter):
        if inter.user.id != self.guild.owner_id: return
        self.db["whitelist"] = []
        save_db(self.guild.id, self.db)
        await self.cog.refresh(inter, "whitelist")

    def toggle_id(self, t_id, t_type):
        if t_id in [x['id'] for x in self.db["whitelist"]]:
            self.db["whitelist"] = [x for x in self.db["whitelist"] if x['id'] != t_id]
        else:
            self.db["whitelist"].append({"id": t_id, "type": t_type})
        save_db(self.guild.id, self.db)

# ==============================================================================
# --------------------------- MODAL & COG --------------------------------------
# ==============================================================================

class SeuilModal(discord.ui.Modal, title="Réglages de Détection"):
    def __init__(self, g_id, module, cog):
        super().__init__()
        self.g_id, self.module, self.cog = g_id, module, cog
        conf = load_db(g_id)["config"].get(module, MODULES_DATA[module]["def"])
        
        self.s = discord.ui.TextInput(label="Nombre d'actions maximum", default=str(conf.get("seuil", 5)), min_length=1)
        self.add_item(self.s)
        if "temps" in conf:
            self.t = discord.ui.TextInput(label="Dans un intervalle de (secondes)", default=str(conf.get("temps", 60)))
            self.add_item(self.t)

    async def on_submit(self, inter):
        db = load_db(self.g_id)
        db["config"][self.module]["seuil"] = int(self.s.value)
        if hasattr(self, 't'): db["config"][self.module]["temps"] = int(self.t.value)
        save_db(self.g_id, db)
        await self.cog.refresh(inter, self.module)

class ConfigSecur(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def refresh(self, inter, page):
        embed = await self.make_embed(inter.guild, inter.user, page)
        view = WhitelistView(inter.guild, self) if page == "whitelist" else SecurView(inter.guild, self, page)
        await inter.response.edit_message(embed=embed, view=view)

    async def make_embed(self, guild, user, page):
        db = load_db(guild.id)
        idx = PAGES_ORDER.index(page)
        p_emoji = PAGE_EMOJIS[idx] if idx < len(PAGE_EMOJIS) else "🔢"

        if page == "whitelist":
            title = f"{p_emoji} Gestion de la Whitelist"
            desc = "⭐ **Entités immunisées**\nLes entités ci-dessous ignorent les protections du système.\n\n"
            
            # Initialisation des listes pour le tri
            roles_list = []
            users_list = []
            bots_list = []

            # Tri des données
            for x in db["whitelist"]:
                t_id = x['id']
                t_type = x['type']
                
                if t_type == "Rôle":
                    roles_list.append(f"• <@&{t_id}> | ID : `{t_id}`")
                elif t_type == "Bot":
                    bots_list.append(f"• <@{t_id}> | ID : `{t_id}`")
                else: # Membre ou ID Manuel
                    users_list.append(f"• <@{t_id}> | ID : `{t_id}`")

            # Construction de la description
            desc += "🎭 **Rôles Whitelist**\n"
            desc += "\n".join(roles_list) if roles_list else "*Aucun rôle*"
            
            desc += "\n\n👤 **Utilisateurs Whitelist**\n"
            desc += "\n".join(users_list) if users_list else "*Aucun utilisateur*"
            
            desc += "\n\n🤖 **Bots Whitelist**\n"
            desc += "\n".join(bots_list) if bots_list else "*Aucun bot*"
            
        elif page == "main":
            title = f"{p_emoji} Panel de Sécurité Intégrale"
            desc = (
                "🛡️ **Bienvenue dans votre centre de contrôle.**\n\n"
                "Ce système protège votre serveur contre les raids, les spams et les abus administratifs.\n\n"
                "**Comment configurer :**\n"
                "1️⃣ Utilisez les flèches ou le menu pour parcourir les modules.\n"
                "2️⃣ Activez le module souhaité.\n"
                "3️⃣ Réglez le seuil (ex: 5 bans en 60s) et la sentence.\n\n"
                "**État des modules :**\n"
            )
            for m, info in MODULES_DATA.items():
                s = "🟢" if db["config"].get(m, {}).get("actif") else "🔴"
                desc += f"{s} `{m.upper()}` : {info['desc']}\n"
        
        else:
            m_info = MODULES_DATA[page]
            conf = db["config"].get(page, m_info["def"])
            title = f"{p_emoji} Module {page.upper()}"
            desc = f"**{m_info['emoji']} Mission :** {m_info['desc']}\n\n"
            desc += f"**État :** `{'✅ Activé' if conf['actif'] else '❌ Désactivé'}`\n"
            
            if page == "bot":
                desc += f"**Action sur le Bot :** `{conf.get('action_bot', 'Kick')}`\n"
                desc += f"**Action sur l'inviteur :** `{conf.get('action_user', 'Dérank')}`"
            else:
                desc += f"**Punition :** `{conf.get('action', 'Dérank')}`\n"
                if "seuil" in conf:
                    desc += f"**Détection :** {conf['seuil']} actions en {conf.get('temps', '∞')} secondes."

        if config_manager:
            return config_manager.get_formatted_embed(guild, user, self.bot, title, desc, guild.id)
        return discord.Embed(title=title, description=desc, color=0x2b2d31)

    @commands.hybrid_command(name="secur", description="🛡️ Ouvrir le panel de sécurité.")
    @app_commands.default_permissions(administrator=True)
    async def secur(self, ctx):
        embed = await self.make_embed(ctx.guild, ctx.author, "main")
        await ctx.send(embed=embed, view=SecurView(ctx.guild, self), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigSecur(bot))