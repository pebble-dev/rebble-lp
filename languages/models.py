import os
import hashlib
import io

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .utils import id_generator
from .settings import config
from .s3 import download_pbl

db = SQLAlchemy()
migrate = Migrate()

def language_pack_id():
    id_generator.generate()

def hash_remote_pbw(filename):
    file = io.BytesIO()
    download_pbl(filename, file)
    sha256 = hashlib.sha256()
    sha256.update(file.read())
    return sha256.hexdigest()

class Language(db.Model):
    __tablename__ = "languages"
    locale = db.Column(db.String(12), primary_key=True)
    name = db.Column(db.String, nullable=False)
    local_name = db.Column(db.String, nullable=False)


class LanguagePack(db.Model):
    __tablename__ = "language_packs"
    id = db.Column(db.String(24), primary_key=True, default=language_pack_id)
    version = db.Column(db.Integer, default=1, nullable=False)
    # Split in 3 to allow easy query of firmware versions
    firmware_major = db.Column(db.Integer, default=0, nullable=False)
    firmware_minor = db.Column(db.Integer, default=0, nullable=False)
    firmware_patch = db.Column(db.Integer, default=0, nullable=False)
    hardware = db.Column(db.String, nullable=False)
    language_id = db.Column(db.String(12), db.ForeignKey('languages.locale'), index=True, nullable=False)
    language = db.relationship('Language', lazy='selectin')
    file = db.Column(db.String, nullable=False)
    file_hash = db.Column(db.String, nullable=False)

    @classmethod
    def from_json(cls, json):
        try:
            language = Language.query.filter_by(locale=json['ISOLocal']).one_or_none()
            
            if language is None:
                language = Language(locale=json['ISOLocal'], name=json['name'], local_name=json['localName'])

            firmware_major, firmware_minor, firmware_patch = [int(part) for part in json['firmware'].split('.')]
            pack = cls(
                id=json['id'],
                version=json['version'],
                firmware_major=firmware_major,
                firmware_minor=firmware_minor,
                firmware_patch=firmware_patch,
                hardware=json['hardware'],
                language=language,
                file=json['file'],
                file_hash=hash_remote_pbw(json['file']),
            )
            return pack
        except (KeyError, ValueError):
            return None

    def to_json(self):
        # TODO: Figure out if the mobile section is necessary
        return {
            'id': self.id,
            'version': self.version,
            'firmware': f"{self.firmware_major}.{self.firmware_minor}.{self.firmware_patch}",
            'hardware': self.hardware,
            'name': self.language.name,
            'localName': self.language.local_name,
            'ISOLocal': self.language.locale,
            'file': os.path.join(config['BINARIES_ROOT'], self.file),
        }

db.Index('language_pack_firmware_hardware_languageid', LanguagePack.firmware_major, LanguagePack.firmware_minor, LanguagePack.firmware_patch, LanguagePack.hardware, LanguagePack.language_id, unique = True)

def init_app(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
