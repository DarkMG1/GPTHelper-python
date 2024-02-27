from discord import app_commands
from discord.ext import commands

from storage.databasehelper import add_user
from storage.confighelper import get_config
from util.builder import getbaseembedbuilder, getnopermsembedbuilder, geterrorembedbuilder
import discord


class Setup(commands.Cog, name="setup"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="setup",
        description="Set up the bot."
    )
    @commands.is_owner()
    @commands.guild_only()
    @app_commands.describe(
        user="The user to set up the bot for."
    )
    async def setup(self,  interaction: discord.Interaction, user: discord.User) -> None:
        if user is None:
            eb = geterrorembedbuilder("Member null", "Message sender as member is null")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return

        guild = interaction.guild
        member = await guild.fetch_member(user.id)
        if member is None:
            eb = geterrorembedbuilder("Member null", "Member is null")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if not member.guild_permissions.administrator:
            await interaction.response.send_message(getnopermsembedbuilder(), ephemeral=True)
            return
        category = guild.get_channel(get_config().gptcategory_id)

        if category is None or not isinstance(category, discord.CategoryChannel):
            eb = geterrorembedbuilder("Category null", "Category is null or not a category")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return

        text_channel = await category.create_text_channel(name=f"GPT Chat - {user.name}",
                                           overwrites={guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                                                       user: discord.PermissionOverwrite(read_messages=True, send_messages=True)},
                                           topic=f"This channel is for {user.name} to ask questions to the bot.",
                                           slowmode_delay=5)

        if text_channel is None:
            eb = geterrorembedbuilder("Channel null", "Channel is null")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return

        await interaction.response.send_message(f"Channel created: {text_channel.mention}")
        add_user(user, text_channel)
        eb1  = await text_channel.send(
            embed= getbaseembedbuilder()
            .settitle("Welcome")
            .setdescription("Welcome to GPTHelper. To use the bot, simply say ""start chat"" and the bot will create a thread within the channel. To archive the thread, simply say ""close chat"". The entire thread history is sent each time you ask a question. Keep in mind this will increase the cost of each time you use the bot. \nIf you would like to start fresh, just say the ""restart  chat"".")
            .black()
            .build()
        )
        eb2 = await text_channel.send(
            embed= getbaseembedbuilder()
            .settitle("Settings")
            .setdescription("To modify the bot's settings, use the /settings command. You can modify the temperature, max tokens, and model. The bot will remember your settings for future use.")
            .black()
            .build()
        )
        await eb1.pin()
        await eb2.pin()

async def setup(bot) -> None:
    await bot.add_cog(Setup(bot))