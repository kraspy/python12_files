import os
import json
import shutil
import zipfile
import logging
from os import path
from datetime import datetime
import charset_normalizer
import jsonschema
from jsonschema import validate

# Define constants for directory paths
PROJECT_ROOT = path.abspath('project_root')
DATA_DIR = path.join(PROJECT_ROOT, 'data')
RAW_DIR = path.join(DATA_DIR, 'raw')
PROCESSED_DIR = path.join(DATA_DIR, 'processed')
LOGS_DIR = path.join(PROJECT_ROOT, 'logs')
BACKUPS_DIR = path.join(PROJECT_ROOT, 'backups')
RESTORE_DIR = path.join(PROJECT_ROOT, 'data_restored')
OUTPUT_DIR = path.join(PROJECT_ROOT, 'output')


def setup_logging():
    """
    Настройки логирования
    """
    if not path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    log_file = path.join(LOGS_DIR, 'log.txt')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()],
    )


def create_project_structure():
    """
    Создание файловой структуры
    """
    directories = [DATA_DIR, RAW_DIR, PROCESSED_DIR, LOGS_DIR, BACKUPS_DIR, OUTPUT_DIR]
    for dir_path in directories:
        if not path.exists(dir_path):
            os.makedirs(dir_path)
            logging.info(f'Создана директория: {dir_path}')
        else:
            logging.info(f'Директория уже существует: {dir_path}')


def create_sample_files():
    """
    Создание файлов в директории raw
    """
    contents = [
        ('Привет мир!', 'utf-8'),
        ('Привет мир!', 'windows-1251'),
        ('Hello, world!', 'iso-8859-1'),
    ]
    for idx, (text, encoding) in enumerate(contents):
        filename = f'file_{idx}.txt'
        file_path = path.join(RAW_DIR, filename)
        if not path.exists(file_path):
            try:
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(text)
                logging.info(f'Создан файл: {file_path} с кодировкой {encoding}')
            except Exception as e:
                logging.error(f'Ошибка создания файла {file_path}: {e}')
        else:
            logging.info(f'Файл уже существует: {file_path}')


def detect_file_encoding(file_path):
    """
    Определение кодировки файла
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = charset_normalizer.detect(raw_data)
        encoding = result['encoding']
    return encoding


def process_files():
    """
    Чтение, преобразование и сериализация данных из файлов raw в processed
    """
    data_list = []
    for filename in os.listdir(RAW_DIR):
        raw_file_path = path.join(RAW_DIR, filename)
        encoding = detect_file_encoding(raw_file_path)
        if encoding is None:
            logging.warning(f'Не удалось определить кодировку для файла {filename}...')
            continue
        logging.info(f'Преобразование файла: {filename}, Кодировка: {encoding}')
        with open(raw_file_path, 'r', encoding=encoding) as f:
            original_text = f.read()
        processed_text = original_text.swapcase()
        processed_filename = f'{path.splitext(filename)[0]}_processed{path.splitext(filename)[1]}'
        processed_file_path = path.join(PROCESSED_DIR, processed_filename)
        with open(processed_file_path, 'w', encoding=encoding) as f:
            f.write(processed_text)
        logging.info(f'Преобразованный файл сохранен: {processed_file_path}')
        file_info = {
            'Имя файла': filename,
            'Исходный текст': original_text,
            'Преобразованный текст': processed_text,
            'Размер файла в байтах': path.getsize(raw_file_path),
            'Дата последнего изменения файла': datetime.fromtimestamp(path.getmtime(raw_file_path)).strftime(
                '%Y-%m-%d %H:%M:%S'
            ),
        }
        data_list.append(file_info)
    json_file_path = path.join(OUTPUT_DIR, 'processed_data.json')
    with open(json_file_path, 'w', encoding=encoding) as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    logging.info(f'Данные сохранены в файл JSON: {json_file_path}')


def create_backup():
    """
    Создание резервной копии
    """
    date_str = datetime.now().strftime('%Y%m%d')
    backup_filename = f'backup_{date_str}.zip'
    backup_filepath = path.join(BACKUPS_DIR, backup_filename)
    with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for foldername, subfolders, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                file_path = path.join(foldername, filename)
                arcname = path.relpath(file_path, PROJECT_ROOT)
                backup_zip.write(file_path, arcname=arcname)
    logging.info(f'Резервная копия создана: {backup_filepath}')


def restore_backup(backup_filename):
    """
    Восстановление данных из резервной копии
    """
    backup_filepath = path.join(BACKUPS_DIR, backup_filename)
    restore_dir = RESTORE_DIR
    temp_backup_dir = path.join(BACKUPS_DIR, 'temp_backup_before_restore')
    if not path.exists(restore_dir):
        os.mkdir(restore_dir)
    with zipfile.ZipFile(backup_filepath, 'r') as backup_zip:
        backup_zip.extractall(restore_dir)
    logging.info(f'Данные восстановлены из резервной копии {backup_filepath} в {restore_dir}')
    if path.exists(temp_backup_dir):
        shutil.rmtree(temp_backup_dir)


class FileInfo:
    """
    Класс для хранения информации о файле
    """

    def __init__(self, file_name, file_path, file_size, date_created, date_modified):
        self.file_name = file_name
        self.file_path = file_path
        self.file_size = file_size
        self.date_created = date_created
        self.date_modified = date_modified

    def to_dict(self):
        return {
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'date_created': self.date_created.isoformat(),
            'date_modified': self.date_modified.isoformat(),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            file_name=data['file_name'],
            file_path=data['file_path'],
            file_size=data['file_size'],
            date_created=datetime.fromisoformat(data['date_created']),
            date_modified=datetime.fromisoformat(data['date_modified']),
        )


def collect_file_info():
    """
    Сбор информации о файлах из processed и сериализация
    """
    file_info_list = []
    for filename in os.listdir(PROCESSED_DIR):
        file_path = path.join(PROCESSED_DIR, filename)
        file_stat = os.stat(file_path)
        file_info = FileInfo(
            file_name=filename,
            file_path=file_path,
            file_size=file_stat.st_size,
            date_created=datetime.fromtimestamp(file_stat.st_ctime),
            date_modified=datetime.fromtimestamp(file_stat.st_mtime),
        )
        file_info_list.append(file_info)
    serialized_data_path = path.join(OUTPUT_DIR, 'file_info.json')
    with open(serialized_data_path, 'w', encoding='utf-8') as f:
        json.dump([fi.to_dict() for fi in file_info_list], f, ensure_ascii=False, indent=4)
    logging.info(f'Инофрмация о файлах сериализована в {serialized_data_path}')
    with open(serialized_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    deserialized_file_info_list = [FileInfo.from_dict(item) for item in data]
    logging.info('Информация о файлах десериализована успешно')
    return deserialized_file_info_list


def validate_json_schema():
    """
    Валидация данных JSON согласно схеме
    """
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "file_name": {"type": "string"},
                "file_path": {"type": "string"},
                "file_size": {"type": "number"},
                "date_created": {"type": "string", "format": "date-time"},
                "date_modified": {"type": "string", "format": "date-time"},
            },
            "required": ["file_name", "file_path", "file_size", "date_created", "date_modified"],
        },
    }
    serialized_data_path = path.join(OUTPUT_DIR, 'file_info.json')
    with open(serialized_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    try:
        validate(instance=data, schema=schema)
        logging.info('JSON-данные соответствуют схеме.')
    except jsonschema.ValidationError as e:
        logging.error(f'Ошибка валидации данных JSON: {e}')


def create_txt_report(text):
    """
    Создание отчёта в формате txt
    """

    report_file_path = path.join(OUTPUT_DIR, 'report.txt')
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    logging.info(f'Отчет сгенерирован в {report_file_path}')


def main():
    setup_logging()
    logging.info('Начало выполнения скрипта.')

    # Задание 1: Управление проектной структурой и файловой системой
    logging.info('Задание 1: Управление проектной структурой и файловой системой.')
    create_project_structure()
    create_sample_files()

    # Задание 2: Чтение, преобразование и сериализация данных
    logging.info('Задание 2: Чтение, преобразование и сериализация данных.')
    process_files()

    # Задание 3: Работа с резервными копиями и восстановлением данных
    logging.info('Задание 3: Работа с резервными копиями и восстановлением данных.')
    create_backup()
    backup_filename = f'backup_{datetime.now().strftime("%Y%m%d")}.zip'
    restore_backup(backup_filename)

    # Задание 4: Дополнительные задачи с сериализацией и JSON Schema
    logging.info('Задание 4: Дополнительные задачи с сериализацией и JSON Schema.')
    collect_file_info()
    validate_json_schema()

    # Задание 5: Отчёт и анализ проделанной работы
    logging.info('Задание 5: Отчёт и анализ проделанной работы.')
    report_text = '''
    # Отчет и анализ проделанной работы
    ## Возникшие трудности
    - Трудностей не возникло

    ## Время, затраченное на выполнение каждого задания
    - Примерное время выполнения каждого задания: 2 часа

    ## Выводы о проделанной работе и предложенные улучшения
    - Получены полезные навыки и знания
    '''
    create_txt_report(report_text)
    logging.info('Скрипт выполнен.')


if __name__ == '__main__':
    main()
