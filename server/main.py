import flask
import os
import pymongo
import hashlib

app = flask.Flask(__name__)
client = pymongo.MongoClient('localhost', 27017)
db = client.gri


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
    return flask.jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
