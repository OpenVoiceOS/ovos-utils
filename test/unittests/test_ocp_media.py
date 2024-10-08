import unittest

from ovos_utils.ocp import MediaEntry, Playlist, MediaType, PlaybackType, TrackState

dict_search_results = [
    {'media_type': MediaType.MUSIC,
     'playback': PlaybackType.AUDIO,
     'image': 'https://freemusicarchive.org/legacy/fma-smaller.jpg',
     'skill_icon': 'https://freemusicarchive.org/legacy/fma-smaller.jpg',
     'uri': 'https://freemusicarchive.org/track/07_-_Quantum_Jazz_-_Orbiting_A_Distant_Planet/stream/',
     'title': 'Orbiting A Distant Planet',
     'artist': 'Quantum Jazz',
     'skill_id': 'skill-free_music_archive.neongeckocom',
     'match_confidence': 65},
    {'media_type': MediaType.MUSIC,
     'playback': PlaybackType.AUDIO,
     'image': 'https://freemusicarchive.org/legacy/fma-smaller.jpg',
     'skill_icon': 'https://freemusicarchive.org/legacy/fma-smaller.jpg',
     'uri': 'https://freemusicarchive.org/track/05_-_Quantum_Jazz_-_Passing_Fields/stream/',
     'skill_id': 'skill-free_music_archive.neongeckocom',
     'title': 'Passing Fields',
     'artist': 'Quantum Jazz',
     'match_confidence': 65},
    {'media_type': MediaType.MUSIC,
     'playback': PlaybackType.AUDIO,
     'image': 'https://freemusicarchive.org/legacy/fma-smaller.jpg',
     'skill_icon': 'https://freemusicarchive.org/legacy/fma-smaller.jpg',
     'skill_id': 'skill-free_music_archive.neongeckocom',
     'uri': 'https://freemusicarchive.org/track/04_-_Quantum_Jazz_-_All_About_The_Sun/stream/',
     'title': 'All About The Sun',
     'artist': 'Quantum Jazz',
     'match_confidence': 65}
]

search_results = [
    MediaEntry(media_type=MediaType.MUSIC,
               playback=PlaybackType.AUDIO,
               image='https://freemusicarchive.org/legacy/fma-smaller.jpg',
               uri='https://freemusicarchive.org/track/07_-_Quantum_Jazz_-_Orbiting_A_Distant_Planet/stream/',
               skill_icon='https://freemusicarchive.org/legacy/fma-smaller.jpg',
               title='Orbiting A Distant Planet',
               artist='Quantum Jazz',
               skill_id='skill-free_music_archive.neongeckocom',
               match_confidence=65
               ),
    MediaEntry(media_type=MediaType.MUSIC,
               playback=PlaybackType.AUDIO,
               image='https://freemusicarchive.org/legacy/fma-smaller.jpg',
               uri='https://freemusicarchive.org/track/05_-_Quantum_Jazz_-_Passing_Fields/stream/',
               skill_icon='https://freemusicarchive.org/legacy/fma-smaller.jpg',
               title='Passing Fields',
               artist='Quantum Jazz',
               skill_id='skill-free_music_archive.neongeckocom',
               match_confidence=65),
    MediaEntry(media_type=MediaType.MUSIC,
               playback=PlaybackType.AUDIO,
               image='https://freemusicarchive.org/legacy/fma-smaller.jpg',
               uri='https://freemusicarchive.org/track/04_-_Quantum_Jazz_-_All_About_The_Sun/stream/',
               skill_icon='https://freemusicarchive.org/legacy/fma-smaller.jpg',
               title='All About The Sun',
               artist='Quantum Jazz',
               skill_id='skill-free_music_archive.neongeckocom',
               match_confidence=65)
]


class TestMediaEntry(unittest.TestCase):
    def test_init(self):
        data = dict_search_results[0]

        # Test MediaEntry init
        entry = MediaEntry(**data)
        self.assertEqual(entry.title, data['title'])
        self.assertEqual(entry.uri, data['uri'])
        self.assertEqual(entry.artist, data['artist'])
        self.assertEqual(entry.skill_id, data['skill_id'])
        self.assertEqual(entry.status, TrackState.DISAMBIGUATION)
        self.assertEqual(entry.playback, data['playback'])
        self.assertEqual(entry.image, data['image'])
        self.assertEqual(entry.skill_icon, data['skill_icon'])
        self.assertEqual(entry.javascript, "")

        # Test playback passed as int
        data['playback'] = int(data['playback'])
        new_entry = MediaEntry(**data)
        self.assertEqual(entry, new_entry)

    def test_as_dict(self):
        for idx, track in enumerate(search_results):
            for k, v in track.as_dict.items():
                if k in dict_search_results[idx]:
                    self.assertEqual(v, dict_search_results[idx][k])

        for idx, track in enumerate(dict_search_results):
            self.assertEqual(MediaEntry.from_dict(track), search_results[idx])

    def test_from_dict(self):
        dict_data = dict_search_results[1]
        from_dict = MediaEntry.from_dict(dict_data)
        self.assertIsInstance(from_dict, MediaEntry)
        from_init = MediaEntry(dict_data["uri"], dict_data["title"],
                               image=dict_data["image"],
                               match_confidence=dict_data["match_confidence"],
                               playback=PlaybackType.AUDIO,
                               skill_icon=dict_data["skill_icon"],
                               skill_id=dict_data["skill_id"],
                               media_type=dict_data["media_type"],
                               artist=dict_data["artist"])
        self.assertEqual(from_init, from_dict)

        # Test int playback
        dict_data['playback'] = int(dict_data['playback'])
        new_entry = MediaEntry.from_dict(dict_data)
        self.assertEqual(from_dict, new_entry)

        self.assertIsInstance(MediaEntry.from_dict({"uri": "xxx"}), MediaEntry)


class TestPlaylist(unittest.TestCase):
    def test_properties(self):
        # Empty Playlist
        pl = Playlist(title="empty playlist")
        self.assertEqual(pl.title, "empty playlist")
        self.assertEqual(pl.position, 0)
        self.assertEqual(pl.entries, [])
        self.assertIsNone(pl.current_track)
        self.assertTrue(pl.is_first_track)
        self.assertTrue(pl.is_last_track)

        # Playlist of dicts
        pl = Playlist(dict_search_results, title="my playlist")
        self.assertEqual(pl.title, "my playlist")
        self.assertEqual(pl.position, 0)
        self.assertEqual(len(pl), len(dict_search_results))
        self.assertEqual(len(pl.entries), len(dict_search_results))
        for entry in pl.entries:
            self.assertIsInstance(entry, MediaEntry)
        self.assertIsInstance(pl.current_track, MediaEntry)
        self.assertTrue(pl.is_first_track)
        self.assertFalse(pl.is_last_track)

        # Playlist of MediaEntry
        pl = Playlist(search_results, title="Test Jazz")
        self.assertEqual(pl.title, "Test Jazz")
        self.assertEqual(pl.position, 0)
        self.assertEqual(len(pl), len(search_results))
        self.assertEqual(len(pl.entries), len(search_results))
        for entry in pl.entries:
            self.assertIsInstance(entry, MediaEntry)
        self.assertIsInstance(pl.current_track, MediaEntry)
        self.assertTrue(pl.is_first_track)
        self.assertFalse(pl.is_last_track)

        self.assertListEqual(pl.entries, search_results)
        for idx, e in enumerate(pl.as_dict["playlist"]):
            self.assertEqual(MediaEntry.from_dict(e), search_results[idx])

        # test serialize/deserialize
        self.assertEqual(Playlist.from_dict(pl.as_dict), pl)

    def test_goto_start(self):
        # TODO
        pass

    def test_clear(self):
        # TODO
        pass

    def test_sort_by_conf(self):
        # TODO
        pass

    def test_add_entry(self):
        # TODO
        pass

    def test_remove_entry(self):
        # TODO
        pass

    def test_replace(self):
        # TODO
        pass

    def test_set_position(self):
        # TODO
        pass

    def test_goto_track(self):
        # TODO
        pass

    def test_next_track(self):
        # TODO
        pass

    def test_prev_track(self):
        # TODO
        pass

    def test_validate_position(self):
        # Test empty playlist
        pl = Playlist()
        pl.position = 0
        pl._validate_position()
        self.assertEqual(pl.position, 0)
        pl.position = -1
        pl._validate_position()
        self.assertEqual(pl.position, 0)
        pl.position = 1
        pl._validate_position()
        self.assertEqual(pl.position, 0)

        # Test playlist of len 1
        pl = Playlist([dict_search_results[0]])
        pl.position = 0
        pl._validate_position()
        self.assertEqual(pl.position, 0)
        pl.position = 1
        pl._validate_position()
        self.assertEqual(pl.position, 0)

        # Test playlist of len>1
        pl = Playlist(dict_search_results)
        pl.position = 0
        pl._validate_position()
        self.assertEqual(pl.position, 0)
        pl.position = 1
        pl._validate_position()
        self.assertEqual(pl.position, 1)
        pl.position = 10
        pl._validate_position()
        self.assertEqual(pl.position, 0)


if __name__ == "__main__":
    unittest.main()
