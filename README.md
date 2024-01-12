# ail-feeder-discord

External Discord feeder for AIL framework. (with a manually created user account)

> :warning: Automating user accounts is against the discord TOS, so use at your own risk

>It is recommended to create a new account specifically for this purpose, as there is a chance that the account may get banned.

## Install & Requirements

Install the Python dependencies:

```
pip3 install -U -r requirements.txt
```

- Copy config file:
```bash
cp etc/conf.cfg.sample etc/conf.cfg
```

## Configuration

#### Discord Token

Add your discord token in `etc/conf.cfg`:
  - Login in with your web browser to discord.
  - Open the developer tools (CTRL+SHIFT+I).
  - Click the Network tab.
  - Click the XHR tab (filter by XHR).
  - Select a request and click the Headers tab.
  - Copy-paste the token value in the Authorization header.

> :warning: Do not share your token! A token gives full access to an account. To reset a user token, logout all your devices

## Usage

feeder.py
* chats ( List all joined chats_ )
* messages [Chat ID] ( _Get all messages from a chat_ )
  * --media ( _Download medias_ TODO: size limit + save_dir )
* monitor ( _Monitor all joined chats_ )
* entity [Entity ID] ( _Get chat or user metadata_ )

## Joining and Leaving Chats/Servers/Guilds

Log in to Discord using your web browser and manually join or leave chats.

> Some servers require you to submit a captcha or fill out a form.

## Get all Chats (servers + groups + DMs)
```bash
python3 bin/feeder.py chats 
```
Running this action will output a list of chats IDs your Discord account has joined.

## Get Chats Messages
```bash
python3 bin/feeder.py messages CHAT_ID
```

## MONITOR Messages from all chats
```bash
python3 bin/feeder.py monitor
```
