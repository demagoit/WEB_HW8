import mongoengine
import faker


class Users(mongoengine.fields.Document):
    fullname = mongoengine.fields.StringField(required=True)
    e_mail = mongoengine.fields.StringField(required=True, unique=True)
    msg_sent = mongoengine.fields.BooleanField(default=False)
    address = mongoengine.fields.StringField(required=False)
    phone = mongoengine.fields.StringField(required=False, unique=True)
    sms_sent = mongoengine.fields.BooleanField(default=False)
    sms_enable = mongoengine.fields.BooleanField(default=True)

def generate_fake_data(n_users=1):
    users = []

    fake = faker.Faker()

    for _ in range(n_users):
        phone = fake.country_calling_code()
        phone = phone if len(phone) == 3 else phone[:3]
        phone += fake.phone_number().replace('+', '')
        phone = phone.replace('(','').replace(')', '').replace('-','').replace('.','')
        sms_enable = False if 'x' in phone else True
        users.append({
            'fullname': fake.name(),
            'e_mail': fake.ascii_free_email(),
            'address': fake.address(),
            'phone': phone,
            'sms_enable': sms_enable
        })

    return users

def fill_db(users):
    ids = []
    for user in users:
        try:
            i = Users(**user).save()
            ids.append(i)

        except mongoengine.queryset.NotUniqueError:
            print(f'User with e-mail {user["e_mail"]} and/or phone {user["phone"]} already exists.')
