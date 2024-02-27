from discord import app_commands
from discord.ext import commands

from storage.classes import Model
from storage.databasehelper import get_gpt_users
from util.builder import getbaseembedbuilder, geterrorembedbuilder
import discord


class Settings(commands.Cog, name="settings"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="settings",
        description="Modify the settings of the chat"
    )
    @commands.guild_only()
    @app_commands.describe(
        model="The model to use for the chat"
    )
    @app_commands.describe(
        temperature="Controls randomness. Higher values mean more randomness. Between 0 and 2"
    )
    @app_commands.describe(
        max_tokens="How many tokens the model should output at max for each message."
    )
    async def settings(self, interaction: discord.Interaction, model: str = Model.GPT_4_TURBO.model_name(), temperature: float = 1.0, max_tokens: int = 4096) -> None:
        channel = interaction.channel
        if isinstance(channel, discord.Thread):
            channel = channel.parent
        gpt_user = None

        for user in get_gpt_users():
            if user.id == interaction.message.author.id and user.gpt_channel.id == channel.id:
                gpt_user = user
                break
        if gpt_user is None:
            eb = geterrorembedbuilder("Unavailable", "You can only use this command in a chat thread or a chat channel.")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if not gpt_user.currently_chatting:
            eb = geterrorembedbuilder("Unavailable", "You don't have an active chat thread.")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if model not in Model:
            eb = geterrorembedbuilder("Invalid model", "The model you provided is invalid.")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if temperature < 0 or temperature > 2:
            eb = geterrorembedbuilder("Invalid temperature", "The temperature you provided is invalid.")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if max_tokens < 1:
            eb = geterrorembedbuilder("Invalid max tokens", "The max tokens you provided is invalid.")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        model = get_model_by_name(model)
        gpt_user.gpt_channel.current_model = model
        gpt_user.gpt_channel.current_temperature = temperature
        gpt_user.gpt_channel.current_max_tokens = max_tokens
        await interaction.response.send_message(
            embed=getbaseembedbuilder()
                .settitle("Settings updated")
                .addfield(name="Model", value=model)
                .addfield(name="Temperature", value=str(temperature))
                .addfield(name="Max Tokens", value=str(max_tokens))
                .black().build(),
            ephemeral=True
        )

def get_model_by_name(model_name):
    for name, model in Model.__members__.items():
        if model.model_name == model_name:
            return model
    return None

async def setup(bot) -> None:
    await bot.add_cog(Settings(bot))