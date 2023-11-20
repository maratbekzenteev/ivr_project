# В этом файле представлены юнит-тесты серверной части проекта

import random, requests

SERVER_ADDRESS = 'http://127.0.0.1:5000/'
username = str(random.randint(1, 10**6))
password = str(random.randint(1, 10**6))


# Тест 1. Регистрация

# Регистрация пользователя с заведомо незанятым логином
response = requests.post(SERVER_ADDRESS + 'add_user', json={'username': username, 'password': password}).json()
print(response)  # status: ok

# Попытка регистрации пользоветеля с заведомо занятым логином
response = requests.post(SERVER_ADDRESS + 'add_user', json={'username': 'username', 'password': 'password'}).json()
print(response)  # status: usernameOccupied


# Тест 2. Авторизация

# Авторизация пользователя с известными (заведомо верными) данными
response = requests.post(SERVER_ADDRESS + 'login', json={'username': username, 'password': password}).json()
print(response)  # status: ok

# Попытка авторизации пользователя с заведомо неверным паролем
response = requests.post(SERVER_ADDRESS + 'login', json={'username': username, 'password': ''}).json()
print(response)  # status: incorrectPassword

# Попытка авторизации пользователя с заведомо неверным именем
response = requests.post(SERVER_ADDRESS + 'login', json={'username': '1' * 40, 'password': password}).json()
print(response)  # status: incorrectUsername


# Тест 3. Смена пароля

# Попытка смены пароля с заведомо неверным именем пользователя
response = requests.post(SERVER_ADDRESS + 'change_password', json={'username': '1' * 40, 'oldPassword': '',
                                                                   'newPassword': ''}).json()
print(response)  # status: incorrectUsername

# Попытка смены пароля с заведомо неверным старым паролем
response = requests.post(SERVER_ADDRESS + 'change_password', json={'username': username, 'oldPassword': '',
                                                                   'newPassword': ''}).json()
print(response)  # status: incorrectPassword

# Смена пароля пользователя с корректными входными данными
response = requests.post(SERVER_ADDRESS + 'change_password', json={'username': username, 'oldPassword': password,
                                                                   'newPassword': ''}).json()
print(response)  # status: ok
