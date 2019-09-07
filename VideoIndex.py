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
        '.m4v',
        '.flv',
        '.avi',
        '.webm',
        '.mov',
    ]

    #Walks through every 
    @rpc
    def load_series(self, name, path):

        #Figure out where videos are stored
        self.video_path = self.config.get('VIDEO_REPO', "./videos")

        self.video_path = os.path.join(self.video_path, path)

        print("self.video_path:")
        print(self.video_path)

        videos = search_directory(self.video_path, self.allowed_extensions)

        for v in videos:
            sub_file = v['path'] + v['track'] + '.en.srt'
            print(sub_file)

            v['show'] = name


            if(os.path.isfile(sub_file)):
                self.dispatch("load_subtitles", v)
            else:
                #If the subtitle file doesn't exist, tell the 
                #encode server to generate it
                #
                print("no sub found!")
                #self.dispatch("generate_subtitles", v)

        return videos

    @rpc
    def load_series_db(self, name, path):

        #Figure out where videos are stored
        self.video_path = self.config.get('VIDEO_REPO', "./videos")

        self.video_path = os.path.join(self.video_path, path)

        print("self.video_path:")
        print(self.video_path)

        videos = search_directory(self.video_path, self.allowed_extensions)

        for v in videos:
            sub_file = v['path'] + v['track'] + '.en.srt'
            print(sub_file)

            v['show'] = name


            if(os.path.isfile(sub_file)):
                self.dispatch("load_subtitles", v)
            else:
                #If the subtitle file doesn't exist, tell the 
                #encode server to generate it
                #
                print("no sub found!")
                #self.dispatch("generate_subtitles", v)

        return videos
