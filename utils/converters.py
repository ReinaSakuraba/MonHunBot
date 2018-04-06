from discord.ext import commands


__all__ = ('CommandConverter',)


class CommandConverter(commands.Converter):
    async def convert(self, ctx, argument):
        obj = ctx.bot.get_cog(argument) or ctx.bot.get_command(argument)
        if obj is None:
            raise commands.BadArgument(f'No command called "{argument}" found.')

        return obj
