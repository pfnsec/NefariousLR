
import os
import re
import stat
from pathlib import Path
import threading
import queue
import subprocess

from nameko.events import EventDispatcher, event_handler
from nameko.dependency_providers import Config
from nameko.rpc import rpc

#ffmpeg's filter input needs to be escaped 3 times (!!!) 
#in order to work with all the special characters
#that will undoubtably be present in this weebiest
#of servers.
def ffmpeg_escape(path):
    path = path.replace('[', '\\[')
    path = path.replace(']', '\\]')
    path = path.replace('\\', '\\\\')
    return path

def ffmpeg_outfile_escape(path):
    path = path.replace('&', '\\&')
    return path




class EncodeServer:
    """ Encoder Server, running FFmpeg """
    name = "encode_server"

    dispatch = EventDispatcher()
    config = Config()

    @event_handler("video_index", "generate_subtitles")
    def generateSubtitles(self, v):
        vid_file = v['path'] + v['name']
        sub_file = v['path'] + v['track'] + '.srt'

        #Figure out where videos are stored
        self.video_path = self.config.get('VIDEO_REPO', "./videos")

    #    vid_file = ffmpeg_escape(vid_file)
    #    sub_file = ffmpeg_escape(sub_file)
        #vid_file = re.escape(vid_file)
        #sub_file = re.escape(sub_file)

        #Extract the subs.
        try:
            #out = subprocess.check_output(f'ffmpeg -txt_format text -i "{vid_file}" "{sub_file}"',
            out = subprocess.check_output(f'ffmpeg -i "{vid_file}"  "{sub_file}"',
                                          encoding='utf-8',
                                          shell=True)
            self.dispatch("load_subtitles", v)
        except subprocess.CalledProcessError as e:
            #If we can't create the subtitle file, we 
            #simply create an empty subtitle file where it _should_ be and 
            #mark it executable to indicate that it's a missing sub.
            #This is just for convenience, so you can type 
            #ls and know which files are missing subs.
            Path(sub_file).touch()
            Path(sub_file).chmod(stat.S_IEXEC)


    @rpc
    def generateClip(self, timestamp, video_in):

        #start = ffmpeg_timestamp(timestamp.milliseconds)
        start = timestamp

        video = os.path.splitext(video_in)

        video_out = f'{video[0]}_{start}.webm'

        print(start)

        try:
            out = subprocess.check_output(f'ffmpeg     \
                                           -ss "{start}"             \
                                           -i "{video_in}"         \
                                           -t 0:0:10               \
                                           -vcodec libvpx-vp9      \
                                           -acodec libvorbis       \
                                           -preset ultrafast       \
                                           -deadline realtime -n   \
                                          "{video_out}"',
                                            encoding='utf-8',
                                            shell=True)
        except subprocess.CalledProcessError as e:
            #Whomp whomp
            pass

        return video_out

                #'-cpu-used', '-5',
