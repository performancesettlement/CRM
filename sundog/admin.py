from django.contrib import admin
from sundog.models import Contact

import logging


logger = logging.getLogger(__name__)


admin.site.register(Contact)
