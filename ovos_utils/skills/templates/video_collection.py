from ovos_utils.waiting_for_mycroft.common_play import CommonPlaySkill, \
    CPSMatchLevel, CPSTrackStatus, CPSMatchType
from os.path import join, dirname, basename
import random
from ovos_utils import get_mycroft_root, datestr2ts, resolve_ovos_resource_file
from ovos_utils.log import LOG
from ovos_utils.parse import fuzzy_match
from json_database import JsonStorageXDG

try:
    from mycroft.skills.core import intent_file_handler
except ImportError:
    import sys
    MYCROFT_ROOT_PATH = get_mycroft_root()
    if MYCROFT_ROOT_PATH is not None:
        sys.path.append(MYCROFT_ROOT_PATH)
        from mycroft.skills.core import intent_file_handler
    else:
        LOG.error("Could not find mycroft root path")
        raise ImportError

try:
    import pyvod
except ImportError:
    LOG.error("py_VOD not installed!")
    LOG.debug("py_VOD>=0.4.0")
    pyvod = None


class VideoCollectionSkill(CommonPlaySkill):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "max_videos" not in self.settings:
            self.settings["max_videos"] = 500
        if "min_duration" not in self.settings:
            self.settings["min_duration"] = -1
        if "max_duration" not in self.settings:
            self.settings["max_duration"] = -1
        if "shuffle_menu" not in self.settings:
            self.settings["shuffle_menu"] = False
        if "filter_live" not in self.settings:
            self.settings["filter_live"] = False
        if "filter_date" not in self.settings:
            self.settings["filter_date"] = False

        if pyvod is None:
            LOG.error("py_VOD not installed!")
            LOG.info("pip install py_VOD>=0.4.0")
            raise ImportError
        self.default_bg = "https://github.com/OpenVoiceOS/ovos_assets/raw/master/Logo/ovos-logo-512.png"
        self.default_image = resolve_ovos_resource_file("ui/images/moviesandfilms.png")
        db_path = join(dirname(__file__), "res", self.name + ".jsondb")
        self.message_namespace = basename(dirname(__file__)) + ".ovos_utils"
        self.media_collection = pyvod.Collection(self.name,
                                           logo=self.default_image,
                                           db_path=db_path)


    def initialize(self):
        self.initialize_media_commons()

    def initialize_media_commons(self):
        # generic ovos events
        self.gui.register_handler("ovos_utils.play_event",
                                  self.play_video_event)
        self.gui.register_handler("ovos_utils.clear_history",
                                  self.handle_clear_history)

        # skill specific events
        self.add_event('{msg_base}.home'.format(msg_base=self.message_namespace),
                       self.handle_homescreen)
        self.gui.register_handler(
            "{msg_base}.play_event".format(msg_base=self.message_namespace),
            self.play_video_event)
        self.gui.register_handler(
            "{msg_base}.clear_history".format(msg_base=self.message_namespace),
            self.handle_clear_history)

    @property
    def videos(self):
        try:
            # load video catalog
            videos = [ch.as_json() for ch in self.media_collection.entries]
            # set skill_id
            for idx, v in enumerate(videos):
                videos[idx]["skill"] = self.skill_id
                # set url
                if len(videos[idx].get("streams", [])):
                    videos[idx]["url"] = videos[idx]["streams"][0]
                else:
                    videos[idx]["url"] = videos[idx].get("stream") or \
                                         videos[idx].get("url")
            # return sorted
            return self.sort_videos(videos)
        except Exception as e:
            LOG.exception(e)
            return []

    # homescreen / menu
    def sort_videos(self, videos):
        # sort by upload date
        if self.settings["filter_date"]:
            videos = sorted(videos,
                        key=lambda kv: datestr2ts(kv.get("upload_date")),
                        reverse=True)

        # this will filter live videos
        live = [v for v in videos if v.get("is_live")]
        videos = [v for v in videos if not v.get("is_live")]

        # live streams before videos
        return live + videos

    def filter_videos(self, videos):
        # this will filter private videos in youtube
        if self.settings["filter_date"]:
            videos = [v for v in videos if v.get("upload_date")]

        # this will filter live videos
        live = [v for v in videos if v.get("is_live")]
        videos = [v for v in videos if not v.get("is_live")]

        # filter by duration
        if self.settings["min_duration"] > 0 or \
                self.settings["max_duration"] > 0:
            videos = [v for v in videos if
                      v.get("duration")]  # might be missing

        if self.settings["min_duration"] > 0:
            videos = [v for v in videos if int(v.get("duration", 0)) >=
                      self.settings["min_duration"]]
        if self.settings["max_duration"] > 0:
            videos = [v for v in videos if int(v.get("duration", 0)) <=
                      self.settings["max_duration"]]

        # TODO filter behind the scenes, clips etc based on
        #  title/tags/description/keywords required or forbidden

        if self.settings["shuffle_menu"]:
            random.shuffle(videos)

        if self.settings["max_videos"]:
            # rendering takes forever if there are too many entries
            videos = videos[:self.settings["max_videos"]]

        # this will filter live videos
        if self.settings["filter_live"]:
            return videos
        return live + videos

    def handle_homescreen(self, message):
        self.gui.clear()
        self.gui["videosHomeModel"] = self.filter_videos(self.videos)
        self.gui["historyModel"] = JsonStorageXDG("{msg_base}.history".format(msg_base=self.message_namespace)) \
            .get("model", [])
        self.gui.show_page("Homescreen.qml", override_idle=True)

    def play_video_event(self, message):
        video_data = message.data["modelData"]
        if video_data["skill_id"] == self.skill_id:
            self.play_video(video_data)

    # watch history database
    def add_to_history(self, video_data):
        # History
        historyDB = JsonStorageXDG("{msg_base}.history".format(msg_base=self.message_namespace))
        if "model" not in historyDB:
            historyDB["model"] = []
        historyDB["model"].append(video_data)
        historyDB.store()
        self.gui["historyModel"] = historyDB["model"]

    def handle_clear_history(self, message):
        video_data = message.data["modelData"]
        if video_data["skill_id"] == self.skill_id:
            historyDB = JsonStorageXDG("{msg_base}.history"
                                       .format(msg_base=self.message_namespace))
            historyDB["model"] = []
            historyDB.store()

    # matching
    def match_media_type(self, phrase, media_type):
        match = None
        score = 0

        if media_type == CPSMatchType.VIDEO:
            score += 0.05
            match = CPSMatchLevel.GENERIC

        return match, score

    def augment_tags(self, phrase, media_type, tags=None):
        return tags or []

    def match_tags(self, video, phrase, match, media_type):
        score = 0
        # score tags
        leftover_text = phrase
        tags = list(set(video.get("tags") or []))
        tags = self.augment_tags(phrase, media_type, tags)
        if tags:
            # tag match bonus
            for tag in tags:
                tag = tag.lower().strip()
                if tag in phrase:
                    match = CPSMatchLevel.CATEGORY
                    score += 0.05
                    leftover_text = leftover_text.replace(tag, "")
        return match, score, leftover_text

    def match_description(self, video, phrase, match):
        # score description
        score = 0
        leftover_text = phrase
        words = video.get("description", "").split(" ")
        for word in words:
            if len(word) > 4 and word in self.normalize_title(leftover_text):
                score += 0.05
                leftover_text = leftover_text.replace(word, "")
        return match, score, leftover_text

    def match_title(self, videos, phrase, match):
        # match video name
        clean_phrase = self.normalize_title(phrase)
        leftover_text = phrase
        best_score = 0
        best_video = random.choice(videos)
        for video in videos:
            title = video["title"]
            score = fuzzy_match(clean_phrase, self.normalize_title(title))
            if phrase.lower() in title.lower() or \
                    clean_phrase in self.normalize_title(title):
                score += 0.3
            if score >= best_score:
                # TODO handle ties
                match = CPSMatchLevel.TITLE
                best_video = video
                best_score = score
                leftover_text = phrase.replace(title, "")
        return match, best_score, best_video, leftover_text

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "video")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join([w for w in title.split(" ") if w])  # remove extra
        # spaces

    # common play
    def calc_final_score(self, phrase, base_score, match_level):
        return base_score, match_level

    def base_CPS_match(self, phrase, media_type):
        best_score = 0
        # see if media type is in query, base_score will depend if "video" is in query
        match, base_score = self.match_media_type(phrase, media_type)
        videos = list(self.videos)
        best_video = random.choice(self.videos)
        # match video data
        scores = []
        for video in videos:
            match, score, _ = self.match_tags(video, phrase, match, media_type)
            # match, score, leftover_text = self.match_description(video, leftover_text, match)
            scores.append((video, score))
            if score > best_score:
                best_video = video
                best_score = score

        self.log.debug("Best Tags Match: {s}, {t}".format(
            s=best_score, t=best_video["title"]))

        # match video name
        match, title_score, best_title, leftover_text = self.match_title(
            videos, phrase, match)
        self.log.debug("Best Title Match: {s}, {t}".format(
            s=title_score, t=best_title["title"]))

        # title more important than tags
        if title_score + 0.15 > best_score:
            best_video = best_title
            best_score = title_score

        # sort matches
        scores = sorted(scores, key=lambda k: k[1], reverse=True)
        scores.insert(0, (best_title, title_score))
        scores.remove((best_video, best_score))
        scores.insert(0, (best_video, best_score))

        # choose from top N
        if best_score < 0.5:
            n = 50
        elif best_score < 0.6:
            n = 10
        elif best_score < 0.8:
            n = 3
        else:
            n = 1

        candidates = scores[:n]
        self.log.info("Choosing randomly from top {n} matches".format(
            n=len(candidates)))
        best_video = random.choice(candidates)[0]

        # calc final confidence
        score = base_score + best_score
        score = self.calc_final_score(phrase, score, match)
        if isinstance(score, float):
            if score >= 0.9:
                match = CPSMatchLevel.EXACT
            elif score >= 0.7:
                match = CPSMatchLevel.MULTI_KEY
            elif score >= 0.5:
                match = CPSMatchLevel.TITLE
        else:
            score, match = score

        self.log.info("Best video: " + best_video["title"])

        if match is not None:
            return (leftover_text, match, best_video)
        return None

    def CPS_match_query_phrase(self, phrase, media_type):
        match = self.base_CPS_match(phrase, media_type)
        if match is None:
            return None
        # match == (leftover_text, CPSMatchLevel, best_video_data)
        return match

    def CPS_start(self, phrase, data):
        self.play_video(data)

    def play_video(self, data):
        self.add_to_history(data)
        bg = data.get("background") or self.default_bg
        image = data.get("image") or self.default_image

        if len(data.get("streams", [])):
            url = data["streams"][0]
        else:
            url = data.get("stream") or data.get("url")

        title = data.get("name") or self.name
        self.CPS_send_status(uri=url,
                             image=image,
                             background_image=bg,
                             playlist_position=0,
                             status=CPSTrackStatus.PLAYING_GUI)
        self.gui.play_video(pyvod.utils.get_video_stream(url), title)

    def stop(self):
        self.gui.release()

