import logging
import requests
import os
import locale

from telegram.ext import Updater
from emoji import emojize


# bot's settings
# your bot's TOKEN
TOKEN_BOT = 'YOUR_BOT_TOKEN_HERE'
# your channel alias ID
CHAT_ID = 'YOUR_CHANNEL_ALIAS_HERE'


locale.setlocale(locale.LC_NUMERIC, 'de_DE')

# start logging to the file of current directory
# logging.basicConfig(filename=os.path.dirname(os.path.realpath(__file__)) + '/infobotcoinbot.log', level=logging.INFO,
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# function to run bot's job by scheduler
def scheduler(bot, job):

    text = ""

    text += request_api("bitcoin")

    if text != "":
        text += "\n`-------------------------`\n"

    text += request_api("ethereum")

    if text != "":

        bot.send_message(CHAT_ID, '💲 CoinMarketCap:\n' + text, parse_mode="Markdown")
        logger.info("Has send a message to a channel %s", CHAT_ID)


# function to request API data
def request_api(ticker):

    url = "https://api.coinmarketcap.com/v1/ticker/" + ticker
    response = requests.get(url)

    if response.status_code == requests.codes.ok:

        # extract a json from response to a class "dict"
        response_dict = response.json()

        if 'error' in response_dict:
            error = response_dict['error']
            logger.error('api.coinmarketcap.com! Error message: %s', error)
        else:

            price = '$?'
            rate24h = '?'
            rate24hemoji = ''

            # current price
            if str(response_dict[0]['price_usd']) != 'None':
                price = '$' + str(locale.format_string('%.2f', float(response_dict[0]['price_usd']), True))

            # 24 hours price change with emoji
            if str(response_dict[0]['percent_change_24h']) != 'None':
                rate24h = float(response_dict[0]['percent_change_24h'])

                if rate24h > 20.0:
                    rate24hemoji = emojize(":rocket:", use_aliases=True)
                elif rate24h <= -20.0:
                    rate24hemoji = emojize(":sos:", use_aliases=True)
                elif rate24h < 0.0:
                    rate24hemoji = emojize(":small_red_triangle_down:", use_aliases=True)
                elif rate24h > 0.0:
                    rate24hemoji = emojize(":white_check_mark:", use_aliases=True)

                rate24h = locale.format_string('%.2f', rate24h, True)

            text = "#" + response_dict[0]['name'] + " actual price" \
                + "\nTicker: #" + response_dict[0]['symbol'] + " - *" + price + "*" \
                + "\nLast 24hours changed for *" + rate24h + "%*" + rate24hemoji

            return text

    else:
        logger.error('Error while request API: "%s". Error code: "%s"' % (url, response.status_code))


def error(bot, job, error):
    logger.warning('Update caused error "%s"', error)


def main():
    logger.info("Start a infobotcoinbot bot!")

    # create an object "bot"
    updater = Updater(token=TOKEN_BOT)
    dispatcher = updater.dispatcher

    # bot's error handler
    dispatcher.add_error_handler(error)

    # here put the job for the bot
    job_queue = updater.job_queue

    # run the bot each 1 hour 3600seconds, to start in 5 min (300seconds)
    job_queue.run_repeating(scheduler, interval=3600, first=300)


    ##################### bot's run method

    # Start the Bot start_polling() method
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.start_polling()
    updater.idle()

    # updater.start_webhook(listen='127.0.0.1', port=5003, url_path=TOKEN_BOT)
    # updater.bot.set_webhook(url='https://0.0.0.0/' + TOKEN_BOT,
    #                        certificate=open('/etc/nginx/PUBLIC.pem', 'rb'))


if __name__ == '__main__':
    main()
