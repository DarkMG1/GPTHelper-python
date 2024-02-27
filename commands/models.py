from discord import app_commands
from discord.ext import commands

from storage.classes import Model
from util.builder import getbaseembedbuilder
import discord


class Models(commands.Cog, name="models"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="models",
        description="Show all the models available"
    )
    @commands.guild_only()
    async def models(self, interaction: discord.Interaction) -> None:
        eb = (getbaseembedbuilder()
              .settitle("Models Supported")
              .setdescription("Below are the models this bot currently supports. When wanting to specify a specific model, use the exact model name used below.")
              .black())
        for model in Model:
            eb.addfield(model.model_name(), "Input: $" + str(model.input_cost()) + "\nOutput: $" + str(model.output_cost()), True)
        await interaction.response.send_message(embed=eb.build(), ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Models(bot))