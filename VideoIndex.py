import os
import json
from nameko.events import EventDispatcher, event_handler
from nameko.dependency_providers import Config
from nameko.rpc import rpc


def search_directory(directory, extensions):
    flist = []

    for root, dirs, files, in os.walk(directory, followlinks=True):
        path = root.split(os.sep)

        for file in files:
            #Filter by extension
            if(os.path.splitext(file)[1] in extensions):

                #We assume that the top-level directory indicates the show, 
                #or at least some other meaningful category
                show = path[2:-1]
                if(len(show) > 0):
                    showdir = '/'.join(show)
                else:
                    showdir = ''

                trackdir = os.path.splitext(file)[0]

                flist.append({
                        'name':file,
                        'track':trackdir,
                        'show':showdir,
                        'path':'/'.join(path) + '/'
                    })

    return flist


class VideoIndex:
    name = "video_index"

    config = Config()

    dispatch = EventDispatcher()

    allowed_extensions = [
        '.mp4',
        '.mkv',
        '.flv',
        '.avi',
        '.webm',
        '.mov',
    ]

    #Gets all video file paths for a particular series
    @rpc
    def videos(self, seriesName):

        #Figure out where videos are stored
        self.video_path = self.config.get('VIDEO_REPO', "./videos")

        videos = search_directory(self.video_path, self.allowed_extensions)

        for v in videos:
            sub_file = v['path'] + v['track'] + '.srt'
            print(sub_file)

            if(os.path.isfile(sub_file)):
                self.dispatch("load_subtitles", v)
            else:
                #If the subtitle file doesn't exist, tell the 
                #encode server to generate it
                self.dispatch("generate_subtitles", v)

        return videos
