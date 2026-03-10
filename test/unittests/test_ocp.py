# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest

from ovos_utils.ocp import (
    MediaEntry,
    MediaType,
    PlaybackType,
    TrackState,
    MediaState,
    PlayerState,
    LoopState,
    PlaybackMode,
    MatchConfidence,
    Playlist,
    PluginStream,
    find_mime,
    OCP_ID,
)


class TestEnums(unittest.TestCase):
    def test_media_type_values(self) -> None:
        self.assertEqual(MediaType.GENERIC, 0)
        self.assertEqual(MediaType.MUSIC, 2)
        self.assertEqual(MediaType.MOVIE, 10)
        self.assertEqual(MediaType.ADULT, 69)

    def test_playback_type_values(self) -> None:
        self.assertEqual(PlaybackType.SKILL, 0)
        self.assertEqual(PlaybackType.VIDEO, 1)
        self.assertEqual(PlaybackType.UNDEFINED, 100)

    def test_track_state_values(self) -> None:
        self.assertEqual(TrackState.DISAMBIGUATION, 1)
        self.assertEqual(TrackState.PLAYING_AUDIO, 23)

    def test_media_state_values(self) -> None:
        self.assertEqual(MediaState.UNKNOWN, 0)
        self.assertEqual(MediaState.END_OF_MEDIA, 7)

    def test_player_state_values(self) -> None:
        self.assertEqual(PlayerState.STOPPED, 0)
        self.assertEqual(PlayerState.PLAYING, 1)
        self.assertEqual(PlayerState.PAUSED, 2)

    def test_loop_state(self) -> None:
        self.assertEqual(LoopState.NONE, 0)
        self.assertEqual(LoopState.REPEAT, 1)
        self.assertEqual(LoopState.REPEAT_TRACK, 2)

    def test_playback_mode(self) -> None:
        self.assertEqual(PlaybackMode.AUTO, 0)
        self.assertEqual(PlaybackMode.AUDIO_ONLY, 10)
        self.assertEqual(PlaybackMode.EVENTS_ONLY, 50)

    def test_match_confidence(self) -> None:
        self.assertEqual(MatchConfidence.EXACT, 95)
        self.assertEqual(MatchConfidence.VERY_LOW, 1)


class TestFindMime(unittest.TestCase):
    def test_mp3(self) -> None:
        mime = find_mime("song.mp3")
        self.assertIsNotNone(mime)
        self.assertIn("audio", mime[0])

    def test_mp4(self) -> None:
        mime = find_mime("video.mp4")
        self.assertIsNotNone(mime)
        self.assertIn("video", mime[0])

    def test_unknown(self) -> None:
        mime = find_mime("http://example.com/stream")
        # May return None or a tuple; no crash expected
        # Just verify no exception is raised
        self.assertTrue(mime is None or isinstance(mime, tuple))


class TestMediaEntry(unittest.TestCase):
    def test_defaults(self) -> None:
        entry = MediaEntry(uri="http://example.com/audio.mp3")
        self.assertEqual(entry.uri, "http://example.com/audio.mp3")
        self.assertEqual(entry.skill_id, OCP_ID)
        self.assertEqual(entry.media_type, MediaType.GENERIC)
        self.assertEqual(entry.playback, PlaybackType.UNDEFINED)
        self.assertEqual(entry.status, TrackState.DISAMBIGUATION)

    def test_as_dict(self) -> None:
        entry = MediaEntry(uri="http://example.com/a.mp3", title="Test Song")
        d = entry.as_dict
        self.assertEqual(d["uri"], "http://example.com/a.mp3")
        self.assertEqual(d["title"], "Test Song")

    def test_from_dict(self) -> None:
        entry = MediaEntry.from_dict({
            "uri": "http://example.com/b.mp3",
            "title": "Another Song",
            "media_type": MediaType.MUSIC,
        })
        self.assertEqual(entry.uri, "http://example.com/b.mp3")
        self.assertEqual(entry.title, "Another Song")
        self.assertEqual(entry.media_type, MediaType.MUSIC)

    def test_from_dict_missing_uri_raises(self) -> None:
        # No 'uri' key → dict2entry raises ValueError (no uri/extractor_id/playlist)
        with self.assertRaises(ValueError):
            MediaEntry.from_dict({"title": "orphan"})

    def test_infocard(self) -> None:
        entry = MediaEntry(uri="http://example.com/c.mp3", title="Song C",
                           image="http://example.com/img.png", length=180)
        card = entry.infocard
        self.assertEqual(card["track"], "Song C")
        self.assertEqual(card["duration"], 180)
        self.assertEqual(card["uri"], "http://example.com/c.mp3")

    def test_mimetype_mp3(self) -> None:
        entry = MediaEntry(uri="http://example.com/song.mp3")
        mime = entry.mimetype
        self.assertIsNotNone(mime)
        self.assertIn("audio", mime[0])

    def test_mimetype_no_uri(self) -> None:
        entry = MediaEntry()
        self.assertIsNone(entry.mimetype)

    def test_equality_same(self) -> None:
        e1 = MediaEntry(uri="http://example.com/a.mp3", title="A")
        e2 = MediaEntry(uri="http://example.com/a.mp3", title="A")
        self.assertEqual(e1, e2)

    def test_equality_different(self) -> None:
        e1 = MediaEntry(uri="http://example.com/a.mp3")
        e2 = MediaEntry(uri="http://example.com/b.mp3")
        self.assertNotEqual(e1, e2)

    def test_equality_with_dict(self) -> None:
        entry = MediaEntry(uri="http://example.com/a.mp3", title="A")
        self.assertEqual(entry, entry.infocard)

    def test_update_from_dict(self) -> None:
        entry = MediaEntry(uri="http://example.com/a.mp3")
        entry.update({"title": "Updated", "length": 120})
        self.assertEqual(entry.title, "Updated")
        self.assertEqual(entry.length, 120)

    def test_update_skipkeys(self) -> None:
        entry = MediaEntry(uri="http://example.com/a.mp3", title="Original")
        entry.update({"title": "New"}, skipkeys=["title"])
        self.assertEqual(entry.title, "Original")

    def test_update_newonly(self) -> None:
        entry = MediaEntry(uri="http://example.com/a.mp3", title="Original")
        entry.update({"title": "New", "artist": "Artist"}, newonly=True)
        self.assertEqual(entry.title, "Original")  # existing not replaced
        self.assertEqual(entry.artist, "Artist")   # new key added

    def test_update_from_media_entry(self) -> None:
        e1 = MediaEntry(uri="http://example.com/a.mp3")
        e2 = MediaEntry(uri="http://example.com/b.mp3", title="B")
        e1.update(e2)
        self.assertEqual(e1.uri, "http://example.com/b.mp3")


class TestPluginStream(unittest.TestCase):
    def test_defaults(self) -> None:
        ps = PluginStream(stream="abc123", extractor_id="youtube")
        self.assertEqual(ps.stream, "abc123")
        self.assertEqual(ps.extractor_id, "youtube")
        self.assertEqual(ps.skill_id, OCP_ID)

    def test_as_dict(self) -> None:
        ps = PluginStream(stream="vid", extractor_id="yt", title="My Video")
        d = ps.as_dict
        self.assertEqual(d["stream"], "vid")
        self.assertEqual(d["extractor_id"], "yt")
        self.assertEqual(d["title"], "My Video")

    def test_from_dict(self) -> None:
        ps = PluginStream.from_dict({"stream": "s1", "extractor_id": "yt"})
        self.assertEqual(ps.stream, "s1")
        self.assertEqual(ps.extractor_id, "yt")

    def test_from_dict_missing_extractor_raises(self) -> None:
        with self.assertRaises(ValueError):
            PluginStream.from_dict({"stream": "s1"})

    def test_from_dict_missing_stream_raises(self) -> None:
        with self.assertRaises(ValueError):
            PluginStream.from_dict({"extractor_id": "yt"})

    def test_infocard(self) -> None:
        ps = PluginStream(stream="v", extractor_id="yt", title="Title",
                          image="http://img.png", length=60)
        card = ps.infocard
        self.assertEqual(card["track"], "Title")
        self.assertEqual(card["duration"], 60)
        self.assertIn("yt//v", card["uri"])

    def test_as_media_entry(self) -> None:
        ps = PluginStream(stream="vid", extractor_id="yt", title="T",
                          media_type=MediaType.VIDEO)
        me = ps.as_media_entry
        self.assertIsInstance(me, MediaEntry)
        self.assertIn("yt//vid", me.uri)


class TestPlaylist(unittest.TestCase):
    def _make_entry(self, uri: str, title: str = "", confidence: int = 0) -> MediaEntry:
        return MediaEntry(uri=uri, title=title, match_confidence=confidence)

    def test_empty_playlist(self) -> None:
        pl = Playlist()
        self.assertEqual(len(pl), 0)
        self.assertIsNone(pl.current_track)
        self.assertTrue(pl.is_first_track)
        self.assertTrue(pl.is_last_track)

    def test_add_entry(self) -> None:
        pl = Playlist()
        e = self._make_entry("http://example.com/a.mp3", "A")
        pl.add_entry(e)
        self.assertEqual(len(pl), 1)

    def test_add_multiple_entries(self) -> None:
        pl = Playlist()
        for i in range(3):
            pl.add_entry(self._make_entry(f"http://example.com/{i}.mp3", str(i)))
        self.assertEqual(len(pl), 3)

    def test_current_track(self) -> None:
        pl = Playlist()
        e = self._make_entry("http://example.com/a.mp3", "Track A")
        pl.add_entry(e)
        track = pl.current_track
        self.assertEqual(track.title, "Track A")

    def test_is_first_track(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/1.mp3"))
        pl.add_entry(self._make_entry("http://a.com/2.mp3"))
        self.assertTrue(pl.is_first_track)
        pl.position = 1
        self.assertFalse(pl.is_first_track)

    def test_is_last_track(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/1.mp3"))
        pl.add_entry(self._make_entry("http://a.com/2.mp3"))
        self.assertFalse(pl.is_last_track)
        pl.position = 1
        self.assertTrue(pl.is_last_track)

    def test_goto_start(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/1.mp3"))
        pl.add_entry(self._make_entry("http://a.com/2.mp3"))
        pl.position = 1
        pl.goto_start()
        self.assertEqual(pl.position, 0)

    def test_clear(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/1.mp3"))
        pl.clear()
        self.assertEqual(len(pl), 0)
        self.assertEqual(pl.position, 0)

    def test_remove_entry_by_object(self) -> None:
        pl = Playlist()
        e = self._make_entry("http://a.com/1.mp3", "Track1")
        pl.add_entry(e)
        pl.remove_entry(e)
        self.assertEqual(len(pl), 0)

    def test_remove_entry_by_index(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/1.mp3"))
        pl.add_entry(self._make_entry("http://a.com/2.mp3"))
        pl.remove_entry(0)
        self.assertEqual(len(pl), 1)

    def test_remove_entry_not_found(self) -> None:
        pl = Playlist()
        e = self._make_entry("http://a.com/1.mp3")
        with self.assertRaises(ValueError):
            pl.remove_entry(e)

    def test_sort_by_conf(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/low.mp3", confidence=10))
        pl.add_entry(self._make_entry("http://a.com/high.mp3", confidence=90))
        pl.sort_by_conf()
        self.assertEqual(pl[0].match_confidence, 90)

    def test_infocard(self) -> None:
        pl = Playlist(title="My List")
        card = pl.infocard
        self.assertEqual(card["track"], "My List")
        self.assertEqual(card["uri"], "")

    def test_length(self) -> None:
        pl = Playlist()
        pl.add_entry(MediaEntry(uri="http://a.com/1.mp3", length=60))
        pl.add_entry(MediaEntry(uri="http://a.com/2.mp3", length=120))
        self.assertEqual(pl.length, 180)

    def test_as_dict(self) -> None:
        pl = Playlist(title="Test PL")
        pl.add_entry(self._make_entry("http://a.com/1.mp3", "Track1"))
        d = pl.as_dict
        self.assertEqual(d["title"], "Test PL")
        self.assertEqual(len(d["playlist"]), 1)

    def test_replace(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/old.mp3"))
        new_entries = [self._make_entry("http://a.com/new1.mp3"),
                       self._make_entry("http://a.com/new2.mp3")]
        pl.replace(new_entries)
        self.assertEqual(len(pl), 2)

    def test_init_from_list(self) -> None:
        entries = [self._make_entry("http://a.com/1.mp3"),
                   self._make_entry("http://a.com/2.mp3")]
        pl = Playlist(entries)
        self.assertEqual(len(pl), 2)

    def test_add_entry_invalid_index(self) -> None:
        pl = Playlist()
        e = self._make_entry("http://a.com/1.mp3")
        with self.assertRaises(ValueError):
            pl.add_entry(e, index=99)

    def test_from_dict(self) -> None:
        d = {
            "title": "FromDict",
            "playlist": [
                {"uri": "http://a.com/1.mp3", "title": "T1"},
            ]
        }
        pl = Playlist.from_dict(d)
        self.assertEqual(pl.title, "FromDict")

    def test_from_dict_missing_playlist_raises(self) -> None:
        with self.assertRaises(ValueError):
            Playlist.from_dict({"title": "No entries"})

    def test_entries_property(self) -> None:
        pl = Playlist()
        pl.add_entry(self._make_entry("http://a.com/1.mp3", "T1"))
        entries = pl.entries
        self.assertEqual(len(entries), 1)
        self.assertIsInstance(entries[0], MediaEntry)


if __name__ == "__main__":
    unittest.main()
