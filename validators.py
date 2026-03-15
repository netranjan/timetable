def slot_invalid(sl, dur, break_slots):
    return any((sl + k) in break_slots for k in range(dur))


def teacher_blocked(teacher, d, sl, dur, unavailability):

    if teacher not in unavailability:
        return False

    if d not in unavailability[teacher]:
        return False

    blocked = unavailability[teacher][d]

    return any((sl + k) in blocked for k in range(dur))


def lab_blocked(lab, d, sl, dur, unavailability):

    if lab not in unavailability:
        return False

    if d not in unavailability[lab]:
        return False

    blocked = unavailability[lab][d]

    return any((sl + k) in blocked for k in range(dur))