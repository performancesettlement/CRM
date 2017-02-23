class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_line(msg, color=None, lines=False):
    print_str = msg
    if color:
        print_str = color + print_str + BColors.ENDC
    if lines:
        print_str = '\n' + print_str + '\n'
    print(print_str)


def print_script_header(msg):
    print_line(msg, BColors.OKGREEN, lines=True)


def print_script_end(msg='Script finished successfully'):
    print_script_header(msg)


def get_or_create_model_instance(model, model_data_kwargs, filter_kwargs, message_name, associated_to=None, tabs=0):
    message_kwargs = {'model': model.__name__, 'name': message_name}
    try:
        instance = model.objects.get(**filter_kwargs)
        msg = "{model} '{name}' is already created."
        color = None
    except model.DoesNotExist:
        instance = model(**model_data_kwargs)
        instance.save()
        msg = "{model} '{name}' created successfully."
        color = BColors.OKBLUE
    if associated_to:
        msg = msg.replace('.', " and associated to '{associated_to}'.")
        message_kwargs['associated_to'] = associated_to
    if tabs > 0:
        msg = ('    ' * tabs) + msg
    print_line(msg.format(**message_kwargs), color=color)
    return instance
