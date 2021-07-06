# ail-feeder-discord

Discord feeder for AIL

> **Warning!** Automating user accounts is technically against TOS, so use at your own risk!

## Discord API

https://discord.com/developers/docs/intro

## How to use?

1. Create a file `token.txt` in the `etc/` folder in the root directory. Add the Discord token of the account you want to use. 
[How to get the Discord user token](https://github.com/Tyrrrz/DiscordChatExporter/wiki/Obtaining-Token-and-Channel-IDs)

2. Create a file `server-invite-codes.txt` in the `etc/` folder in the root directory if you want to automatically join and scan new servers. Add the invite codes in separate lines in this file. (Make sure to not add the complete links! e.g., abcd1234 instead of https://discord.gg/abcd1234)

3. Run the command below with the desired parameters and wait for execution to finish.

```
ail-feeder-discord: python3 bin/feeder.py --help
usage: feeder.py [-h] [--verbose] [--nocache] [--messagelimit MESSAGELIMIT] query

positional arguments:
  query                 query to search on Discord to feed AIL

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose output
  --nocache             disable cache
  --messagelimit MESSAGELIMIT
                        maximum number of messages to fetch
```