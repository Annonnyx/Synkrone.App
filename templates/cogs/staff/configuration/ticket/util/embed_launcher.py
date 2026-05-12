import discord
from discord import ui, Embed, Interaction
import os

# --- MODAL D'OUVERTURE DE TICKET ---
class TicketCreationModal(ui.Modal):
    def __init__(self, category_name, config): # Ajout de config ici
        super().__init__(title=f"Ouverture Ticket : {category_name}")
        self.category_name = category_name
        self.config = config # On stocke la config dans l'objet
        
        self.subject = ui.TextInput(
            label="Sujet de votre demande",
            placeholder="Ex: Problème de grade, Question boutique...",
            style=discord.TextStyle.short,
            min_length=5,
            max_length=100,
            required=True
        )
        
        self.description = ui.TextInput(
            label="Description détaillée",
            placeholder="Expliquez ici votre problème avec le plus de détails possible...",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=1000,
            required=True
        )
        
        self.add_item(self.subject)
        self.add_item(self.description)

    async def on_submit(self, it: Interaction):
        await it.response.send_message(
            f"⌛ Création de votre ticket (**{self.category_name}**) en cours...", 
            ephemeral=True
        )

        try:
            # Import dynamique pour éviter les imports circulaires
            from .embed_private import create_ticket_process
            
            # Ici self.config est maintenant bien défini
            channel = await create_ticket_process(
                it, 
                self.config, 
                self.category_name, 
                self.subject.value, 
                self.description.value
            )

            await it.edit_original_response(
                content=f"✅ Votre ticket a été créé avec succès : {channel.mention}"
            )

        except Exception as e:
            await it.edit_original_response(
                content=f"❌ Une erreur est survenue lors de la création du ticket : {e}"
            )

# --- EMBED DU LAUNCHER ---
class LauncherEmbed(Embed):
    def __init__(self, config):
        cats = config.get("categories", [])
        custom_desc = config.get("custom_description")

        if custom_desc:
            desc = custom_desc
        elif len(cats) <= 1:
            desc = "Appuyez sur le bouton ci-dessous pour ouvrir un ticket et contacter notre équipe."
        else:
            desc = "Veuillez choisir le motif de votre demande dans le menu ci-dessous pour ouvrir un ticket."
            
        super().__init__(title="🎫 Support - Ouverture de Ticket", description=desc, color=0x3498db)
        
        if config.get("local_image_path") and os.path.exists(config["local_image_path"]):
            filename = os.path.basename(config["local_image_path"])
            self.set_image(url=f"attachment://{filename}")

# --- VUE DU LAUNCHER ---
class LauncherView(ui.View):
    def __init__(self, config):
        super().__init__(timeout=None)
        self.config = config
        cats = config.get("categories", [])

        if len(cats) <= 1:
            label_name = "Ouvrir un ticket" 
            btn = ui.Button(label=label_name, style=discord.ButtonStyle.primary, emoji="🎫", custom_id="launcher_btn_gen")
            btn.callback = self.button_callback
            self.add_item(btn)
        else:
            options = []
            for c in cats:
                bullet = "🔸 " if "Général" in c["name"] else "🔹 "
                options.append(discord.SelectOption(
                    label=f"{bullet}{c['name']}",
                    description=c.get("desc", "Cliquez pour ouvrir ce ticket")[:100],
                    value=c["name"]
                ))
            
            select = ui.Select(placeholder="Choisissez le motif de votre demande...", options=options, custom_id="launcher_select")
            select.callback = self.select_callback
            self.add_item(select)

    async def button_callback(self, it: Interaction):
        cat_name = self.config["categories"][0]["name"] if self.config.get("categories") else "⚙️ Général"
        # On passe self.config au Modal
        await it.response.send_modal(TicketCreationModal(cat_name, self.config))

    async def select_callback(self, it: Interaction):
        cat_name = it.data['values'][0]
        # On passe self.config au Modal
        await it.response.send_modal(TicketCreationModal(cat_name, self.config))