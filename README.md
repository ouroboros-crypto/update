# Скрипт помощи в обновлении блокчейна

Проект помогает синхронно обновлять блокчейн на множестве нод почти одновременно (макс разница - 5 секунд).

Работа построена в виде задач (tasks), которые приходят с сервера (update.ouroboros-crypto.com), нода исполняет задачу и отправляет результат на сервер.

Пример запуска скрипта:

 python3 update.py --identifier developer_old --service_name node --executables_path /usr/local/bin --ouroborosd_path /home/ec2-user/.ouroborosd test
 
 Где
 
 --identifier - уникальный идентификатор валидатора
 --executables_path - путь до папки, где находится ouroborosd, обычно это /usr/local/bin
 --ouroborosd_path - путь до папки .ouroborosd, обычно это ~/.ouroborosd 
 
 test в конце запускает тестовые сценарии, чтобы убедиться, что все настроено и работает ОК. После test стоит настроить service, который будет запускать скрипт как:
 
 python3 update.py --identifier developer_old --service_name node --executables_path /usr/local/bin --ouroborosd_path /home/ec2-user/.ouroborosd
 
 Без test в конце строки файл будет запрашивать новые задачи каждые 5 секунд.