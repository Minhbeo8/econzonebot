# Trong file cogs/misc/help_slash_cmd.py, bên trong class HelpSlashCommandCog

    @nextcord.slash_command(name="menu", description="Mở menu trợ giúp chính.")
    async def menu_slash_command(self, interaction: nextcord.Interaction):
        try:
            # Defer ngay lập tức để báo cho Discord rằng "tôi đã nhận được lệnh"
            await interaction.response.defer(ephemeral=True)

            # Tạo embed và view như cũ
            initial_embed = nextcord.Embed(
                title=f"{ICON_INFO} Menu Trợ giúp",
                description="Chào mừng đến với EconZone! Vui lòng chọn một mục từ menu bên dưới để xem chi tiết các lệnh.",
                color=nextcord.Color.blue()
            )
            initial_embed.set_footer(text="Bot được phát triển bởi minhbeo8")
            
            all_cogs_info = [cog for cog in self.cogs_data if not cog.get("hide_from_menu")]
            view = HelpMenuView(all_cogs_info, interaction.user, self.bot)

            # Gửi tin nhắn trả lời bằng followup vì đã defer
            await interaction.followup.send(embed=initial_embed, view=view, ephemeral=True)
            view.message = await interaction.original_message()

        except nextcord.errors.HTTPException as e:
            # Ghi lại log khi có lỗi timeout hoặc double-ack, thay vì làm sập chương trình
            logger.warning(f"Lỗi khi phản hồi tương tác /menu (có thể do timeout): {e}")
            # Không cần làm gì thêm, vì tương tác đã thất bại
            pass
        except Exception as e:
            # Bắt các lỗi khác nếu có
            logger.error(f"Lỗi không xác định trong /menu: {e}", exc_info=True)
