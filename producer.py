import configparser
import mongoengine
import pika
import pathlib
from mailer_db import Users, generate_fake_data, fill_db


def mongo_connect(config: configparser.ConfigParser) -> None:
    user = config.get('CLUSTER', 'USER')
    pwd = config.get('CLUSTER', 'PWD')
    domain = config.get('CLUSTER', 'DOMAIN')
    db_name = config.get('MAILER', 'DB_NAME')

    uri = f"mongodb+srv://{user}:{pwd}@{domain}/{db_name}?retryWrites=true&w=majority"
    mongoengine.connect(host=uri, ssl=True)

def rabbit_connect(config: configparser.ConfigParser) -> None:
    params = {
        'user': config.get('RABBIT', 'USER'),
        'pwd': config.get('RABBIT','PWD'),
        'host': config.get('RABBIT','HOST'),
        'port': int(config.get('RABBIT','PORT')),
        'exchange': config.get('RABBIT','EXCHANGE'),
        'e_queue': config.get('RABBIT', 'E_QUEUE'),
        'sms_queue': config.get('RABBIT', 'SMS_QUEUE')
    }
    credentials = pika.PlainCredentials(params['user'], params['pwd'])
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=params['host'], port=params['port'], credentials=credentials))
    e_channel = connection.channel()
    sms_channel = connection.channel()
    
    e_channel.exchange_declare(exchange=params['exchange'], exchange_type='direct')
    e_channel.queue_declare(queue=params['e_queue'], durable=False)
    e_channel.queue_bind(queue=params['e_queue'], exchange=params['exchange'])

    sms_channel.exchange_declare(exchange=params['exchange'], exchange_type='direct')
    sms_channel.queue_declare(queue=params['sms_queue'], durable=False)
    sms_channel.queue_bind(queue=params['sms_queue'], exchange=params['exchange'])

    return e_channel, sms_channel

if __name__ == "__main__":
    config = configparser.ConfigParser()
    if pathlib.Path('config_dev.ini').exists():
        config.read('config_dev.ini')
    else:
        config.read('config.ini')

    mongo_connect(config)
    users = generate_fake_data(5)
    fill_db(users)

    e_channel, sms_channel = rabbit_connect(config)

    with e_channel as e_channel:
        with sms_channel as sms_channel:
            for item in Users.objects(msg_sent = False):
                if item.sms_enable and not item.sms_sent:
                    sms_channel.basic_publish(exchange=config.get('RABBIT','EXCHANGE'), routing_key=config.get('RABBIT', 'SMS_QUEUE'), body=str(item.id),
                                        properties=pika.BasicProperties(delivery_mode=pika.spec.TRANSIENT_DELIVERY_MODE))
                                        #    properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))
                    print(f" [S] {item.id} Sent to SMS queue")
                else:
                    e_channel.basic_publish(exchange=config.get('RABBIT','EXCHANGE'), routing_key=config.get('RABBIT', 'E_QUEUE'), body=str(item.id),
                                        properties=pika.BasicProperties(delivery_mode=pika.spec.TRANSIENT_DELIVERY_MODE))
                                        #    properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))
                    print(f" [E] {item.id} Sent to E-mail queue")
    
