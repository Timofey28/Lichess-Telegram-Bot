import logging
from typing import Optional

import requests
from telegram.helpers import escape_markdown

from schemas import Activity, GeneralActivity, human_type
from utils import prettify_interval

logger = logging.getLogger('httpx')


def get_lichess_activity_message(username: str) -> Optional[str]:
    url = 'https://lichess.org/api/user/{username}/activity'
    response = requests.get(url.format(username=username))
    if response.status_code != 200:
        logger.error(f'Ошибка при получении активности пользователя {username} на Lichess: {response.status_code} - {response.json()}')
        return None

    general_activity = GeneralActivity([Activity(**activity) for activity in response.json()])
    if not general_activity.games and not general_activity.puzzles:
        return f'У *{escape_markdown(username, version=2)}* в последнее время не было активности на Lichess'

    msg = f'*Последняя активность {escape_markdown(username, version=2)} на Lichess ({prettify_interval(general_activity.from_date, general_activity.to_date)})*'
    for game in general_activity.games:
        msg += f'\n\n  __{human_type(game.type)}__\n    Побед: {game.wins}\n    Поражений: {game.losses}\n    Ничьих: {game.draws}'
        msg += f'\n    Изменение рейтинга: {game.rating_before} → {game.rating_after}'
        if game.rating_before != game.rating_after:
            diff = f'{"+" if game.rating_after > game.rating_before else "−"}{abs(game.rating_after - game.rating_before)}'
            msg += f'  ({diff})'

    if general_activity.puzzles:
        msg += f'\n\n  __Шахматные задачи__\n    Решено: {general_activity.puzzles.wins}\n    Не решено: {general_activity.puzzles.losses}'
        msg += f'\n    Изменение рейтинга: {general_activity.puzzles.rating_before} → {general_activity.puzzles.rating_after}'
        if general_activity.puzzles.rating_before != general_activity.puzzles.rating_after:
            diff = f'{"+" if general_activity.puzzles.rating_after > general_activity.puzzles.rating_before else "−"}{abs(general_activity.puzzles.rating_after - general_activity.puzzles.rating_before)}'
            msg += f'  ({diff})'

    return msg.replace('(', '\(').replace(')', '\)').replace('+', '\+').replace('-', '\-')


def get_lichess_username_from_id(lichess_id: str) -> Optional[str]:
    url = f'https://lichess.org/api/user/{lichess_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('username')
    if response.status_code != 404:
        logging.error(f'Ошибка при получении пользователя по ID {lichess_id} на Lichess: {response.status_code} - {response.json()}')