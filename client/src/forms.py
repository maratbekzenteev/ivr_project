from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel, QListWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, Qt
from client.src.signals import FormSignals
import requests

# В этом файле описаны все виды форм, используемые для взаимодействия пользователя с сервером ("облаком")
# для регистрации, входа, смены пароля, открытия проекта


# Обобщённый класс формы, содержащий атрибуты, характерные для унаследованных от него форм. Набор сигналов - FormSignals
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания графических элементов внутри формы
# - self.usernameField - QLineEdit, поле ввода имени пользователя
# - self.passwordField - QLineEdit, поле ввода (текущего) пароля (не скрыт только последний введённый символ)
# - self.newPasswordField - QLineEdit, поле ввода нового пароля (не скрыт только последний введённый символ)
# - self.message - QLabel, сообщение о текущем состоянии заполняемой формы (неверное имя пользователя, вход выполнен,..)
# Атрибуты:
# - self.address - str, адрес сервера, к которому подключается программа
# - self.messageTextFromStatus - dict, возвращает сообщение для поля self.message по статусу отправленного запроса
class AbstractForm(QWidget):
    # Инициализация графических элементов и атрибутов формы. title - заголовок окна формы
    def __init__(self, address: str, title: str) -> None:
        super().__init__()

        self.signals = FormSignals()

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowTitle(title)
        self.address = address

        self.messageTextFromStatus = {
            'ok': 'Операция выполнена успешно',
            'incorrectUsername': 'Неверное имя пользователя',
            'incorrectPassword': 'Введён неверный пароль',
            'usernameOccupied': 'Имя пользователя занято'
        }

        self.usernameField = QLineEdit()
        self.passwordField = QLineEdit()
        self.passwordField.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.newPasswordField = QLineEdit()
        self.newPasswordField.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.message = QLabel()

        self.layout.addWidget(QLabel('Имя пользователя'), 0, 0)
        self.layout.addWidget(self.usernameField, 0, 1)
        self.layout.addWidget(QLabel('Пароль'), 1, 0)
        self.layout.addWidget(self.passwordField, 1, 1)

    # Обновление отображаемого состояния формы по статусу последнего запроса, передаваемому в аргументе text
    def updateMessage(self, text: str) -> None:
        self.message.setText(self.messageTextFromStatus[text])


# Класс формы для регистрации и входа. Набор сигналов - FormSignals
# Графические элементы:
# - self.loginButton - QPushButton, кнопка совершения попытки входа (уже зарегистрированного пользователя)
# - self.signupButton - QPushButton, кнопка совершения попытки регистрации. В случае успеха вход проходит автоматически
# - self.changePasswordButton - QPushButton, кнопка перехода в форму смены пароля
# - и все графические элементы дополняемого класса AbstractForm (self.newPasswordButton скрыта за ненадобностью)
# Атрибуты:
# - все атрибуты дополняемого класса AbstractForm
class LoginForm(AbstractForm):
    # Инициализация графических элементов и атрибутов формы, подключение сигналов к слотам
    def __init__(self, address: str) -> None:
        super().__init__(address, 'Вход в аккаунт')
        self.messageTextFromStatus['ok'] = 'Вход выполнен успешно'
        self.loginButton = QPushButton('Войти')
        self.loginButton.clicked.connect(self.submitRequest)
        self.signupButton = QPushButton('Зарегистрироваться')
        self.signupButton.clicked.connect(self.submitRequest)
        self.changePasswordButton = QPushButton('Изменить пароль')
        self.changePasswordButton.clicked.connect(self.submitRequest)

        self.layout.addWidget(self.loginButton, 2, 0)
        self.layout.addWidget(self.signupButton, 2, 1)
        self.layout.addWidget(self.changePasswordButton, 3, 0, 1, 2, Qt.AlignJustify)
        self.layout.addWidget(self.message, 4, 0, 1, 2, Qt.AlignJustify)

    # Функция обновления извне (родительским классом). Вызывается при успешном входе (так как он мог пройти и через
    # другую форму ChangePasswordForm)
    def setLoginData(self, username, password):
        self.usernameField.setText(username)
        self.passwordField.setText(password)

    # Функция отправки запроса серверу и попытки регистрации/входа(последнее выбирается в зависимости от нажатой кнопки)
    # Слот сигналов self.loginButton.clicked и self.signupButton.clicked. В случае успеха сообщает сигнал
    # signals.requestAccepted c данными пользователя (они понадобятся форме ProjectOpenForm при отправке запросов
    # на получение списка имён проектов пользователя и при сохранении/открытии проектов)
    @pyqtSlot()
    def submitRequest(self):
        if self.sender().text() == 'Изменить пароль':
            self.signals.openForm.emit()
            return

        if self.sender().text() == 'Войти':
            response = requests.post(self.address + 'login', data={'username': self.usernameField.text(),
                                                                   'password': self.passwordField.text()}).json()
        else:
            response = requests.post(self.address + 'add_user', data={'username': self.usernameField.text(),
                                                                      'password': self.passwordField.text()}).json()

        self.updateMessage(response['status'])
        if response['status'] == 'ok':
            self.signals.requestAccepted.emit(self.usernameField.text(), self.passwordField.text(), dict())


# Класс формы смены пароля. Для этого пользователю нужны имя пользователя и текущий пароль. Набор сигналов - FormSignals
# Графические элементы:
# - self.changePasswordButton - QPushButton, кнопка совершения попытки смены пароля
# - и все графические элементы дополняемого класса AbstractForm
# Атрибуты:
# - все атрибуты дополняемого класса AbstractForm
class ChangePasswordForm(AbstractForm):
    # Инициализация графических элементов и атрибутов формы, подключение сигналов к слотам
    def __init__(self, address: str):
        super().__init__(address, 'Изменение пароля')
        self.messageTextFromStatus['ok'] = 'Пароль успешно изменён'
        self.changePasswordButton = QPushButton('Изменить пароль и войти')
        self.changePasswordButton.clicked.connect(self.submitRequest)

        self.layout.itemAtPosition(1, 0).widget().setText('Старый пароль')
        self.layout.addWidget(QLabel('Новый пароль'), 2, 0)
        self.layout.addWidget(self.newPasswordField, 2, 1)
        self.layout.addWidget(self.changePasswordButton, 3, 0, 1, 2, Qt.AlignJustify)
        self.layout.addWidget(self.message, 4, 0, 1, 2, Qt.AlignJustify)

    # Функция отправки серверу запроса на смену пароля. В случае успеха сообщает сигнал
    # signals.requestAccepted c данными пользователя (они понадобятся форме ProjectOpenForm при отправке запросов
    # на получение списка имён проектов пользователя и при сохранении/открытии проектов) (фактически совершается вход)
    @pyqtSlot()
    def submitRequest(self):
        response = requests.post(self.address + 'change_password',
                                 data={'username': self.usernameField.text(),
                                       'oldPassword': self.passwordField.text(),
                                       'newPassword': self.newPasswordField.text()}).json()
        self.updateMessage(response['status'])
        if response['status'] == 'ok':
            self.signals.requestAccepted.emit(self.usernameField.text(), self.passwordField.text(), dict())


# Класс формы выбора открываемого проекта пользователем. (!)Не унаследован от AbstractForm. Набор сигналов - FormSignals
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания графических элементов формы
# - self.projectList - QListWidget, список проектов пользователя. Пуст, если вход не выполнен или сервер посчитал
# - - отправленный запрос некорректным (например, когда введён неверный пароль)
# - self.openButton - QPushButton, кнопка открытия выбранного в списке проекта. Если проект не выбран, ничего не делает
# Атрибуты:
# - self.address - str, адрес сервера, к которому подключается программа
# - self.username - str, имя пользователся (хранится, чтобы не спрашивать пользователя при каждом открытии проекта)
# - self.password - str, пароль (хранится, чтобы не спрашивать пользователя при каждом открытии проекта)
class ProjectOpenForm(QWidget):
    # Инициализация графических элементов и атрибутов класса, подключение сигналов к слотам
    def __init__(self, address: str) -> None:
        super().__init__()

        self.signals = FormSignals()

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowTitle('Открыть проект из облака')
        self.address = address
        self.username = ''
        self.password = ''

        self.openButton = QPushButton('Открыть')
        self.openButton.clicked.connect(self.openSelectedProject)
        self.projectList = QListWidget()

        self.layout.addWidget(self.projectList, 0, 0)
        self.layout.addWidget(self.openButton, 1, 0)

    # Обновление атрибутов данных пользователя извне (при успешном входе через формы входа/регистрации или смены пароля)
    # Также запускает обновление графики, т.е. списка проектов
    def setLoginData(self, username: str, password: str) -> None:
        self.username, self.password = username, password
        self.updateProjectNames()

    # Обновление списка проектов (чтобы пользователь видел, какие его проекты доступны для открытия с сервера)
    # В случае неуспеха (например, сервер посчитал пароль пользователя неверным) список остается пустым, а пользователь
    # уведомляется о причине неуспеха в модальном диалоге
    def updateProjectNames(self) -> None:
        self.projectList.clear()
        response = requests.post(self.address + 'get_project_names', data={'username': self.username,
                                                                           'password': self.password}).json()
        if response['status'] == 'incorrectUsername':
            QMessageBox(QMessageBox.Information, 'Открытие проекта',
                        'Введено неверное имя пользователя.', QMessageBox.Ok).exec()
            return
        if response['status'] == 'incorrectPassword':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Введён неверный пароль.', QMessageBox.Ok).exec()
            return
        if response['status'] != 'ok':
            return
        for name in response['data']:
            self.projectList.addItem(name)

    # Слот сигнала self.openButton.clicked. Отправляет серверу запрос на открытие проекта определенного пользователя
    # с определенным названием проекта. В случае успеха сообщает сигнал signals.requestAccepted с данными проекта и
    # пользователя. В случае неуспеха уведомляет пользователя о его причине через модальный диалог
    @pyqtSlot()
    def openSelectedProject(self) -> None:
        if self.projectList.currentRow == -1:
            return

        response = requests.post(self.address + 'get_project',
                                 data={'username': self.username,
                                       'password': self.password,
                                       'name': self.projectList.currentItem().text().rstrip()}).json()
        if response['status'] == 'incorrectUsername':
            QMessageBox(QMessageBox.Information, 'Открытие проекта',
                        'Введено неверное имя пользователя.', QMessageBox.Ok).exec()
            return
        if response['status'] == 'incorrectPassword':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Введён неверный пароль.', QMessageBox.Ok).exec()
            return
        if response['status'] != 'ok':
            return
        self.signals.requestAccepted.emit(self.username, self.password, response['data'])
