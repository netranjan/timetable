def minutes_to_time(m):
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}"