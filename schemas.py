from datetime import date, datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class GameType(StrEnum):
    ULTRA_BULLET = 'ultraBullet'
    BULLET = 'bullet'
    BLITZ = 'blitz'
    RAPID = 'rapid'
    CLASSICAL = 'classical'
    ANTICHESS = 'antichess'
    ATOMIC = 'atomic'
    CHESS960 = 'chess960'
    CRAZYHOUSE = 'crazyhouse'
    HORDE = 'horde'
    KING_OF_THE_HILL = 'kingOfTheHill'
    RACING_KINGS = 'racingKings'
    THREE_CHECK = 'threeCheck'
    CORRESPONDENCE = 'correspondence'


def human_type(game_type: GameType) -> str:
    type_map = {
        GameType.ULTRA_BULLET: 'Ультрапуля',
        GameType.BULLET: 'Пуля',
        GameType.BLITZ: 'Блиц',
        GameType.RAPID: 'Рапид',
        GameType.CLASSICAL: 'Классика',
        GameType.ANTICHESS: 'Антишахматы (поддавки)',
        GameType.ATOMIC: 'Атомные шахматы',
        GameType.CHESS960: 'Chess 960',
        GameType.CRAZYHOUSE: 'Крейзи хаус',
        GameType.HORDE: 'Орда',
        GameType.KING_OF_THE_HILL: 'Король горы',
        GameType.RACING_KINGS: 'Гонки королей',
        GameType.THREE_CHECK: 'Три шаха',
        GameType.CORRESPONDENCE: 'Переписка',
    }
    return type_map.get(game_type, game_type.value.title())


class Game(BaseModel):
    type: GameType
    wins: int
    losses: int
    draws: int
    rating_before: int
    rating_after: int

    @model_validator(mode='before')
    def prepare_fields(cls, values):
        game_type = list(values.keys())[0]
        values["type"] = GameType(game_type)
        values["wins"] = values[game_type]["win"]
        values["losses"] = values[game_type]["loss"]
        values["draws"] = values[game_type]["draw"]
        values["rating_before"] = values[game_type]["rp"]["before"]
        values["rating_after"] = values[game_type]["rp"]["after"]
        del values[game_type]
        return values

    def add(self, other):
        assert isinstance(other, Game), 'Cannot add non-Game object'
        assert self.type == other.type, 'Cannot add games of different types'
        self.wins += other.wins
        self.losses += other.losses
        self.draws += other.draws
        self.rating_after = other.rating_after


class Puzzles(BaseModel):
    wins: int
    losses: int
    rating_before: int
    rating_after: int

    @model_validator(mode='before')
    def prepare_fields(cls, values):
        assert values["score"]["draw"] == 0
        values["wins"] = values["score"]["win"]
        values["losses"] = values["score"]["loss"]
        values["rating_before"] = values["score"]["rp"]["before"]
        values["rating_after"] = values["score"]["rp"]["after"]
        return values

    def add(self, other):
        assert isinstance(other, Puzzles), 'Cannot add non-Puzzles object'
        self.wins += other.wins
        self.losses += other.losses
        self.rating_after = other.rating_after


class Tournament(BaseModel):
    id: str
    url: str
    name: str
    games_amount: int  # Только игры юзера
    score: int  # Сколько очков набрано
    rank: int  # Место в турнире
    rank_percent: int = Field(alias='rankPercent')  # "36% лучших" - эта хуйня

    @model_validator(mode='before')
    def prepare_fields(cls, values):
        values["id"] = values["tournament"]["id"]
        values["name"] = values["tournament"]["name"]
        values["url"] = 'https://lichess.org/tournament/' + values["id"]
        values["games_amount"] = values["nbGames"]
        return values


class Follows(BaseModel):
    in_: list[str] = Field(None, alias='in')
    out: list[str] = None

    @model_validator(mode='before')
    def prepare_fields(cls, values):
        if 'in' in values:
            values["on_user"] = values["in"]["ids"]
            del values["in"]
        if 'out' in values:
            values["out"] = values["out"]["ids"]
        return values


class Team(BaseModel):
    url: str
    name: str

    @model_validator(mode='after')
    def complete_url(self):
        self.url = 'https://lichess.org' + self.url
        return self


class Activity(BaseModel):
    date: date
    games: list[Game] = None
    puzzles: Puzzles = None
    tournaments: list[Tournament] = None
    follows: Follows = None
    teams: list[Team] = None

    class Config:
        extra = 'forbid'

    @model_validator(mode='before')
    def vali_date(cls, values):
        values["date"] = datetime.fromtimestamp(values["interval"]["start"] / 1000).date()
        del values["interval"]

        if 'games' in values:
            values["games_"] = []
            for game_type, game_data in values["games"].items():
                values["games_"].append({game_type: game_data})
            values["games"] = values["games_"].copy()
            del values["games_"]

        if 'tournaments' in values:
            values["tournaments"] = values["tournaments"]["best"]

        return values


class GeneralActivity:
    def __init__(self, activities: list[Activity]):
        activities.sort(key=lambda x: x.date)
        self._from_date: date = activities[0].date
        self._to_date: date = activities[-1].date
        self._games: list[Game] = []
        self._puzzles = None

        games_by_type: dict[GameType, Game] = {}
        for activity in activities:
            if activity.games:
                for game in activity.games:
                    if game.type in games_by_type:
                        games_by_type[game.type].add(game)
                    else:
                        games_by_type[game.type] = game
            if activity.puzzles:
                if self._puzzles is not None:
                    self._puzzles.add(activity.puzzles)
                else:
                    self._puzzles = activity.puzzles
        self._games = list(games_by_type.values())

    @property
    def from_date(self) -> date:
        return self._from_date

    @property
    def to_date(self) -> date:
        return self._to_date

    @property
    def games(self) -> list[Game]:
        return self._games

    @property
    def puzzles(self) -> Puzzles:
        return self._puzzles


class User(BaseModel):
    id: int
    tg_id: int
    tg_username: str
    tg_first_name: str
    tg_last_name: Optional[str]
    lichess_username: Optional[str]