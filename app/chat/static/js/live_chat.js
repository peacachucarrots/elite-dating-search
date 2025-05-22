/* static/js/live_chat.js */
import { io }      from "https://cdn.socket.io/4.7.5/socket.io.esm.min.js";
import { renderLine as baseRenderLine } from "/static/js/chat_common.js";

(() => {
  // ────────── DOM hooks ──────────
  const chatBox = document.getElementById("chatbox");
  if (!chatBox) return;                         // page doesn’t include the widget

  const messagesPane = document.getElementById("messages");
  const form     = document.getElementById("chatForm");
  const input    = document.getElementById("msgInput");
  const toggle   = chatBox.querySelector(".toggle");

  // ────────── local-storage keys & limits ──────────
  const OPEN_KEY   = "chatboxOpen";             // "true" | "false"
  const LOG_KEY    = "chatboxLog";              // JSON array of { who, body, ts }
  const MAX_STORED = 200;                       // rotate beyond this length

  // ────────── Socket.IO setup ──────────
  const socket = io({
  path : "/socket.io",
  query: { role: "visitor" }
});

  // incoming
  socket.on("visitor_msg", data => renderLine(data, messagesPane));
  socket.on("rep_msg",     data => renderLine(data, messagesPane));
  socket.on("system",      txt  => renderLine(txt,  messagesPane));
  socket.on("disconnect", () =>
    renderLine({ author: "system", body: "Chat disconnected…", ts: Date.now() }, messagesPane)
  );
  socket.on("chat_closed", () => {
  form.style.display = "none";         // hide input row
  ratingBox.classList.remove("hidden"); // show 1-5 stars (or buttons)
});

/* rating buttons */
document.querySelectorAll(".rate-btn").forEach(btn => {
  btn.onclick = () => {
    const score = +btn.dataset.score;
    socket.emit("satisfaction", { score });
    ratingBox.innerHTML = "<p>Thanks for your feedback!</p>";

    const newBtn = document.createElement("button");
    newBtn.textContent = "Start new chat";
    newBtn.onclick = () => window.location.reload();
    ratingBox.appendChild(newBtn);
  };
});

  // outgoing
  form.addEventListener("submit", e => {
    e.preventDefault();
    const txt = input.value.trim();
    if (!txt) return;

    socket.emit("visitor_msg", txt);                            // send to server
    renderLine({ author: "visitor", body: txt, ts: Date.now() }, messagesPane); // echo locally
    input.value = "";
  });

  function renderLine(line, target) {
  baseRenderLine(line, target);
}

  // ────────── open / collapse state ──────────
  let isOpen = localStorage.getItem(OPEN_KEY) === "true";
  if (isOpen) chatBox.classList.remove("collapsed");
  toggle.textContent = isOpen ? "▼" : "▲";

  toggle.addEventListener("click", () => {
    isOpen = !chatBox.classList.toggle("collapsed");
    toggle.textContent = isOpen ? "▼" : "▲";
    localStorage.setItem(OPEN_KEY, isOpen);
  });
})();