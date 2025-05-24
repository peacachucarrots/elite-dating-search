/* ----------------------------------------------------------------------
   rep_dashboard.js  (ES-module)
---------------------------------------------------------------------- */
import { renderLine } from "/static/js/chat_common.js";
import { io }         from "https://cdn.socket.io/4.7.5/socket.io.esm.min.js";

/* -------------------- socket setup ---------------------------------- */
const socket = io({ path: "/socket.io", query: { role: "rep" } });
socket.on("connect", () => socket.emit("iam_rep"));

/* -------------------- globals --------------------------------------- */
let messagesPane   = null;   // <div id="messages">
let pastPane       = null;   // <div id="pastTranscript">
let historyList    = null;   // <ul id="historyList">
let lists          = {};     // { active:<ul>, new:<ul> }
let activeVisitor  = null;   // SID of visitor currently in chat

/* ==================== DOM ready ===================================== */
document.addEventListener("DOMContentLoaded", () => {
  /* grab all elements once */
  messagesPane  = document.getElementById("messages");
  pastPane      = document.getElementById("pastTranscript");
  historyList   = document.getElementById("historyList");
  const form    = document.getElementById("chatForm");
  const inp     = document.getElementById("msgInput");
  const discBtn = document.getElementById("disconnectBtn");

  /* left-pane lists */
  lists = {
    active : document.getElementById("visitorList"),
    new    : document.getElementById("newChatList")
  };

  /* ------------- socket listeners (DOM safe) ----------------------- */
  socket.on("visitor_msg", data => renderLine(data, messagesPane));
  socket.on("system",      data => renderLine(data, messagesPane));

  socket.on("visitor_online",  ({ sid, username }) => placeIn("active", sid, username));
  socket.on("visitor_offline", ({ sid }) => drop(sid));
  socket.on("new_chat",        ({ sid, username }) => placeIn("new",    sid, username));
  socket.on("new_chat_remove", ({ sid }) => drop(sid));

  socket.on("session_list", list => {
    historyList.innerHTML = "";
    list.forEach(addHistoryRow);
  });

  socket.on("history_result", list => {
    pastPane.innerHTML = "";
    list.forEach(line => renderLine(line, pastPane, "rep"));
  });

  socket.on("live_chat_ready", () => {
    hideTranscript();
  });

  /* ------------- form submit & buttons ----------------------------- */
  form.addEventListener("submit", e => {
    e.preventDefault();
    if (!activeVisitor) return;
    const text = inp.value.trim();
    if (!text) return;

    socket.emit("rep_msg", text);                         // to server
    renderLine({ body:text, author:"rep", ts:Date.now() }, messagesPane);
    inp.value = "";
  });

  discBtn.addEventListener("click", () => {
    if (!activeVisitor) return;
    socket.emit("leave_visitor", { sid: activeVisitor });
    activeVisitor = null;
    messagesPane.innerHTML = "";
    hideTranscript();
    historyList.innerHTML = "";
  });

  /* row click (delegate) */
  document.addEventListener("click", e => {
    const li = e.target.closest("li[data-sid]");
    if (li) joinVisitor(li.dataset.sid);
  });
});

/* ==================== helper functions ============================== */
function row(sid, username){
  const li = document.createElement("li");
  li.dataset.sid = sid;
  li.className   = "px-2 py-1 cursor-pointer hover:bg-gray-100";
  li.textContent = username ? `${username} (${sid.slice(0,8)})`
                            : sid.slice(0,8);
  li.onclick = () => joinVisitor(sid);
  return li;
}

function placeIn(listKey, sid, username){
  document.querySelectorAll(`li[data-sid="${sid}"]`).forEach(el => el.remove());
  lists[listKey].appendChild(row(sid, username));
}

function drop(sid){
  document.querySelectorAll(`li[data-sid="${sid}"]`).forEach(el => el.remove());
}

/* ----- transcript helpers ------------------------------------------ */
function showTranscript(){
  pastPane.classList.remove("hidden");
  pastPane.innerHTML = "";
}
function hideTranscript(){
  pastPane.classList.add("hidden");
  pastPane.innerHTML =
    '<p class="text-center text-slate-500">Select a chat ↑</p>';
}

function addHistoryRow({ chat_id, label, opened }){
  const li = document.createElement("li");
  li.dataset.chat = chat_id;
  li.className = "px-2 py-1 cursor-pointer hover:bg-gray-100";
  li.textContent = `Chat ${label} • ${opened.slice(0,10)}`; // YYYY-MM-DD
  li.onclick = () => viewOldChat(chat_id);
  historyList.appendChild(li);
}

function viewOldChat(chat_id){
  document.querySelectorAll("#historyList li").forEach(li =>
    li.classList.toggle("bg-blue-50", li.dataset.chat == chat_id));

  showTranscript();
  socket.emit("history_request", { chat_id });
}

/* ----- join live visitor chat -------------------------------------- */
export function joinVisitor(sid){
  if (activeVisitor === sid) return;
  activeVisitor  = sid;
  messagesPane.innerHTML = "";
  drop(sid);
  socket.emit("join_visitor", { sid });
}