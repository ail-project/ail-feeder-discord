# Discord&#46;py

[The official GitHub page](https://github.com/Rapptz/discord.py)

While trying to connect to the Discord servers using this API wrapper, the connection could not be established.

```Python
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

client = MyClient()
client.run('token')
```

This code with the token linked to the account that should be used gives the following error message: `discord.errors.LoginFailure: Improper token has been passed.`

Doing some more research also showed that this library is mostly useful for creating bots and not for creating self-bots.
"Discord.py was created to work on bot accounts not user accounts." This means that this is not the best choice for this kind of job.

Still maintained? &rarr; Yes

Open-source library? &rarr; Yes

# Discum

[The official GitHub page](https://github.com/Merubokkusu/Discord-S.C.U.M)

Still maintained? &rarr; Yes

Open-source library? &rarr; Yes