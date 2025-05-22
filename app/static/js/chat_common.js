// /static/js/chat_common.js
//--------------------------------------------------------------------------
// Escape anything that could become HTML so people can’t inject tags
export function escape(str = "") {
  return str.replace(/[&<>"']/g, s =>
    ({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;" }[s])
  );
}

/* ---  NEW: parse ts safely, treating bare ISO strings as UTC  ---------- */
function toDate(ts) {
  if (typeof ts === "string") {
    if (!ts.endsWith("Z") && !/[+-]\d\d:\d\d$/.test(ts)) ts += "Z";
    return new Date(ts);
  }
  return new Date(ts);
}

export function pretty(ts) {
  return toDate(ts).toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" });
}

/**
 * Render one chat line.
 * @param {object|string} line   Packet or raw string (system)
 * @param {HTMLElement}  pane   Container (<div id="messages">)
 */
export function renderLine({ author, body, ts }, container) {
  const div = document.createElement("div");
  div.className = `msg ${author}`;
  div.innerHTML = `
    <p class="bubble">${escape(body)}</p>
    <time>${pretty(ts)}</time>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}