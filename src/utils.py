from datetime import datetime, timedelta


def generate_datetime_strings(initial_date: str, final_date: str, dt: int=1 ) -> list[str]:
    """Return 10-minute timestamps from the start through the end date, inclusive.

    Dates must be provided in ``YYYYMMDD`` format. Returned timestamps use
    ``YYYYMMDDHH:MM:SS`` format, from 00:00:00 through 23:50:00 each day.
    """
    start = datetime.strptime(initial_date, "%Y%m%d")
    end_date = datetime.strptime(final_date, "%Y%m%d")
    if start > end_date:
        raise ValueError("initial_date must be on or before final_date")

    end = end_date + timedelta(days=1) - timedelta(minutes=10)
    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current.strftime("%Y%m%d%H:%M:%S"))
        current += timedelta(minutes=dt)

    return timestamps
