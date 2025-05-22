/* ----------------------------------------------------------------------
   rep_dashboard.js      (ES-module — import from <script type="module">)
---------------------------------------------------------------------- */
import { renderLine } from "/static/js/chat_common.js";
import { io }         from "https://cdn.socket.io/4.7.5/socket.io.esm.min.js";

/* -------------------- socket setup ---------------------------------- */
const socket = io({
  path : "/socket.io",
  query: { role: "rep" }
});

socket.on("connect", () => {
  socket.emit("iam_rep");
});

/* -------------------- globals that need DOM ------------------------- */
let messagesPane   = null;   // <div id="messages">
let activeVisitor  = null;   // SID of visitor currently in chat

/* -------------------- DOM ready ------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  /* panes & form elements */
  messagesPane = document.getElementById("messages");
  const form   = document.getElementById("chatForm");
  const inp    = document.getElementById("msgInput");
  const historyList = document.getElementById("historyList");
  const disconnectBtn = document.getElementById("disconnectBtn");
  
  socket.on("visitor_msg", data => renderLine(data, messagesPane));
  socket.on("system",      data => renderLine(data, messagesPane));
  socket.on("visitor_online",  ({ sid, username }) => placeIn("active", sid, username));
  socket.on("visitor_offline", ({ sid }) => drop(sid));

  socket.on("new_chat",        ({ sid, username }) => placeIn("new", sid, username));
  socket.on("new_chat_remove", ({ sid }) => drop(sid));

  socket.on("session_list", list => {
    historyList.innerHTML = "";
    list.forEach(addHistoryRow);
  });

  form.addEventListener("submit", e => {
    e.preventDefault();
    if (!activeVisitor) return;

    const text = inp.value.trim();
    if (!text) return;
    
    socket.emit("rep_msg", text);
    renderLine({ body: text, author: "rep", ts: Date.now() }, messagesPane);
    inp.value = "";
  });

  document.addEventListener("click", e => {
    const li = e.target.closest("li[data-sid]");
    if (li) joinVisitor(li.dataset.sid);
  });

  disconnectBtn.addEventListener("click", () => {
    if (!activeVisitor) return;
    socket.emit("leave_visitor", { sid: activeVisitor });
    activeVisitor = null;
    messagesPane.innerHTML = "";
  });
});

const lists = {
  active : document.getElementById("visitorList"),
  new    : document.getElementById("newChatList")
};

/* -------------------- visitor list helpers -------------------------- */
function row(sid, username) {
  const li = document.createElement("li");
  li.dataset.sid = sid;
  li.className   = "px-2 py-1 cursor-pointer hover:bg-gray-100";
  li.textContent = username
      ? `${username} (${sid.slice(0, 8)})`
      : sid.slice(0, 8);
  li.onclick     = () => joinVisitor(sid);
  return li;
}

function placeIn(listKey, sid, username) {
  document.querySelectorAll(`li[data-sid="${sid}"]`).forEach(el => el.remove());
  lists[listKey].appendChild(row(sid, username));
}

function drop(sid) {
  document.querySelectorAll(`li[data-sid="${sid}"]`).forEach(el => el.remove());
}

function addHistoryRow({ chat_id, label, opened, closed }) {
  const li = document.createElement("li");
  li.dataset.chat = chat_id;
  li.textContent = `Chat ${label} • ${opened.slice(0,10)}`; 
  li.onclick = () => viewOldChat(chat_id);
  historyList.appendChild(li);
}

function viewOldChat(chat_id) {
  document.querySelectorAll("#historyList li")
          .forEach(li => li.classList.remove("bg-blue-50"));
  const li = document.querySelector(`#historyList li[data-chat='${chat_id}']`);
  if (li) li.classList.add("bg-blue-50");
  // Clear the message pane and label it read-only
  document.getElementById("chatForm").style.display = "none";
  messagesPane.dataset.readonly = "1";
  socket.emit("history_request", { chat_id });
}

socket.on("history_result", list => {
  messagesPane.innerHTML = "";
  list.forEach(line => renderLine(line, messagesPane));
});

socket.on("live_chat_ready", () => {
  document.getElementById("chatForm").style.display = "";
  delete messagesPane.dataset.readonly;
});


/* -------------------- join a visitor chat --------------------------- */
export function joinVisitor(sid) {
  if (activeVisitor === sid) return;
  activeVisitor        = sid;
  if (messagesPane) messagesPane.innerHTML = "";
  drop(sid);
  socket.emit("join_visitor", { sid });
}