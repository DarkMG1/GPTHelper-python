from discord import app_commands
from discord.ext import commands
import discord

from storage.databasehelper import remove_user, get_gpt_users
from util.builder import getbaseembedbuilder, geterrorembedbuilder, getnopermsembedbuilder


class Delete(commands.Cog, name="delete"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="delete",
        description="Deletes a user's data and channel from the bot"
    )
    @commands.guild_only()
    @app_commands.describe(
        user="The user to delete the data for."
    )
    async def delete(self, interaction: discord.Interaction, user: discord.User) -> None:
        member = interaction.guild.fetch_member(interaction.user.id)
        if member is None:
            eb = geterrorembedbuilder("Member null", "Member is null")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if not member.guild_permissions.administrator:
            await interaction.response.send_message(getnopermsembedbuilder(), ephemeral=True)
            return

        if get_gpt_users()[user.id] is None:
            eb = geterrorembedbuilder("User not foundl", "The user specified was not found. Please try again.")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return

        gpt_user = get_gpt_users()[user.id]
        remove_user(gpt_user)
        textchannel = interaction.guild.get_channel(gpt_user.gpt_channel.id)
        if textchannel is not None:
            await textchannel.delete()

        eb = (getbaseembedbuilder()
              .settitle("Successfully Deleted User")
              .setdescription(f"Successfully deleted {user.name}'s data and channel.")
              .black()
              .build())
        await interaction.response.send_message(embed=eb)

async def setup(bot) -> None:
    await bot.add_cog(Delete(bot))