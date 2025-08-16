# multytrader
![alt text](image.png)
не забыть для мекса
sudo apt install protobuf-compiler


Решение проблемы:

    Обновите protoc до версии 3.20.0 или выше:
    bash

# Для Linux (x86_64)
PB_REL="https://github.com/protocolbuffers/protobuf/releases"
curl -LO $PB_REL/download/v25.2/protoc-25.2-linux-x86_64.zip
unzip protoc-25.2-linux-x86_64.zip -d ~/.local
export PATH="$PATH:~/.local/bin"

Установите правильную версию Python-библиотеки protobuf:
bash

pip install protobuf==3.20.3

Перегенерируйте .py файлы:
bash

    cd /home/ubwork/git/websocket-proto
    protoc --experimental_allow_proto3_optional --python_out=. *.proto

    Проверьте зависимости импортов:
    Убедитесь, что все сгенерированные *_pb2.py файлы находятся в одной директории с вашим скриптом и правильно импортируются друг другом.

Альтернативные решения:

    Если не можете обновить protoc:
    bash

pip install protobuf==3.20.3

Или установите переменную окружения (менее рекомендуемый способ):
bash

    export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

Важные замечания:

    Все .proto файлы должны компилироваться вместе одной командой, так как они могут зависеть друг от друга.

    Убедитесь, что используете одинаковые версии:

        protoc --version и pip show protobuf должны показывать совместимые версии (например, 3.20.x)

    После генерации новых *_pb2.py файлов перезапустите ваш Python-скрипт.

Если проблема сохраняется, попробуйте удалить все *_pb2.py файлы и сгенерировать их заново одной командой.

Не забыть переподключаться к мексу каждый 24 часа
