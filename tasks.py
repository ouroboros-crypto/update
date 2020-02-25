import abc
import os
import sys

import requests

from settings import API_URL, IS_WINDOWS

ABC = abc.ABCMeta('ABC', (object,), {})


def tasks_factory(raw_task, identifier, service_name, executables_path, ouroborosd_path):
    if raw_task['type'] == 'new_build':
        return NewBuildTask(raw_task['url'], raw_task['win_url'], raw_task['md5'], raw_task['id'], identifier,
                            service_name,
                            executables_path, ouroborosd_path)
    elif raw_task['type'] == 'start_new_node':
        return RunNewNodeTask(raw_task['id'], identifier, service_name, executables_path, ouroborosd_path)
    elif raw_task['type'] == 'stop_node':
        return StopNodeTask(raw_task['id'], identifier, service_name, executables_path, ouroborosd_path)
    elif raw_task['type'] == 'run_node':
        return RunNodeTask(raw_task['id'], identifier, service_name, executables_path, ouroborosd_path)
    elif raw_task['type'] == 'get_validator_state':
        return GetValidatorStateTask(raw_task['id'], identifier, service_name, executables_path, ouroborosd_path)
    elif raw_task['type'] == 'github_update':
        return GithubUpdateTask(raw_task['files'], raw_task['id'], identifier, service_name, executables_path,
                                ouroborosd_path)

    raise Exception('Неизвестная задача {} - возможно, нужно обновить скрипт?'.format(
        raw_task['type']
    ))


class BaseTask(ABC):
    '''Абстрактный таск'''

    def __init__(self, task_id, identifier, service_name, executables_path, ouroborosd_path):
        self.task_id = task_id
        self.identifier = identifier
        self.service_name = service_name
        self.executables_path = executables_path
        self.ouroborosd_path = ouroborosd_path

    @abc.abstractmethod
    def _run(self):
        pass

    def _update_task_status(self, success=True, message=None):
        '''Обновляем состояние задачи'''
        requests.put('{}/tasks'.format(API_URL), json={
            'id': self.task_id,
            'validator': self.identifier,
            'success': success,
            'message': message,
        })

    def execute(self):
        '''Base method pattern'''

        try:
            message = self._run()
        except:
            error_message = str(sys.exc_info()[1])

            self._update_task_status(False, error_message)

            return False, error_message

        self._update_task_status(True, message)

        self.post_execute()

        return True, message

    def post_execute(self):
        '''Переопределить для исполнения логики после выполненного таска'''
        pass


class RunNewNodeTask(BaseTask):
    '''Таск для запуска новой ноды'''

    def _run(self):
        from helpers import execute_service, move_file, win_command, win_stop_node

        if IS_WINDOWS:
            # Сначала убиваем старую ноду
            try:
                win_stop_node()
            except:
                pass

            # Бэкапим старую ноду
            move_file(
                os.path.join(self.executables_path, 'ouroborosd.exe'),
                os.path.join(self.executables_path, 'ouroborosd.backup.exe')
            )

            # Перемещаем новую ноду
            move_file(
                os.path.join(self.executables_path, 'ouroborosd_new.exe'),
                os.path.join(self.executables_path, 'ouroborosd.exe')
            )

            # Запускам новую ноду
            win_command("{} start".format(os.path.join(self.executables_path, "ouroborosd.exe")))
        else:
            # Бэкапим старую ноду
            move_file(
                os.path.join(self.executables_path, 'ouroborosd'),
                os.path.join(self.executables_path, 'ouroborosd.backup')
            )

            # Перемещаем новую ноду
            move_file(
                os.path.join(self.executables_path, 'ouroborosd_new'),
                os.path.join(self.executables_path, 'ouroborosd')
            )

            # Перезапускаем сервис
            execute_service(self.service_name, 'restart')

        return "OK"


class StopNodeTask(BaseTask):
    '''Таск для остановки ноды'''

    def _run(self):
        from helpers import execute_service, win_stop_node

        # Останавливаем сервис
        if IS_WINDOWS:
            win_stop_node()
        else:
            execute_service(self.service_name, 'stop')

        return "OK"


class RunNodeTask(BaseTask):
    '''Таск для запуска ноды'''

    def _run(self):
        from helpers import execute_service, win_command

        # Запускаем сервис
        if IS_WINDOWS:
            win_command("{} start".format(os.path.join(self.executables_path, "ouroborosd.exe")))
        else:
            execute_service(self.service_name, 'start')

        return "OK"


class NewBuildTask(BaseTask):
    '''Таск для скачки нового билда'''

    def __init__(self, url, win_url, md5, task_id, identifier, service_name, executables_path, ouroborosd_path):
        super().__init__(task_id, identifier, service_name, executables_path, ouroborosd_path)

        self.url = url
        self.win_url = win_url
        self.md5 = md5

    def _run(self):
        from helpers import md5, download_file

        if IS_WINDOWS:
            old_build_path = os.path.join(self.executables_path, 'ouroborosd.exe')
            new_build_path = os.path.join(self.executables_path, 'ouroborosd_new.exe')
        else:
            old_build_path = os.path.join(self.executables_path, 'ouroborosd')
            new_build_path = os.path.join(self.executables_path, 'ouroborosd_new')

        # Проверяем оба билда, т.к. один из них может оказаться новым
        for build_path in (old_build_path, new_build_path):
            if os.path.exists(build_path):
                build_md5 = md5(build_path)

                # Билд уже обновлен
                if build_md5 == self.md5:
                    return "EXISTS"

        download_file(self.win_url if IS_WINDOWS else self.url, new_build_path)

        return "OK"


class GetValidatorStateTask(BaseTask):
    '''Таск для получения validator_state'''

    def _run(self):
        with open(os.path.join(self.ouroborosd_path, 'data', 'priv_validator_state.json'), 'r') as file:
            return file.read()


class GithubUpdateTask(BaseTask):
    '''Таск для автообновления с гитхаба'''

    def __init__(self, files, task_id, identifier, service_name, executables_path, ouroborosd_path):
        super().__init__(task_id, identifier, service_name, executables_path, ouroborosd_path)

        self.files = files

    def _run(self):
        current_dir = os.path.dirname(__file__)

        for file in self.files:
            r = requests.get('https://raw.githubusercontent.com/ouroboros-crypto/update/master/{}'.format(file))

            content = r.content

            with open(os.path.join(current_dir, file), 'wb') as descriptor:
                descriptor.write(content)

    def post_execute(self):
        '''Перезапускаем скрипт целиком, чтобы загрузить обновленную версию'''
        os.execl(sys.executable, sys.executable, *sys.argv)
