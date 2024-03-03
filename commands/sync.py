from discord.ext import commands

from util.builder import getbaseembedbuilder


class Sync(commands.Cog, name="sync"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(
        name="sync",
        description="Sync all of the commands"
    )
    @commands.is_owner()
    @commands.guild_only()
    async def sync(self, ctx: commands.Context) -> None:
        synced = await self.bot.tree.sync()

        eb = (getbaseembedbuilder()
              .settitle("Synced Commands")
              .setdescription(f"Synced {len(synced)} commands. The commands are below.")
              .black())
        for command in self.bot.tree.walk_commands():
            eb.addfield(command.name, command.description, True)
        await ctx.send(embed=eb.build(), ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Sync(bot))
