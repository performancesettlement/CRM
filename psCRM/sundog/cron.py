from haystack.query import SearchQuerySet
from datetime import datetime
from sundog.models import FileStatusStat
import logging

# initialize logger
logger = logging.getLogger(__name__)


def create_status_daily_stats():
    try:
        date_stat = datetime.now()
        facets = SearchQuerySet().facet('status')
        results = facets.facet_counts()['fields']['status']
        for row_stat in results:
            new_stat_row = FileStatusStat(date_stat=date_stat)
            new_stat_row.file_status = row_stat[0]
            new_stat_row.file_count = row_stat[1]
            new_stat_row.save()

    except Exception, e:
        logger.error("An error occurred trying to save the daily status count.")
        logger.error(e)
