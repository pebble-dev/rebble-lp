import os

domain_root = os.environ.get('DOMAIN_ROOT', 'rebble.io')
http_protocol = os.environ.get('HTTP_PROTOCOL', 'https')
s3_path = os.environ.get('S3_PATH', 'lp/')

config = {
    'DOMAIN_ROOT': domain_root,
    'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    'BINARIES_ROOT': os.environ.get('BINARIES_ROOT', f'https://binaries.{domain_root}/{s3_path}'),
    'S3_BUCKET': os.environ.get('S3_BUCKET', 'rebble-binaries'),
    'S3_PATH': s3_path,
    'HONEYCOMB_KEY': os.environ.get('HONEYCOMB_KEY', None),
    'AWS_ACCESS_KEY': os.environ.get('AWS_ACCESS_KEY', None),
    'AWS_SECRET_KEY': os.environ.get('AWS_SECRET_KEY', None),
    'S3_ENDPOINT': os.environ.get('S3_ENDPOINT', None),
}
