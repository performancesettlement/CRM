from datetime import datetime


def random_username():
    now_string = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    new_username = 'anon%s' % now_string
    return new_username
