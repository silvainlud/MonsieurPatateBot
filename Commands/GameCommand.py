import discord
import typing
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_slash.model import SlashCommandOptionType

from Commands import ReloadGameCommand
from Database.AllowUserCommand import AllowUserCommand
from Database.GameRoleAllow import GameRoleAllow
from Database.Games import Game


class GameCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @cog_ext.cog_slash(name="allowusercmd",
                       description="ajout un utilsateur a lites des utilisateurs pour les commandes", options=[
            create_option(
                name="user",
                description="nom d'un utilisateur",
                option_type=SlashCommandOptionType.USER,
                required=False
            ), create_option(
                name="remove",
                description="remove",
                option_type=SlashCommandOptionType.BOOLEAN,
                required=False
            )
        ])
    async def allowusercmd(self, ctx: SlashContext, user: discord.User = None, remove: bool = False):
        if ctx.author_id != ctx.guild.owner_id:
            await ctx.send(content=("ERROR : Non autorisé !!!"), hidden=True)

        if user is None:
            user = ctx.author

        if remove:
            allow: AllowUserCommand = AllowUserCommand.findByUser(str(user.id))
            if allow is None:
                await ctx.send(content=("ERROR : " + user.mention + " n'est pas autorisé."), hidden=True)
                return

            AllowUserCommand.delete(allow)

            await ctx.send(content=("Pour " + user.mention + " suppresion de l'autorisation."), hidden=True)
        else:
            allow: AllowUserCommand = AllowUserCommand.findByUser(str(user.id))
            if allow is not None:
                await ctx.send(content=("ERROR : " + user.mention + " est autorisé."), hidden=True)
                return

            allow = AllowUserCommand()
            allow.MemberId = str(user.id)
            AllowUserCommand.create(allow)

            await ctx.send(content=("Pour " + user.mention + " ajout de l'autorisation."), hidden=True)

    @cog_ext.cog_slash(name="adduser", description="ajout un utilsateur", options=[
        create_option(
            name="name",
            description="nom",
            option_type=SlashCommandOptionType.STRING,
            required=True
        ), create_option(
            name="user",
            description="nom d'un utilisateur",
            option_type=SlashCommandOptionType.USER,
            required=False
        ), create_option(
            name="remove",
            description="remove",
            option_type=SlashCommandOptionType.BOOLEAN,
            required=False
        )
    ])
    async def adduser(self, ctx: SlashContext, name: str, user: discord.User = None, remove: bool = False):
        if AllowUserCommand.accessDeniedUser(ctx.author_id):
            await ctx.send(content=("ERROR : Non autorisé !!!"), hidden=True)
            return

        game = Game.findOneByName(name, ctx.guild.id)
        if Game.findOneByName(name, ctx.guild.id) is None:
            print("[AddGame] " + name + " n'existe pas.")
            await ctx.send(content=("[AddGame] " + name + " n'existe pas."), hidden=True)
            return

        if user is None:
            member: discord.Member = ctx.author
        else:
            member: discord.Member = ctx.guild.get_member(user.id)

        role: discord.Role = ctx.guild.get_role(int(game.roleId))
        if role is not None and member is not None:
            if remove:
                await member.remove_roles(role)
                await ctx.send(content=(member.display_name + " suppression de " + game.name), hidden=True)
            else:
                await member.add_roles(role)
                await ctx.send(content=(member.display_name + " accès à " + game.name), hidden=True)

    @cog_ext.cog_slash(name="allowgame", description="restriction d un jeux", options=[
        create_option(
            name="name",
            description="nom du jeux",
            option_type=SlashCommandOptionType.STRING,
            required=True
        ), create_option(
            name="role",
            description="Role de la section",
            option_type=SlashCommandOptionType.ROLE,
            required=True
        ), create_option(
            name="allow",
            description="allow",
            option_type=SlashCommandOptionType.BOOLEAN,
            required=False
        )
    ])
    async def allowgame(self, ctx: SlashContext, name: str, role: discord.Role = None, allow: bool = True):

        if AllowUserCommand.accessDeniedUser(ctx.author_id):
            await ctx.send(content=("ERROR : Non autorisé !!!"), hidden=True)
            return

        game = Game.findOneByName(name, ctx.guild.id)
        if Game.findOneByName(name, ctx.guild.id) is None:
            print("[AddGame] " + name + " n'existe pas.")
            await ctx.send(content=("[AddGame] " + name + " n'existe pas."), hidden=True)
            return

        if not game.restricted:
            print("[AddGame] " + name + " n'est pas en mode de restriction.")
            await ctx.send(content=("[AddGame] " + name + " n'est pas en mode de restriction."), hidden=True)
            return

        if allow:
            if GameRoleAllow.findOneByGameRole(game.id, role.id) is not None:
                await ctx.send(content=("[AddGame] pour " + name + " la restriction existe déjà."), hidden=True)
                return
            allow = GameRoleAllow()
            allow.GameId = game.id
            allow.RoleId = role.id
            GameRoleAllow.create(allow)
        else:
            allow = GameRoleAllow.findOneByGameRole(game.id, role.id)
            if allow is None:
                await ctx.send(content=("[AddGame] pour " + name + " aucune restriction existe pour ce role."),
                               hidden=True)
                return
            GameRoleAllow.delete(allow)

        await ctx.send(content=("[AddGame] OK !."), hidden=True)

    @cog_ext.cog_slash(name="addgame", description="ajout d un jeux", options=[
        create_option(
            name="name",
            description="nom du jeux",
            option_type=SlashCommandOptionType.STRING,
            required=True
        ), create_option(
            name="emoticon",
            description="emoticon",
            option_type=SlashCommandOptionType.STRING,
            required=True
        ), create_option(
            name="category",
            description="Categorie de la section",
            option_type=SlashCommandOptionType.CHANNEL,
            required=False
        ), create_option(
            name="role",
            description="Role de la section",
            option_type=SlashCommandOptionType.ROLE,
            required=False
        ), create_option(
            name="restricted",
            description="restricted",
            option_type=SlashCommandOptionType.BOOLEAN,

            required=False
        )
    ])
    async def addgame(self, ctx: SlashContext, name: str, emoticon: str,
                      category: typing.Union[discord.CategoryChannel, discord.VoiceChannel, discord.TextChannel] = None,
                      role: discord.Role = None, restricted: bool = False
                      ):

        if AllowUserCommand.accessDeniedUser(ctx.author_id):
            await ctx.send(content=("ERROR : Non autorisé !!!"), hidden=True)
            return

        if Game.findOneByName(name, ctx.guild.id) is not None:
            print("[AddGame] " + name + " existe déjà.")
            await ctx.send(content=("[AddGame] " + name + " existe déjà."), hidden=True)
            return

        game: Game = Game()
        game.name = name
        game.emoticon = emoticon
        game.memberIdCreate = ctx.author.id
        game.memberUsernameCreate = ctx.author.name
        game.restricted = restricted

        guild: discord.Guild = ctx.guild
        game.guildId = guild.id

        if category == None:
            category: discord.CategoryChannel = await guild.create_category(name)
        elif category.type != discord.ChannelType.category:
            await ctx.send(content=("[AddGame] " + category.name + " n'est pas une category."), hidden=True)
            return
        game.categoryId = category.id

        if role == None:
            role: discord.Role = await guild.create_role(name=name, mentionable=True, hoist=False,
                                                         permissions=discord.Permissions(0))
        game.roleId = role.id

        await category.set_permissions(ctx.guild.default_role, view_channel=False, connect=False, read_messages=False,
                                       send_messages=False, speak=False)
        await category.set_permissions(role, view_channel=True, connect=True, read_messages=True, send_messages=True,
                                       speak=True)

        generalChannel = discord.utils.get(category.channels, name="general")
        if generalChannel is None:
            await guild.create_text_channel("general", category=category, sync_permissions=True)

        voiceChannel = discord.utils.get(category.channels, name="Vocal#1")
        if voiceChannel is None:
            await guild.create_voice_channel("Vocal#1", category=category, sync_permissions=True)

        Game.create(game)
        await ctx.send(content=("Ok ! <@&" + str(role.id) + ">"), hidden=True)
        await ReloadGameCommand.reloadChannelAnnounce(guild)

    @cog_ext.cog_slash(name="removegame", description="delete a game", options=[
        create_option(
            name="name",
            description="nom du jeux",
            option_type=SlashCommandOptionType.STRING,
            required=True
        ),
        create_option(
            name="delete",
            description="delete (par defaut false) cela ne concerne que les channels mais pas les roles",
            option_type=SlashCommandOptionType.BOOLEAN,
            required=False
        )
    ])
    async def removegame(self, ctx: SlashContext, name: str, delete : bool = False):

        if AllowUserCommand.accessDeniedUser(ctx.author_id):
            await ctx.send(content=("ERROR : Non autorisé !!!"), hidden=True)
            return

        game: Game = Game.findOneByName(name, ctx.guild.id)
        if game is None:
            print("[RemoveGame] " + name + " n'existe pas.")
            await ctx.send(content=("[RemoveGame] " + name + " n'existe pas."), hidden=True)
            return

        guild: discord.Guild = ctx.guild
        role: discord.Role = guild.get_role(int(game.roleId))
        category: discord.CategoryChannel = discord.utils.get(guild.categories, id=int(game.categoryId))

        if category is not None and delete:
            for c in category.channels:
                await c.delete(reason="Remove game : " + game.name)
            await category.delete(reason="Remove game : " + game.name)

        if role is not None:
            await role.delete(reason="Remove game : " + game.name)

        await ctx.send(content=("Aurevoir ! " + game.name), hidden=True)

        Game.delete(game)
        await ReloadGameCommand.reloadChannelAnnounce(guild)

        return


def setup(bot):
    bot.add_cog(GameCommand(bot))
