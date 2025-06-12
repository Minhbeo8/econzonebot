import nextcord
from nextcord.ext import commands
from core.checks import is_bot_owner_or_moderator
from core.icons import Icons # SỬA ĐỔI

class UnmuteBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(self.bot, 'muted_channels'):
            self.bot.muted_channels = {}

    @commands.command(name="unmutebot")
    @is_bot_owner_or_moderator()
    async def unmute_bot(self, ctx, channel: nextcord.TextChannel = None):
        target_channel = channel or ctx.channel
        
        if self.bot.muted_channels.pop(target_channel.id, None):
            embed = nextcord.Embed(
                title=f"{Icons.unmute} Bot đã được bật tiếng", # SỬA ĐỔI
                description=f"Bot đã được bật tiếng trở lại trong kênh {target_channel.mention}.",
                color=nextcord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title=f"{Icons.info} Bot không bị tắt tiếng", # SỬA ĐỔI
                description=f"Bot hiện không bị tắt tiếng trong kênh {target_channel.mention}.",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(UnmuteBot(bot))
