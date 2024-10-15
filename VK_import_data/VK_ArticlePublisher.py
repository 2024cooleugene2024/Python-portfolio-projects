import sys
import vk_api
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QCheckBox,
                             QFileDialog, QMessageBox)
from vk_api.utils import get_random_id


def upload_image_to_vk(vk, owner_id):
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
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        return None


def upload_video_to_vk(vk, owner_id):
    try:
        upload_server = vk.video.save(name="Test Video", group_id=abs(owner_id) if owner_id < 0 else None)
        video_path, _ = QFileDialog.getOpenFileName(None, "Выберите видео", "", "Video files (*.mp4 *.avi *.mov)")
        if video_path:
            with open(video_path, 'rb') as file:
                response = vk_api.VkUpload(vk).http.post(upload_server['upload_url'], files={'video_file': file})
            video_info = f"video{response['owner_id']}_{response['video_id']}"
            return video_info
        return None
    except Exception as e:
        print(f"Ошибка загрузки видео: {e}")
        return None


def preview_article(text):
    preview_window = QWidget()
    preview_window.setWindowTitle("Предпросмотр статьи")
    layout = QVBoxLayout()
    preview_text = QTextEdit()
    preview_text.setPlainText(text)
    preview_text.setReadOnly(True)
    layout.addWidget(preview_text)
    close_button = QPushButton("Закрыть")
    close_button.clicked.connect(preview_window.close)
    layout.addWidget(close_button)
    preview_window.setLayout(layout)
    preview_window.exec_()


def post_to_vk(text, token, owner_id, attachments):
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    try:
        vk.wall.post(
            owner_id=owner_id,
            message=text,
            attachments=attachments,
            random_id=get_random_id()
        )
        QMessageBox.information(None, "Успех", "Статья успешно опубликована!")
    except Exception as e:
        print(f"Ошибка при публикации: {e}")
        QMessageBox.critical(None, "Ошибка", f"Ошибка при публикации: {e}")


class ArticleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Написание статьи для ВКонтакте")
        self.setGeometry(300, 300, 600, 500)
        self.token_label = QLabel("Токен ВКонтакте:")
        self.token_entry = QLineEdit()
        self.owner_id_label = QLabel("ID страницы или группы:")
        self.owner_id_entry = QLineEdit()
        self.text_area = QTextEdit()
        self.image_checkbox = QCheckBox("Загрузить изображение")
        self.video_checkbox = QCheckBox("Загрузить видео")
        self.preview_button = QPushButton("Предпросмотр")
        self.preview_button.clicked.connect(self.preview_article)
        self.publish_button = QPushButton("Опубликовать")
        self.publish_button.clicked.connect(self.publish_article)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_entry)
        layout.addWidget(self.owner_id_label)
        layout.addWidget(self.owner_id_entry)
        layout.addWidget(self.text_area)
        layout.addWidget(self.image_checkbox)
        layout.addWidget(self.video_checkbox)
        layout.addWidget(self.preview_button)
        layout.addWidget(self.publish_button)
        self.setLayout(layout)

    def preview_article(self):
        text = self.text_area.toPlainText()
        preview_article(text)

    def publish_article(self):
        text = self.text_area.toPlainText()
        attachments = []
        vk_session = vk_api.VkApi(token=self.token_entry.text())
        vk = vk_session.get_api()

        if self.image_checkbox.isChecked():
            photo_info = upload_image_to_vk(vk, int(self.owner_id_entry.text()))
            if photo_info:
                attachments.append(photo_info)

        if self.video_checkbox.isChecked():
            video_info = upload_video_to_vk(vk, int(self.owner_id_entry.text()))
            if video_info:
                attachments.append(video_info)

        post_to_vk(text, self.token_entry.text(), int(self.owner_id_entry.text()), ",".join(attachments))


def main():
    app = QApplication(sys.argv)
    window = ArticleApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()