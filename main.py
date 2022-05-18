import datetime
import json
import traceback

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard


class Main:

    def __init__(self):
        self.api = vk_api.VkApi(token=locale.get_config_value("token"))

        self.buttons = ["current_collection_button", "discounts_button", "need_help_button", "about_button"]
        self.with_manager = []
        self.has_carousel_support = []
        self.main_message_id = {}

        self.longpoll = VkBotLongPoll(self.api, int(locale.get_config_value("public_id")))
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
            print(self.main_message_id, peer_id)
            message_id = self.main_message_id.get(int(peer_id))
            print(message_id)
            if message_id is None:
                raise "message id None"

            data = {'peer_id': peer_id, "message_id": message_id, "message": message}
            if template is not None:
                data["template"] = template
            if keyboard is not None:
                data["keyboard"] = keyboard
            if attachment is not None:
                data["attachment"] = attachment
            return self.api.method('messages.edit', data)
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.send_main_menu(peer_id, refresh=True)

    def send_main_menu(self, event_client_id, refresh=False):
        if event_client_id in self.main_message_id.keys() and not refresh:
            return
        a = self.write_msg(event_client_id,
                           locale.get_locale("main_menu_text"),
                           keyboard=Keyboard.get_default_keyboard(
                               event_client_id))
        self.main_message_id[int(event_client_id)] = int(a)
        print(str(event_client_id) + " added " + str(self.main_message_id), "new menu created")

    def main(self):
        try:
            self.register_event_loop()
        except Exception as e:
            print(e)
            print("Another event loop has been created")
            self.register_event_loop()

    def register_event_loop(self):
        print("Event loop has been registered successfully!")
        for event in self.longpoll.listen():
            print(event.type)
            if event.type == VkBotEventType.MESSAGE_REPLY:
                if event.object.text is not None:
                    if event.object.text == locale.get_locale("message_to_close_ticket"):
                        self.send_main_menu(event.object.peer_id, True)
            if event.type == VkBotEventType.MESSAGE_NEW:

                has_carousel = event.client_info.get("carousel")
                if has_carousel:
                    self.has_carousel_support.append(event.message.from_id)
                elif not has_carousel:
                    self.has_carousel_support.pop(event.message.from_id)

                if event.message.from_id not in self.with_manager:
                    self.send_main_menu(event.message.from_id)

            if event.type == VkBotEventType.MESSAGE_EVENT:
                print(self.main_message_id)
                event_type: str = event.object.get('payload').get('type')
                event_name = event_type.split(":")[0]
                event_client_id = event_type.split(":")[1]

                Logging.add_string(f'"","{event_client_id}","{event_name}","{datetime.datetime.now()}"')

                if event_name == "about_button":
                    self.edit_msg(event_client_id, locale.get_locale("about_text"),
                                  keyboard=Keyboard.get_back_keyboard(event_client_id),
                                  attachment=locale.get_locale("about_image"))

                if event_name == "discounts_button":
                    if int(event_client_id) in self.has_carousel_support:
                        self.edit_msg(event_client_id,
                                      locale.get_locale("discounts_text"),
                                      keyboard=Keyboard.get_back_keyboard(event_client_id))
                        self.edit_msg(event_client_id,
                                      locale.get_locale("discounts_text"),
                                      template=Carousel.get_carousel_from_config("discounts_carousel"))
                    else:
                        self.edit_msg(event_client_id,
                                      locale.get_locale("discounts_legacy_text").get("text"),
                                      attachment=locale.get_locale("discounts_legacy_text").get("photos"),
                                      keyboard=Keyboard.get_back_keyboard(event_client_id))

                if event_name == "current_collection_button":

                    if int(event_client_id) in self.has_carousel_support:
                        self.edit_msg(event_client_id,
                                      locale.get_locale("current_collection_text"),
                                      keyboard=Keyboard.get_back_keyboard(event_client_id))
                        self.edit_msg(event_client_id,
                                      locale.get_locale("current_collection_text"),
                                      template=Carousel.get_carousel_from_config("current_collection_carousel"))
                    else:
                        self.edit_msg(event_client_id,
                                      locale.get_locale("current_collection_legacy_text").get("text"),
                                      attachment=locale.get_locale("current_collection_legacy_text").get("photos"),
                                      keyboard=Keyboard.get_back_keyboard(event_client_id))

                if event_name == "back_button":
                    self.edit_msg(event_client_id,
                                  locale.get_locale("main_menu_text"),
                                  keyboard=Keyboard.get_default_keyboard(event_client_id))

                if event_name == "need_help_button":

                    for id in locale.get_config_value("managers_ids"):
                        self.write_msg(int(id), locale.get_locale("manager_SOMEONE_NEED_HELP") + f'\nhttps://vk.com/gim{locale.get_config_value("public_id")}?sel={event_client_id}')

                    self.write_msg(event_client_id, locale.get_locale("manager_start_message"),
                                   keyboard=Keyboard.get_empty_keyboard())
                    # todo remove
                    if int(event_client_id) in self.main_message_id.values(): del self.main_message_id[
                        int(event_client_id)]
                    print(self.main_message_id)
                    self.with_manager.append(int(event_client_id))


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


        for i in range(len(photos)):
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
        for label in ["about_button", "discounts_button", "need_help_button", "current_collection_button"]:
            kb.add_callback_button(label=locale.get_locale(label), color=locale.get_locale(label + "_color"),
                                   payload={"type": label + ":" + str(user_id)})
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
        kb.add_callback_button(label=locale.get_locale("back_button"), color=locale.get_locale("back_button_color"),
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
    main = Main()
