
import os
import re
import stat
from pathlib import Path
import threading
import queue
import subprocess
import base64
import hashlib



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
    def generateClip(self, timestamp, video_in, seriesName):

        #start = ffmpeg_timestamp(timestamp.milliseconds)
        start = timestamp

        path = video_in.split(os.sep)

        #./video/<show>/<season>/
        in_dir = path[0:-1]
        in_dir = os.path.join(*in_dir)

        #episode_1.webm
        episode = path[-1]

        print(episode)

        episode = os.path.splitext(episode)

        print(in_dir)

        out_dir = os.path.join(in_dir, episode[0])

        video = os.path.splitext(video_in)

        #video_out = f'{video[0]}_{start}.webm'
        print(video)
        print(out_dir)

        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        #ext = '.webm'
        #ext = video[1]
        ext = '.jpeg'


        #video_out = f'{video[0]}/{video[0]}_{start}.webm'
        #video_out = f'{out_dir}/{episode[0]}_{start}{video[1]}'
        video_out = f'{out_dir}/{episode[0]}_{start}{ext}'

        print(video_out)


        #Generate hash for output content path

        hash_id = hashlib.md5(video_out.encode('utf-8')).digest()

        hash_id = base64.urlsafe_b64encode(hash_id).decode('utf-8')

        content_path = f"content/{seriesName}/{hash_id}{ext}"


        #If successfully processed output exists at content path,
        #return it. (Cache hit)
        if os.path.exists(content_path):
            return content_path

        #However, if a processing output exists without a corresponding 
        #content path, it was likely a failed run. 
        #Delete it and try again (false cache hit? encoder error?)
        if(os.path.exists(video_out)):
            os.remove(video_out)


        try:
            out = subprocess.check_output(f'ffmpeg                 \
                                           -ss "{start}"           \
                                           -i  "{video_in}"        \
                                           -qscale:v 4 -frames:v 1 \
                                          "{video_out}"',
                                          #-vf subtitles="{in_dir}/{episode[0]}.en.srt"     \
                                            encoding='utf-8',
                                            shell=True)

           #out = subprocess.check_output(f'ffmpeg     \
           #                               -ss "{start}"             \
           #                               -i "{video_in}"         \
           #                               -t 0:0:10               \
           #                               -vcodec libvpx-vp9      \
           #                               -acodec libvorbis       \
           #                               -preset ultrafast       \
           #                               -deadline realtime -n   \
           #                              "{video_out}"',
           #                                encoding='utf-8',
           #                                shell=True)
           #out = subprocess.check_output(f'ffmpeg                 \
           #                               -ss "{start}"           \
           #                               -i  "{video_in}"        \
           #                               -t 0:0:20               \
           #                               -vcodec copy            \
           #                               -acodec copy            \
           #                              "{video_out}"',
           #                                encoding='utf-8',
           #                                shell=True)

        except subprocess.CalledProcessError as e:
            #Whomp whomp
            return None


        os.symlink(f"../../{video_out}", content_path)

        return content_path

                #'-cpu-used', '-5',
