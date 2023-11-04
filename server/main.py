import flask
import os
import pymongo
import hashlib

# Файл серверной части проекта. Здесь обрабатываются запросы по регистрации пользователей, входу, передаче информации о
# проекте, передаче названий проектов пользователя, сохранению проекта в базе данных.
# Переменные:
# - app - Flask, само веб-приложение
# - client - MongoClient, подключение mongoDB, запущенной локально
# - db - единственная используемая база данных, состоящая из двух коллекций:
# - - users с документами вида
# - - - username - str, имя пользователя
# - - - password - str, хеш пароля по sha256
# - - projects c документами вида
# - - - username - str, имя пользователя, владеющего
# - - - password- str, хеш пароля по sha256
# - - - name - str, имя проекта
# - - - все остальные пары "ключ-значение" согласно нотации, описанной в main.py клиентской части проекта

app = flask.Flask(__name__)
client = pymongo.MongoClient('localhost', 27017)
db = client.gri


# Обработчик запроса на регистрацию пользователя. В запросе передаются имя пользователя и пароль.
# Если пользователь с таким именем есть, возвращается статус usernameOccupied. Иначе регистрация завершается статусом ok
# пользователь с такими данными появляется в базе данных
@app.route('/add_user', methods=['POST'])
def addUser():
    hashGenerator = hashlib.new('sha256')

    data = flask.request.get_json()
    username = data['username']
    password = data['password']

    userCollection = db['users']
    sameUsernameCount = userCollection.count_documents({'username': username})
    if sameUsernameCount != 0:
        return flask.jsonify({'status': 'usernameOccupied'})

    hashGenerator.update(bytes(password, 'utf-8'))
    userCollection.insert_one({'username': username, 'password': hashGenerator.hexdigest()})

    return flask.jsonify({'status': 'ok'})


# Обработчик входа пользователя (фактически проверка на верность данных). В запросе передаются имя пользователя и пароль
# Если пользователя с таким именем нет, возвращается статус incorrectUsername, если пользователь есть, но пароль неверен
# возвращается статус incorrectPassword. Иначе данные пользователя корректны => их можно использовать для получения
# проектов, возвращается статус ok
@app.route('/login', methods=['POST'])
def login():
    hashGenerator = hashlib.new('sha256')

    data = flask.request.get_json()
    username = data['username']
    password = data['password']

    userCollection = db['users']
    sameUsernameCount = userCollection.count_documents({'username': username})
    if sameUsernameCount == 0:
        return flask.jsonify({'status': 'incorrectUsername'})

    user = userCollection.find_one({'username': username})
    hashGenerator.update(bytes(password, 'utf-8'))
    if user['password'] != hashGenerator.hexdigest():
        return flask.jsonify({'status': 'incorrectPassword'})

    return flask.jsonify({'status': 'ok'})


# Обработчик запроса на получение имён проектов пользователя. В запросе передаются имя пользователя и пароль.
# Их корректность проверяется аналогично обработчику login, ответы сервера идентичны, но в случае успеха по ключу data
# возвращается также список имён проектов
@app.route('/get_project_names', methods=['POST'])
def getProjectNames():
    hashGenerator = hashlib.new('sha256')

    data = flask.request.get_json()
    username = data['username']
    password = data['password']

    userCollection = db['users']
    sameUsernameCount = userCollection.count_documents({'username': username})
    if sameUsernameCount == 0:
        return flask.jsonify({'status': 'incorrectUsername'})

    user = userCollection.find_one({'username': username})
    hashGenerator.update(bytes(password, 'utf-8'))
    if user['password'] != hashGenerator.hexdigest():
        return flask.jsonify({'status': 'incorrectPassword'})

    projectCollection = db['projects']
    projects = [i['name'] for i in projectCollection.find({'username': username})]
    return flask.jsonify({'status': 'ok', 'data': projects})


# Обработчик запроса на получение проекта. В запросе передаются имя пользователя, пароль и имя проекта.
# Если пользователя с таким именем нет, возвращается статус incorrectUsername, если пользователь есть, но пароль неверен
# возвращается статус incorrectPassword, иначе возвращается статус ok и содержимое самого проекта
@app.route('/get_project', methods=['POST'])
def getProject():
    hashGenerator = hashlib.new('sha256')

    data = flask.request.get_json()
    username = data['username']
    password = data['password']
    name = data['name']

    userCollection = db['users']
    sameUsernameCount = userCollection.count_documents({'username': username})
    if sameUsernameCount == 0:
        return flask.jsonify({'status': 'incorrectUsername'})

    user = userCollection.find_one({'username': username})
    hashGenerator.update(bytes(password, 'utf-8'))
    if user['password'] != hashGenerator.hexdigest():
        return flask.jsonify({'status': 'incorrectPassword'})

    projectCollection = db['projects']
    result = projectCollection.find_one({'username': username, 'name': name})
    result.pop('_id', None)
    result['status'] = 'ok'
    return flask.jsonify(result)


# Обработчик запроса на сохранение проекта. В запросе передаются имя пользователя, пароль и все данные о проекте.
# Если данные пользователя корректны (проверка аналогична обработчику login), проект сохраняется (с перезаписью, если
# проект с таким именем у пользователя уже есть)
@app.route('/save_project', methods=['POST'])
def saveProject():
    hashGenerator = hashlib.new('sha256')

    data = flask.request.get_json()
    username = data['username']
    password = data['password']
    name = data['name']

    userCollection = db['users']
    sameUsernameCount = userCollection.count_documents({'username': username})
    if sameUsernameCount == 0:
        return flask.jsonify({'status': 'incorrectUsername'})

    user = userCollection.find_one({'username': username})
    hashGenerator.update(bytes(password, 'utf-8'))
    if user['password'] != hashGenerator.hexdigest():
        return flask.jsonify({'status': 'incorrectPassword'})

    data.pop('password', None)

    projectCollection = db['projects']
    matchingProjectsCount = projectCollection.count_documents({'username': username, 'name': name})

    if matchingProjectsCount != 0:
        projectCollection.delete_one({'username': username, 'name': name})
    projectCollection.insert_one(data)
    return flask.jsonify({'status': 'ok'})


# Обработчик запроса на изменение пароля. В запросе передаются имя пользователя, старый и новый пароли.
# Если данные пользователя корректны (проверка аналогична обработчику login), пароль меняется как у пользователя, так и
# у всех его проектов
@app.route('/change_password', methods=['POST'])
def changePassword():
    hashGenerator = hashlib.new('sha256')

    data = flask.request.get_json()
    username = data['username']
    oldPassword = data['oldPassword']
    newPassword = data['newPassword']

    userCollection = db['users']
    sameUsernameCount = userCollection.count_documents({'username': username})
    if sameUsernameCount == 0:
        return flask.jsonify({'status': 'incorrectUsername'})

    user = userCollection.find_one({'username': username})
    hashGenerator.update(bytes(oldPassword, 'utf-8'))
    if user['password'] != hashGenerator.hexdigest():
        return flask.jsonify({'status': 'incorrectPassword'})

    hashGenerator = hashlib.new('sha256')
    hashGenerator.update(bytes(newPassword, 'utf-8'))
    userCollection.find_one_and_replace({'username': username}, {'username': username,
                                                                 'password': hashGenerator.hexdigest()})

    projectCollection = db['projects']
    projectCollection.update_many({'username': username}, {'$set': {'password': hashGenerator.hexdigest()}})

    return flask.jsonify({'status': 'ok'})


# Запуск веб-приложения
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
