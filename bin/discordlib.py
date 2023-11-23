#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import os
import sys

import discord

import logging
# logging.basicConfig(level=logging.DEBUG)

from datetime import datetime

from pyail import PyAIL

dir_path = os.path.dirname(os.path.realpath(__file__))
pathConf = os.path.join(dir_path, '../etc/conf.cfg')

# TODO ADD TO LOGS
# Check the configuration and do some preliminary structure checks
try:
    config = configparser.ConfigParser()
    config.read(pathConf)

# Check AIL configuration, set variables and do the connection test to AIL API
    if 'AIL' not in config:
        print('[ERROR] The [AIL] section was not defined within conf.cfg. Ensure conf.cfg contents are correct.')
        sys.exit(0)

    try:
        # Set variables required for the Telegram Feeder
        feeder_uuid = config.get('AIL', 'feeder_uuid')
        ail_url = config.get('AIL', 'url')
        ail_key = config.get('AIL', 'apikey')
        ail_verifycert = config.getboolean('AIL', 'verifycert')
        ail_feeder = config.getboolean('AIL', 'ail_feeder')
    except Exception as e:
        print(e)
        print('[ERROR] Check ../etc/conf.cfg to ensure the following variables have been set:\n')
        print('[AIL] feeder_uuid \n')
        print('[AIL] url \n')
        print('[AIL] apikey \n')
        sys.exit(0)

    if ail_feeder:
        try:
            ail = PyAIL(ail_url, ail_key, ssl=ail_verifycert)
        except Exception as e:
            print('[ERROR] Unable to connect to AIL Framework API. Please check [AIL] url, apikey and verifycert in ../etc/conf.cfg.\n')
            sys.exit(0)
    else:
        # print('[INFO] AIL Feeder has not been enabled in [AIL] ail_feeder. Feeder script will not send output to AIL.\n')
        ail = None
    # /End Check AIL configuration

    # Check Telegram configuration, set variables and do the connection test to Telegram API
    if 'DISCORD' not in config:
        print('[ERROR] The [DISCORD] section was not defined within conf.cfg. Ensure conf.cfg contents are correct.')
        sys.exit(0)

    try:
        token = config.get('DISCORD', 'token')
    except Exception as e:
        print('[ERROR] Check ../etc/conf.cfg to ensure the following variables have been set:\n')
        print('[DISCORD] token \n')
        sys.exit(0)
    # /End Check Discord configuration

except FileNotFoundError:
    print('[ERROR] ../etc/conf.cfg was not found. Copy conf.cfg.sample to conf.cfg and update its contents.')
    sys.exit(0)


USERS = {}


def unpack_datetime(datetime_obj):
    date_dict = {'datestamp': datetime.strftime(datetime_obj, '%Y-%m-%d %H:%M:%S'),
                 'timestamp': datetime_obj.timestamp(),
                 'timezone': datetime.strftime(datetime_obj, '%Z')}
    return date_dict

def _unpack_user(user):  # TODO RENAME KEYS NAME
    meta = {'username': user.name,
            'display_name': user.display_name,
            'bot': user.bot,
            'id': user.id,
            'date': unpack_datetime(user.created_at)}

    # discriminator
    # user.is_pomelo() -> check if use uniq username

    # mention
    # avatar
    # default_avatar
    # display_avatar
    return meta

def _unpack_member(member):
    meta = _unpack_user(member)
    if member.nick:
        meta['nick'] = member.nick

    # pending
    # status
    # raw_status
    # mobile_status
    # desktop_status
    # web_status
    # activities
    # activity
    # voice

    # roles
    # guild_avatar

    # guild
    return meta

async def _unpack_author(author):
    if isinstance(author, discord.Member):
        # await get_user_profile(author)
        return _unpack_member(author)
    elif isinstance(author, discord.User):
        # await get_user_profile(author)
        return _unpack_user(author)
    # elif isinstance(author, discord.abc.User): # TODO RAISE ERROR
    #     return

async def get_user_profile(user):  # TODO Restrict by guild ???
    if user.id in USERS:
        meta = USERS[user.id]
    else:
        meta = {'id': user.id}
        try:
            profile = await user.profile()
            if profile.bio:
                meta['about'] = profile.bio

            # if profile.avatar:
            #     print(await profile.avatar.read())

            print(meta)
            # sys.exit(0)
        except discord.errors.NotFound:
            pass
        USERS[user.id] = meta
    return meta

def _unpack_guild(chat):
    meta = {'id': chat.id, 'name': chat.name, 'type': 'server'}
    if chat.description:
        meta['info'] = chat.description
    meta['date'] = unpack_datetime(chat.created_at)
    if chat.member_count:
        meta['participants'] = chat.member_count
    # owner_id
    # owner
    # vanity_url_code

    # icon
    # banner
    # joined_at

    # channels
    # threads
    # voice_channels
    # stage_channels ???
    # text_channels ???
    # categories
    # forum ??????????????????????????
    # directory_channels
    # vanity_url
    # vanity_invite

    # members
    # online_count

    # roles
    # default_role

    # scheduled_events

    # premium_subscribers
    # premium_subscription_count

    # leave()
    return meta

def _unpack_dm_channel(channel):
    meta = {'id': channel.id,
            'date': unpack_datetime(channel.created_at),
            'type': 'dm',
            'user': _unpack_user(channel.recipient)}

    # type
    # last_message_id
    return meta

def _unpack_group_channel(channel):
    meta = {'id': channel.id,
            'date': unpack_datetime(channel.created_at),
            'type': 'group'}
    if channel.name:
        meta['name'] = channel.name
    if channel.owner:
        meta['owner'] = _unpack_user(channel.owner)
    meta['users'] = []
    for user in channel.recipients:
        meta['users'].append(_unpack_user(user))
    # icon
    # nicks
    return meta

def _unpack_private_channel(channel):
    if isinstance(channel, discord.DMChannel):
        return _unpack_dm_channel(channel)
    elif isinstance(channel, discord.GroupChannel):
        return _unpack_group_channel(channel)

def _unpack_guid_channel(channel):
    meta = {'id': channel.id,
            'date': unpack_datetime(channel.created_at),
            'type': 'server_channel'}
    if channel.name:
        meta['name'] = channel.name

    return meta

def _unpack_channel(channel): # TODO type=Thread:unpack thread
    if isinstance(channel, discord.abc.PrivateChannel):
        return _unpack_private_channel(channel)
    elif isinstance(channel, discord.abc.GuildChannel):
        return _unpack_guid_channel(channel)
    # TODO unpack thread

def _unpack_embedded(embedded):
    # image
    # thumbnail
    # video
    # provider
    # author

    embed = embedded.to_dict()
    content = ''  # TODO icon URL
    if 'title' in embed:
        if 'url' in embed:
            content = f'[{embed["title"]}]({embed["url"]})\n'
        else:
            content = f'{embed["title"]}\n'
    elif 'url' in embed:
        content = f'{embed["url"]}\n'
    if 'description' in embed:
        content = f'{content}{embed["description"]}\n'
    for field in embed.get('fields', []):
        if field['inline']:
            content = f'{content}{field["name"]}    {field["value"]}\n'
        else:
            content = f'{content}{field["name"]}\n{field["value"]}\n'
    if embed.get('footer'):
        content = f'{content}\n'
        if 'icon_url' in embed['footer']:
            content = f'{content}{embed["footer"]["icon_url"]}\n'
        if 'text' in embed['footer']:
            content = f'{content}{embed["footer"]["text"]}\n'
    # print(content)
    return content

async def get_attachment(meta, attachment):
    print(attachment.to_dict())
    print(attachment.content_type)
    if attachment.content_type:
        if attachment.content_type.startswith('image'):
            media_content = await attachment.read()
            meta['type'] = 'image'
            if ail:
                ail.feed_json_item(media_content, meta, 'discord', feeder_uuid)

def _unpack_reference(reference):
    meta = {}
    if reference.message_id:
        meta['message_id'] = reference.message_id
    if reference.guild_id:
        meta['guild_id'] = reference.guild_id
    if reference.channel_id:
        meta['channel_id'] = reference.channel_id
    return meta

def get_reply_to(meta): # TODO check if reference is not None
    reply_to = None
    chat_id = meta['chat']['id']
    if 'subchannel' in meta['chat']:
        subchannel_id = meta['chat']['subchannel']['id']
    else:
        subchannel_id = None

    # TODO check if guild id is NULL
    if chat_id == meta['reference'].get('guild_id'):
        if subchannel_id:
            if subchannel_id == meta['reference'].get('channel_id'):
                reply_to = meta['reference']['message_id']
            else:
                pass
                # reference to to other subchannel  # TODO SAVE AS REPLY ????
        else:
            reply_to = meta['reference']['message_id']
    else:
        pass
        # reference

    return reply_to

async def _unpack_message(message):
    meta = {'id': message.id, 'type': 'message'}  # embeds
    if message.edited_at:
        meta['edit_date'] = unpack_datetime(message.edited_at)
    meta['sender'] = await _unpack_author(message.author)
    meta['date'] = unpack_datetime(message.created_at)
    if message.edited_at:
        meta['edit_date'] = unpack_datetime(message.edited_at)

    if message.guild:
        meta['chat'] = _unpack_guild(message.guild)

        if message.channel:
            meta['chat']['subchannel'] = _unpack_guid_channel(message.channel)

    # mentions
    # raw_mentions
    # raw_channel_mentions
    # channel_mentions
    # attachments
    # pinned ?
    # reactions

    # jump url

    # is_acked
    # ack -> mark message as read

    print(meta)
    print()
    if message.reference:
        meta['reference'] = _unpack_reference(message.reference)
        reply_to = get_reply_to(meta)
        if reply_to:
            meta['reply_to'] = reply_to
            print(meta['reply_to'])
    print()
    # print(json.dumps(meta, indent=4, sort_keys=True))

    content = ''
    if message.embeds:
        for embedded in message.embeds:
            content = f'{content}\n{_unpack_embedded(embedded)}'
            # print()
            # print('------------------------------------------------------------------')
            # print()

    meta['data'] = f'{message.content}\n{content}'
    data = f'{message.content}{content}'

    # if message.embeds:
    print(json.dumps(meta, indent=4, sort_keys=True))

    if data:
        ail.feed_json_item(data, meta, 'discord', feeder_uuid)
    else:
        if message.attachments:
            print(meta)
            print()
            print(message.attachments)          # -> file
            print(message.system_content)       # discord.embeds
            print()
            print(json.dumps(meta, indent=4, sort_keys=True))
            # sys.exit(0)

    if message.attachments:
        for attachment in message.attachments:
            await get_attachment(meta, attachment)

    return meta


# # # # # # # # # # # # # # # #
#           CLI               #
# # # # # # # # # # # # # # # #

def get_entity(entity_id):
    class DiscordGetEntity(discord.Client):
        async def on_ready(self):
            meta = {}
            guild = self.get_guild(entity_id)
            if guild:
                meta['server'] = _unpack_guild(guild)
            channel = self.get_channel(entity_id)
            if channel:
                meta['channel'] = _unpack_channel(channel)
            user = self.get_user(entity_id)
            if user:
                meta['user'] = _unpack_user(user)
            print(json.dumps(meta, indent=4, sort_keys=True))
            await self.close()
    client = DiscordGetEntity()
    client.run(token)

def get_chats(l_channels=False):
    class DiscordChats(discord.Client):
        async def on_ready(self):
            chats = []
            for guild in self.guilds:
                meta = _unpack_guild(guild)
                if l_channels:
                    meta['subchannels'] = []
                    for channel in guild.channels:
                        meta['subchannels'].append(_unpack_channel(channel))
                chats.append(meta)
            for channel in self.private_channels:
                chats.append(_unpack_private_channel(channel))

            print(json.dumps(chats, indent=4, sort_keys=True))
            await self.close()
    client = DiscordChats()
    client.run(token)

async def _get_messages(entity, limit=20):
    try:
        async for message in entity.history(limit=limit):
            print(message)
            await _unpack_message(message)
    except discord.errors.Forbidden as e:
        print(e)

def get_channel_messages(channel_id, limit=5):  # TODO +> get thread + private dm
    class DiscordChannelMessage(discord.Client):
        async def on_ready(self):
            channel = client.get_channel(channel_id)
            if channel:
                await _get_messages(channel, limit=limit)
            else:
                pass
                # TODO ERROR IF channel NONE

            await self.close()
    client = DiscordChannelMessage()
    client.run(token)

def get_guild_messages(guild_id, limit=5):
    class DiscordGuildMessage(discord.Client):
        async def on_ready(self):
            guild = self.get_guild(guild_id)
            if guild:
                for channel in guild.channels:
                    print(type(channel))
                    if isinstance(channel, discord.CategoryChannel) or isinstance(channel, discord.ForumChannel): # TODO
                        continue
                    if channel.last_message_id:
                        await _get_messages(channel, limit=limit)
                    else:
                        pass
                        # TODO ERROR MESSAGE

            await self.close()
    client = DiscordGuildMessage()
    client.run(token)


def get_all_messages(limit=5):
    class DiscordAllMessages(discord.Client):
        async def on_ready(self):
            for guild in self.guilds:
                for channel in guild.channels:
                    print(type(channel))
                    # if not isinstance(channel, discord.ForumChannel): # TODO
                    #     continue
                    if isinstance(channel, discord.CategoryChannel) or isinstance(channel, discord.ForumChannel):  # TODO
                        continue
                    if channel.last_message_id:
                        await _get_messages(channel, limit=limit)

            for channel in self.private_channels:
                await _get_messages(channel, limit=limit)

            await self.close()
    client = DiscordAllMessages()
    client.run(token)


def join_guild(guild_id):
    class DiscordJoinGuild(discord.Client):
        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')

            try:
                await self.join_guild(guild_id)
            except discord.NotFound:
                print(f'ERROR: Guild {guild_id} not found')
            except discord.HTTPException as e:
                print(f'HTTP ERROR: {e}')
            await self.close()

    client = DiscordJoinGuild()
    client.run(token)

def leave_guild(guild_id):
    class DiscordLeaveGuild(discord.Client):
        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')

            try:
                await self.join_guild(guild_id)
            except discord.HTTPException as e:
                print(f'HTTP ERROR: {e}')
            await self.close()

    client = DiscordLeaveGuild()
    client.run(token)


def monitor():
    class DiscordMonitor(discord.Client):
        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')

        async def on_message(self, message):
            await _unpack_message(message)
    client = DiscordMonitor()
    client.run(token)


if __name__ == '__main__':
    # get_chats(l_channels=True)
    # get_all_messages()
    # get_chat_messages()
    # get_channel_messages()
    # get_guild_messages()
    monitor()

