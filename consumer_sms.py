import pika
import sys
import configparser
import time
import mongoengine
from mailer_db import Users
import pathlib

config = configparser.ConfigParser()
if pathlib.Path('config_dev.ini').exists():
    config.read('config_dev.ini')
else:
    config.read('config.ini')

params = {
    'user': config.get('RABBIT', 'USER'),
    'pwd': config.get('RABBIT','PWD'),
    'host': config.get('RABBIT','HOST'),
    'port': int(config.get('RABBIT','PORT')),
    'exchange': config.get('RABBIT','EXCHANGE'),
    'queue': config.get('RABBIT', 'SMS_QUEUE')
}

def mongo_connect(config: configparser.ConfigParser) -> None:
    user = config.get('CLUSTER', 'USER')
    pwd = config.get('CLUSTER', 'PWD')
    domain = config.get('CLUSTER', 'DOMAIN')
    db_name = config.get('MAILER', 'DB_NAME')

    uri = f"mongodb+srv://{user}:{pwd}@{domain}/{db_name}?retryWrites=true&w=majority"
    mongoengine.connect(host=uri, ssl=True)

def send_sms_callback(ch, method, properties, body):
    responce = Users.objects(id=body.decode())[0]
    print(f" [x] Sending SMS to {responce.fullname}...", end='')
    time.sleep(1)
    responce.update(sms_sent=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"SMS sent to {responce.phone}")

def main():

    mongo_connect(config)

    credentials = pika.PlainCredentials(params['user'], params['pwd'])
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=params['host'], port=params['port'], credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue=params['queue'], durable=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=params['queue'], on_message_callback=send_sms_callback, auto_ack=False)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
