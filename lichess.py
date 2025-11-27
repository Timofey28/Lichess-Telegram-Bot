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

    msg = ''
    matches_played = 0
    for game in general_activity.games:
        matches_played += game.matches
        msg += f'\n\n  __{human_type(game.type)}__\n    Партий сыграно: {game.matches}\n    Побед: {game.wins}\n    Поражений: {game.losses}\n    Ничьих: {game.draws}'
        msg += f'\n    Изменение рейтинга: {game.rating_before} → {game.rating_after}'
        if game.rating_before != game.rating_after:
            diff = f'{"+" if game.rating_after > game.rating_before else "−"}{abs(game.rating_after - game.rating_before)}'
            msg += f'  ({diff})'

    if general_activity.correspondence_moves:
        msg += f'\n\n  __Игра по переписке:__\n    Сделано ходов: {general_activity.correspondence_moves.total_moves}'
        opponent_ratings: list[tuple[str, int]] = general_activity.correspondence_moves.opponent_ratings
        opponents: str = ', '.join(f'_{escape_markdown(opponent_username)} ({opponent_rating})_' for opponent_username, opponent_rating in opponent_ratings)
        msg += f'\n    В играх с: {opponents}'
        if general_activity.correspondence_ends:
            matches_played += general_activity.correspondence_ends.matches
            opponent_ratings = general_activity.correspondence_ends.opponent_ratings
            opponents = ', '.join(f'_{escape_markdown(opponent_username)} ({opponent_rating})_' for opponent_username, opponent_rating in opponent_ratings)
            msg += f'\n    Завершено партий: {general_activity.correspondence_ends.matches}\n    С оппонентами: {opponents}\n    Побед: {general_activity.correspondence_ends.wins}'
            msg += f'\n    Поражений: {general_activity.correspondence_ends.losses}\n    Ничьих: {general_activity.correspondence_ends.draws}'

    if general_activity.puzzles:
        msg += f'\n\n  __Шахматные задачи__\n    Решено: {general_activity.puzzles.wins}\n    Не решено: {general_activity.puzzles.losses}'
        msg += f'\n    Изменение рейтинга: {general_activity.puzzles.rating_before} → {general_activity.puzzles.rating_after}'
        if general_activity.puzzles.rating_before != general_activity.puzzles.rating_after:
            diff = f'{"+" if general_activity.puzzles.rating_after > general_activity.puzzles.rating_before else "−"}{abs(general_activity.puzzles.rating_after - general_activity.puzzles.rating_before)}'
            msg += f'  ({diff})'

    intro = f'*Последняя активность {escape_markdown(username, version=2)} на Lichess ({prettify_interval(general_activity.from_date, general_activity.to_date)})*'
    if matches_played > 0:
        msg = intro + f'\n\nВсего партий сыграно: {matches_played}' + msg
    else:
        msg = intro + msg

    return msg.replace('(', '\(').replace(')', '\)').replace('+', '\+').replace('-', '\-')


def get_lichess_username_from_id(lichess_id: str) -> Optional[str]:
    url = f'https://lichess.org/api/user/{lichess_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('username')
    if response.status_code != 404:
        logging.error(f'Ошибка при получении пользователя по ID {lichess_id} на Lichess: {response.status_code} - {response.json()}')