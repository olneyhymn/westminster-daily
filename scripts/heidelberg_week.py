"""
Shared Heidelberg Weekly week-number calculation.

Week 1 begins on the first Sunday of January of the current year; each
week runs Sunday through Saturday. Days before the first Sunday of
January belong to week 52 of the previous cycle, and a 53rd Sunday
(which occurs in years with 53 Sundays, e.g. 2028) repeats week 52
rather than wrapping back to week 1 early.

Used by the Makefile to pick the index page's week and importable by
the feed generator so the two can never disagree.
"""

import datetime as dt


def first_sunday_of_january(year, tzinfo=None):
    jan_1 = dt.datetime(year, 1, 1, tzinfo=tzinfo)
    days_until_sunday = (6 - jan_1.weekday()) % 7
    return jan_1 + dt.timedelta(days=days_until_sunday)


def week_number_for_date(date):
    """Return the Heidelberg week number (1-52) for a datetime."""
    first_sunday = first_sunday_of_january(date.year, date.tzinfo)
    if date < first_sunday:
        return 52
    week = (date - first_sunday).days // 7 + 1
    return min(week, 52)


if __name__ == "__main__":
    print(f"{week_number_for_date(dt.datetime.now()):02d}")
