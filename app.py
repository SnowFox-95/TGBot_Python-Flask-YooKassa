from flask import Flask, request
import requests
from dotenv import load_dotenv
import os
from os.path import join, dirname
import uuid
from yookassa import Configuration, Payment
import json

app = Flask(__name__)


def create_invoice(chat_id):
    Configuration.account_id = get_from_env("SHOP_ID")
    Configuration.secret_key = get_from_env("PAYMENT_TOKEN")

    payment = Payment.create({
        "amount": {
            "value": "10.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://www.google.com"
        },
        "capture": True,
        "description": "Заказ №1",
        "metadata": {"chat_id": chat_id}
    }, uuid.uuid4())
    return payment.confirmation.confirmation_url


def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)


def send_message(chat_id, text):
    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


def send_pay_button(chat_id, text):
    invoice_url = create_invoice(chat_id)

    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"

    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": [[{
        "text": "Оплатить!",
        "url": f"{invoice_url}"
    }]]})}

    requests.post(url, data=data)


def check_if_successful_payment(request):
    try:
        if request.json["event"] == "payment.succeeded":
            return True
    except KeyError:
        return False

    return False


@app.route('/', methods={"POST"})
def process():  # put application's code here
    # Обработка запроса от ЮКассы
    if check_if_successful_payment(request):
        chat_id = request.json["object"]["metadata"]["chat_id"]
        send_message(chat_id, "Оплата успешна")
    else:
        # Обработка запроса от Телеграмм
        chat_id = request.json["message"]["chat"]["id"]
        send_pay_button(chat_id=chat_id, text="Тестовая оплата")
    return {"ok": True}


if __name__ == '__main__':
    app.run()
