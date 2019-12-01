# インストールした discord.py を読み込む
import discord
import credentials.discord

ID_CHANNEL_README = 648808489262645248
ID_EMOJI_REACTION = '👍'

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
    # 「/neko」と発言したら「にゃーん」が返る処理
    if message.content == '/neko':
        await message.channel.send('にゃーん')

@client.event
async def on_raw_reaction_add(payload):  
    channel = client.get_channel(payload.channel_id)  
    if channel.id == ID_CHANNEL_README:  
        guild = client.get_guild(payload.guild_id)  
        member = guild.get_member(payload.user_id)  
        emoji = payload.emoji
        if emoji.is_unicode_emoji() and emoji.name == ID_EMOJI_REACTION:
            await channel.send('rawリアクション' + member.name + ', ' + str(emoji.name))  

# Botの起動とDiscordサーバーへの接続
client.run(credentials.discord.TOKEN)