/* ----------------------------------------------------------------------
   rep_dashboard.js   (loaded from <script type="module"> in rep.html)
---------------------------------------------------------------------- */
import { renderLine } from "/static/js/chat_common.js";
import { io }         from "https://cdn.socket.io/4.7.5/socket.io.esm.min.js";

/* ── Socket.IO ------------------------------------------------------ */
const socket = io({ path: "/socket.io", query: { role: "rep" } });
socket.on("connect", () => socket.emit("iam_rep"));

/* ── globals tied to DOM ------------------------------------------- */
let messagesPane, pastPane, historyList;
let lists   = {};             // { active:<ul>, new:<ul> }
let activeVisitor = null;     // SID of visitor currently in live chat
const typingDots  = new Map();   // { visitor_sid ➜ <div…> }
const TYPING_MS = 3000;
let typingTimer;

/* ── DOM ready ------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", () => {
  /* grab elements once */
  messagesPane = document.getElementById("messages");
  pastPane     = document.getElementById("pastTranscript");
  historyList  = document.getElementById("historyList");
  const form   = document.getElementById("chatForm");
  const inp    = document.getElementById("msgInput");
  const disc   = document.getElementById("disconnectBtn");
  
  const banner   = document.getElementById("soundBanner");
  const enableBt = document.getElementById("enableAudioBtn");
  const ping     = new Audio("/chat/static/audio/new_chat.mp3");
  
  function unlockAudio() {
    ping.play()
        .then(() => {
          ping.pause();
          banner?.remove();
        })
        .catch(() => {});
  }
  
  enableBt?.addEventListener("click", unlockAudio);

  lists = {
    active : document.getElementById("visitorList"),
    new    : document.getElementById("newChatList")
  };

  /* -------------------------------------------------------------- */
  /* socket listeners                                               */
  /* -------------------------------------------------------------- */
  socket.on("visitor_msg", d => renderLine(d, messagesPane));
  socket.on("rep_msg",     d => renderLine(d, messagesPane));
  socket.on("system",      d => renderLine(d, messagesPane));

  socket.on("visitor_online",  ({ sid, username }) => placeIn("active", sid, username));
  socket.on("visitor_offline", ({ sid })           => drop(sid));

  socket.on("new_chat", ({ sid, username }) => {
    placeIn("new", sid, username);
    ping.currentTime = 0;
    ping.play().catch(()=>{});
  });
  socket.on("new_chat_remove", ({ sid }) => drop(sid));

  /* typing from visitor */
  socket.on("typing", ({ sid, is_typing }) => {
    if (sid !== activeVisitor) return;
    if (is_typing) {
      if (!typingDots.has(sid)) {
        const d = document.createElement("div");
        d.className = "msg visitor";
        d.innerHTML = '<p class="bubble">…</p>';
        messagesPane.appendChild(d);
        typingDots.set(sid, d);
      }
    } else {
      const d = typingDots.get(sid);
      if (d) d.remove();
      typingDots.delete(sid);
    }
  });

  /* past-chat side-panel */
  socket.on("session_list", list => {
    historyList.innerHTML = "";
    list.forEach(addHistoryRow);
  });
  socket.on("history_result", list => {
    pastPane.innerHTML = "";
    list.forEach(l => renderLine(l, pastPane, "rep"));
  });
  socket.on("live_chat_ready", hideTranscript);

  /* -------------------------------------------------------------- */
  /* form / input handlers                                          */
  /* -------------------------------------------------------------- */
  form.onsubmit = e => {
    e.preventDefault();
    if (!activeVisitor) {
      renderLine({ body:"Select a visitor first.", author:"system", ts:Date.now() }, messagesPane);
      return;
    }
    const txt = inp.value.trim();
    if (!txt) return;
    socket.emit("rep_msg", txt);
    renderLine({ body:txt, author:"rep", ts:Date.now() }, messagesPane);
    inp.value = "";
  };

  inp.oninput = () => {
    socket.emit("rep_typing", { is_typing:true });
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() =>
      socket.emit("rep_typing", { is_typing:false }), TYPING_MS);
  };

  disc.onclick = () => {
    if (!activeVisitor) return;
    socket.emit("leave_visitor", { sid: activeVisitor });
    activeVisitor = null;
    messagesPane.innerHTML = "";
    hideTranscript();
    historyList.innerHTML = "";
  };

  /* list row click (delegated) */
  document.addEventListener("click", e => {
    const li = e.target.closest("li[data-sid]");
    if (li) joinVisitor(li.dataset.sid);
  });
});

/* ---------------- helper funcs ------------------------------------ */
function row(sid, username){
  const li = document.createElement("li");
  li.dataset.sid = sid;
  li.className   = "px-2 py-1 cursor-pointer hover:bg-gray-100";
  li.textContent = username ? `${username} (${sid.slice(0,8)})`
                            : sid.slice(0,8);
  li.onclick = () => joinVisitor(sid);
  return li;
}
function placeIn(key, sid, username){
  document.querySelectorAll(`li[data-sid="${sid}"]`).forEach(el => el.remove());
  lists[key].appendChild(row(sid, username));
}
function drop(sid){
  document.querySelectorAll(`li[data-sid="${sid}"]`).forEach(el => el.remove());
}

/* transcript panel */
function showTranscript(){
  pastPane.classList.remove("hidden");
  pastPane.innerHTML = "";
}
function hideTranscript(){
  pastPane.classList.add("hidden");
  pastPane.innerHTML = '<p class="text-center text-slate-500">Select a chat ↑</p>';
}
function addHistoryRow({ chat_id, label, opened }){
  const li = document.createElement("li");
  li.dataset.chat = chat_id;
  li.className = "px-2 py-1 cursor-pointer hover:bg-gray-100";
  li.textContent = `Chat ${label} • ${opened.slice(0,10)}`;
  li.onclick = () => viewOldChat(chat_id);
  historyList.appendChild(li);
}
function viewOldChat(id){
  document.querySelectorAll("#historyList li").forEach(li =>
    li.classList.toggle("bg-blue-50", li.dataset.chat == id));
  showTranscript();
  socket.emit("history_request", { chat_id: id });
}

/* join live visitor */
export function joinVisitor(sid){
  if (activeVisitor === sid) return;
  activeVisitor = sid;
  messagesPane.innerHTML = "";
  drop(sid);                           // remove from lists
  socket.emit("join_visitor", { sid });
}