import logging


logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)
logging.getLogger('aiogram').setLevel(logging.CRITICAL)
logger = logging.getLogger('bot')