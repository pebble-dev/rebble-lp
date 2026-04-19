import langcodes
import hashlib
import click
import json

from flask import Blueprint, request, jsonify, cli

from .models import db, LanguagePack, Language
from .settings import config
from .s3 import upload_pbl
from .utils import id_generator

parent_app = None
api = Blueprint('api', __name__)

@api.route('/languages')
def get_languages():
    packs = LanguagePack.query
    hardware = request.args.get('hw')
    if hardware:
        packs = packs.filter_by(hardware=hardware)
    # TODO: Don't filter by it, use this value for translating local names
    #locale = request.args.get('isoLocal')
    #if locale:
    #    packs = packs.filter_by(language_id=locale)
    firmware = request.args.get('firmware')
    if firmware:
        try:
            firmware_major, firmware_minor = [int(part) for part in firmware.split('.')[:2]]
            packs = packs.filter(LanguagePack.firmware_major == firmware_major, LanguagePack.firmware_minor <= firmware_minor)
        except ValueError:
            return 'Wrong firmware paramter', 400
    return jsonify({
        'languages': [pack.to_json() for pack in packs]
    })


@api.route('/languages/<id>')
def language(id):
    pack = LanguagePack.query.filter_by(id=id).one_or_none()
    if pack is None:
        return 'No such language pack', 404
    return jsonify(pack.to_json())


@click.command(name='submit_language_pack')
@click.argument('iso_locale')
@click.argument('hardware')
@click.argument('min_firmware_version')
@click.argument('file', type=click.File('rb'))
@cli.with_appcontext
def submit_language_pack(iso_locale, hardware, min_firmware_version, file):
    locale = langcodes.standardize_tag(iso_locale).replace('-', '_')
    firmware_minor, firmware_major, firmware_patch = [int(part) for part in min_firmware_version.split('.')]
    sha256 = hashlib.sha256()
    sha256.update(file.read())
    file_hash = sha256.hexdigest()

    language = Language.query.filter_by(locale=locale).one_or_none()
    if language is None:
        language_name = langcodes.Language.get(locale).display_name()
        local_name = langcodes.Language.get(locale).display_name(locale)
        language = Language(locale=locale, name=language_name, local_name=local_name)
        db.session.add(language)

    language_pack = LanguagePack.query.filter_by(firmware_major=firmware_major, firmware_minor=firmware_minor, firmware_patch=firmware_patch,
                                                 hardware=hardware, language_id=locale).one_or_none()
    if language_pack is None:  # create language pack
        filename = upload_pbl(file, locale)
        language_pack = LanguagePack(id=id_generator.generate(), firmware_major=firmware_major, firmware_minor=firmware_minor, firmware_patch=firmware_patch,
                                     hardware=hardware, language_id=locale, file=filename, file_hash=file_hash)

        db.session.add(language_pack)
        db.session.commit()
    else:  # update language pack
        # Nothing to do, already the correct version
        if language_pack.file_hash == file_hash:
            return 'OK'

        filename = upload_pbl(file, locale)
        LanguagePack.query.filter_by(id=language_pack.id).update({
            'version': LanguagePack.version + 1,
            'file': filename,
            'file_hash': file_hash
        })

        db.session.commit()
    return 'OK'

@click.command(name='import_json')
@cli.with_appcontext
def import_json():
    with open('language_packs.json') as f:
        languages = json.load(f)['languages']

    for language in languages:
        language_pack = LanguagePack.from_json(language)
        db.session.add(language_pack)
        parent_app.logger.info(f"Fetched {language_pack.id}")

    db.session.commit()

def init_app(app, url_prefix='/v1'):
    global parent_app
    parent_app = app
    app.cli.add_command(import_json)
    app.cli.add_command(submit_language_pack)
    app.register_blueprint(api, url_prefix=url_prefix)
