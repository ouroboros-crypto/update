import os
import argparse
import sys
import time

from helpers import fetch_tasks
from tasks import tasks_factory


def __validate_args(identifier, service_name, executables_path, ouroborosd_path):
    from settings import IS_WINDOWS
    from helpers import execute_service

    if not os.path.exists(os.path.join(executables_path, 'ouroborosd')) and not os.path.exists(
            os.path.join(executables_path, 'ouroborosd.exe')):
        raise Exception('The directoy {} doesn\'t exist or there is no ouroborosd inside'.format(
            executables_path
        ))

    if not os.path.exists(os.path.join(ouroborosd_path, 'data', 'priv_validator_state.json')):
        raise Exception('The directory {} does not exist or there is no ouroborosd configuration files inside'.format(
            ouroborosd_path
        ))

    if not IS_WINDOWS:
        try:
            execute_service(service_name, 'status')
        except:
            raise Exception('The {} service is stopped or does not exist'.format(
                service_name
            ))


def test(identifier, service_name, executables_path, ouroborosd_path):
    '''Тестируем скрипт и параметры'''

    test_tasks = (
        {
            'id': 123,
            'type': 'new_build',
            'url': 'https://github.com/ouroboros-crypto/executables/raw/master/build/linux.64bit/ouroborosd',
            'win_url': 'https://github.com/ouroboros-crypto/executables/raw/master/build/windows.64bit/ouroborosd.exe',
            'md5': 'ac90c2ab0e3bb8825b44ac4a3b9099df',
        }, {
            'id': 456,
            'type': 'get_validator_state'
        },
    )

    for raw_task in test_tasks:
        task = tasks_factory(raw_task, identifier, service_name, executables_path, ouroborosd_path)
        success, message = task.execute()

        print('The {} task ended up with the {} status'.format(
            raw_task['type'], success
        ))


def update(identifier, service_name, executables_path, ouroborosd_path):
    '''Цикл апдейта'''
    print('The script is running')

    while True:
        try:
            tasks = fetch_tasks(identifier)

            for raw_task in tasks:
                task = tasks_factory(raw_task, identifier, service_name, executables_path, ouroborosd_path)

                success, message = task.execute()

                print('The {} task ended up with the {} status'.format(
                    raw_task['type'], success
                ))
        except:
            error_message = str(sys.exc_info()[1])

            print("Error message while processing the tasks: {}".format(error_message))

        time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Скрипт для помощи с апгрейдом блокчейна')

    parser.add_argument("--identifier", required=True, type=str, help="Уникальное имя валидатора,")
    parser.add_argument("--service_name", required=True, type=str, help="Имя сервиса ouroborosd")
    parser.add_argument("--executables_path", required=True, type=str,
                        help="Путь до папки с ouroborosd, например /usr/local/bin")
    parser.add_argument("--ouroborosd_path", required=True, type=str,
                        help="Путь до папки .ouroborosd с конфигурацией, например /home/ubuntu/.ouroborosd")
    parser.add_argument('command', nargs='?', type=str, default='run',
                        help='Команда для исполнения, может быть test или run')

    args = parser.parse_args()

    # Валидируем аргументы
    __validate_args(args.identifier, args.service_name, args.executables_path, args.ouroborosd_path)

    if args.command == 'test':
        test(args.identifier, args.service_name, args.executables_path, args.ouroborosd_path)
    else:
        update(args.identifier, args.service_name, args.executables_path, args.ouroborosd_path)
