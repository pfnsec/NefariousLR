#!/usr/bin/python3

import json
from nameko.dependency_providers import Config
from nameko.web.handlers import http
from nameko.rpc import rpc, RpcProxy

class HttpService:
    name = "http_service"

    video_index   = RpcProxy("video_index")
    search_engine = RpcProxy("search_engine")
    axi_service   = RpcProxy("axi_service")


    @http('GET', '/videos/<string:series>')
    def load_videos(self, request, series):
        videos = self.video_index.videos("series")
        return json.dumps({'videos': videos})

    @http('GET', '/subtitle/<string:query>')
    def search_subtitles(self, request, query):
        videos = self.search_engine.search('', query)
        return json.dumps({'videos': videos})

    @http('GET', '/axi/write/<string:addr>/<string:data>/')
    def axi_write(self, request, addr, data):
        resp = self.axi_service.write('', addr, data)
        print(resp)
        return resp
        #return json.dumps({'resp': resp})

    @http('GET', '/axi/read/<string:addr>')
    def axi_read(self, request, addr):
        resp = self.axi_service.read(addr)
        print(resp)
        return resp
        #return json.dumps({'resp': resp})

    @http('GET', '/axi/reset')
    def axi_reset(self, request):
        self.axi_service.reset()
        return "reset"
