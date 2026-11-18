/**
 * Office Script: PreSurveyIntake
 * Called by Power Automate each time someone submits the AI pre-survey (Microsoft Forms).
 *  1. Adds the response to ResponsesTable on the "Responses" sheet.
 *  2. Rebuilds the "Group Summary" sheet: one row per class code.
 *  3. Returns an email subject and HTML body (the participant's answers + their class's running group result).
 * Ratings may arrive as "4" (Rating question) or "4 – ..." (Choice question); both are read correctly.
 */

interface IntakeResult {
  subject: string;
  html: string;
}

const LEVEL_NAMES = ["Prompt engineering", "Workflow engineering", "Agentic & harness engineering"];
const Q_LABELS = [
  "One-shot comprehensive prompt",
  "Structured prompt (role, context, task, format, constraints)",
  "Diagnose and fix a bad answer",
  "Reusable prompts / templates / projects",
  "Break a task into AI-ready steps",
  "Chain prompts (output feeds next step)",
  "Connect AI to tools (Zapier, Make, n8n, Power Automate)",
  "Build checks and human review into workflows",
  "Explain chatbot vs workflow vs agent",
  "Give an agent tools and limit its access",
  "Design the harness (instructions, memory, guardrails, evals)",
  "Run a multi-step agent with little supervision",
];
const THRESHOLD = 3.5;
const HEADERS = [
  "Submitted", "Class code", "Name", "Email", "Role", "AI use", "Tools",
  "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12",
  "L1 avg", "L2 avg", "L3 avg", "Suggested level", "Task to hand to AI", "What makes it worthwhile",
];
const SUMMARY_HEADERS = [
  "Class code", "Responses", "Avg L1 Prompt", "Avg L2 Workflow", "Avg L3 Agentic",
  "Suggested cohort start", "People at L1", "People at L2", "People at L3", "People at L3+",
  "Group note", "Most used tools", "Last response",
];

function main(
  workbook: ExcelScript.Workbook,
  submitted: string,
  classCode: string,
  name: string,
  email: string,
  role: string,
  aiUse: string,
  tools: string,
  q1: string, q2: string, q3: string, q4: string,
  q5: string, q6: string, q7: string, q8: string,
  q9: string, q10: string, q11: string, q12: string,
  task: string,
  goal: string
): IntakeResult {
  const code = (classCode || "").trim().toUpperCase() || "NO-CODE";
  const ratings = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12].map(toRating);
  const avgs = [0, 1, 2].map(l => avgOf(ratings.slice(l * 4, l * 4 + 4)));
  const toolList = parseTools(tools);

  // 1. Append the response
  const table = getResponsesTable(workbook);
  const row: (string | number)[] = [
    submitted || new Date().toISOString(), code, (name || "").trim(), (email || "").trim(), (role || "").trim(),
    aiUse || "", toolList.join(", "),
    ...ratings.map(r => (isNaN(r) ? "" : r)),
    round1(avgs[0]), round1(avgs[1]), round1(avgs[2]), levelOf(avgs),
    (task || "").trim(), (goal || "").trim(),
  ];
  const body = table.getRangeBetweenHeaderAndTotal();
  const existing = body.getValues();
  const onlyBlankRow = existing.length === 1 && existing[0].every(v => v === "" || v === null);
  if (onlyBlankRow) {
    body.getRow(0).setValues([row]);
  } else {
    table.addRow(-1, row);
  }

  // 2. Rebuild the group summary for every class
  const all = table.getRangeBetweenHeaderAndTotal().getValues()
    .filter(r => String(r[1]).trim() !== "");
  const classes = Array.from(new Set(all.map(r => String(r[1])))).sort();
  const summaryRows = classes.map(c => summarise(c, all.filter(r => String(r[1]) === c)));
  writeSummary(workbook, summaryRows);

  // 3. Build the email for this class
  const mine = summaryRows[classes.indexOf(code)];
  return {
    subject: `AI pre-survey: ${(name || "New response").trim()} (${code}) · ${mine.n} response${mine.n === 1 ? "" : "s"} so far`,
    html: buildEmail(code, name, email, role, aiUse, toolList, ratings, avgs, task, goal, mine),
  };
}

// ---------- helpers ----------
interface ClassSummary {
  code: string; n: number; avg: number[]; start: string;
  counts: { [k: string]: number }; note: string; topTools: string; last: string;
}

function toRating(v: string): number {
  const n = parseFloat(String(v || "").trim());
  return n >= 1 && n <= 5 ? n : NaN;
}
function avgOf(xs: number[]): number {
  const ok = xs.filter(x => !isNaN(x));
  return ok.length ? ok.reduce((a, b) => a + b, 0) / ok.length : 0;
}
function round1(x: number): number { return Math.round(x * 10) / 10; }
function levelOf(a: number[]): string {
  if (a[0] < THRESHOLD) return "L1";
  if (a[1] < THRESHOLD) return "L2";
  if (a[2] < THRESHOLD) return "L3";
  return "L3+";
}
function parseTools(raw: string): string[] {
  const s = (raw || "").trim();
  if (!s) return [];
  try {
    const arr = JSON.parse(s) as string[];
    if (Array.isArray(arr)) return arr.map((x: string) => String(x).trim()).filter((x: string) => x !== "");
  } catch (e) { /* not JSON */ }
  return s.split(/[;,]/).map(x => x.trim()).filter(x => x);
}
function esc(s: string): string {
  return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function getResponsesTable(workbook: ExcelScript.Workbook): ExcelScript.Table {
  let table = workbook.getTable("ResponsesTable");
  if (table) return table;
  let sheet = workbook.getWorksheet("Responses") || workbook.addWorksheet("Responses");
  const hdr = sheet.getRangeByIndexes(0, 0, 1, HEADERS.length);
  hdr.setValues([HEADERS]);
  table = workbook.addTable(sheet.getRangeByIndexes(0, 0, 2, HEADERS.length), true);
  table.setName("ResponsesTable");
  return table;
}

function summarise(code: string, rows: (string | number | boolean)[][]): ClassSummary {
  const avg = [19, 20, 21].map(i => round1(avgOf(rows.map(r => Number(r[i])))));
  const counts: { [k: string]: number } = { L1: 0, L2: 0, L3: 0, "L3+": 0 };
  rows.forEach(r => { const k = String(r[22]); if (k in counts) counts[k]++; });
  const start = levelOf(avg);
  const n = rows.length;
  const biggest = Math.max(counts.L1, counts.L2, counts.L3, counts["L3+"]);
  let note = "Fairly even group: one shared starting point should work.";
  if (n < 3) note = "Too few responses to judge the group yet.";
  else if (biggest / n < 0.6) note = "Mixed group: plan extra support for the lower end and stretch tasks for the top.";
  const toolCount: { [k: string]: number } = {};
  rows.forEach(r => String(r[6]).split(",").map(t => t.trim()).filter(t => t)
    .forEach(t => { toolCount[t] = (toolCount[t] || 0) + 1; }));
  const topTools = Object.keys(toolCount).sort((a, b) => toolCount[b] - toolCount[a]).slice(0, 4)
    .map(t => `${t} (${toolCount[t]})`).join(", ");
  return { code, n, avg, start, counts, note, topTools, last: String(rows[rows.length - 1][0]) };
}

function writeSummary(workbook: ExcelScript.Workbook, rows: ClassSummary[]) {
  const sheet = workbook.getWorksheet("Group Summary") || workbook.addWorksheet("Group Summary");
  sheet.getRange("A4:M1000").clear(ExcelScript.ClearApplyTo.contents);
  sheet.getRangeByIndexes(3, 0, 1, SUMMARY_HEADERS.length).setValues([SUMMARY_HEADERS]);
  if (!rows.length) return;
  const values = rows.map(s => [
    s.code, s.n, s.avg[0], s.avg[1], s.avg[2], startLabel(s.start),
    s.counts.L1, s.counts.L2, s.counts.L3, s.counts["L3+"], s.note, s.topTools, s.last,
  ]);
  sheet.getRangeByIndexes(4, 0, values.length, SUMMARY_HEADERS.length).setValues(values);
  sheet.getRangeByIndexes(4, 2, values.length, 3).setNumberFormatLocal("0.0");
}

function startLabel(l: string): string {
  if (l === "L1") return "Level 1 · Prompt engineering";
  if (l === "L2") return "Level 2 · Workflow engineering";
  if (l === "L3") return "Level 3 · Agentic & harness engineering";
  return "Advanced Level 3";
}

function bar(v: number, color: string): string {
  const w = Math.round((v / 5) * 160);
  return `<span style="display:inline-block;width:160px;height:8px;background:#e3e6ec;border-radius:4px;vertical-align:middle">` +
    `<span style="display:block;width:${w}px;height:8px;background:${color};border-radius:4px"></span></span>`;
}

function buildEmail(code: string, name: string, email: string, role: string, aiUse: string, tools: string[],
  ratings: number[], avgs: number[], task: string, goal: string, g: ClassSummary): string {
  const colors = ["#0f8a6a", "#1f4fd1", "#7a3fc4"];
  const td = "padding:4px 8px;border-bottom:1px solid #eceef2;";
  const ratingRows = ratings.map((r, i) =>
    `${i % 4 === 0 ? `<tr><td colspan="2" style="padding:10px 8px 4px;font-weight:600;color:${colors[Math.floor(i / 4)]}">Level ${Math.floor(i / 4) + 1} · ${LEVEL_NAMES[Math.floor(i / 4)]} (avg ${round1(avgs[Math.floor(i / 4)]).toFixed(1)})</td></tr>` : ""}` +
    `<tr><td style="${td}">Q${i + 1}. ${esc(Q_LABELS[i])}</td><td style="${td}text-align:right;font-family:Consolas,monospace">${isNaN(r) ? "–" : r}</td></tr>`
  ).join("");
  const groupRows = [0, 1, 2].map(l =>
    `<tr><td style="${td}">Level ${l + 1} · ${LEVEL_NAMES[l]}</td><td style="${td}">${bar(g.avg[l], colors[l])}</td>` +
    `<td style="${td}text-align:right;font-family:Consolas,monospace">${g.avg[l].toFixed(1)}</td></tr>`
  ).join("");
  return `<div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#151a24;max-width:640px">
<p style="font-size:12px;color:#5b6475;margin:0">AI PRE-SURVEY · CLASS ${esc(code)}</p>
<h2 style="margin:4px 0 14px;font-size:20px">New response from ${esc(name || "a participant")}</h2>
<p style="margin:0 0 4px"><b>Email:</b> ${esc(email || "–")}<br><b>Role:</b> ${esc(role || "–")}<br>
<b>AI use today:</b> ${esc(aiUse || "–")}<br><b>Tools used:</b> ${esc(tools.join(", ") || "–")}</p>

<h3 style="margin:22px 0 6px;font-size:16px">Group result so far · ${esc(code)} (${g.n} response${g.n === 1 ? "" : "s"})</h3>
<table style="border-collapse:collapse;width:100%">${groupRows}</table>
<p style="margin:10px 0 0"><b>Suggested cohort starting point:</b> ${esc(startLabel(g.start))}<br>
<b>Spread:</b> L1 ${g.counts.L1} · L2 ${g.counts.L2} · L3 ${g.counts.L3} · L3+ ${g.counts["L3+"]}<br>
<span style="color:#5b6475">${esc(g.note)}</span></p>

<h3 style="margin:22px 0 6px;font-size:16px">This participant's ratings (1–5)</h3>
<table style="border-collapse:collapse;width:100%">${ratingRows}</table>

<h3 style="margin:22px 0 6px;font-size:16px">In their words</h3>
<p style="margin:0 0 8px"><b>Task they want AI to take off their plate:</b><br>${esc(task || "–")}</p>
<p style="margin:0"><b>What would make the training worth it:</b><br>${esc(goal || "–")}</p>
<p style="margin:22px 0 0;font-size:12px;color:#5b6475">The participant did not see any score. Full data is in the "AI Pre-Survey Responses" workbook on your OneDrive.</p>
</div>`;
}
