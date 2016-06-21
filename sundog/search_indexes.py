from haystack import indexes
from sundog.models import MyFile


class FileIndex(indexes.SearchIndex, indexes.Indexable):
    file_id = indexes.IntegerField(model_attr='file_id')
    text = indexes.CharField(document=True, use_template=True)
    status = indexes.CharField(model_attr='current_status__name', faceted=True)
    created_time = indexes.DateTimeField(model_attr='created_time', indexed=False)
    priority = indexes.IntegerField(model_attr='priority', indexed=False, default=0)
    completion = indexes.IntegerField(model_attr='current_status__related_percent', indexed=False, default=None)
    rendered = indexes.CharField(use_template=True, indexed=False)
    description = indexes.CharField(model_attr='description', indexed=False)
    sorted_description = indexes.CharField(indexed=False)
    participants = indexes.MultiValueField()

    def get_model(self):
        return MyFile

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare_participants(self, obj):
        return [participant.id for participant in obj.participants.all()]

    def prepare_sorted_description(self, obj):
        return obj.description.lower().replace(" ", "_")
