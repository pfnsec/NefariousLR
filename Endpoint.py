#!/usr/bin/python3
# __init__.py


import eventlet
eventlet.monkey_patch()

import flask
from flask import Flask, request
from flask_nameko import FlaskPooledClusterRpcProxy
from flask_socketio import SocketIO, emit

import nameko
from nameko.runners import ServiceRunner

import EncodeServer
import VideoIndex
import SearchEngine
import Directories


runner = ServiceRunner(config=dict(
    AMQP_URI='amqp://localhost'
))

runner.add_service(EncodeServer.EncodeServer)
runner.add_service(VideoIndex.VideoIndex)
runner.add_service(SearchEngine.SearchEngine)

rpc = FlaskPooledClusterRpcProxy()

def create_app():
    app = Flask(__name__)
    app.config.update(dict(
        NAMEKO_AMQP_URI='amqp://localhost'
    ))

    rpc.init_app(app)

    #uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))

    app.config['SECRET_KEY'] = 'secret!'
    return app


app = create_app()

socketio = SocketIO(app)

@app.before_first_request
def load_shows():
    for k in Directories.showdirs.keys():
        videos = rpc.video_index.load_series(k, Directories.showdirs[k])


@app.route('/search')
def add_video():
    show  = request.args.get('show')
    query = request.args.get('query')

    if(show is None or query is None):
        flask.abort(401)
    else:
        #rpc.playlist_server.add_video(v_id)
        res = rpc.search_engine.search(show, query)
        return flask.jsonify(res), 200


@socketio.on('skip')
def skip():
    rpc.playlist_server.next_video()

    res = rpc.playlist_server.get_video()
    emit('resync', res, broadcast=True)

    #return flask.jsonify(res), 200


@app.route('/content/<path:path>')
def send_file(path):
    return flask.send_from_directory('content', path)



if __name__ == '__main__':
    print("running service")
    runner.start()
    print("running flask")

    socketio.run(app, debug=False, port=4020)

print("Stopping")
