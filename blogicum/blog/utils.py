import datetime as dt

NOW_DATE = dt.datetime.now().date()


def object_filter(obj):
    return obj.filter(
        pub_date__lte=NOW_DATE,
        is_published=True,
        category__is_published=True,
        location__is_published=True,
    )
