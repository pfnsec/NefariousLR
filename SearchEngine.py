from nameko.events import EventDispatcher, event_handler
from nameko.rpc import rpc, RpcProxy

import srt
try:
    from cfuzzyset import cFuzzySet as FuzzySet
except ImportError:
    from fuzzyset import FuzzySet

from html.parser import HTMLParser

#Class to strip HTML tags from subtitles
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


#Serialize the timestamp (datetime.timedelta) properly
def ffmpeg_timestamp(ts):
    ms = int(ts.total_seconds() * 1000)
    print(ms)
    return f"{ms // 3600000}:{ms // 60000 % 60}:{ms // 1000 % 60}.{ms % 1000}"


class SearchEngine:
    """ Search through fuzzy sets """
    name = "search_engine"

    dispatch = EventDispatcher()
    encode_server = RpcProxy("encode_server")

    subs = {}


    @event_handler("video_index", "load_subtitles")
    def indexLoadSubtitles(self, v):
        self.loadSubtitles(v)

    @event_handler("encode_server", "load_subtitles")
    def encoderLoadSubtitles(self, v):
        self.loadSubtitles(v)

    def loadSubtitles(self, v):
        if not v['show'] in self.subs:
            self.subs[v['show']] = {}


        index = v['path'] + v['track']
        sub_file = v['path'] + v['track'] + '.srt'

        if not index in self.subs[v['show']]:
            self.subs[v['show']][index] = {}
            self.subs[v['show']][index]['captions'] = {}
            self.subs[v['show']][index]['path'] = v
            self.subs[v['show']][index]['fuzz'] = FuzzySet()



        with open(sub_file, 'r') as sub:
            sub_text = sub.read()

        gen = srt.parse(sub_text)

        captions = list(gen)

        for c in captions:

            #Strip HTML
            strip_content = strip_tags(c.content)


            #Ok, this gets weird.
            #So, we index the set of captions for an episode by the caption content. 
            #However, this might have collisions.
            #The trick is that, for a given search query, two captions with the 
            #same content would be equally ranked, so we instead store 
            #a list of all timestamps for each content index
            #in order to resolve multiple timestamps with the 
            #same caption.
            if not strip_content in self.subs[v['show']][index]['captions']:
                self.subs[v['show']][index]['captions'][strip_content] = [c.start]
            else:
                self.subs[v['show']][index]['captions'][strip_content].append(c.start)

            self.subs[v['show']][index]['fuzz'].add(strip_content)

    #Gets the exact quote & timestamp from a query
    @rpc
    def search(self, seriesName, query):
        show_select = []

        show = self.subs['Steven Universe']

        results = []

        for index in show:

            res = show[index]['fuzz'].get(query)

            results.append([res, index])

        results = sorted(results, key = lambda r: r[0][0])

        top_result = results[-1]

        top_episode = top_result[1]
        top_quote   = top_result[0][0][1]

        timestamp = ffmpeg_timestamp(show[top_episode]['captions'][top_quote][0])
        path = show[top_episode]['path']

        video_in = path['path'] + path['name']

        self.encode_server.generateClip(timestamp, video_in)
