import os
from os import path
from datetime import datetime
import json

import charset_normalizer

GREEN_TEXT = '\033[92m{}\033[0m'
RED_TEXT = '\033[91m{}\033[0m'


def create_dir(dir_path: str):
    if not path.exists(dir_path):
        os.makedirs(dir_path)
        log(msg=f'Directory created: {dir_path}')
        print(GREEN_TEXT.format('✅ Directory created'))
    else:
        log(msg=f'Directory already exists: {dir_path}')
        print(RED_TEXT.format('🚫 Directory already exists'))
    print()


def create_dirs_structure(struct: dict, base_dir: str | None = None):
    for dir_name, subdirs in struct.items():

        dir_path = path.abspath(dir_name) if base_dir is None else path.join(base_dir, dir_name)

        log(msg=f'Creating directory: {dir_path}')
        print(f'🛠️  Creating directory "{GREEN_TEXT.format(dir_path)}"...')
        create_dir(dir_path)

        create_dirs_structure(subdirs, base_dir=dir_path)


def create_file(file_path: str, charset: str):
    if not path.exists(file_path):
        with open(file_path, 'w', encoding=charset) as f:
            f.write(f'Привет, Мир! (encoding: {charset})')
            log(msg=f'File created: {file_path}')
            print(GREEN_TEXT.format(f'✅ File created: {file_path}'))
    else:
        log(msg=f'File already exists: {file_path}')
        print(RED_TEXT.format(f'🚫 File already exists: {file_path}'))
    print()


def format_datetime(dt: datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def log(log_dir: str = path.abspath('logs'), log_file: str = 'log.txt', msg: str = ''):
    if not path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = path.join(log_dir, log_file)
    with open(log_path, 'a') as f:
        f.write(f'{format_datetime(datetime.now())}: {msg}\n')


def detect_encoding(file_path: str):
    with open(file_path, 'rb') as f:
        result = charset_normalizer.detect(f.read())
        return result['encoding']


def serialize_file_data(
    filename: str,
    file_text: str,
    file_text_proccessed: str,
):
    data = {
        'Имя файла': filename,
        'Исходный текст': file_text,
        'Преобразованный текст': file_text_proccessed,
        'Размер файла в байтах': len(file_text.encode('utf-8')),
        'Дата последнего изменения файла': datetime.fromtimestamp(
            path.getmtime(file_path),
        ).strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
        return json.dumps(data)


def load_to_json(output_path: str, data: dict):
    file_path = path.join(output_path, 'proccessed_data.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':

    '''
    Задание 1. Создание и управление директориями:
    '''
    CHARSETS = ['utf-8', 'windows-1251', 'utf-16']

    dir_struct = {
        'project_root': {
            'data': {
                'raw': {},
                'processed': {},
            },
            'logs': {},
            'backups': {},
            'output': {},
        },
    }

    create_dirs_structure(dir_struct)

    dir_raw = path.join(path.abspath('project_root'), 'data', 'raw')

    for i in range(len(CHARSETS)):
        charset = CHARSETS[i]
        file_path = path.join(dir_raw, f'file_{i}_{charset}.txt')

        log(msg=f'Creating file: {file_path}')
        print(f'🛠️  Creating file "{GREEN_TEXT.format(file_path)}"')
        create_file(file_path, charset)

    '''
    Задание 2. Чтение, преобразование и сериализация данных:
    '''

    parse_path = path.abspath('project_root/data/raw')
    proccessed_path = path.abspath('project_root/data/processed')
    for file in os.listdir(parse_path):
        file_path = path.join(parse_path, file)
        encoding = detect_encoding(file_path)
        print(f'File: {file}, encoding: {encoding}')

        with open(file_path, 'r', encoding=encoding) as f:
            data = f.read()
            filename, extention = file.rsplit('.', 1)
            new_filename = path.join(proccessed_path, f'{filename}_processed.{extention}')
            with open(path.join(proccessed_path, new_filename), 'w', encoding=encoding) as f:
                swapped_data = data.swapcase()
                f.write(swapped_data)

                serialize_file_data(
                    filename=file,
                    file_text=data,
                    file_text_proccessed=swapped_data,
                )
                print(f'File {file} processed')
