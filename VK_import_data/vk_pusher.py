import vk_api
from vk_api.utils import get_random_id
from vk_api.exceptions import ApiError
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QTextEdit,
                             QPushButton, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QCheckBox)
import sys


# Функция для загрузки изображения на сервер ВК
def upload_image_to_vk(vk, token, owner_id):
    try:
        upload_server = vk.photos.getWallUploadServer(group_id=abs(owner_id) if owner_id < 0 else None)
        image_path, _ = QFileDialog.getOpenFileName(None, "Выберите изображение", "",
                                                    "Image files (*.jpg *.jpeg *.png)")
        if image_path:
            with open(image_path, 'rb') as file:
                response = vk_api.VkUpload(vk).photo_wall(file, group_id=abs(owner_id) if owner_id < 0 else None)
            photo_info = f"photo{response[0]['owner_id']}_{response[0]['id']}"
            return photo_info
        return None
    except ApiError as e:
        print(f"Ошибка загрузки изображения API: {e}")
        return None
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        return None


# Функция для загрузки видео на сервер ВК
def upload_video_to_vk(vk, token, owner_id, name):
    try:
        upload_server = vk.video.save(name=name, group_id=abs(owner_id) if owner_id < 0 else None)
        video_path, _ = QFileDialog.getOpenFileName(None, "Выберите видео", "", "Video files (*.mp4 *.avi *.mov)")
        if video_path:
            with open(video_path, 'rb') as file:
                # Загружаем видео по ссылке
                response = vk_api.VkUpload(vk).http.post(upload_server['upload_url'], files={'video_file': file})
            video_info = f"video{response['owner_id']}_{response['video_id']}"
            return video_info
        return None
    except ApiError as e:
        print(f"Ошибка загрузки видео API: {e}")
        return None
    except Exception as e:
        print(f"Ошибка загрузки видео: {e}")
        return None


# Функция для публикации статьи на стене ВКонтакте
def post_to_vk(text, token, owner_id, attachments):
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    try:
        vk.wall.post(
            owner_id=owner_id,
            message=text,
            attachments=attachments,  # Добавляем изображения и видео к посту
            random_id=get_random_id()
        )
        QMessageBox.information(None, "Успех", "Статья успешно опубликована!")
    except ApiError as e:
        print(f"Ошибка при публикации API: {e}")
        QMessageBox.critical(None, "Ошибка", f"Ошибка при публикации API: {e}")
    except Exception as e:
        print(f"Ошибка при публикации: {e}")
        QMessageBox.critical(None, "Ошибка", f"Ошибка при публикации: {e}")


# Основное окно приложения
class ArticleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Написание статьи для ВКонтакте")
        self.setGeometry(300, 100, 600, 500)
        # Виджеты
        self.token_label = QLabel("Токен ВКонтакте", self)
        self.token_input = QLineEdit(self)
        self.owner_id_label = QLabel("ID страницы или группы", self)
        self.owner_id_input = QLineEdit(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Введите текст статьи здесь...")
        self.image_check = QCheckBox("Загрузить изображение", self)
        self.video_check = QCheckBox("Загрузить видео", self)
        self.preview_button = QPushButton("Предпросмотр", self)
        self.preview_button.clicked.connect(self.preview_article)
        self.publish_button = QPushButton("Опубликовать", self)
        self.publish_button.clicked.connect(self.publish_article)
        # Расположение виджетов
        layout = QVBoxLayout()
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_input)
        layout.addWidget(self.owner_id_label)
        layout.addWidget(self.owner_id_input)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.image_check)
        layout.addWidget(self.video_check)
        layout.addWidget(self.preview_button)
        layout.addWidget(self.publish_button)
        # Устанавливаем компоновку
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # Функция предпросмотра
    def preview_article(self):
        text = self.text_edit.toPlainText()
        preview_window = QMainWindow(self)
        preview_window.setWindowTitle("Предпросмотр статьи")
        preview_window.setGeometry(350, 150, 400, 300)
        preview_text = QTextEdit(preview_window)
        preview_text.setReadOnly(True)
        preview_text.setText(text)
        preview_text.setGeometry(10, 10, 380, 280)
        preview_window.show()

    # Функция публикации статьи
    def publish_article(self):
        text = self.text_edit.toPlainText()
        attachments = []
        vk_session = vk_api.VkApi(token=self.token_input.text())
        vk = vk_session.get_api()
        # Если нужно загрузить изображение
        if self.image_check.isChecked():
            photo_info = upload_image_to_vk(vk, self.token_input.text(), int(self.owner_id_input.text()))
            if photo_info:
                attachments.append(photo_info)
        # Если нужно загрузить видео
        if self.video_check.isChecked():
            video_info = upload_video_to_vk(vk, self.token_input.text(), int(self.owner_id_input.text()), "Test Video")
            if video_info:
                attachments.append(video_info)
        # Публикация
        post_to_vk(text, self.token_input.text(), int(self.owner_id_input.text()), ",".join(attachments))


# Запуск приложения
def main():
    app = QApplication(sys.argv)
    window = ArticleApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()