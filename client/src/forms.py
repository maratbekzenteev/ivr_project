from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel, QListWidget
from PyQt5.QtCore import pyqtSlot, Qt
from client.src.signals import FormSignals
import requests


class AbstractForm(QWidget):
    def __init__(self, address, title):
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

    def updateMessage(self, text):
        self.message.setText(self.messageTextFromStatus[text])


class LoginForm(AbstractForm):
    def __init__(self, address):
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
        self.layout.addWidget(self.changePasswordButton, 3, 0, 1, 2, Qt.AlignLeft)
        self.layout.addWidget(self.message, 4, 0, 1, 2, Qt.AlignLeft)

    def setLoginData(self, username, password):
        self.usernameField.setText(username)
        self.passwordField.setText(password)

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


class ChangePasswordForm(AbstractForm):
    def __init__(self, address):
        super().__init__(address, 'Изменение пароля')
        self.messageTextFromStatus['ok'] = 'Пароль успешно изменён'
        self.changePasswordButton = QPushButton('Изменить пароль и войти')
        self.changePasswordButton.clicked.connect(self.submitRequest)

        self.layout.itemAtPosition(1, 0).widget().setText('Старый пароль')
        self.layout.addWidget(QLabel('Новый пароль'), 2, 0)
        self.layout.addWidget(self.newPasswordField, 2, 1)
        self.layout.addWidget(self.changePasswordButton, 3, 0, 1, 2, Qt.AlignLeft)
        self.layout.addWidget(self.message, 4, 0, 1, 2, Qt.AlignLeft)

    @pyqtSlot()
    def submitRequest(self):
        response = requests.post(self.address + 'change_password',
                                 data={'username': self.usernameField.text(),
                                       'oldPassword': self.passwordField.text(),
                                       'newPassword': self.newPasswordField.text()}).json()
        self.updateMessage(response['status'])
        if response['status'] == 'ok':
            self.signals.requestAccepted.emit(self.usernameField.text(), self.passwordField.text(), dict())


class ProjectOpenForm(QWidget):
    def __init__(self, address):
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

    def setLoginData(self, username, password):
        self.username, self.password = username, password

    def updateProjectNames(self):
        self.projectList.clear()
        response = requests.post(self.address + 'get_project_names', data={'username': self.username,
                                                                           'password': self.password}).json()
        if response['status'] != 'ok':
            return
        for name in response['data']:
            self.projectList.addItem(name)

    @pyqtSlot()
    def openSelectedProject(self):
        if self.projectList.currentRow == -1:
            return

        response = requests.post(self.address + 'get_project',
                                 data={'username': self.username,
                                       'password': self.password,
                                       'name': self.projectList.currentItem().text().rstrip()}).json()
        if response['status'] != 'ok':
            return
        self.signals.requestAccepted.emit(self.username, self.password, response['data'])
