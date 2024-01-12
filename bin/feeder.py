#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
# import configparser
# import sys
# import os

import discordlib


def _create_messages_subparser(subparser):
    # subparser.add_argument('--replies', action='store_true', help='Get replies')
    subparser.add_argument('--media', action='store_true', help='Download medias')
    subparser.add_argument('--size_limit', type=int, help='Size limit for downloading medias')
    subparser.add_argument('--save_dir', help='Directory to save downloaded medias')
    # subparser.add_argument('--mark_as_read', action='store_true', help='Mark messages as read')

# def _json_print(mess):
#     print(json.dumps(mess, indent=4, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Discord feeder')

    subparsers = parser.add_subparsers(dest='command')

    list_chats_parser = subparsers.add_parser('chats', help='List all joined chats')

    # join_chat_parser = subparsers.add_parser('join', help='Join a chat by its id, username or with a hash invite')
    # join_chat_parser.add_argument('-n', '--name', type=str, help='ID, hash or username of the chat to join')
    # join_chat_parser.add_argument('-i', '--invite', type=str, help='Invite hash of the chat to join')

    # get_chat_users_parser = subparsers.add_parser('leave', help='Leave a chat')
    # get_chat_users_parser.add_argument('chat_id', help='ID, hash or username of the chat to leave')

    # get_chat_users_parser = subparsers.add_parser('check', help='Check a chat/invite hash without joining')
    # get_chat_users_parser.add_argument('invite', help='invite hash to check')

    # TODO
    messages_parser = subparsers.add_parser('messages', help='Get all messages from a chat')
    messages_parser.add_argument('chat_id', help='ID of the chat.')
    _create_messages_subparser(messages_parser)

    monitor_chats_parser = subparsers.add_parser('monitor', help='Monitor chats')
    _create_messages_subparser(monitor_chats_parser)

    # get_unread_parser = subparsers.add_parser('unread', help='Get all unread messages from all chats')
    # _create_messages_subparser(get_unread_parser)

    # return meta if no flags
    # get_chat_users_parser = subparsers.add_parser('chat', help='Get a chat metadata, list of users')
    # get_chat_users_parser.add_argument('chat_id', help='ID, hash or username of the chat')
    # get_chat_users_parser.add_argument('--users', action='store_true', help='Get a list of all the users of a chat')
    # get_chat_users_parser.add_argument('--admins', action='store_true', help='Get a list of all the admin users of a chat')
    # join ? leave ? shortcut

    get_metas_parser = subparsers.add_parser('entity', help='Get chat or user metadata')
    get_metas_parser.add_argument('entity_name', help='ID, hash or username of the chat/user')

    args = parser.parse_args()

    # Call the corresponding function based on the command
    if args.command == 'monitor':
        if args.media:
            download = True
        else:
            download = False
        discordlib.monitor(download=download)
    else:
        if args.command == 'chats':
            r = discordlib.get_chats(l_channels=False)
        # elif args.command == 'join':
        #     if not args.name and not args.invite:
        #         join_chat_parser.print_help()
        #         sys.exit(0)
        #     if args.name:
        #         chat = args.name
        #     else:
        #         chat = None
        #     if args.invite:
        #         invite = args.invite
        #     else:
        #         invite = None
        #     r = loop.run_until_complete(tg.join_chat(chat=chat, invite=invite))
        # elif args.command == 'leave':
        #     chat = args.chat_id
        #     r = loop.run_until_complete(tg.leave_chat(chat=chat))
        # elif args.command == 'check':
        #     invite = args.invite
        #     r = loop.run_until_complete(tg.check_invite(invite))
        elif args.command == 'messages':
            chat = args.chat_id

            # subparser.add_argument('--size_limit', type=int, help='Size limit for downloading medias')
            # subparser.add_argument('--save_dir', help='Directory to save downloaded medias')
            # if args.replies:
            #     replies = True
            # else:
            #     replies = False
            # if args.mark_as_read:
            #     mark_read = True
            # else:
            #     mark_read = False
            if args.media:
                download = True
            else:
                download = False
            discordlib.get_chat_messages(chat, download=download, replies=False, limit=20)
        # elif args.command == 'unread':
        #     if args.replies:
        #         replies = True
        #     else:
        #         replies = False
        #     if args.media:
        #         download = True
        #     else:
        #         download = False
        #     loop.run_until_complete(tg.get_unread_message(download=download, replies=replies))
        # elif args.command == 'chat': # TODO
        #     chat = args.chat_id
        #     if args.users or args.admins:
        #         if args.admins:
        #             admin = True
        #         else:
        #             admin = False
        #         discordlib.get_chat_users(chat, admin=admin)
        #     else:
        #         discordlib.get_entity(chat)
        elif args.command == 'entity':
            entity = args.entity_name
            discordlib.get_entity(entity)
        else:
            parser.print_help()
