import json

from engine.scheduler import TimetableScheduler
from output.html_output import generate_html


def main():

    # load input
    with open("input/testcase.json") as f:
        data = json.load(f)

    # create scheduler
    scheduler = TimetableScheduler(data)

    # generate schedule
    schedule = scheduler.run()

    if not schedule:
        print("No timetable could be generated")
        return

    # generate HTML output
    generate_html(schedule, scheduler.activities, data)

    print("Timetable generated successfully!")
    print("Open timetable.html in browser")


if __name__ == "__main__":
    main()