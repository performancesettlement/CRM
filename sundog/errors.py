class ConcurrencyError(Exception):
    def __init__(self, *args, **kwargs):
        super(ConcurrencyError, self).__init__(*args, **kwargs)
