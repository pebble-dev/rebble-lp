try:
    import google.auth.exceptions
    try:
        import googleclouddebugger
        googleclouddebugger.enable(module='notif-app-icons')
    except (ImportError, google.auth.exceptions.DefaultCredentialsError):
        print("Couldn't start cloud debugger")
except ImportError:
    print("Couldn't import google exceptions")

import json
from os import environ

import beeline
from beeline.middleware.flask import HoneyMiddleware
from flask import Flask, request, jsonify

app = Flask(__name__)

if environ.get('HONEYCOMB_KEY'):
     beeline.init(writekey=environ['HONEYCOMB_KEY'], dataset='rws', service_name='lp')
     HoneyMiddleware(app, db_events=True)

with open('language_packs.json') as f:
    languages = json.load(f)['languages']


def urlify(pack):
    return {**pack, 'file': f"https://binaries.rebble.io/lp/{pack['file']}"}


@app.route('/heartbeat')
@app.route('/lp/heartbeat')
def heartbeat():
    return 'ok'


@app.route('/v1/languages')
def list_languages():
    packs = languages[:]
    if request.args.get('hw'):
        packs = [x for x in packs if x['hardware'] == request.args['hw']]
    fw = request.args.get('firmware')
    if fw:
        major, minor = [int(x) for x in fw.split('.')[:2]]
        version_packs = []
        for pack in packs:
            pack_major, pack_minor = [int(x) for x in pack['firmware'].split('.')[:2]]
            if major == pack_major and minor >= pack_minor:
                version_packs.append(pack)
        packs = version_packs
    return jsonify(languages=[urlify(x) for x in packs])


@app.route('/v1/languages/<pack_id>')
def get_pack(pack_id):
    try:
        pack = next(x for x in languages if x['id'] == pack_id)
    except StopIteration:
        return "No such language pack", 404
    return jsonify(urlify(pack))
