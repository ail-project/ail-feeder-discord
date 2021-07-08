# ail-feeder-discord

Discord feeder for AIL

> **Warning!** Automating user accounts is technically against TOS, so use at your own risk!

## Discord API

https://discord.com/developers/docs/intro

## How does it work?

The program does the following in this order:

1. login with the given account (token in `etc/token.txt`)
2. fetch all the servers the user is already part of
3. scan the channels in each server for the given query, if a match is found, extract the data and upload it
4. after scanning for the query in the messages, the program looks for URLs in the channels, if a URL is found, extract the data and upload it
5. once all the servers, the user has been part of, are scanned, the program joins all the servers in `etc/server-invite-codes.txt` and repeats steps 3 and 4 for the newly joined servers
6. after this, the program starts to listen for incoming messages for `scantime` seconds
7. when a message comes in, matching the query or containing a link, the data is extracted and uploaded
8. when the `scantime` seconds are up, the program exits

NB: When a new message arrives during steps 2-5, the program treats the new message first and continues the previous scan after completing the new incoming message.

## Requirements

TODO

## How to use? (Work in progress)

1. Create a file `token.txt` in the `etc/` folder in the root directory. Add the Discord token of the account you want to use. 
[How to get the Discord user token](https://github.com/Tyrrrz/DiscordChatExporter/wiki/Obtaining-Token-and-Channel-IDs)

2. Create a file `server-invite-codes.txt` in the `etc/` folder in the root directory if you want to automatically join and scan new servers. Add the invite codes in separate lines in this file. (Make sure to not add the complete links! e.g., abcd1234 instead of https://discord.gg/abcd1234)

3. Run the command below with the desired parameters and wait for execution to finish.

```
ail-feeder-discord/: python3 bin/feeder.py --help
usage: feeder.py [-h] [--verbose] [--nocache] [--messagelimit MESSAGELIMIT] [--replies] [--maxsize MAXSIZE] [--scantime SCANTIME] query

positional arguments:
  query                 query to search on Discord to feed AIL

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose output
  --nocache             disable cache
  --messagelimit MESSAGELIMIT
                        maximum number of message to fetch
  --replies             follow the messages of a thread
  --maxsize MAXSIZE     the maximum size of a url in bytes
  --scantime SCANTIME   the amount of time the application should keep listening for new messages in seconds (turned off by default)
```