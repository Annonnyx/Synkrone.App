import discord
from discord import ui, ButtonStyle, Embed, Interaction
import os
from .config_util import save_config
from .embed_launcher import LauncherEmbed, LauncherView

NAME_CHANNEL  = "🎫│𝑻𝒊𝒄𝒌𝒆𝒕"
NAME_ROLE     = "🆘│𝑺𝒖𝒑𝒑𝒐𝒓𝒕"
NAME_CATEGORY = "📂│𝑻𝒊𝒄𝒌𝒆𝒕 𝒆𝒏 𝒄𝒐𝒖𝒓𝒔"
NAME_ARCHIVE  = "🗄️│𝑻𝒊𝒄𝒌𝒆𝒕 𝒂𝒓𝒄𝒉𝒊𝒗𝒆́"

# Configuration du motif fixe
GEN_NAME = "⚙️ Général"

EXEMPLE_DATA = [
    {"name": "🤝 Partenariat", "desc": "Proposez une collaboration ou un échange."},
    {"name": "📝 Recrutement", "desc": "Postulez pour rejoindre nos rangs."},
    {"name": "🎉 Animation", "desc": "Suggestions ou problèmes liés aux events."},
    {"name": "🛡️ Report", "desc": "Signaler un joueur ou un abus."},
    {"name": "💎 Boutique", "desc": "Problème avec un achat ou un grade."},
    {"name": "💡 Suggestion", "desc": "Partagez vos idées pour le serveur."},
    {"name": "🛠️ Bug", "desc": "Signaler un dysfonctionnement technique."},
    {"name": "❓ Question", "desc": "Besoin d'une information générale."}
]

class AdminEmbed(Embed):
    def __init__(self, guild, cfg):
        status_color = 0x2ecc71 if cfg["enabled"] else 0xe74c3c
        super().__init__(title="🛠️ Panneau de Contrôle - Tickets", color=status_color)
        
        role = guild.get_role(cfg.get('support_role_id'))
        chan = guild.get_channel(cfg.get('channel_id'))
        cat_open = guild.get_channel(cfg.get('category_id'))
        cat_arch = guild.get_channel(cfg.get('archive_id'))
        
        self.add_field(name="🛡️ Support", value=role.mention if role else "❌", inline=True)
        self.add_field(name="📍 Salon", value=chan.mention if chan else "❌", inline=True)
        self.add_field(name="📊 État", value="🟢 Actif" if cfg["enabled"] else "🔴 Inactif", inline=True)
        
        # Affichage des catégories de gestion comme demandé
        self.add_field(name="📂 Ouverts", value=f"{cat_open.mention if cat_open else '❌'}", inline=True)
        self.add_field(name="🗄️ Archives", value=f"{cat_arch.mention if cat_arch else '❌'}", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=True)

        lines = []
        for c in cfg.get('categories', []):
            bullet = "🔸 " if "Général" in c['name'] else "🔹 "
            desc = f" - {c.get('desc')}" if c.get('desc') else ""
            lines.append(f"{bullet}**{c['name']}**{desc}")
        
        self.add_field(name=f"📁 Motifs ({len(lines)}/25)", value="\n".join(lines) if lines else "Vide", inline=False)

class AdminView(ui.View):
    def __init__(self, bot, config, author):
        super().__init__(timeout=None)
        self.bot = bot
        self.config = config
        self.author = author
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        t_style = ButtonStyle.success if self.config["enabled"] else ButtonStyle.danger
        ex_names = [e["name"] for e in EXEMPLE_DATA]
        has_examples = any(c["name"] in ex_names for c in self.config.get("categories", []))
        
        self.add_item(ui.Button(label="État", style=t_style, emoji="⚡", custom_id="adm_toggle", row=0))
        self.add_item(ui.Button(label="Ajouter", style=ButtonStyle.secondary, emoji="➕", custom_id="adm_add", row=0))
        self.add_item(ui.Button(label="Setup", style=ButtonStyle.secondary, emoji="⚙️", custom_id="adm_ids", row=0))
        
        self.add_item(ui.Button(label="Image", style=ButtonStyle.secondary, emoji="🖼️", custom_id="adm_img", row=1))
        self.add_item(ui.Button(label="Texte", style=ButtonStyle.secondary, emoji="📝", custom_id="adm_desc", row=1))
        self.add_item(ui.Button(label="Exemples", style=ButtonStyle.primary if not has_examples else ButtonStyle.danger, emoji="💡", custom_id="adm_example", row=1))

        editable = [c for c in self.config.get('categories', []) if "Général" not in c['name']]
        if editable:
            m_opts = [discord.SelectOption(label=f"Modifier : {c['name']}", value=c['name']) for c in editable]
            self.add_item(ui.Select(placeholder="📝 Modifier un motif...", options=m_opts, custom_id="adm_mod_select", row=2))
            
            d_opts = [discord.SelectOption(label=f"Supprimer : {c['name']}", value=c['name']) for c in editable]
            self.add_item(ui.Select(placeholder="🗑️ Supprimer des motifs...", options=d_opts, min_values=1, max_values=len(d_opts), custom_id="adm_del_select", row=3))

    async def sync(self, it: Interaction):
        if not any("Général" in c['name'] for c in self.config["categories"]):
            self.config["categories"].insert(0, {"name": GEN_NAME, "desc": "Support classique."})
        
        save_config(it.guild_id, self.config)
        self.update_buttons()
        
        embed = AdminEmbed(it.guild, self.config)
        if not it.response.is_done():
            await it.response.edit_message(embed=embed, view=self)
        else:
            await it.edit_original_response(embed=embed, view=self)
        
        chan = it.guild.get_channel(self.config.get("channel_id"))
        if chan and self.config.get("msg_id"):
            try:
                msg = await chan.fetch_message(self.config["msg_id"])
                files = [discord.File(self.config["local_image_path"])] if self.config.get("local_image_path") and os.path.exists(self.config["local_image_path"]) else []
                await msg.edit(embed=LauncherEmbed(self.config), view=LauncherView(self.config), attachments=files)
            except: pass

    async def interaction_check(self, it: Interaction) -> bool:
        if it.user.id != self.author.id: return False
        cid = it.data.get("custom_id")
        
        if cid == "adm_mod_select":
            sel_name = it.data['values'][0]
            idx = next((i for i, c in enumerate(self.config["categories"]) if c["name"] == sel_name), None)
            if idx is not None:
                cat = self.config["categories"][idx]
                modal = ui.Modal(title="Modification")
                n = ui.TextInput(label="Nom du motif", default=cat["name"], max_length=25)
                d = ui.TextInput(label="Description", default=cat.get("desc", ""), style=discord.TextStyle.paragraph, required=False, max_length=100)
                modal.add_item(n); modal.add_item(d)
                async def modal_cb(im):
                    self.config["categories"][idx]["name"], self.config["categories"][idx]["desc"] = n.value, d.value
                    await self.sync(im)
                modal.on_submit = modal_cb
                await it.response.send_modal(modal)

        elif cid == "adm_toggle":
            self.config["enabled"] = not self.config["enabled"]
            if self.config["enabled"]:
                cat = await it.guild.create_category(NAME_CATEGORY)
                arc = await it.guild.create_category(NAME_ARCHIVE)
                role = await it.guild.create_role(name=NAME_ROLE, color=discord.Color.red())
                chan = await it.guild.create_text_channel(NAME_CHANNEL, category=None)
                self.config.update({"category_id": cat.id, "archive_id": arc.id, "support_role_id": role.id, "channel_id": chan.id})
                msg = await chan.send(embed=LauncherEmbed(self.config), view=LauncherView(self.config))
                self.config["msg_id"] = msg.id
            await self.sync(it)

        elif cid == "adm_example":
            ex_names = [e["name"] for e in EXEMPLE_DATA]
            if any(c["name"] in ex_names for c in self.config["categories"]):
                self.config["categories"] = [c for c in self.config["categories"] if c["name"] not in ex_names]
            else:
                for e in EXEMPLE_DATA:
                    if not any(c['name'] == e['name'] for c in self.config["categories"]):
                        self.config["categories"].append(e)
            await self.sync(it)

        elif cid == "adm_add":
            modal = ui.Modal(title="➕ Ajouter un Motif")
            n = ui.TextInput(label="Nom du motif", max_length=25)
            d = ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=100, required=False)
            modal.add_item(n); modal.add_item(d)
            async def cb(i):
                self.config["categories"].append({"name": n.value, "desc": d.value})
                await self.sync(i)
            modal.on_submit = cb
            await it.response.send_modal(modal)

        elif cid == "adm_ids":
            modal = ui.Modal(title="⚙️ Setup Manuel")
            r = ui.TextInput(label="ID Rôle Support", default=str(self.config.get("support_role_id") or ""))
            c = ui.TextInput(label="ID Salon Accueil", default=str(self.config.get("channel_id") or ""))
            o = ui.TextInput(label="ID Catégorie Ouverts", default=str(self.config.get("category_id") or ""))
            a = ui.TextInput(label="ID Catégorie Archives", default=str(self.config.get("archive_id") or ""))
            for x in [r, c, o, a]: modal.add_item(x)
            async def cb(i):
                try:
                    self.config.update({"support_role_id": int(r.value), "channel_id": int(c.value), "category_id": int(o.value), "archive_id": int(a.value)})
                    await self.sync(i)
                except: await i.response.send_message("ID Invalide.", ephemeral=True)
            modal.on_submit = cb
            await it.response.send_modal(modal)

        elif cid == "adm_img":
            await it.response.send_message("📸 Envoyez l'image/GIF.", ephemeral=True)
            try:
                msg = await self.bot.wait_for("message", check=lambda m: m.author == it.user and m.attachments, timeout=30)
                path = f"./data/ticket/{it.guild_id}/{msg.attachments[0].filename}"
                os.makedirs(os.path.dirname(path), exist_ok=True)
                await msg.attachments[0].save(path)
                self.config["local_image_path"] = path
                await msg.delete(); await self.sync(it)
            except: pass

        elif cid == "adm_desc":
            modal = ui.Modal(title="📝 Texte d'accueil")
            t = ui.TextInput(label="Description Launcher", style=discord.TextStyle.paragraph, default=self.config.get("custom_description", ""), required=False)
            modal.add_item(t)
            async def cb(i):
                self.config["custom_description"] = t.value
                await self.sync(i)
            modal.on_submit = cb
            await it.response.send_modal(modal)

        elif cid == "adm_del_select":
            vals = it.data['values']
            self.config["categories"] = [c for c in self.config["categories"] if c["name"] not in vals or "Général" in c["name"]]
            await self.sync(it)

        return True