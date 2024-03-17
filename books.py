import configparser
import mongoengine
import json
import datetime

SRC = {
    'authors': 'authors.json',
    'quotes': 'quotes.json'
}

config = configparser.ConfigParser()
config.read('config.ini')

user = config.get('DB', 'USER')
pwd = config.get('DB', 'PASS')
db_name = config.get('DB', 'DB_NAME')
domain = config.get('DB', 'DOMAIN')

uri = f"mongodb+srv://{user}:{pwd}@{domain}/{db_name}?retryWrites=true&w=majority"
mongoengine.connect(host=uri, ssl=True)

class Author(mongoengine.fields.Document):
    born_date = mongoengine.fields.DateField()
    fullname = mongoengine.fields.StringField(required=True, unique_with='born_date')
    born_location = mongoengine.fields.StringField()
    description = mongoengine.fields.StringField()

class Tag(mongoengine.fields.EmbeddedDocument):
     tag = mongoengine.fields.StringField()

class Quote(mongoengine.fields.Document):
      tags = mongoengine.fields.ListField(mongoengine.fields.EmbeddedDocumentField(Tag))
      author  = mongoengine.fields.ReferenceField(Author, dbref=False, required=True)
      quote  = mongoengine.fields.StringField(required=True)

def fill_db():
    with open(SRC['authors'], 'r') as fh:
        auth_json = json.load(fh)

    with open(SRC['quotes'], 'r') as fh:
        qoutes_json = json.load(fh)


    for auth in auth_json:
        fullname = auth['fullname']
        born_date = datetime.datetime.strptime(auth['born_date'], "%B %d, %Y").date()
        born_location = auth['born_location']
        description = auth['description']
        try:
            Author(fullname=fullname, born_date=born_date, born_location=born_location, description=description).save()
        except mongoengine.queryset.NotUniqueError:
            # Author(fullname=fullname, born_date=born_date, born_location=born_location, description=description).update()
            pass

    for qt in qoutes_json:
        tags = [Tag(tag= i) for i in qt['tags']]
        try:
            # print(qt['author'])
            author = Author.objects.get(fullname=qt['author']).id
            # print(author)
        except mongoengine.queryset.DoesNotExist as err:
            print('1', err)
        except mongoengine.queryset.MultipleObjectsReturned as err:
            author = Author.objects.first(fullname=qt['author']).id

        quote = qt['quote']
        Quote(tags=tags, author=author, quote=quote).save()

def find_name(name):
    responce = Author.objects(fullname=name[0])

    if not responce:
        responce = Author.objects(fullname__iregex=f'{name[0]}')
        if not responce:
            print(f'nothing was fond by name: {name[0]}')
            return

    auth = {item.id: item.fullname for item in responce}

    for auth_id, auth_name in auth.items():
        quotes = Quote.objects(author=auth_id)
        for item in quotes:
            print(f'{auth_name}: {item.quote}')

def find_tag(tag):
    responce = Quote.objects(tags__tag=tag[0])
    if not responce:
        responce = Quote.objects(tags__tag__iregex=f'{tag[0]}')
        if not responce:
            print(f'nothing was fond by tag: {tag[0]}')
            return
    for item in responce:
        print(f'{item.author.fullname}: {item.quote}')

def find_tags(tags):
    responce = Quote.objects(tags__tag__in=tags)
    for item in responce:
        print(f'{item.author.fullname}: {item.quote}')

CMD = {
    'name': find_name,
    'tag': find_tag,
    'tags': find_tags
}

test_input = [
    'name: Albert Einstein',
    'name:Albert Einstein',
    'name: Albert Einstein ',
    'name: Steve Martin',
    'name: st',
    'name: --',
    'tag: change',
    'tag:change',
    'tag: change ',
    'tag: humor',
    'tag: hum',
    'tag: or',
    'tag: ---',
    'tags:life,live',
    'tags: life,live',
    'tags: life, live',
    'tags: life ,live',
    'exit'
]

if __name__ == '__main__':
    # fill_db()

    counter = 0

    while True:
        ui = input('Введить команду у форматі <команда>: <значення>: ')
        # ui = test_input[counter]
        # counter += 1

        if ui.strip().lower() == 'exit':
            break
        
        try:
            com, params = ui.split(':')
            com = com.strip()
            params = params.split(',')
            params = [i.strip() for i in params]
        except Exception as err:
            print(err)

        func = CMD[com]
        func(params)
