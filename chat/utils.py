import os
import codecs

from core.settings import MEDIA_ROOT


def file_from_string_to_file(s, filename, file_type_check=None, encoding='utf-8'):
    metadata, data = s.split(',')
    metadata = metadata.replace('data:', '')
    mime, enc = metadata.split(';')

    bytes_data = bytes(data, encoding)
    filetype, ext = mime.split('/')

    if file_type_check is not None:
        if filetype != file_type_check:
            msg = f"Wrong type! Expect {file_type_check}, get {filetype}"
            raise Exception(msg)
    q = codecs.decode(bytes_data, enc)
    filepath = f'{MEDIA_ROOT}{os.sep}attachments{os.sep}{filename}.{ext}'
    with open(filepath, 'wb') as f:
        f.write(q)
    return [q, ext]
