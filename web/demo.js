// Demo mode for the static GitHub Pages build: there is no backend there, so the two
// Gemma calls return the sample data below. Turn it on locally with ?demo.

const DEMO = location.hostname.endsWith("github.io") || new URLSearchParams(location.search).has("demo");

const DEMO_CLASSES = [
  { code: "CS201", course: "Data Structures", type: "Lecture", day: "Mon", start: "09:00", end: "11:00", room: "LT1", lecturer: "Dr. Okafor" },
  { code: "MA210", course: "Linear Algebra", type: "Lecture", day: "Mon", start: "11:05", end: "12:30", room: "B204", lecturer: "Prof. Mensah" },
  { code: "CS201", course: "Data Structures", type: "Lab", day: "Tue", start: "14:00", end: "17:00", room: "Lab 3", lecturer: "Ms. Achieng" },
  { code: "PH150", course: "Physics for Engineers", type: "Lecture", day: "Wed", start: "08:00", end: "10:00", room: "LT2", lecturer: "Dr. Banda" },
  { code: "EN105", course: "Technical Writing", type: "Tutorial", day: "Wed", start: "09:30", end: "11:00", room: "C12", lecturer: "Mr. Mwangi" },
  { code: "MA210", course: "Linear Algebra", type: "Tutorial", day: "Thu", start: "10:00", end: "11:00", room: "B110", lecturer: "Prof. Mensah" },
  { code: "PH150", course: "Physics for Engineers", type: "Lab", day: "Thu", start: "11:00", end: "13:00", room: "Lab 1", lecturer: "Dr. Banda" },
  { code: "CS220", course: "Databases", type: "Lecture", day: "Thu", start: "13:00", end: "15:00", room: "LT1", lecturer: "Dr. Nyambura" },
  { code: "CS220", course: "Databases", type: "Lab", day: "Fri", start: "10:00", end: "12:00", room: "Lab 2", lecturer: "Mr. Otieno" },
];

const DEMO_TIPS = [
  { title: "Fix the Wednesday clash first.", detail: "PH150 and EN105 overlap from 09:30 to 10:00. Ask about another EN105 tutorial group before the add/drop deadline." },
  { title: "Plan the Monday room change.", detail: "You have 5 minutes to get from LT1 to B204. Sit near the exit in CS201 and pack up a minute early." },
  { title: "Use Tuesday morning for Linear Algebra.", detail: "Your day starts at 14:00, so 09:00 to 12:00 is a good block for MA210 problem sets." },
  { title: "Eat before Thursday.", detail: "Thursday runs from 10:00 to 15:00 with no break. Bring lunch, and review Databases notes on Wednesday evening." },
  { title: "Turn Friday afternoon into weekly review.", detail: "After the CS220 lab you are free. Spend an hour going over the week's notes while they are fresh." },
];

const pause = ms => new Promise(r => setTimeout(r, ms));

async function demoExtract() {
  await pause(1500);
  return DEMO_CLASSES.map(c => ({ ...c }));
}

async function demoTips() {
  await pause(1200);
  return DEMO_TIPS;
}
