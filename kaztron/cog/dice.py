import logging
import random

import discord
from discord.ext import commands

from kaztron import errors
from kaztron.config import get_kaztron_config
from kaztron.utils.checks import in_channels
from kaztron.utils.logging import message_log_str

logger = logging.getLogger(__name__)


class DiceCog:
    config = get_kaztron_config()
    ch_allowed_list = (
        config.get('dice', 'channel_dice'),
        config.get("discord", "channel_test"),
        config.get("discord", "channel_output")
    )

    def __init__(self, bot):
        self.bot = bot
        self.ch_dice = None

    async def on_ready(self):
        self.ch_dice = self.bot.get_channel(self.config.get('dice', 'channel_dice'))
        if self.ch_dice is None:
            raise ValueError("Channel {} not found".format(self.config.get('dice', 'channel_dice')))

    @commands.command(pass_context=True, ignore_extra=False, aliases=['rolls'])
    @in_channels(ch_allowed_list)
    async def roll(self, ctx, dice: str):
        """
        Rolls dice.

        Rolls a <sides>-sided die <num> times, and reports the rolls and total.

        Example: `.rolls 3d6` rolls three six-sided dice.
        """
        logger.info("roll: {}".format(message_log_str(ctx.message)))

        try:
            num_rolls, num_sides = map(int, dice.split('d'))
        except ValueError:
            err_msg = "Invalid format: {}".format(message_log_str(ctx.message))
            logger.warning("rolls(): " + err_msg)
            await self.bot.say('Invalid format. Please enter `.rolls XdY`, '
                               'where X and Y are positive whole numbers.')
            return

        if num_rolls <= 0:
            logger.warning("rolls(): arguments out of range")
            await self.bot.say("You have to roll at least 1 die.")
        elif num_sides <= 1:
            logger.warning("rolls(): arguments out of range")
            await self.bot.say("Dice must have at least 2 sides.")
        elif num_sides > 100 or num_rolls > 100:
            logger.warning("rolls(): arguments out of range")
            await self.bot.say("The limit for dice number and sides is 100 each.")
        else:
            result = [random.randint(1, num_sides) for _ in range(num_rolls)]
            total = sum(result)
            await self.bot.say("{!s}\n**Sum:** {:d}".format(result, total))
            logger.info("Rolled dice: {:d}d{:d} = {!r} (sum={})"
                .format(num_rolls, num_sides, result, total))

    @commands.command(pass_context=True, ignore_extra=False)
    @in_channels(ch_allowed_list)
    async def rollf(self, ctx):
        """
        Rolls four dice for the FATE tabletop roleplaying game system.

        Arguments: None
        """
        logger.info("roll: {}".format(message_log_str(ctx.message)))
        dice = (-1, -1, 0, 0, 1, 1)
        str_map = {-1: '-', 0: '0', 1: '+'}
        roll_results = [random.choice(dice) for _ in range(4)]
        total = sum(roll_results)
        rolls_str = [str_map[roll] for roll in roll_results]
        await self.bot.say("{!s}\n**Sum:** {:d}".format(rolls_str, total))
        logger.info("Rolled FATE dice: {!r} (sum={})".format(rolls_str, total))

    @roll.error
    @rollf.error
    async def roll_on_error(self, exc, ctx):
        cmd_string = message_log_str(ctx.message)
        if isinstance(exc, commands.CommandInvokeError):
            root_exc = exc.__cause__ if exc.__cause__ is not None else exc

            if isinstance(root_exc, errors.UnauthorizedChannelError):
                logger.error("Unauthorized use of command in #{1}: {0}"
                    .format(cmd_string, ctx.message.channel.name))
                await self.bot.send_message(ctx.message.channel,
                    "Sorry, this command can only be used in {}".format(self.ch_dice.mention))

            else:
                core_cog = self.bot.get_cog("CoreCog")
                await core_cog.on_command_error(exc, ctx, force=True)  # Other errors can bubble up
        else:
            core_cog = self.bot.get_cog("CoreCog")
            await core_cog.on_command_error(exc, ctx, force=True)  # Other errors can bubble up


def setup(bot):
    bot.add_cog(DiceCog(bot))
