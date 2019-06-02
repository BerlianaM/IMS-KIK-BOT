from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, PictureMessage, \
    SuggestedResponseKeyboard, TextResponse, StartChattingMessage
import pymysql
from mysql.connector import cursor

conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='mca')
cirs = conn.cursor()
curs = conn.cursor()


class KikBot(Flask):
    """ Flask kik bot application class"""

    def __init__(self, kik_api, import_name, static_path=None, static_url_path=None, static_folder="static",
                 template_folder="templates", instance_path=None, instance_relative_config=False,
                 root_path=None):

        self.kik_api = kik_api

        super(KikBot, self).__init__(import_name, static_path, static_url_path, static_folder, template_folder,
                                     instance_path, instance_relative_config, root_path)

        self.route("/incoming", methods=["POST"])(self.incoming)

    def incoming(self):
        """Handle incoming messages to the bot. All requests are authenticated using the signature in
        the 'X-Kik-Signature' header, which is built using the bot's api key (set in main() below).
        :return: Response
        """
        # verify that this is a valid request
        if not self.kik_api.verify_signature(
                request.headers.get("X-Kik-Signature"), request.get_data()):
            return Response(status=403)

        messages = messages_from_json(request.json["messages"])

        response_messages = []

        for message in messages:
            user = self.kik_api.get_user(message.from_user)
            # Check if its the user's first message. Start Chatting messages are sent only once.
            if isinstance(message, StartChattingMessage):
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Hey {}, how are you?".format(user.first_name),
                    # keyboards are a great way to provide a menu of options for a user to respond with!
                    keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad")])]))


            # Check if the user has sent a text message.
            elif isinstance(message, TextMessage):
                user = self.kik_api.get_user(message.from_user)
                message_body = message.body.lower()

                try:
                    cekpesan = message_body.lower()
                    cekpesan1 = cekpesan[0:6]
                    print(cekpesan1)
                except:
                   cekpesan1 = message_body
                   print(cekpesan1)

                if message_body == "kumal":
                    url = 'https://kucingpedia.com/wp-content/uploads/2017/08/Gambar-Harga-Kucing-Persia-Warna-Abu-Abu.jpg'
                    print(str(url))
                    response_messages.append(PictureMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        pic_url=str(url)))

                elif cekpesan1 == "gambar":
                    userid = message.from_user
                    pesan = message_body
                    chatid = message.chat_id
                    sql = "INSERT INTO tb_inbox (id_inbox, id_user, id_chat, in_msg, tipee, flag) VALUES (NULL, '%s', '%s', '%s', 'img', '1')" % (
                        userid, chatid, pesan)
                    curs.execute(sql)
                    conn.commit()
                    print("1 pesan img handle")

                    sql1 = "SELECT id_outbox, id_user, id_chat, out_msg FROM tb_outbox WHERE flag = '1' AND tipee = 'img' ;"
                    cirs.execute(sql1)
                    results = cirs.fetchall()
                    print("Tables : ", cirs.rowcount)
                    for row in results:
                        print(row[0])
                        print(row[1])
                        print(row[2])
                        print(row[3], "\n")

                        url = row[3]
                        print(str(url))
                        response_messages.append(PictureMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            pic_url=str(url)))

                        sql2 = "UPDATE tb_outbox SET flag='2' WHERE id_outbox='%s';" % (str(row[0]))
                        curs.execute(sql2)
                        conn.commit()



                elif cekpesan1 != "gambar":
                    # Insert Pesan ke tabel inbox
                    userid = message.from_user
                    pesan = message_body
                    chatid = message.chat_id
                    sql = "INSERT INTO tb_inbox (id_inbox, id_user, id_chat, in_msg, tipee, flag) VALUES (NULL, '%s', '%s', '%s', 'msg', '1')" % (
                        userid, chatid, pesan)
                    curs.execute(sql)
                    conn.commit()
                    print("1 pesan msg handle")

                    # Select Pesan dari tabel outbox
                    sql1 = "SELECT id_outbox, id_user, id_chat, out_msg FROM tb_outbox WHERE flag = '1' AND tipee = 'msg';"
                    cirs.execute(sql1)
                    results = cirs.fetchall()
                    print("Tables : ", cirs.rowcount)
                    for row in results:
                        print(row[0])
                        print(row[1])
                        print(row[2])
                        print(row[3], "\n")


                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body=str(row[3])))

                        sql2 = "UPDATE tb_outbox SET flag='2' WHERE id_outbox='%s';" % (str(row[0]))
                        curs.execute(sql2)
                        conn.commit()







                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Sorry {}, I didn't quite understand that. How are you?".format(user.first_name),
                        keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad")])]))


                # If its not a text message, give them another chance to use the suggested responses.

            else:
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Sorry, I didn't quite understand that. How are you, {}?".format(user.first_name),
                    keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Good"), TextResponse("Bad")])]))
                    # We're sending a batch of messages. We can send up to 25 messages at a time (with a limit of
                    # 5 messages per user).

            self.kik_api.send_messages(response_messages)

            return Response(status=200)

    @staticmethod
    def profile_pic_check_messages(user, message):
        """Function to check if user has a profile picture and returns appropriate messages.
        :param user: Kik User Object (used to acquire the URL the profile picture)
        :param message: Kik message received by the bot
        :return: Message
        """

        messages_to_send = []
        profile_picture = user.profile_pic_url

        if profile_picture is not None:
            messages_to_send.append(
                # Another type of message is the PictureMessage - your bot can send a pic to the user!
                PictureMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    pic_url=profile_picture
                ))

            profile_picture_response = "Here's your profile picture!"
        else:
            profile_picture_response = "It does not look like you have a profile picture, you should set one"

        messages_to_send.append(
            TextMessage(to=message.from_user, chat_id=message.chat_id, body=profile_picture_response))

        return messages_to_send


if __name__ == "__main__":
    """ Main program """
    kik = KikApi('bottugasims', '29f7eec2-62bd-4f38-bfc7-821b29f73023')
    # For simplicity, we're going to set_configuration on startup. However, this really only needs to happen once
    # or if the configuration changes. In a production setting, you would only issue this call if you need to change
    # the configuration, and not every time the bot starts.
    kik.set_configuration(Configuration(webhook='https://15246a06.ngrok.io/incoming'))
    app = KikBot(kik, __name__)
    app.run(port=8080, host='127.0.0.1', debug=True)
