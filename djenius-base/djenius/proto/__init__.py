"""
Defines public models and protocol messages sent over the wire.
"""

import dataclasses
import enum
import json
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase  # type: ignore
from typing import Optional, List, Any, NewType, Set


def from_json(data: str) -> Any:
    decoded = json.loads(data)
    t = decoded.pop("type")
    cls = globals()[t]
    if not dataclasses.is_dataclass(cls):
        raise TypeError()
    return cls.from_json(json.dumps(decoded))


def to_json(msg: Any) -> str:
    data = json.loads(msg.to_json())
    return json.dumps({**data, "type": msg.__class__.__name__})


SongId = NewType("SongId", str)
CoverId = NewType("CoverId", str)
UserId = NewType("UserId", str)


class Ability(enum.Enum):
    up_vote = "UpVote"
    down_vote = "DownVote"
    search = "Search"
    suggest = "Suggest"
    ban = "Ban"
    accept = "Accept"
    pause = "Pause"
    seek = "Seek"
    volume = "Volume"
    skip = "Skip"
    admin_queue = "AdminQueue"
    edit_song = "EditSong"
    update_settings = "UpdateSettings"


class SongState(enum.Enum):
    new = "New"
    available = "Available"
    banned = "Banned"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Song:
    id: SongId
    cover_id: CoverId
    title: str
    artist: str
    album: str
    duration: int
    explicit: bool
    resolver: str

    def summary(self) -> str:
        return f"{self.title} {self.artist} {self.album}"

    def review_required(self) -> bool:
        return self.explicit or self.resolver == "youtube"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class StatefulSong:
    song: Song
    state: SongState
    review_required: bool
    added_by: str
    added_on: str
    play_count: int
    votes: int
    user_vote: int
    admin_index: Optional[int] = None


@dataclasses.dataclass
class User:
    id: UserId
    abilities: Set[Ability] = dataclasses.field(default_factory=set)

    def can_see_song_in_search(self, state: SongState) -> bool:
        if state in (SongState.new, SongState.available):
            return True
        if state is SongState.banned:
            return self.can(Ability.ban)
        raise TypeError("unreachable code")

    def can_see_song_in_queue(self, state: SongState, is_admin_song: bool) -> bool:
        return is_admin_song or self.can_see_song_in_search(state)

    def can(self, ability: Ability) -> bool:
        return ability in self.abilities


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Welcome:
    my_id: str
    cover_url: str
    library_page_size: int
    caps: List[Ability] = field(default_factory=list)
    login_path: str = None
    logout_path: str = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PlayerState:
    position: int = 0
    duration: int = 0
    volume: int = 100
    is_playing: bool = False
    song: Optional[StatefulSong] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SongUpdate:
    song: StatefulSong


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SearchRequest:
    query: str
    opaque: str
    filter: Optional[str]
    offset: Optional[int] = 0


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SearchResponse:
    results: List[StatefulSong]
    opaque: str
    has_more: bool = False


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class QueueRequest:
    pass


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class QueueResponse:
    queue: List[StatefulSong]
    urgent: bool = False


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SongSubUnsub:
    subscribe: List[SongId] = field(default_factory=list)
    unsubscribe: List[SongId] = field(default_factory=list)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AcceptSongRequest:
    song_id: SongId


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Vote:
    song_id: SongId
    value: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SetBanned:
    song_id: SongId
    is_banned: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Seek:
    position: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Skip:
    pass


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SetPlaying:
    is_playing: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SetVolume:
    volume: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AdminQueueInsert:
    song_id: SongId
    position: Optional[int] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AdminQueueRemove:
    song_id: SongId


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AdminQueueMoveUp:
    position: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AdminQueueMoveDown:
    position: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class UpdateSettings:
    key: str
    value: Any
