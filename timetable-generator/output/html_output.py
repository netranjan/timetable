def generate_html(schedule, activities, data):

    days = data["calendar"]["days"]
    slots_per_day = data["calendar"]["slots_per_day"]

    class_map = {}
    teacher_map = {}
    lab_map = {}

    for activity in activities:

        if activity.id not in schedule:
            continue

        slot = schedule[activity.id]

        class_map.setdefault(activity.year, {})
        class_map[activity.year][slot] = activity

        teacher_map.setdefault(activity.teacher, {})
        teacher_map[activity.teacher][slot] = activity

        if activity.type == "practical":
            for lab in activity.labs:
                lab_map.setdefault(lab, {})
                lab_map[lab][slot] = activity

    html = """
<html>
<head>

<style>

body{
font-family:Arial;
background:#f4f6f7;
margin:20px;
}

h1{
text-align:center;
}

.tabs{
text-align:center;
margin-bottom:20px;
}

.tabs button{
padding:10px 20px;
margin:5px;
border:none;
background:#3498db;
color:white;
cursor:pointer;
border-radius:5px;
}

.tabs button:hover{
background:#2980b9;
}

table{
border-collapse:collapse;
width:100%;
margin-bottom:40px;
background:white;
}

th,td{
border:1px solid #ccc;
padding:8px;
text-align:center;
}

th{
background:#2c3e50;
color:white;
}

.break{
background:#f5b7b1;
}

.lecture{
background:#d6eaf8;
}

.practical{
background:#d5f5e3;
}

.section{
display:none;
}

</style>

<script>

function showSection(id){

let sections=document.getElementsByClassName("section")

for(let s of sections){
s.style.display="none"
}

document.getElementById(id).style.display="block"

}

</script>

</head>

<body>

<h1>Academic Timetable</h1>

<div class="tabs">
<button onclick="showSection('class')">Class Timetable</button>
<button onclick="showSection('teacher')">Teacher Timetable</button>
<button onclick="showSection('lab')">Lab Timetable</button>
</div>

"""

    # -------------------------
    # CLASS TIMETABLE
    # -------------------------

    html += "<div id='class' class='section' style='display:block'>"
    html += "<h2>Class Timetables</h2>"

    for year in data["years"]:

        year_id = year["id"]
        breaks = year["break_slots"]

        html += f"<h3>{year_id}</h3>"
        html += "<table>"

        html += "<tr><th>Day</th>"

        for s in range(1, slots_per_day + 1):
            html += f"<th>{s}</th>"

        html += "</tr>"

        for d_index, day in enumerate(days):

            html += f"<tr><td><b>{day}</b></td>"

            for s in range(1, slots_per_day + 1):

                slot = d_index * slots_per_day + s

                if s in breaks:
                    html += "<td class='break'>BREAK</td>"
                    continue

                activity = class_map.get(year_id, {}).get(slot)

                if not activity:
                    html += "<td></td>"
                    continue

                if activity.type == "lecture":

                    cell = f"{activity.subject}<br>{activity.teacher}"
                    html += f"<td class='lecture'>{cell}</td>"

                else:

                    cell = f"{activity.subject}<br>Batch {activity.batch}"
                    html += f"<td class='practical'>{cell}</td>"

            html += "</tr>"

        html += "</table>"

    html += "</div>"


    # -------------------------
    # TEACHER TIMETABLE
    # -------------------------

    html += "<div id='teacher' class='section'>"
    html += "<h2>Teacher Timetables</h2>"

    for teacher in teacher_map:

        html += f"<h3>{teacher}</h3>"
        html += "<table>"

        html += "<tr><th>Day</th>"

        for s in range(1, slots_per_day + 1):
            html += f"<th>{s}</th>"

        html += "</tr>"

        for d_index, day in enumerate(days):

            html += f"<tr><td><b>{day}</b></td>"

            for s in range(1, slots_per_day + 1):

                slot = d_index * slots_per_day + s

                activity = teacher_map.get(teacher, {}).get(slot)

                if not activity:
                    html += "<td></td>"
                    continue

                cell = f"{activity.subject}<br>{activity.year}"
                html += f"<td class='lecture'>{cell}</td>"

            html += "</tr>"

        html += "</table>"

    html += "</div>"


    # -------------------------
    # LAB TIMETABLE
    # -------------------------

    html += "<div id='lab' class='section'>"
    html += "<h2>Lab Timetables</h2>"

    for lab in lab_map:

        html += f"<h3>{lab}</h3>"
        html += "<table>"

        html += "<tr><th>Day</th>"

        for s in range(1, slots_per_day + 1):
            html += f"<th>{s}</th>"

        html += "</tr>"

        for d_index, day in enumerate(days):

            html += f"<tr><td><b>{day}</b></td>"

            for s in range(1, slots_per_day + 1):

                slot = d_index * slots_per_day + s

                activity = lab_map.get(lab, {}).get(slot)

                if not activity:
                    html += "<td></td>"
                    continue

                cell = f"{activity.subject}<br>{activity.year} Batch {activity.batch}"
                html += f"<td class='practical'>{cell}</td>"

            html += "</tr>"

        html += "</table>"

    html += "</div>"

    html += "</body></html>"

    with open("timetable.html", "w") as f:
        f.write(html)