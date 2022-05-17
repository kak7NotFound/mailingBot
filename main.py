import datetime
import json

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard


class Main:

    def __init__(self):
        self.api = vk_api.VkApi(token=locale.get_config_value("token"))

        self.buttons = ["current_collection_button", "discounts_button", "need_help_button", "about_button"]
        self.with_manager = []
        self.main_message_id = {}

        self.longpoll = VkBotLongPoll(self.api, 191719521)
        self.main()

    def write_msg(self, user_id, message, keyboard=None, template=None, attachment=None):

        data = {'user_id': user_id, 'random_id': int(datetime.datetime.now().timestamp()), 'message': message}
        if template is not None:
            data["template"] = template
        if keyboard is not None:
            data["keyboard"] = keyboard
        if attachment is not None:
            data["attachment"] = attachment

        return self.api.method('messages.send', data)

    def edit_msg(self, peer_id, message, template=None, keyboard=None, attachment=None):
        try:

            message_id = self.main_message_id[peer_id]

            data = {'peer_id': peer_id, "message_id": message_id, "message": message}
            if template is not None:
                data["template"] = template
            if keyboard is not None:
                data["keyboard"] = keyboard
            if attachment is not None:
                data["attachment"] = attachment
        except:
            # todo test it
            return self.write_msg(peer_id, message, template, keyboard, attachment)
        return self.api.method('messages.edit', data)

    def main(self):
        self.register_event_loop()

    def register_event_loop(self):
        print("Event loop has been registered successfully!")
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                # todo add a command?
                Replyer.send_main_menu(event.message.from_id)

            if event.type == VkBotEventType.MESSAGE_EVENT:
                event_type: str = event.object.get('payload').get('type')
                event_name = event_type.split(":")[0]
                event_client_id = event_type.split(":")[1]

                Logging.add_string(f'"","{event_client_id}","{event_name}","{datetime.datetime.now()}"')

                if event_name == "about_button":
                    self.write_msg(event_client_id, locale.get_locale("about_text"),
                                   keyboard=Keyboard.get_back_keyboard(event_client_id),
                                   attachment=locale.get_locale("about_image"))

                if event_name == "back_button":
                    self.edit_msg(event_client_id,
                                  locale.get_locale("main_menu_text"),
                                  keyboard=Keyboard.get_default_keyboard(event_client_id))

                if event_name == "current_collection_button":
                    self.edit_msg(event_client_id,
                                  locale.get_locale("current_collection_text"),
                                  keyboard=Keyboard.get_empty_keyboard(), template=Carousel.get_carousel_from_config("current_collection_carousel"))


class Replyer:

    @staticmethod
    def send_main_menu(event_client_id, refresh=False):
        if event_client_id in main.main_message_id.keys() and refresh:
            return
        main.main_message_id[event_client_id] = main.write_msg(event_client_id,
                                                               locale.get_locale("main_menu_text"),
                                                               keyboard=Keyboard.get_default_keyboard(
                                                                   event_client_id))


class Carousel:

    @staticmethod
    def get_carousel_from_config(key):
        carousel_date: dict = locale.get_locale(key)

        carousel = {"type": "carousel"}

        elements = []

        photos: list = carousel_date.get("photos")
        text: list = carousel_date.get("text")
        description: list = carousel_date.get("description")
        button_text: list = carousel_date.get("button_text")
        button_links: list = carousel_date.get("button_links")

        for i in range(3):
            elements.append({
                "title": f"{text[i]}",
                "description": f"{description[i]}",
                "photo_id": f"{photos[i]}",
                "action": {
                    "type": "open_link",
                    "link": f"{button_links[i]}"
                },
                "buttons": [{
                    "action": {
                        "type": "text",
                        "label": f"{button_text[i]}",
                        "payload": "{}"
                    }
                }]})

        carousel["elements"] = elements
        return json.dumps(carousel)


class Keyboard:

    @staticmethod
    def get_default_keyboard(user_id):
        i = 0
        kb: VkKeyboard = VkKeyboard(False)
        for label in ["current_collection_button", "discounts_button", "need_help_button", "about_button"]:
            kb.add_callback_button(label=locale.get_locale(label), payload={"type": label + ":" + str(user_id)})
            if i % 2 == 0:
                kb.add_line()
            i = i + 1
        return kb.get_keyboard()

    @staticmethod
    def get_empty_keyboard():
        return VkKeyboard().get_empty_keyboard()

    @staticmethod
    def get_back_keyboard(user_id):
        kb: VkKeyboard = VkKeyboard(False)
        kb.add_callback_button(label=locale.get_locale("back_button"),
                               payload={"type": "back_button" + ":" + str(user_id)})
        return kb.get_keyboard()


class Locale:

    def __init__(self):
        try:
            self.raw_json = open(f'locale.json', 'r', encoding='utf8').read()
        except:
            raise Exception('locale.json not found')

    def get_locale(self, key):
        return json.loads(self.raw_json).get("locale").get(key)

    def get_config_value(self, key):
        return json.loads(self.raw_json).get("config").get(key)


class Logging:

    @staticmethod
    def add_string(new_string):
        file = open("logging.csv", 'a', encoding='utf8')
        file.write("\n" + new_string)
        file.close()


if __name__ == "__main__":
    locale = Locale()
    print(Carousel.get_carousel_from_config("current_collection_carousel"))
    # main = Main()
