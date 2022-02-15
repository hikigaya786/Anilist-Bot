import logging
import requests
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from textwrap import dedent
from telegram import Bot, BotCommand


# setting up port for webhook
PORT = int(os.environ.get('PORT', 5000))


# setting up logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

base_url = "https://graphql.anilist.co"

# Format of querry in our api
api_query = """
query($search :String, $type :MediaType, $page: Int, $perPage :Int){
    Page(page : $page, perPage: $perPage){
        pageInfo{
            total
        }
    
    media(search :$search, type :$type){
         title{
            english
            romaji
            native
        }
        type
        startDate{
            year,month,day
        }
        endDate{
            year,month,day
        }
        episodes
        chapters
        duration
        genres
        trending
        averageScore
        popularity
        description
        bannerImage
        coverImage{
            extraLarge
        }
        }
    }
}
"""

variables = {
    'search': '',
    'type': '',
    'page': 1,
    'perPage': 5
}

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


def date_parser(date_dict: dict) -> str:
    """json output for date is of the form 
    {year : int, month : int, day : int}
    we convert that into normal date format"""

    from datetime import date
    if date_dict['year']:
        dt = date(year=date_dict['year'],
                  month=date_dict['month'], day=date_dict['day'])
        return f"{dt : %d-%b-%Y}"
    return "Not Finished"


def description_parser(descr: str) -> str:
    """media-description might have html tags within it so we should
    remove them"""
    from bs4 import BeautifulSoup
    return BeautifulSoup(descr, "lxml").text


def genre_parser(genre_list: list) -> str:
    """Default genre list looks like ['x','y','z'] we need to print
    x, y, z"""

    ans = ""
    for genre in genre_list:
        ans += genre + ","
    return ans[:-1]   # so that last ',' is removed


def start(update: Update, context: CallbackContext) -> None:
    """Simple Start massage for bot"""
    update.message.reply_text("Use /help to know how to use the bot")


def help_command(update: Update, context: CallbackContext) -> None:
    """/helpl command for bot"""
    text = """Use it as follow:
/anime <name of anime>
/manga <name of manga>"""
    update.message.reply_text(dedent(text))


def anime_query(update: Update, context: CallbackContext) -> None:
    """To get the anime query from website"""

    variables['type'] = 'ANIME'
    variables['search'] = update.effective_message.text.replace("/anime ", "")
    variables['perPage'] = 5
    response = requests.post(
        base_url, json={'query': api_query, 'variables': variables}, headers=headers)
    json_response = response.json()

    media_list = json_response['data']['Page']['media']
    title_list = [media['title']['romaji'] for media in media_list]

    keyboard = [
        [InlineKeyboardButton(title_list[0], callback_data=title_list[0])],
        [InlineKeyboardButton(title_list[1], callback_data=title_list[1])],
        [InlineKeyboardButton(title_list[2], callback_data=title_list[2])],
        [InlineKeyboardButton(title_list[3], callback_data=title_list[3])],
        [InlineKeyboardButton(title_list[4], callback_data=title_list[4])],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Search Results :", reply_markup=reply_markup)


def manga_query(update: Update, context: CallbackContext) -> None:
    """To get the manga query from website"""

    variables['type'] = 'MANGA'
    variables['search'] = update.effective_message.text.replace("/manga ", "")
    variables['perPage'] = 5
    response = requests.post(
        base_url, json={'query': api_query, 'variables': variables}, headers=headers)
    json_response = response.json()

    media_list = json_response['data']['Page']['media']
    title_list = [media['title']['romaji'] for media in media_list]

    keyboard = [
        [InlineKeyboardButton(title_list[0], callback_data=title_list[0])],
        [InlineKeyboardButton(title_list[1], callback_data=title_list[1])],
        [InlineKeyboardButton(title_list[2], callback_data=title_list[2])],
        [InlineKeyboardButton(title_list[3], callback_data=title_list[3])],
        [InlineKeyboardButton(title_list[4], callback_data=title_list[4])],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Search results :", reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """To get the answer from our anime query"""

    callback_query = update.callback_query
    variables['search'] = callback_query.data
    variables['perPage'] = 1
    response = requests.post(
        base_url, json={'query': api_query, 'variables': variables}, headers=headers)
    json_response = response.json()
    media = json_response['data']['Page']['media'][0]
    if variables['type'] == 'ANIME':
        text = f"""
{media['title']['romaji']} ({media['title']['native']})
Type : {media['type']}
Aired from : {date_parser(media['startDate'])} to {date_parser(media['endDate'])}
Genre : {genre_parser(media['genres'])}
Episodes : {media['episodes']}
Duration : {media['duration']} Mins.
Average Score : {media['averageScore']}
Trending : {media['trending']}


{description_parser(media['description'])}
{media['coverImage']['extraLarge']}
    """
    if variables['type'] == 'MANGA':
        text = f"""
{media['title']['romaji']} ({media['title']['native']})
Type : {media['type']}
Serialized from : {date_parser(media['startDate'])} to {date_parser(media['endDate'])}
Genre : {genre_parser(media['genres'])}
Chapters : {media['chapters']}
Average Score : {media['averageScore']}
Trending : {media['trending']}


{description_parser(media['description'])}
{media['bannerImage']}
    """
    print(dedent(text))
    callback_query.edit_message_text(text=dedent(text))


def error_handler(update: Update, context: CallbackContext) -> None:
    """Error handler for bot"""
    update.message.reply_text(
        "sorry a error occured try again after some time")


def main():
    from config import token
    updater = Updater(token)
    bot = Bot(token)

    commands = [
        BotCommand('start', 'To start the bot'),
        BotCommand('anime', 'To Search Anime'),
        BotCommand('manga', 'To search Manga'),
        BotCommand('help', 'To know how to use the bot')
    ]
    bot.set_my_commands(commands)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('anime', anime_query))
    updater.dispatcher.add_handler(CommandHandler('manga', manga_query))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_error_handler(error_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=token)

    updater.bot.set_webhook(
        'https://anilist-telegram-bot.herokuapp.com/'+token)

    updater.idle()


if __name__ == "__main__":
    main()
