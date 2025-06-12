import nextcord
from nextcord.ext import commands
from core.checks import is_bot_owner_or_moderator
from datetime import datetime, timedelta
from core.icons import Icons # SỬA ĐỔI

class MuteBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mutebot")
    @is_bot_owner_or_moderator()
    async def mute_bot(self, ctx, channel: nextcord.TextChannel = None):
        target_channel = channel or ctx.channel
        
        # Giả sử bot có thuộc tính này để quản lý mute
        if not hasattr(self.bot, 'muted_channels'):
            self.bot.muted_channels = {}

        self.bot.muted_channels[target_channel.id] = True
        
        embed = nextcord.Embed(
            title=f"{Icons.mute} Bot đã được tắt tiếng", # SỬA ĐỔI
            description=f"Bot đã bị tắt tiếng trong kênh {target_channel.mention}.",
            color=nextcord.Color.orange()
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(MuteBot(bot))
