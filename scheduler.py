from ortools.sat.python import cp_model
from collections import defaultdict

from utils import minutes_to_time
from validators import slot_invalid, teacher_blocked, lab_blocked


def build_and_solve(config):

    days = config["days"]
    slots_per_day = config["slots_per_day"]

    slot_duration = config["slot_duration_minutes"]
    start_min = config["day_start_minute"]

    labs = config["labs"]
    batches = config["batches"]
    teachers = config["teachers"]

    teacher_unavailability = config.get("teacher_unavailability", {})
    lab_unavailability = config.get("lab_unavailability", {})
    break_slots = config.get("break_slots", [])

    subjects = config["subjects"]
    year_rooms = config["year_rooms"]

    GAP_WEIGHT = 20
    LATE_WEIGHT = 1
    CONSEC_WEIGHT = 15

    model = cp_model.CpModel()

    lecture_data = []
    practical_data = []

    teacher_slot_vars = defaultdict(list)
    year_slot_vars = defaultdict(list)
    lab_slot_vars = defaultdict(list)
    batch_slot_vars = defaultdict(list)

    teacher_day_all = defaultdict(list)
    subject_day_vars = defaultdict(list)

    penalties = []

    # ---------------- LECTURES ----------------

    for subj in subjects:

        lec = subj.get("lectures_per_week", 0)
        dur = subj.get("lecture_duration_slots", 1)

        teacher = subj["teacher"]
        year = subj["year"]
        name = subj["name"]

        for i in range(lec):

            placements = []

            for d in range(days):

                for sl in range(slots_per_day - dur + 1):

                    if slot_invalid(sl, dur, break_slots):
                        continue

                    if teacher_blocked(teacher, d, sl, dur, teacher_unavailability):
                        continue

                    v = model.NewBoolVar(f"L_{name}_{i}_{d}_{sl}")

                    lecture_data.append((v, subj, d, sl, dur))
                    placements.append(v)

                    teacher_day_all[(teacher, d)].append(v)
                    subject_day_vars[(year, name, d)].append(v)

                    penalties.append(v * sl * LATE_WEIGHT)

                    for k in range(dur):

                        slot = sl + k

                        teacher_slot_vars[(teacher, d, slot)].append(v)
                        year_slot_vars[(year, d, slot)].append(v)

            if not placements:
                raise ValueError(f"No valid placement for lecture {name}")

            model.Add(sum(placements) == 1)

    # ---------------- PRACTICALS ----------------

    for subj in subjects:

        prac = subj.get("practicals_per_week", 0)

        if prac == 0:
            continue

        dur = subj["practical_duration_slots"]
        year = subj["year"]
        teacher = subj["teacher"]
        name = subj["name"]

        for batch in batches[year]:

            for i in range(prac):

                placements = []

                for d in range(days):

                    for sl in range(slots_per_day - dur + 1):

                        if slot_invalid(sl, dur, break_slots):
                            continue

                        if teacher_blocked(teacher, d, sl, dur, teacher_unavailability):
                            continue

                        for lab in labs:

                            if lab_blocked(lab, d, sl, dur, lab_unavailability):
                                continue

                            v = model.NewBoolVar(
                                f"P_{name}_{batch}_{i}_{d}_{sl}_{lab}"
                            )

                            practical_data.append(
                                (v, subj, batch, lab, d, sl, dur)
                            )

                            placements.append(v)

                            teacher_day_all[(teacher, d)].append(v)

                            penalties.append(v * sl * LATE_WEIGHT)

                            for k in range(dur):

                                slot = sl + k

                                teacher_slot_vars[(teacher, d, slot)].append(v)
                                year_slot_vars[(year, d, slot)].append(v)
                                lab_slot_vars[(lab, d, slot)].append(v)
                                batch_slot_vars[(batch, d, slot)].append(v)

                if not placements:
                    raise ValueError(
                        f"No valid placement for practical {name} batch {batch}"
                    )

                model.Add(sum(placements) == 1)

    # ---------------- HARD CONSTRAINTS ----------------

    for vars_list in teacher_slot_vars.values():
        model.Add(sum(vars_list) <= 1)

    for vars_list in lab_slot_vars.values():
        model.Add(sum(vars_list) <= 1)

    for vars_list in year_slot_vars.values():
        model.Add(sum(vars_list) <= 1)

    for vars_list in batch_slot_vars.values():
        model.Add(sum(vars_list) <= 1)

    for vars_list in subject_day_vars.values():
        model.Add(sum(vars_list) <= 1)

    for teacher in teachers:

        max_lec = teachers[teacher]["max_lectures_per_day"]

        for d in range(days):

            if (teacher, d) in teacher_day_all:

                model.Add(sum(teacher_day_all[(teacher, d)]) <= max_lec)

    # ---------------- TEACHING SLOT VARIABLES ----------------

    teacher_teach = defaultdict(dict)

    for (teacher, d, slot), vars_list in teacher_slot_vars.items():

        teach = model.NewBoolVar(f"teach_{teacher}_{d}_{slot}")

        model.Add(sum(vars_list) >= 1).OnlyEnforceIf(teach)
        model.Add(sum(vars_list) <= 0).OnlyEnforceIf(teach.Not())

        teacher_teach[(teacher, d)][slot] = teach

    # ---------------- GAP MINIMIZATION ----------------

    for (teacher, d), slots in teacher_teach.items():

        slot_ids = sorted(slots.keys())

        before = {}
        after = {}

        for s in slot_ids:

            before[s] = model.NewBoolVar(f"before_{teacher}_{d}_{s}")
            after[s] = model.NewBoolVar(f"after_{teacher}_{d}_{s}")

        for i, s in enumerate(slot_ids):

            earlier = [slots[x] for x in slot_ids[:i]]
            later = [slots[x] for x in slot_ids[i+1:]]

            if earlier:
                model.Add(sum(earlier) >= 1).OnlyEnforceIf(before[s])
                model.Add(sum(earlier) <= 0).OnlyEnforceIf(before[s].Not())
            else:
                model.Add(before[s] == 0)

            if later:
                model.Add(sum(later) >= 1).OnlyEnforceIf(after[s])
                model.Add(sum(later) <= 0).OnlyEnforceIf(after[s].Not())
            else:
                model.Add(after[s] == 0)

        for s in slot_ids:

            teach = slots[s]

            idle = model.NewBoolVar(f"idle_{teacher}_{d}_{s}")

            model.Add(teach == 0).OnlyEnforceIf(idle)
            model.Add(teach == 1).OnlyEnforceIf(idle.Not())

            gap = model.NewBoolVar(f"gap_{teacher}_{d}_{s}")

            model.AddBoolAnd([before[s], after[s], idle]).OnlyEnforceIf(gap)
            model.AddBoolOr(
                [before[s].Not(), after[s].Not(), idle.Not()]
            ).OnlyEnforceIf(gap.Not())

            penalties.append(gap * GAP_WEIGHT)

    # ---------------- PREVENT 3 CONSECUTIVE LECTURES ----------------

    for (teacher, d), slots in teacher_teach.items():

        slot_ids = sorted(slots.keys())

        for i in range(len(slot_ids) - 2):

            s1 = slots[slot_ids[i]]
            s2 = slots[slot_ids[i + 1]]
            s3 = slots[slot_ids[i + 2]]

            consec = model.NewBoolVar(
                f"three_consecutive_{teacher}_{d}_{i}"
            )

            model.Add(s1 + s2 + s3 >= 3).OnlyEnforceIf(consec)
            model.Add(s1 + s2 + s3 <= 2).OnlyEnforceIf(consec.Not())

            penalties.append(consec * CONSEC_WEIGHT)

    # ---------------- OBJECTIVE ----------------

    model.Minimize(sum(penalties))

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return {"status": "error", "message": "No feasible timetable found"}

    lectures = []
    practicals = []

    for v, s, d, sl, dur in lecture_data:

        if solver.Value(v):

            start = start_min + sl * slot_duration
            end = start + dur * slot_duration

            room = year_rooms[s["year"]]

            lectures.append({
                "subject": s["name"],
                "year": s["year"],
                "room": room,
                "day": d + 1,
                "start": minutes_to_time(start),
                "end": minutes_to_time(end),
                "teacher": s["teacher"]
            })

    for v, s, b, lab, d, sl, dur in practical_data:

        if solver.Value(v):

            start = start_min + sl * slot_duration
            end = start + dur * slot_duration

            practicals.append({
                "subject": s["name"],
                "year": s["year"],
                "batch": b,
                "lab": lab,
                "day": d + 1,
                "start": minutes_to_time(start),
                "end": minutes_to_time(end),
                "teacher": s["teacher"]
            })

    return {
        "status": "success",
        "lectures": lectures,
        "practicals": practicals
    }