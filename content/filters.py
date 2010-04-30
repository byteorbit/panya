from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

from content.models import ModelBase

import django_filters
    
from secretballot.models import Vote
from django.contrib.contenttypes.models import ContentType

class IntervalFilter(django_filters.DateRangeFilter):
    """
    Filters queryset on week (in reality the last 7 days) or month.
    """
    options = {
        'week': (_('This Week'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
            '%s__lt' % name: (datetime.today()+timedelta(days=1)).strftime('%Y-%m-%d'),
        })),
        'month': (_('This Month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: datetime.today().year,
            '%s__month' % name: datetime.today().month
        })),
    }
    def filter(self, qs, value):
        try:
            return self.options[value][1](qs, self.name)
        except KeyError:
            return qs

class OrderFilter(django_filters.ChoiceFilter):
    """
    Ordering filter ordering queryset items by most-recent(by created)
    or most-liked(with score being calculated by positive votes).
    """
    options = {
        'most-recent': (_('Most Recent'), lambda qs, name: qs.order_by('-%s' % name)),
        'most-liked': (_('Most Liked'), lambda qs, name: qs.extra(
            select={
                'vote_score': '(SELECT COUNT(*) from %s WHERE vote=1 AND object_id=%s.%s AND content_type_id=%s) - (SELECT COUNT(*) from %s WHERE vote=-1 AND object_id=%s.%s AND content_type_id=%s)' % (Vote._meta.db_table, qs.model._meta.db_table, qs.model._meta.pk.attname, ContentType.objects.get_for_model(qs.model).id, Vote._meta.db_table, qs.model._meta.db_table, qs.model._meta.pk.attname, ContentType.objects.get_for_model(qs.model).id)}).order_by('-vote_score')),
    }
    def filter(self, qs, value):
        try:
            return self.options[value][1](qs, self.name)
        except KeyError:
            return qs

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [(key, value[0]) for key, value in self.options.iteritems()]
        super(OrderFilter, self).__init__(*args, **kwargs)

class IntervalOrderFilterSet(django_filters.FilterSet):
    """
    Filters queryset through an IntervalFilter('interval').
    Orders queryset through an OrderFilter('order').
    """
    interval = IntervalFilter(
        name="created",
        label="Filter By",
    )
    order = OrderFilter(
        name="created",
        label="Order By",
    )

    def __init__(self, data=None, queryset=None, prefix=None, action_url=''):
        self.action_url = action_url 
        super(IntervalOrderFilterSet, self).__init__(data, queryset, prefix)
        
    class Meta:
        model = ModelBase
        fields = ['order', 'interval']
