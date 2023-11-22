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
    meta = {}
    meta['username'] = user.name
    meta['display_name'] = user.display_name
    meta['bot'] = user.bot

    meta['id'] = user.id
    meta['date'] = unpack_datetime(user.created_at)

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
    print(type(author))

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
            'date': unpack_datetime(channel.created_at)}
    if channel.name:
        meta['name'] = channel.name

    return meta

def _unpack_embedded(embedded): # TODO reconstruct embed content
    # image
    # thumbnail
    # video
    # provider
    # author

    # print()
    # print('ooooooooooooooooooooooooo')
    # print(embedded.to_dict())
    # print()

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
    if embed.get('footer'): # TODO icon URL
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


class DiscordMonitor(discord.Client):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        print(message)
        print()
        await _unpack_message(message)

def monitor():
    client = DiscordMonitor()
    client.run(token)

class DiscordDefault(discord.Client):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

        i = {}

        for guild in self.guilds:
            print(_unpack_guild(guild))
            for channel in guild.channels:
                str_c = str(type(channel))
                if str_c not in i:
                    i[str_c] = 0
                i[str_c] += 1
                print(type(channel))
                # if not isinstance(channel, discord.ForumChannel): # TODO
                #     continue
                if isinstance(channel, discord.CategoryChannel) or isinstance(channel, discord.ForumChannel): # TODO
                    continue
                print(_unpack_guid_channel(channel))
                print(channel.last_message_id)
                print(channel.last_message)

                if channel.last_message_id:
                    try:
                        async for message in channel.history(limit=20):
                            print(message)
                            await _unpack_message(message)
                            print()
                    except discord.errors.Forbidden as e:
                        print(e)

            if channel.last_message_id:
                # mess_id = channel.last_message_id
                # print(mess_id)
                try:
                    async for message in channel.history(limit=5):
                        print(message)
                        _unpack_message(message)
                except discord.errors.Forbidden as e:
                    print(e)

        # print('--------------------------------------------------------------------------------')
        # print(i)
        #
        # for channel in self.private_channels:
        #     # print(type(channel))
        #     # print(channel)
        #     print(_unpack_private_channel(channel))
        #     if channel.last_message_id:
        #         mess_id = channel.last_message_id
        #         print(mess_id)
        #     async for message in channel.history(limit=None):
        #         print(message)
        #         _unpack_message(message)

        # for r in client.get_all_channels():
        #     print(type(r))
        #     print(r)

        await self.close()

def get_all_messages():
    client = DiscordDefault()
    client.run(token)

def get_chat_messages(channel_id):

    class DiscordChatMessage(discord.Client):

        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')
            r = client.get_channel(channel_id)
            print(r.guild)
            print(type(r))
            print(client.get_channel(channel_id))

            await self.close()

    client = DiscordChatMessage()
    client.run(token)

class DiscordChats(discord.Client):

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

        chats = []

        for guild in self.guilds:
            chats.append(_unpack_guild(guild))

        for channel in self.private_channels:
            # print(type(channel))
            # print(channel)
            chats.append(_unpack_private_channel(channel))

        print(json.dumps(chats, indent=4, sort_keys=True))

        # print('--------------------------------------------------------------------------------')
        # for r in self.get_all_channels():
        #     print(type(r))
        #     print(r)

        await self.close()

def get_chats():
    client = DiscordChats()
    client.run(token)

# def get_chats(client):
#     print(client.get_all_channels)


# TODO LIST CHATS
# TODO ALL Messages from CHAT
# TODO LIST CHANNELS
if __name__ == '__main__':
    # get_chats()
    # get_all_messages()
    # get_chat_messages()
    get_chat_messages()

