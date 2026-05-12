import discord
from discord.ext import commands
from discord import app_commands, ui
import re
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ----------------------------- INTERFACES UI ----------------------------------
# ==============================================================================

class EditModal(ui.Modal, title="Modifier le calcul"):
    calcul_input = ui.TextInput(
        label="Expression mathématique",
        placeholder="Exemple: (10 + 5) * 2",
        min_length=1,
        max_length=100,
    )

    def __init__(self, view, bot):
        super().__init__()
        self.view = view
        self.bot = bot
        self.calcul_input.default = self.view.expression

    async def on_submit(self, interaction: discord.Interaction):
        new_val = self.calcul_input.value.replace(" ", "")
        self.view.expression = new_val
        
        result = self.view.calculate()
        if result != "Erreur":
            display_expr = new_val.replace("*", "×").replace("/", "÷")
            self.view.history += f"{display_expr}\n= {result}\n"
            self.view.expression = result
            self.view.is_result = True
        else:
            self.view.expression = "Erreur"

        # Mise à jour de l'embed via le manager
        embed = self.view.cog.get_calc_embed(
            interaction.guild, 
            interaction.user, 
            self.view.history, 
            self.view.expression
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

class CalculatorButton(ui.Button):
    def __init__(self, label, user_id, style, row, custom_id_suffix=None):
        super().__init__(
            label=label, 
            style=style, 
            row=row, 
            custom_id=f"btn_calc_{user_id}_{custom_id_suffix or label}"
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce n'est pas votre calculatrice !", ephemeral=True)

        view = self.view
        label = self.label

        if label == "EDIT":
            await interaction.response.send_modal(EditModal(view, view.cog.bot))
            return

        if label in ["C", "CE"]:
            view.expression = "0"
            view.history = ""
            view.is_result = False
        elif label == "⌫":
            if view.is_result:
                view.expression = "0"
                view.is_result = False
            else:
                view.expression = view.expression[:-1] if len(view.expression) > 1 else "0"
        elif label == "=":
            if view.is_result:
                return await interaction.response.defer()
            
            result = view.calculate()
            if result != "Erreur":
                display_expr = view.expression.replace("*", "×").replace("/", "÷")
                view.history += f"{display_expr}\n= {result}\n"
                view.expression = result
                view.is_result = True
            else:
                view.expression = "Erreur"
        else:
            is_operator = label in ["+", "-", "×", "÷", "*", "/"]
            if view.is_result:
                if is_operator:
                    view.expression += label.replace("×", "*").replace("÷", "/")
                    view.is_result = False
                else:
                    view.expression = label
                    view.is_result = False
            else:
                if view.expression == "0" or view.expression == "Erreur":
                    view.expression = label if not is_operator else view.expression + label
                else:
                    view.expression += label

        embed = view.cog.get_calc_embed(interaction.guild, interaction.user, view.history, view.expression)
        await interaction.response.edit_message(embed=embed, view=view)

class CalculatorView(ui.View):
    def __init__(self, user_id, cog, initial_expression="0"):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.cog = cog
        self.expression = initial_expression
        self.history = ""
        self.is_result = False
        self.create_buttons()

    def create_buttons(self):
        btns_config = [
            ("EDIT", discord.ButtonStyle.primary, 0), ("CE", discord.ButtonStyle.danger, 0),
            ("C", discord.ButtonStyle.danger, 0), ("⌫", discord.ButtonStyle.danger, 0, "back"),
            ("1", discord.ButtonStyle.secondary, 1), ("2", discord.ButtonStyle.secondary, 1),
            ("3", discord.ButtonStyle.secondary, 1), ("÷", discord.ButtonStyle.primary, 1, "/"),
            ("4", discord.ButtonStyle.secondary, 2), ("5", discord.ButtonStyle.secondary, 2),
            ("6", discord.ButtonStyle.secondary, 2), ("×", discord.ButtonStyle.primary, 2, "*"),
            ("7", discord.ButtonStyle.secondary, 3), ("8", discord.ButtonStyle.secondary, 3),
            ("9", discord.ButtonStyle.secondary, 3), ("-", discord.ButtonStyle.primary, 3),
            (".", discord.ButtonStyle.secondary, 4, "dot"), ("0", discord.ButtonStyle.secondary, 4),
            ("=", discord.ButtonStyle.success, 4), ("+", discord.ButtonStyle.primary, 4)
        ]
        for b in btns_config:
            self.add_item(CalculatorButton(b[0], self.user_id, b[1], b[2], b[3] if len(b) > 3 else b[0]))

    def calculate(self):
        expr = self.expression.replace("×", "*").replace("÷", "/")
        if not re.match(r'^[0-9+\-*/.() ]+$', expr): return "Erreur"
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return f"{float(result):.2f}".rstrip('0').rstrip('.')
        except:
            return "Erreur"

# ==============================================================================
# ----------------------------- COG CALC ---------------------------------------
# ==============================================================================

class Calc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_calc_embed(self, guild, user, history, expression):
        """Génère l'embed de la calculatrice via le manager ou standard"""
        current_display = expression.replace("*", "×").replace("/", "÷")
        full_display = f"{history}{current_display}"
        
        if len(full_display) > 1500:
            full_display = "..." + full_display[-1497:]

        title = "🧮 Calculatrice"
        description = f"```\n{full_display}\n```"

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None
            )
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return embed

    @commands.hybrid_command(name="calc", description="Ouvre la calculatrice interactive.")
    @app_commands.describe(calcul="Expression mathématique optionnelle")
    async def calc(self, ctx: commands.Context, calcul: str = None):
        try:
            # Accusé de réception
            await ctx.defer(ephemeral=False)

            initial_expr = calcul.replace(" ", "") if calcul else "0"
            view = CalculatorView(ctx.author.id, self, initial_expr)
            
            if calcul:
                res = view.calculate()
                if res != "Erreur":
                    view.history = f"{initial_expr}\n= {res}\n"
                    view.expression = res
                    view.is_result = True

            embed = self.get_calc_embed(ctx.guild, ctx.author, view.history, view.expression)

            if ctx.interaction:
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=True)

        except Exception:
            traceback.print_exc()

async def setup(bot: commands.Bot):
    if bot.get_command("calc"):
        bot.remove_command("calc")
    await bot.add_cog(Calc(bot))