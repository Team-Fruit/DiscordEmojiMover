# インストールした discord.py を読み込む
# py -3 -m pip install -U discord.py
import discord
import credentials.discord
import urllib.request
import urllib.error
import re

# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # 「/register」と発言したら絵文字が登録される処理
    if message.content.startswith('/register '):
        if message.author.permissions_in(message.channel).manage_emojis:
            await message.channel.send('絵文字登録中...')
            headers = {
                "User-Agent":  "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"}
            custom_emojis = re.findall(r'<a?:\w*:\d*>', message.content)
            custom_emojis = [(e.split(':')[1], int(e.split(':')[2].replace('>', '')))
                            for e in custom_emojis]
            # From now, `custom_emojis` is `list` of `discord.Emoji` that `msg` contains.
            for (emojiname, emojiid) in custom_emojis:
                if discord.utils.get(message.guild.emojis, name=emojiname) == None:
                    try:
                        req = urllib.request.Request(
                            f'https://cdn.discordapp.com/emojis/{emojiid}', None, headers)
                        contents = urllib.request.urlopen(req).read()
                        await message.guild.create_custom_emoji(name=emojiname, image=contents)
                    except discord.Forbidden as e:
                        await message.channel.send(f'Forbidden: {e}')
                    except discord.HTTPException as e:
                        await message.channel.send(f'HTTPException: {e}')
                    except Exception as e:
                        await message.channel.send(f'Exception: {e}')
                else:
                    await message.channel.send(f':{emojiname}:の名前は既に登録されているので登録されません')
            if custom_emojis:
                await message.channel.send('絵文字登録完了')
            else:
                await message.channel.send('カスタム絵文字が含まれていません')
        else:
            await message.channel.send('絵文字登録権限がありません')


# Botの起動とDiscordサーバーへの接続
client.run(credentials.discord.TOKEN)
