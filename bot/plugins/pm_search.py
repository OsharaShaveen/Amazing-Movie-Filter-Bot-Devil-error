import re
import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import ButtonDataInvalid, FloodWait

from bot.database import Database  # pylint: disable=import-error
from bot.bot import Bot  # pylint: disable=import-error

FIND = {}
db = Database()


@Bot.on_message(filters.text & filters.group & ~filters.bot, group=0)
async def pm_search(bot, update):
    group_id = update.chat.id
    query = re.sub(r"[1-2]\d{3}", "", update.text)
    results = []

    allow_video = True
    allow_audio = False
    allow_document = True

    # maximum page result of a query
    max_pages = 5
    # should file to be send from bot pm to user
    pm_file_chat = True
    # maximum total result of a query
    max_results = 50
    # maximum buttom per page
    max_per_page = 10
    # should or not show active chat invite link
    show_invite = False

    # turn show_invite to False if pm_file_chat is True
    show_invite = (False if pm_file_chat == True else show_invite)

    filters = await db.get_filters(group_id, query)

    if filters:
        for filter in filters:  # iterating through each files
            file_name = filter.get("file_name")
            file_type = filter.get("file_type")
            file_link = filter.get("file_link")
            file_size = int(filter.get("file_size", "0"))

            # from B to MiB

            if file_size < 1024:
                file_size = f"[{file_size} B]"
            elif file_size < (1024**2):
                file_size = f"[{str(round(file_size/1024, 2))} KiB] "
            elif file_size < (1024**3):
                file_size = f"[{str(round(file_size/(1024**2), 2))} MiB] "
            elif file_size < (1024**4):
                file_size = f"[{str(round(file_size/(1024**3), 2))} GiB] "

            file_size = "" if file_size == ("[0 B]") else file_size

            # add emoji down below inside " " if you want..
            button_text = f"{file_size}{file_name}"

            if file_type == "video":
                if allow_video:
                    pass
                else:
                    continue

            elif file_type == "audio":
                if allow_audio:
                    pass
                else:
                    continue

            elif file_type == "document":
                if allow_document:
                    pass
                else:
                    continue

            if len(results) >= max_results:
                break

            if pm_file_chat:
                unique_id = filter.get("unique_id")
                if not FIND.get("bot_details"):
                    try:
                        bot_ = await bot.get_me()
                        FIND["bot_details"] = bot_
                    except FloodWait as e:
                        asyncio.sleep(e.x)
                        bot_ = await bot.get_me()
                        FIND["bot_details"] = bot_

                bot_ = FIND.get("bot_details")
                file_link = f"https://t.me/{bot_.username}?start={unique_id}"

            results.append(
                [
                    InlineKeyboardButton(button_text, url=file_link)
                ]
            )

    else:
        return  # return if no files found for that query

    if len(results) == 0:  # double check
        return

    else:

        result = []
        # seperating total files into chunks to make as seperate pages
        result += [results[i * max_per_page:(i + 1) * max_per_page] for i in range(
            (len(results) + max_per_page - 1) // max_per_page)]
        len_result = len(result)
        len_results = len(results)
        results = None  # Free Up Memory

        FIND[query] = {"results": result, "total_len": len_results,
                       "max_pages": max_pages}  # TrojanzHex's Idea Of Dicts😅

        # Add next buttin if page count is not equal to 1
        if len_result != 1:
            result[0].append(
                [
                    InlineKeyboardButton(
                        "Next ⏩", callback_data=f"navigate(0|next|{query})")
                ]
            )

        # Just A Decaration
        result[0].append([
            InlineKeyboardButton(
                f"🔰 Page 1/{len_result if len_result < max_pages else max_pages} 🔰", callback_data="ignore")
        ])

        reply_markup = InlineKeyboardMarkup(result[0])

        try:
            await bot.send_message(
                chat_id=update.chat.id,
                text=f"Found {(len_results)} Results For Your Query: <code>{query}</code>",
                reply_markup=reply_markup,
                parse_mode="html",
                reply_to_message_id=update.message_id
            )

        except ButtonDataInvalid:
            print(result[0])

        except Exception as e:
            print(e)
