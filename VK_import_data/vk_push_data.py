import vk_api
from vk_api.utils import get_random_id
from tkinter import *
from tkinter import filedialog, messagebox


# Функция для загрузки изображения на сервер ВК
def upload_image_to_vk(vk, token, owner_id):
    """
    :param vk: An instance of the VK API client.
    :param token: The authentication token for accessing the VK API.
    :param owner_id: The ID of the owner of the wall where the image will be uploaded.
    A negative value represents a group ID.
    :return: The photo information as a string in the format "photo{owner_id}_{id}" if successful, None otherwise.
    """
    try:
        upload_server = vk.photos.getWallUploadServer(group_id=abs(owner_id) if owner_id < 0 else None)
        image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])

        if image_path:
            with open(image_path, 'rb') as file:
                response = vk_api.VkUpload(vk).photo_wall(file, group_id=abs(owner_id) if owner_id < 0 else None)

            photo_info = f"photo{response[0]['owner_id']}_{response[0]['id']}"
            return photo_info
        return None
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        return None


# Функция для загрузки видео на сервер ВК
def upload_video_to_vk(vk, token, owner_id, name):
    """
    :param vk: An instance of the VK API client used to interact with the VKontakte API.
    :param token: API token used for authentication with VKontakte.
    :param owner_id: ID of the owner (user or group) for whom the video is being uploaded.
    :param name: The name of the video to be uploaded.
    :return: The identifier of the uploaded video in the format
    'video<owner_id>_<video_id>', or None if an error occurs.
    """
    try:
        upload_server = vk.video.save(name=name, group_id=abs(owner_id) if owner_id < 0 else None)
        video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])

        if video_path:
            with open(video_path, 'rb') as file:
                # Загружаем видео по ссылке
                response = vk_api.VkUpload(vk).http.post(upload_server['upload_url'], files={'video_file': file})
            video_info = f"video{response['owner_id']}_{response['video_id']}"
            return video_info
        return None
    except Exception as e:
        print(f"Ошибка загрузки видео: {e}")
        return None


# Функция для предпросмотра статьи
def preview_article(text):
    """
    :param text: The article text to be displayed in the preview window.
    :return: None
    """
    preview_window = Toplevel()
    preview_window.title("Предпросмотр статьи")
    preview_text = Text(preview_window, height=15, width=60)
    preview_text.insert(END, text)
    preview_text.config(state=DISABLED)  # Предотвращаем редактирование
    preview_text.pack()
    Button(preview_window, text="Закрыть", command=preview_window.destroy).pack()


# Функция для публикации статьи на стене ВКонтакте
def post_to_vk(text, token, owner_id, attachments):
    """
    :param text: The text content to be posted on the VK wall.
    :param token: The authentication token required for accessing the VK API.
    :param owner_id: The ID of the user or community on whose wall to post.
    :param attachments: Media attachments (images, videos) to include in the post.
    :return: None
    """
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    try:
        vk.wall.post(
            owner_id=owner_id,
            message=text,
            attachments=attachments,  # Добавляем изображения и видео к посту
            random_id=get_random_id()
        )
        messagebox.showinfo("Успех", "Статья успешно опубликована!")
    except Exception as e:
        print(f"Ошибка при публикации: {e}")
        messagebox.showerror("Ошибка", f"Ошибка при публикации: {e}")


# Интерфейс для написания статьи
def create_article_gui():
    """
    Initializes and runs the GUI for writing an article for VKontakte.
    The interface allows the user to input a VK token,
    specify an owner ID, write the text of the article,
    and choose to upload images and videos as part of the article.

    :return: None
    """
    def publish_article(vk=None):
        text = text_area.get("1.0", "end-1c")
        attachments = []

        # Загружаем изображение
        if image_check_var.get():
            photo_info = upload_image_to_vk(vk, token_entry.get(), int(owner_id_entry.get()))
            if photo_info:
                attachments.append(photo_info)

        # Загружаем видео
        if video_check_var.get():
            video_info = upload_video_to_vk(vk, token_entry.get(), int(owner_id_entry.get()), "Test Video")
            if video_info:
                attachments.append(video_info)

        post_to_vk(text, token_entry.get(), int(owner_id_entry.get()), ",".join(attachments))

    def preview():
        text = text_area.get("1.0", "end-1c")
        preview_article(text)

    root = Tk()
    root.title("Написание статьи для ВКонтакте")
    root.geometry("600x500")

    Label(root, text="Токен ВКонтакте").pack()
    token_entry = Entry(root, width=50)
    token_entry.pack()

    Label(root, text="ID страницы или группы").pack()
    owner_id_entry = Entry(root, width=50)
    owner_id_entry.pack()

    text_area = Text(root, height=15, width=60)
    text_area.pack()

    # Флажки для загрузки изображений и видео
    image_check_var = BooleanVar()
    Checkbutton(root, text="Загрузить изображение", variable=image_check_var).pack()

    video_check_var = BooleanVar()
    Checkbutton(root, text="Загрузить видео", variable=video_check_var).pack()

    Button(root, text="Предпросмотр", command=preview).pack()
    Button(root, text="Опубликовать", command=publish_article).pack()

    root.mainloop()


# Запуск интерфейса
create_article_gui()
