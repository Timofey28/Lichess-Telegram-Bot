from datetime import date, datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Color(StrEnum):
    WHITE = 'белый'
    BLACK = 'черный'


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
        GameType.CRAZYHOUSE: 'Crazyhouse',
        GameType.HORDE: 'Орда',
        GameType.KING_OF_THE_HILL: 'Король горы',
        GameType.RACING_KINGS: 'Гонки королей',
        GameType.THREE_CHECK: 'Три шаха',
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
        self.rating_before = other.rating_before

    @property
    def matches(self) -> int:
        return self.wins + self.losses + self.draws


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
        self.rating_before = other.rating_before


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


class CorrespondenceGame(BaseModel):
    id_: str = Field(..., alias='id')
    color: Color
    url: str
    opponent_username: str
    opponent_rating: int

    class Config:
        extra = 'forbid'

    @model_validator(mode='before')
    def prepare_fields(cls, values):
        assert values["color"] in ('white', 'black')
        values["color"] = Color.WHITE if values["color"] == 'white' else Color.BLACK
        values["opponent_username"] = values["opponent"]["user"]
        values["opponent_rating"] = values["opponent"]["rating"]
        del values["opponent"]
        return values

class CorrespondenceMoves(BaseModel):
    total_moves: int = Field(..., alias='nb')
    games: list[CorrespondenceGame]

    class Config:
        extra = 'forbid'

    def add(self, other):
        assert isinstance(other, CorrespondenceMoves), 'Cannot add non-CorrespondenceMoves object'
        self.total_moves += other.total_moves
        opponents = set(game.opponent_username for game in self.games)
        for game in other.games:
            if game.opponent_username not in opponents:
                self.games.append(game)

    @property
    def opponent_ratings(self) -> list[tuple[str, int]]:
        return [(game.opponent_username, game.opponent_rating,) for game in self.games]

class CorrespondenceEnds(BaseModel):
    wins: int
    losses: int
    draws: int
    rating_before: int
    rating_after: int
    games: list[CorrespondenceGame]

    class Config:
        extra = 'forbid'

    @model_validator(mode='before')
    def prepare_fields(cls, values):
        values["wins"] = values["correspondence"]["score"]["win"]
        values["losses"] = values["correspondence"]["score"]["loss"]
        values["draws"] = values["correspondence"]["score"]["draw"]
        values["rating_before"] = values["correspondence"]["score"]["rp"]["before"]
        values["rating_after"] = values["correspondence"]["score"]["rp"]["after"]
        values["games"] = values["correspondence"]["games"]
        del values["correspondence"]
        return values

    def add(self, other):
        assert isinstance(other, CorrespondenceEnds), 'Cannot add non-CorrespondenceEnds object'
        self.wins += other.wins
        self.losses += other.losses
        self.draws += other.draws
        self.rating_before = other.rating_before
        opponents = set(game.opponent_username for game in self.games)
        for game in other.games:
            if game.opponent_username not in opponents:
                self.games.append(game)

    @property
    def opponent_ratings(self) -> list[tuple[str, int]]:
        return [(game.opponent_username, game.opponent_rating,) for game in self.games]

    @property
    def matches(self) -> int:
        return self.wins + self.losses + self.draws


class Activity(BaseModel):
    date: date
    games: list[Game] = None
    puzzles: Puzzles = None
    tournaments: list[Tournament] = None
    follows: Follows = None
    teams: list[Team] = None
    correspondence_moves: CorrespondenceMoves = Field(None, alias='correspondenceMoves')
    correspondence_ends: CorrespondenceEnds = Field(None, alias='correspondenceEnds')

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
        if not activities:
            self._from_date = None
            self._to_date = None
            self._games = []
            self._puzzles = None
            self._correspondence_moves = None
            self._correspondence_ends = None
            return
        activities.sort(key=lambda x: x.date, reverse=True)
        self._from_date: date = activities[-1].date
        self._to_date: date = activities[0].date
        self._games: list[Game] = []
        self._puzzles = None
        self._correspondence_moves = None
        self._correspondence_ends = None

        games_by_type: dict[GameType, Game] = {}
        for activity in activities:
            if activity.games:
                for game in activity.games:
                    if game.type in games_by_type:
                        games_by_type[game.type].add(game)
                    else:
                        games_by_type[game.type] = game

            if activity.puzzles:
                if self._puzzles is None:
                    self._puzzles = activity.puzzles
                else:
                    self._puzzles.add(activity.puzzles)

            if activity.correspondence_moves:
                if self._correspondence_moves is None:
                    self._correspondence_moves = activity.correspondence_moves
                else:
                    self._correspondence_moves.add(activity.correspondence_moves)

            if activity.correspondence_ends:
                if self._correspondence_ends is None:
                    self._correspondence_ends = activity.correspondence_ends
                else:
                    self._correspondence_ends.add(activity.correspondence_ends)

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

    @property
    def correspondence_moves(self) -> CorrespondenceMoves:
        return self._correspondence_moves

    @property
    def correspondence_ends(self) -> CorrespondenceEnds:
        return self._correspondence_ends


class User(BaseModel):
    id: int
    tg_id: int
    tg_username: str
    tg_first_name: str
    tg_last_name: Optional[str]
    lichess_username: Optional[str]
