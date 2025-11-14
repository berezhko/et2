# acr

Проект предназначен для автоматизации построения кабельного журнала (КЖ), схем подключения кабелей, спецификации к проекту а также создания подготовке документации по проектируемым шкафам в электротехнических проектах.

## Основные возможности в части создания схем вторичной коммутации

- Генерация кабельных журналов (КЖ)
- Автоматизация построения схем подключения кабелей
- Формирование спецификации к проекту
- Заполнения листа общих данных
- Добавления на схемы имена кабелей в блоке с информацией о кабеле
- Добавдения на схемы номера листов в ссылочных блоках

## Основные возможности в части создания сборочных схем на проектируемые шкафы

- Подготовка блоков устройств и их контактов
- Подготовка блоков клеммников и их контактов
- Построение схемы соединения проводок
- Построение схемы подключения проводок
- Заполнение спецификации на проектируемый шкаф

## Структура проекта

- **autocad-lisp/** — скрипты и утилиты для AutoCAD
- **config/** — конфигурационные файлы
- **data/** — исходные и промежуточные данные
- **notebook/** — Jupyter ноутбуки для анализа и визуализации
- **src/** — основной исходный код проекта
- **requirements.txt** — список зависимостей
- **requirements-dev.txt** — зависимости для разработки
- **.flake8**, **mypy.ini** — настройки для проверки кода

## Быстрый старт

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/berezhko/acr.git autocad
   ```
2. Установите зависимости:
   ```bash
   python -m venv --prompt autocad autocad/.venv
   cd autocad
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
   Либо для разработки:
   ```bash
   pip install -r requirements-dev.txt
   nbdime config-git --enable --global
   ```
3. Используйте Jupyter Notebook для генерации отчётов и схем:
   ```bash
   export PYTHONPATH="/home/ivan/autocad/:$PYTHONPATH"
   jupyter lab --port 8888 --no-browser --ip="0.0.0.0"
   ```
4. Для запуска через systemd используйте следующий юнит:
   ```bash
   ~ $ cat /etc/systemd/system/autocad-lab.service
   [Unit]
   Description=${NAME}
    
   [Service]
   Type=simple
   ExecStart=/bin/autocad-lab.sh
   WorkingDirectory=/home/ivan/autocad
   User=ivan
   Group=ivan
   Restart=on-failure
   RestartSec=5s
    
   [Install]
   WantedBy=multi-user.target
   ```
   И скрипт запуска:
   ```bash
   ~ $ cat /bin/autocad-lab.sh
   #!/bin/bash

   . /home/ivan/autocad/.venv/bin/activate

   export PYTHONPATH="/home/ivan/autocad/:$PYTHONPATH"
   jupyter lab --port 8888 --no-browser --ip="0.0.0.0"

   deactivate
   ```

   ```bash
   ~ $ sudo systemctl start autocad-lab.service
   ```

## Вклад и поддержка

Для обсуждения и решения вопросов используйте раздел Issues.
