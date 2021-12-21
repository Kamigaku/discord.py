from __future__ import annotations

import copy
import inspect
import typing

if typing.TYPE_CHECKING:
    from discord import ChannelType, InvalidArgument
from dataclasses import dataclass

import discord.ext.commands as ext_commands
import discord.enums
import discord.http

__all__ = ['ApplicationCommand',
           'slash_command']

_pre_registration_commands = {}
_registered_global_commands = {}
_registered_guild_commands = {}


#  ENUMS


class ApplicationCommandOptionType(discord.enums.Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 8
    NUMBER = 10


class ApplicationCommandType(discord.enums.Enum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


# DATACLASSES


@dataclass
class ApplicationCommandInteractionDataOption:
    name: str
    type: int
    value: ApplicationCommandOptionType | None = None
    options: typing.List[ApplicationCommandInteractionDataOption] | None = None
    focused: bool = False

    def __repr__(self):
        data = {
            "name": self.name,
            "type": self.type,
            "focused": self.focused
        }

        if self.value is not None:
            data["value"] = self.value.value

        if self.options is not None:
            data["options"] = []
            for option in self.options:
                data["options"].append(option)

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandInteractionDataOption):
            return False
        if (self.name != other.name or
                self.type != other.type or
                self.value.value != other.value.value or
                self.options != other.options or
                self.focused != other.focused):
            return False
        return True


@dataclass
class ApplicationCommandOptionChoice:
    name: str
    value: typing.Union[str | int | float]

    def __repr__(self):
        data = {
            "name": self.name,
            "value": self.value
        }
        return data

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandOptionChoice):
            return False
        if self.name != other.name or self.value != other.value:
            return False
        return True

    def __ne__(self, other):
        return not self == other


@dataclass
class ApplicationCommandOption:
    type: ApplicationCommandOptionType
    name: str
    description: str
    required: bool = False
    choices: typing.List[ApplicationCommandOptionChoice] | None = None
    options: typing.List[ApplicationCommandOption] | None = None
    channel_types: typing.List[ChannelType] | None = None
    min_value: int | None = None
    max_value: int | None = None
    autocomplete: bool = False

    def __post_init__(self):
        if self.type is not None and isinstance(self.type, int):
            self.type = ApplicationCommandOptionType(self.type)
        if self.choices is not None and any(not isinstance(x, ApplicationCommandOptionChoice) for x in self.choices):
            buffer_choices = copy.copy(self.choices)
            self.choices = []
            for buffer_choice in buffer_choices:
                self.choices.append(ApplicationCommandOptionChoice(**buffer_choice))
        if self.options is not None and any(not isinstance(x, ApplicationCommandOption) for x in self.options):
            buffer_options = copy.copy(self.options)
            self.options = []
            for buffer_option in buffer_options:
                self.options.append(ApplicationCommandOption(**buffer_option))

    def __repr__(self):
        data = {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "required": self.required,
            "autocomplete": self.autocomplete
        }
        if self.choices is not None:
            data["choices"] = []
            for choice in self.choices:
                data["choices"].append(choice.__repr__())

        if self.options is not None:
            data["options"] = []
            for option in self.options:
                data["options"].append(option.__repr__())

        if self.channel_types is not None:
            data["channel_types"] = []
            for channel_type in self.channel_types:
                data["channel_types"].append(channel_type.value)

        if self.min_value is not None:
            data["min_value"] = self.min_value

        if self.max_value is not None:
            data["max_value"] = self.max_value

        return data

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommandOption):
            return False
        if (self.type.value != other.type.value or
                self.name != other.name or
                self.description != other.description or
                self.autocomplete != other.autocomplete or
                self.max_value != other.max_value or
                self.min_value != other.min_value or
                self.channel_types != other.channel_types or
                self.required != other.required or
                self.options != other.options or
                self.choices != other.options):
            return False
        return True

    def __ne__(self, other):
        return not self == other

    @classmethod
    def from_payload(cls, data: dict[str, typing.Any] | None):
        if data is None:
            return cls()
        return cls(**data)


class ApplicationCommand:

    def __init__(self, name: str,
                 description: str,
                 callback: typing.Any | None = None,
                 id: int | None = None,
                 application_id: int | None = None,
                 version: int | None = None,
                 type: int | ApplicationCommandType = ApplicationCommandType.CHAT_INPUT,
                 guild_id: int = None,
                 options: typing.List[ApplicationCommandOption] = None,
                 default_permission: bool = True,
                 default_member_permissions: bool | None = None,
                 dm_permission: bool | None = None,
                 cog: ext_commands.Cog | None = None):
        self.callback: typing.Any | None = callback
        self.id: int | None = id
        if isinstance(type, int):
            self.type: ApplicationCommandType = ApplicationCommandType(type)
        else:
            self.type: ApplicationCommandType = type
        self.application_id: int | None = application_id
        self.guild_id: int | None = guild_id
        self.name: str = name
        self.description: str = description
        # options est une list de ApplicationCommandOption
        if options is None or any(isinstance(x, ApplicationCommandOption) for x in options):
            self.options: typing.List[ApplicationCommandOption] | None = options
        else:
            self.options: typing.List[ApplicationCommandOption] = []
            for option in options:
                self.options.append(ApplicationCommandOption.from_payload(option))
        self.default_permission: bool = default_permission
        self.default_member_permissions: bool | None = default_member_permissions
        self.dm_permission: bool | None = dm_permission
        self.version: int = version
        self.cog = cog

    @classmethod
    def from_payload(cls, data: dict[str, typing.Any] | None):
        if data is None:
            return cls()
        return cls(**data)

    def __copy__(self):
        return ApplicationCommand(type=self.type,
                                  name=self.name,
                                  description=self.description,
                                  callback=self.callback,
                                  options=self.options)

    def __repr__(self):
        data = {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "default_permission": self.default_permission
        }
        if self.id is not None:
            data["id"] = self.id
        if self.application_id is not None:
            data["application_id"] = self.application_id
        if self.version is not None:
            data["version"] = self.version
        if self.guild_id is not None:
            data["guild_id"] = self.guild_id
        if self.options is not None:
            data["options"] = []
            for option in self.options:
                data["options"].append(option.__repr__())
        return data

    def __eq__(self, other):
        if not isinstance(other, ApplicationCommand):
            return False
        if (self.type.value != other.type.value or
                self.name != other.name or
                self.description != other.description or
                self.guild_id != other.guild_id or
                self.default_permission != other.default_permission or
                self.default_member_permissions != other.default_member_permissions or
                self.dm_permission != other.dm_permission or
                self.options != other.options):
            return False
        return True

    def __ne__(self, other):
        return not self == other


async def register_commands(bot: 'ext_commands.Bot'):
    application_info = await bot.application_info()

    # Registering guild commands
    pre_registration_guild_commands = []
    # for command in _pre_registration_guild_commands:
    #     pre_registration_guild_commands.extend(commands)
    # for guild in bot.guilds:
    #     pre_registration_guild_commands_data = [command.register_data for command
    #                                             in pre_registration_guild_commands]
    #     result = await bot._connection.http.request(
    #         Route('PUT', '/applications/{application_id}/guilds/{guild_id}/commands',
    #               application_id=application_info.id, guild_id=guild.id),
    #         json=pre_registration_guild_commands_data)
    #
    #     for i in range(len(result)):
    #         server_command = copy(pre_registration_guild_commands[i])
    #         server_command.update_data(result[i])
    #         server_command.cog = pre_registration_guild_commands[i].cog
    #         _registered_guild_commands[server_command.id] = server_command
    for guild in bot.guilds:
        pre_registration_guild_commands_data = [command for command
                                                in pre_registration_guild_commands]
        result = await bot._connection.http.request(
            discord.http.Route('PUT', '/applications/{application_id}/guilds/{guild_id}/commands',
                               application_id=application_info.id, guild_id=guild.id),
            json=pre_registration_guild_commands_data)

    # Registering global commands
    # pre_registration_global_commands = []
    # for _, commands in _pre_registration_global_commands.items():
    #     pre_registration_global_commands.extend(commands)
    # pre_registration_global_commands_data = [command.register_data for command
    #                                          in pre_registration_global_commands]
    # result = await bot._connection.http.request(
    #     Route('PUT', '/applications/{application_id}/commands',
    #           application_id=application_info.id),
    #     json=pre_registration_global_commands_data)


# async def retrieve_global_commands(bot: ext_commands.Bot):
#     application_info = await bot.application_info()
#     result = await bot._connection.http.request(
#         Route('GET', '/applications/{application_id}/commands',
#               application_id=application_info.id))
#     return result
#
#
# async def retrieve_guild_commands(bot: ext_commands.Bot, guild_id: int):
#     application_info = await bot.application_info()
#     result = await bot._connection.http.request(
#         Route('GET', '/applications/{application_id}/guilds/{guild_id}/commands',
#               application_id=application_info.id, guild_id=guild_id))
#     return result


def slash_command(callback, name=None, description=None, guild_id=None):
    if not description:
        description = inspect.getdoc(callback)
    if not description:
        description = 'No description yet'
    if not name:
        name = callback.__name__
    args = inspect.getfullargspec(callback)
    options = None
    if len(args.annotations) > 0:
        options = []
        for arg_name, arg_type in args.annotations.items():
            if issubclass(arg_type, str):
                current_type = ApplicationCommandOptionType.STRING
            elif issubclass(arg_type, int):
                current_type = ApplicationCommandOptionType.INTEGER
            elif issubclass(arg_type, bool):
                current_type = ApplicationCommandOptionType.BOOLEAN
            elif issubclass(arg_type, discord.User):
                current_type = ApplicationCommandOptionType.USER
            elif issubclass(arg_type, discord.abc.GuildChannel):
                current_type = ApplicationCommandOptionType.CHANNEL
            elif issubclass(arg_type, discord.Role):
                current_type = ApplicationCommandType.ROLE
            elif issubclass(arg_type, discord.Mentionable):
                current_type = ApplicationCommandOptionType.MENTIONABLE
            elif issubclass(arg_type, float):
                current_type = ApplicationCommandOptionType.NUMBER
            # Il faudra aussi ajouter un cas "Context" qui sera ignoré
            else:
                raise InvalidArgument(f"The type for the argument {arg_name} for the slash commands "
                                      f"{callback.__name__} does not match any type expected.")
            options.append(ApplicationCommandOption(type=current_type,
                                                    name=arg_name,
                                                    description="temporary description"))

    command = ApplicationCommand(type=ApplicationCommandType.CHAT_INPUT, name=name,
                                 description=description, callback=callback, guild_id=guild_id,
                                 options=options)
    if guild_id not in _pre_registration_commands:
        _pre_registration_commands[guild_id] = []
    _pre_registration_commands[guild_id].append(command)
    return command
