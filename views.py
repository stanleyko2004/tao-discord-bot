from collections import deque
import discord


class PaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()

        self._embeds = embeds
        self._len = len(embeds)
        self._initial = embeds[0]
        self._queue = deque(embeds)
        self._current_page = 0
        self.children[0].disabled = True
        if len(embeds) == 1: self.children[1].disabled = True

        for i in range(self._len):
            self._embeds[i].set_footer(text=f"Page {i+1} of {self._len}")

    # Updates buttons to disable when at ends and enable otherwise
    async def update_view(self, interaction: discord.Interaction):

        if self._current_page == self._len - 1:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False

        if self._current_page == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        await interaction.message.edit(view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page -= 1
        await self.update_view(interaction)
        await interaction.response.edit_message(embed=embed)
        
    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def forward_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self._current_page += 1
        await self.update_view(interaction)
        await interaction.response.edit_message(embed=embed)

    # Used to access and display inital page
    @property
    async def initial(self) -> discord.Embed:
        return self._embeds[0]