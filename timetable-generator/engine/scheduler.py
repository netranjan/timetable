import random


class Activity:

    def __init__(self, id, year, subject, teacher, type,
                 batch=None, duration=1, labs=None, rooms=None):

        self.id = id
        self.year = year
        self.subject = subject
        self.teacher = teacher
        self.type = type
        self.batch = batch
        self.duration = duration
        self.labs = labs or []
        self.rooms = rooms or []


class TimetableScheduler:

    def __init__(self, data):

        self.data = data

        self.activities = []
        self.slots = []
        self.domains = {}
        self.schedule = {}

        self.teacher_busy = {}
        self.batch_busy = {}

        self.activity_conflicts = {}

        self.slots_per_day = data["calendar"]["slots_per_day"]

        self.generate_slots()
        self.generate_activities()
        self.build_conflict_graph()
        self.build_domains()


    # -----------------------
    # SLOT GENERATION
    # -----------------------

    def generate_slots(self):

        days = self.data["calendar"]["days"]

        slot_id = 1

        for day in days:
            for s in range(1, self.slots_per_day + 1):

                self.slots.append({
                    "id": slot_id,
                    "day": day,
                    "index": s
                })

                slot_id += 1


    # -----------------------
    # ACTIVITY GENERATION
    # -----------------------

    def generate_activities(self):

        aid = 1

        for year in self.data["years"]:

            batches = year["batches"]

            for subject in year["subjects"]:

                # lectures
                for _ in range(subject["weekly_lectures"]):

                    self.activities.append(
                        Activity(
                            f"A{aid}",
                            year["id"],
                            subject["name"],
                            subject["teacher"],
                            "lecture",
                            rooms=subject["lecture_rooms"]
                        )
                    )

                    aid += 1

                # practicals
                for batch in batches:

                    for _ in range(subject["practicals_per_batch"]):

                        self.activities.append(
                            Activity(
                                f"A{aid}",
                                year["id"],
                                subject["name"],
                                subject["teacher"],
                                "practical",
                                batch=batch,
                                duration=subject["practical_duration"],
                                labs=subject["labs"]
                            )
                        )

                        aid += 1


    # -----------------------
    # CONFLICT GRAPH
    # -----------------------

    def build_conflict_graph(self):

        for a in self.activities:

            conflicts = []

            for b in self.activities:

                if a.id == b.id:
                    continue

                if a.teacher == b.teacher:
                    conflicts.append(b.id)

                if a.batch and b.batch:
                    if a.year == b.year and a.batch == b.batch:
                        conflicts.append(b.id)

            self.activity_conflicts[a.id] = conflicts


    # -----------------------
    # DOMAIN BUILDER
    # -----------------------

    def build_domains(self):

        for activity in self.activities:

            valid = []

            for slot in self.slots:

                if self.valid_initial(activity, slot):
                    valid.append(slot["id"])

            self.domains[activity.id] = valid


    def valid_initial(self, activity, slot):

        year = next(y for y in self.data["years"]
                    if y["id"] == activity.year)

        if slot["index"] in year["break_slots"]:
            return False

        if slot["index"] + activity.duration - 1 > self.slots_per_day:
            return False

        return True


    # -----------------------
    # ACTIVITY SELECTION
    # -----------------------

    def select_activity(self):

        unscheduled = [
            a for a in self.activities
            if a.id not in self.schedule
        ]

        if not unscheduled:
            return None

        unscheduled.sort(key=lambda a: (
            len(self.domains[a.id]),
            -a.duration
        ))

        if len(self.domains[unscheduled[0].id]) == 0:
            return None

        return unscheduled[0]


    # -----------------------
    # SLOT VALIDATION
    # -----------------------

    def slot_valid(self, activity, slot):

        for i in range(activity.duration):

            s = slot + i

            if (activity.teacher, s) in self.teacher_busy:
                return False

            if activity.batch:
                if (activity.year, activity.batch, s) in self.batch_busy:
                    return False

        return True


    # -----------------------
    # ASSIGN
    # -----------------------

    def assign(self, activity, slot):

        self.schedule[activity.id] = slot

        for i in range(activity.duration):

            s = slot + i

            self.teacher_busy[(activity.teacher, s)] = True

            if activity.batch:
                self.batch_busy[(activity.year, activity.batch, s)] = True


    # -----------------------
    # UNASSIGN
    # -----------------------

    def unassign(self, activity, slot):

        del self.schedule[activity.id]

        for i in range(activity.duration):

            s = slot + i

            del self.teacher_busy[(activity.teacher, s)]

            if activity.batch:
                del self.batch_busy[(activity.year, activity.batch, s)]


    # -----------------------
    # FORWARD CHECKING
    # -----------------------

    def forward_check(self, activity, slot):

        removed = []

        for conflict in self.activity_conflicts[activity.id]:

            if conflict in self.schedule:
                continue

            domain = self.domains[conflict]

            for i in range(activity.duration):

                s = slot + i

                if s in domain:

                    domain.remove(s)
                    removed.append((conflict, s))

                    if not domain:
                        return None

        return removed


    def restore_domains(self, removed):

        for act, slot in removed:
            self.domains[act].append(slot)


    # -----------------------
    # SEARCH
    # -----------------------

    def search(self):

        activity = self.select_activity()

        if activity is None:

            if len(self.schedule) == len(self.activities):
                return True

            return False

        for slot in self.domains[activity.id][:]:

            if self.slot_valid(activity, slot):

                self.assign(activity, slot)

                removed = self.forward_check(activity, slot)

                if removed is not None:

                    if self.search():
                        return True

                    self.restore_domains(removed)

                self.unassign(activity, slot)

        return False


    # -----------------------
    # RUN
    # -----------------------

    def run(self):

        success = self.search()

        if not success:
            print("No valid schedule found")

        return self.schedule