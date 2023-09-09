import datetime as dt

NOW_DATE = dt.datetime.now().date()


def object_filter(obj):
    result = obj.filter(
        pub_date__lte=NOW_DATE,
        is_published=True,
        category__is_published=True
    )
    return result
