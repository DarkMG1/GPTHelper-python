from decimal import Decimal, ROUND_HALF_UP

from discord import app_commands
from discord.ext import commands

import discord
from util.builder import geterrorembedbuilder, getbaseembedbuilder, getnopermsembedbuilder
from storage.databasehelper import get_requests


class Billing(commands.Cog, name="billing"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="billing",
        description="Get the billing information."
    )
    @commands.guild_only()
    @app_commands.describe(
        user="The user to get the billing information for.",
    )
    async def billing(self, interaction: discord.Interaction, user: discord.User = None) -> None:
        member = await interaction.guild.fetch_member(interaction.user.id)
        if member is None:
            eb = geterrorembedbuilder("Member null", "Member is null")
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        target = member
        target_id = member.id
        if member.guild_permissions.administrator and user is not None:
            target = user
            target_id = user.id
        elif user is not None:
            eb = getnopermsembedbuilder()
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return
        if get_requests().get(target_id) is None:
            eb = (getbaseembedbuilder()
                  .settitle("No Information")
                  .setdescription("No billing information available for this user.")
                  .setcolor(discord.Color.red())
                  .build())
            await interaction.response.send_message(embed=eb, ephemeral=True)
            return

        requests = get_requests().get(target_id)
        input_cost, output_cost, total_cost = 0.0, 0.0, 0.0
        for request in requests:
            input_cost += ((request.model.input_cost() / 1000.0) * request.model.input_cost())
            output_cost += ((request.model.output_cost() / 1000.0) * request.model.output_cost())

        input_cost = Decimal(input_cost).quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)
        output_cost = Decimal(output_cost).quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)

        total_cost = input_cost + output_cost
        total_cost = Decimal(total_cost).quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)

        eb = (getbaseembedbuilder()
              .settitle("Billing Information")
              .setdescription("Below is the breakdown for the user's usage of the bot")
              .addfield("Username", target.name, True)
              .addfield("GPT Requests", f"{len(requests)}", True)
              .addfield("Input Cost", f"${input_cost}", True)
              .addfield("Output Cost", f"${output_cost}", True)
              .addfield("Total Cost", f"${total_cost}", True)
              .black()
              .build())
        await interaction.response.send_message(embed=eb, ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Billing(bot))


