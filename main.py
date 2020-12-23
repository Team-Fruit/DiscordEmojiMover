# インストールした discord.py を読み込む
import discord
import urllib.request
import urllib.error
import re
import os
from enum import Enum, auto
from typing import Dict, List, Set, DefaultDict
from collections import defaultdict


# 絵文字ステータス
class EmojiStatus(Enum):
    PENDING = auto()
    FULFILLED = auto()
    REJECTED = auto()


# 絵文字タスク
class EmojiTask:
    def __init__(self, name, url, *, status=EmojiStatus.PENDING, error=None, error_desc=None, done=None):
        self.name = name
        self.url = url
        self.status = status
        self.error = error
        self.error_desc = error_desc
        self.done = done

    def complete(self, done):
        self.status = EmojiStatus.FULFILLED
        self.done = done

    def fail(self, error, error_desc=None):
        self.status = EmojiStatus.REJECTED
        self.error = error
        self.error_desc

    @classmethod
    def from_url(cls, name, url):
        return cls(name, url)

    @classmethod
    def from_id(cls, name, id):
        return cls(name, f'https://cdn.discordapp.com/emojis/{id}')


processing_emojis: Set[str] = set()

# 接続に必要なオブジェクトを生成
client = discord.Client()


# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message: discord.Message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return

    # help
    if message.content == '/register' or message.content.startswith('/register help'):
        await message.channel.send(
            embed=discord.Embed(
                title='ℹ️ 使い方',
                description=
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

    # 「/showreactions」と発言したらリアクションが羅列
    if message.content.startswith('/showreactions'):
        ref = message.reference
        if ref is not None:
            latest_msg = await message.channel.fetch_message(ref.message_id)
            if not latest_msg.reactions:
                await message.channel.send('リアクションがついていません')
            else:
                emojis = [f':{reaction.emoji.name}:{reaction.emoji.id}' for reaction in latest_msg.reactions]
                await message.channel.send('絵文字 `' + " ".join(emojis) + '`')
        else:
            await message.channel.send('リアクション付きメッセージに返信する形で送信してください')
        return

    # 「/register」と発言したら絵文字が登録される処理
    if not message.content.startswith('/register '):
        return

    # 権限チェック
    if not message.author.permissions_in(message.channel).manage_emojis:
        await message.channel.send('絵文字登録権限がありません')
        return

    # 絵文字パターン
    regex_emojis = re.compile(
        r'(?:<a?:(\w+):(\d+)>)|(?::(\w+):https:\/\/cdn\.discordapp\.com\/emojis\/(\d+))|(?::(\w+):(\d+))')

    # 絵文字確認
    if regex_emojis.search(message.content) is None:
        await message.channel.send('カスタム絵文字が含まれていません')
        return

    # ヘッダ
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    }

    # From now, `custom_emojis` is `list` of `discord.Emoji` that `msg` contains.
    pending_emojis: Dict[str, EmojiTask] = {}
    rejected_emojis: DefaultDict[str, List[EmojiTask]] = defaultdict(list)
    result_emojis = regex_emojis.finditer(message.content)
    for match_emoji in result_emojis:
        emoji: EmojiTask = None
        if match_emoji.group(1):
            emoji = EmojiTask.from_id(match_emoji.group(1), match_emoji.group(2))
        elif match_emoji.group(3):
            emoji = EmojiTask.from_id(match_emoji.group(3), match_emoji.group(4))
        elif match_emoji.group(5):
            emoji = EmojiTask.from_id(match_emoji.group(5), match_emoji.group(6))

        if emoji.name in pending_emojis:
            continue

        if emoji.name in processing_emojis or discord.utils.get(message.guild.emojis, name=emoji.name) is not None:
            emoji.fail("既に登録されているため登録できません")

        pending_emojis[emoji.name] = emoji
        processing_emojis.add(emoji.name)

        if emoji.status == EmojiStatus.REJECTED:
            rejected_emojis[emoji.error].append(emoji)

    result_change_msgs = []
    if rejected_emojis:
        result_change_msgs.append('失敗:')
        for why, errors in rejected_emojis.items():
            rejected_emojis_msg = [f'`:{error.name}:`' for error in errors]
            result_change_msgs.append(f'  <:terminus:451694123779489792>{why}: {" ".join(rejected_emojis_msg)}')
            for error in errors:
                if error.error_desc is not None:
                    result_change_msgs.append(f'    `{error.name}`: {error.error_desc}')
    await message.channel.send('​' + "\n".join(result_change_msgs))

    rejected_emojis.clear()

    if discord.utils.get(pending_emojis.values(), status=EmojiStatus.PENDING) is not None:
        start_message = await message.channel.send('<a:loading:513406664716845067>絵文字登録中...')
        async with message.channel.typing():
            for emoji in pending_emojis.values():
                if emoji.status == EmojiStatus.PENDING:
                    try:
                        req = urllib.request.Request(emoji.url, None, headers)
                        contents = urllib.request.urlopen(req).read()
                        emoji.complete(await message.guild.create_custom_emoji(name=emoji.name, image=contents))
                    except discord.DiscordException as e:
                        emoji.error('Discordエラー', e)
                    except urllib.error.HTTPError as e:
                        emoji.error('絵文字ダウンロードエラー', e)
                    except Exception as e:
                        emoji.error('不明なエラー', e)

        result_change_msgs = []
        done_emojis_msg = [f'{emoji.done}' for emoji in pending_emojis.values() if
                           emoji.status == EmojiStatus.FULFILLED]
        if done_emojis_msg:
            result_change_msgs.append(f'追加: {"".join(done_emojis_msg)}')
        if rejected_emojis:
            result_change_msgs.append('失敗:')
            for why, errors in rejected_emojis.items():
                rejected_emojis_msg = [f'`:{error.name}:`' for error in errors]
                result_change_msgs.append(f'  <:terminus:451694123779489792>{why}: {" ".join(rejected_emojis_msg)}')
                for error in errors:
                    if error.error_desc is not None:
                        result_change_msgs.append(f'    `{error.name}`: {error.error_desc}')
        if result_change_msgs:
            await message.channel.send('​' + "\n".join(result_change_msgs))

        result_msg = '✅絵文字登録完了' if discord.utils.get(pending_emojis.values(),
                                                     status=EmojiStatus.REJECTED) is None else '💥絵文字登録失敗'
        await start_message.edit(content=f'{result_msg}')

    for emoji in pending_emojis.values():
        processing_emojis.remove(emoji.name)


# Botの起動とDiscordサーバーへの接続
client.run(os.environ["DISCORD_TOKEN"])
