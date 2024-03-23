# WEB_HW8
MongoDB, Radis, RabbitMQ

MongoDB - in the cloud
Radis, RabbitMQ - in containers

raise docker:
docker compose up

books.py
    uncomment fill_db() to populate DB from files
    ui input can be switched to go through test inputs instead of manual input 

producer.py - generates fake data to fill MongoDB from mailer_db.py and fills 2 queues:
    1. SMS - for users that do not have x... extension in phone number
    2. E-mail - for the rest of users
consumer_email.py - proccess E-mail queue
consumer_sms.py - proccess SMS queue
