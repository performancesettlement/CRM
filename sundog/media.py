from django.db.models import FileField


class S3PrivateFileField(FileField):
    def __init__(
        self,
        verbose_name=None,
        name=None,
        upload_to='',
        storage=None,
        **kwargs
    ):
        super().__init__(
            verbose_name=verbose_name,
            name=name,
            upload_to=upload_to,
            storage=storage,
            **kwargs
        )
        self.storage.default_acl = 'private'
