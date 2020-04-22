# インストールした discord.py を読み込む
import discord
import urllib.request
import urllib.error
import re
import os

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

    # help
    if message.content == '/register' or message.content.startswith('/register help'):
        await message.channel.send(
            embed = discord.Embed(
                title = 'ℹ️ 使い方',
                description =
                    '`/register 絵文字` (Nitro専用)\n'
                    '`/register <:名前:ID:>` (Nitro専用)\n'
                    '`/register :名前:ID`\n'
                    '`/register :名前:URL`\n'
                    '※複数同時登録に対応しています\n'
                    '※絵文字URL以外のURLには対応していません\n'
                    '　　(セキュリティ上の観点から)'
            )
        )
        return

    # 「/register」と発言したら絵文字が登録される処理
    if not message.content.startswith('/register '):
        return

    # 権限チェック
    if not message.author.permissions_in(message.channel).manage_emojis:
        await message.channel.send('絵文字登録権限がありません')
        return

    # 絵文字パターン
    regex_emojis = re.compile(r'(?:<a?:(\w+):(\d+)>)|(?::(\w+):https:\/\/cdn\.discordapp\.com\/emojis\/(\d+))|(?::(\w+):(\d+))')

    # 絵文字確認
    if regex_emojis.search(message.content) is None:
        await message.channel.send('カスタム絵文字が含まれていません')
        return

    # ヘッダ
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    }

    start_message = await message.channel.send('<a:loading:513406664716845067>絵文字登録中...')
    async with message.channel.typing():
        # From now, `custom_emojis` is `list` of `discord.Emoji` that `msg` contains.
        done_emojis = []
        error_emojis = []
        result_emojis = regex_emojis.finditer(message.content)
        for match_emoji in result_emojis:
            emoji_name = None
            emoji_id = None
            emoji_done = None
            if match_emoji.group(1):
                emoji_name, emoji_id = match_emoji.group(1), match_emoji.group(2)
            elif match_emoji.group(3):
                emoji_name, emoji_id = match_emoji.group(3), match_emoji.group(4)
            elif match_emoji.group(5):
                emoji_name, emoji_id = match_emoji.group(5), match_emoji.group(6)
            if discord.utils.get(message.guild.emojis, name=emoji_name) is not None:
                await message.channel.send(f'​　<:terminus:451694123779489792>`:{emoji_name}:`の名前は既に登録されているので登録されません')
            else:
                try:
                    req = urllib.request.Request(
                        f'https://cdn.discordapp.com/emojis/{emoji_id}', None, headers)
                    contents = urllib.request.urlopen(req).read()
                    emoji_done = await message.guild.create_custom_emoji(name=emoji_name, image=contents)
                except discord.Forbidden as e:
                    await message.channel.send(f'​　<:terminus:451694123779489792>Forbidden: {e}')
                except discord.HTTPException as e:
                    await message.channel.send(f'​　<:terminus:451694123779489792>HTTPException: {e}')
                except Exception as e:
                    await message.channel.send(f'​　<:terminus:451694123779489792>Exception: {e}')
            if emoji_done is not None:
                done_emojis.append(emoji_done)
            else:
                error_emojis.append(emoji_name)

    result_change_msgs = []
    if done_emojis:
        done_emojis_msg = [f'<:{emoji.name}:{emoji.id}>' for emoji in done_emojis]
        done_emojis_msg = f'　追加: {"".join(done_emojis_msg)}'
        result_change_msgs.append(done_emojis_msg)
    if error_emojis:
        error_emojis_msg = [f'`:{emoji}:`' for emoji in error_emojis]
        error_emojis_msg = f'　失敗: {" ".join(error_emojis_msg)}'
        result_change_msgs.append(error_emojis_msg)
    await message.channel.send('​' + "\n".join(result_change_msgs))

    result_msg = '✅絵文字登録完了' if not error_emojis else '💥絵文字登録失敗'
    await start_message.edit(content = f'{result_msg}')


# Botの起動とDiscordサーバーへの接続
client.run(os.environ["DISCORD_TOKEN"])
