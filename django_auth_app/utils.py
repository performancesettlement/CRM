from datetime import datetime
import json
from django.core import serializers


def random_username():
    now_string = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    new_username = 'anon%s' % now_string
    return new_username


def serialize_user(user):
    json_user = serializers.serialize('json', [user])
    parser_user = json.loads(json_user)[0]
    parser_user['fields']['id'] = parser_user['pk']
    return parser_user['fields']
