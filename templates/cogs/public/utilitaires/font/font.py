import discord
from discord.ext import commands
import json
import os

class Font(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        base_path = os.path.dirname(__file__)
        json_path = os.path.join(base_path, "font.json")

        with open(json_path, "r", encoding="utf-8") as f:
            self.font_map = json.load(f)

    def stylize(self, text: str) -> str:
        return "".join(self.font_map.get(c, c) for c in text)

    @commands.hybrid_command(name="font")
    async def font(self, ctx, *, message: str):
        await ctx.send(self.stylize(message))

async def setup(bot):
    await bot.add_cog(Font(bot))
