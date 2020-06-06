import logging
import requests
import os
import locale
import json

from telegram.ext import Updater
from emoji import emojize

# bot's settings
# your bot's TOKEN
TOKEN_BOT = 'YOUR_BOT_TOKEN_HERE'
# your channel alias ID
CHAT_ID = 'YOUR_CHANNEL_ALIAS_HERE'

# CoinMarketCap Pro API Key
CMC_PRO_API_KEY = 'YOUR_CMC_PRO_API_KEY_HERE'
ADMIN_CHAT_ID = 'YOUR_ADMIN_ID_HERE'

# start logging to the file of current directory
logging.basicConfig(filename=os.path.dirname(os.path.realpath(__file__)) + '/infobotcoinbot.log', level=logging.INFO,
                    # logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MACOS: 'en_GB', RASPBERRY: 'es_ES.utf8'
try:
    locale.setlocale(locale.LC_NUMERIC, 'en_GB')
except Exception as ex:
    if hasattr(ex, 'message'):
        ex_msg = ex.message
    else:
        ex_msg = ex

    logger.error('locale.setlocale EXCEPTION %s', ex_msg)


# function to run bot's job by scheduler
def scheduler(context):
    # request CMC actual data
    json_dict = cmc_request_tickers()

    if 'error_code' in json_dict['status'] and json_dict['status']['error_code'] > 0:
        error_code = str(json_dict['status']['error_code'])
        logger.error('api.coinmarketcap.com! Error code: %s', error_code)
        context.bot.send_message(ADMIN_CHAT_ID, 'Error api.coinmarketcap.com! Error code: '
                                 + error_code, parse_mode="Markdown")
    else:
        try:
            # send BTC, ETH, BNB to main chat
            text = request_api(json_dict['data'], 'BTC')
            if text != "":
                text += "\n`-------------------------`\n"
            text += request_api(json_dict['data'], 'ETH')
            text += "\n`-------------------------`\n"
            text += request_api(json_dict['data'], 'BNB')

            if text:
                context.bot.send_message(CHAT_ID, '💲 CoinMarketCap:\n' + text, parse_mode="Markdown")

        except Exception as ex:
            logger.error("General bot.send_message Error: %s", ex)
            context.bot.send_message(ADMIN_CHAT_ID, 'General bot.send_message error - request_api(...)',
                                     parse_mode="Markdown")


# function to request CMC API data of the earlier predefined tickers
def cmc_request_tickers():

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC,ETH,BNB"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_PRO_API_KEY,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == requests.codes.ok:

        # extract a json from response to a class "dict"
        response_dict = response.json()
        return response_dict

    else:
        logger.error('Error while request CMC PRO API: "%s". Error code: "%s"' % (url, response.status_code))
        return json.loads('{"status": {"error_code": ' + str(response.status_code) + '}}')


# function to request API data
def request_api(json_dict, ticker):
    price = '$?'
    rate24h = '?'
    rate24hemoji = ''

    # current price
    if str(json_dict[ticker]['quote']['USD']) != 'None':

        if int(float(json_dict[ticker]['quote']['USD']['price'])) > 1:
            rounding = 2
        else:
            rounding = 4

        price = '$' + str(locale.format_string('%.' + str(rounding) + 'f', float(json_dict[ticker]['quote']['USD']['price']), True))

    # 24 hours price change with emoji
    if str(json_dict[ticker]['quote']['USD']['percent_change_24h']) != 'None':
        rate24h = float(json_dict[ticker]['quote']['USD']['percent_change_24h'])

        if rate24h > 20.0:
            rate24hemoji = emojize(":rocket:", use_aliases=True)
        elif rate24h <= -20.0:
            rate24hemoji = emojize(":sos:", use_aliases=True)
        elif rate24h < 0.0:
            rate24hemoji = emojize(":small_red_triangle_down:", use_aliases=True)
        elif rate24h > 0.0:
            rate24hemoji = emojize(":white_check_mark:", use_aliases=True)

        rate24h = locale.format_string('%.2f', rate24h, True)

    text = "*" + json_dict[ticker]['name'] + "* actual price" \
           + "\nTicker: #" + json_dict[ticker]['symbol'] + " - *" + price + "*" \
           + "\nLast 24hours changed for *" + rate24h + "%*" + rate24hemoji

    return text


def error(update, context):
    logger.warning('Update caused error "%s"', context.error)


def main():
    logger.info("Start a infobotcoinbot bot!")

    # create an object "bot"
    updater = Updater(token=TOKEN_BOT, use_context=True)
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
