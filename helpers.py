import hashlib
import os
import subprocess
import requests


def fetch_tasks(identifier):
    from settings import API_URL
    '''Возвращает список задач'''
    r = requests.get('{}/tasks?validator={}'.format(API_URL, identifier))

    return r.json()['tasks']


def download_file(url, path):
    '''Скачиваем и сохраняем файл'''
    content = requests.get(url).content

    with open(path, 'wb') as file:
        file.write(content)

    # Чтобы у всех был доступ к файлу
    os.chmod(path, 0o777)


def move_file(old_path, new_path) -> bool:
    '''Перемещаем файл, если он существует'''
    if os.path.exists(old_path):
        os.rename(old_path, new_path)

        return True

    return False


def md5(path):
    '''Генерирует и возвращает хэш файла'''
    hash_md5 = hashlib.md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def win_command(command):
    '''Исполняет команду в окружении windows, нужно тестировать'''
    os.system(command)


def execute_service(service, command):
    '''Исполняет service команду'''
    result = subprocess.check_output(["service", service, command])

    return result
