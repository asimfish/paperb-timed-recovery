"use strict";
window.calibrationLoaded = false;
const assetBase = document.body.dataset.assetBase;
function element(tag, text, className) { const node = document.createElement(tag); if (text != null) node.textContent = text; if (className) node.className = className; return node; }
function badgeClass(status) { if (status.startsWith("PASS_")) return "pass"; if (status.startsWith("FAIL") || status.startsWith("REJECT") || status === "FAILED_RETAINED") return "failure"; if (status.startsWith("UNKNOWN")) return "unknown"; return "pending"; }
function render(data) {
  if (!data || data.schema !== "PaperBCalibrationPublicStatus/1" || !Array.isArray(data.cases) || data.cases.length !== 5) throw new Error("Five source-bound cases required");
  const tbody = document.querySelector("#case-table tbody"); tbody.replaceChildren();
  let audited = 0;
  for (const item of data.cases) {
    const tr = element("tr"); tr.dataset.caseId = item.case_id;
    const name = element("td"); name.append(element("span", item.title, "case-name"), element("span", item.case_id, "case-id"));
    const question = element("td", item.question);
    const windowCell = element("td"); windowCell.append(element("span", `${item.controlled_steps} 步`), element("span", `POST ${item.window[0]}–${item.window[1]} · 49 点`, "case-id"));
    const state = element("td", null, "case-state"); state.append(element("span", item.label, `pill ${badgeClass(item.audit_status || item.execution_status)}`));
    state.append(element("p", item.note));
    if (item.audit_status) { audited++; state.append(element("span", item.audit_status, "case-id")); }
    if (item.mechanism) state.append(element("p", item.mechanism));
    const links = element("td", null, "case-links");
    for (const [label, key] of [["审计报告 ↗", "report_url"], ["49 点序列 ↗", "series_url"]]) {
      if (item[key]) { const a = element("a", label); a.href = item[key]; links.append(a); }
    }
    if (!links.children.length) links.append(element("span", "尚无审计材料", "note"));
    tr.append(name, question, windowCell, state, links); tbody.append(tr);
  }
  document.getElementById("case-count").textContent = `${audited} / 5 项已有实际审计报告`;
  document.getElementById("current-summary").textContent = data.summary;
  document.getElementById("updated").textContent = `来源快照 · ${data.generated_at_utc}`;
  const v02 = document.getElementById("v02-state"); v02.textContent = data.batch_label; v02.className = `pill ${badgeClass(data.batch_status)}`;
  const img = document.getElementById("figure-image");
  if (data.figure && data.figure.available) {
    img.src = data.figure.svg_url; img.hidden = false; document.getElementById("figure-placeholder").hidden = true;
    if (data.figure.pdf_url) { const pdf = document.getElementById("figure-pdf"); pdf.href = data.figure.pdf_url; pdf.hidden = false; }
    document.getElementById("figure-caption").textContent = data.figure.caption;
  }
  if (data.links) for (const [id, key] of [["paper-link","paper"],["paper-link-bottom","paper"],["protocol-link","protocol"]]) if (data.links[key]) document.getElementById(id).href = data.links[key];
  window.calibrationData = data; window.calibrationLoaded = true;
}
fetch(`${assetBase}/DATA/status.json`, {cache:"no-store"}).then(response => { if (!response.ok) throw new Error(`Status HTTP ${response.status}`); return response.json(); }).then(render).catch(error => {
  const warning = document.getElementById("load-error"); warning.hidden = false; warning.dataset.failure = error.message;
  document.getElementById("current-summary").textContent = "实际证据尚未成功载入，不能判断本轮结果。";
});
