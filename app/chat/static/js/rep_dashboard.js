/* ----------------------------------------------------------------------
   rep_dashboard.js   (loaded via <script type="module"> in rep.html)
---------------------------------------------------------------------- */
import { renderLine } from "/static/js/chat_common.js";
import { io }         from "https://cdn.socket.io/4.7.5/socket.io.esm.min.js";

/* ── Socket.IO ------------------------------------------------------ */
const socket = io({ path: "/socket.io", query: { role: "rep" } });
socket.on("connect", () => socket.emit("iam_rep"));

/* ── globals tied to DOM ------------------------------------------- */
let messagesPane, pastPane, historyList, markBtn;
let lists   = {};
let liveSID = null;
const typingDots  = new Map();
const TYPING_MS   = 3000;
let typingState = false;

/* ── DOM ready ------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", () => {
  messagesPane = document.getElementById("messages");
  pastPane     = document.getElementById("pastTranscript");
  historyList  = document.getElementById("historyList");
  const form   = document.getElementById("chatForm");
  const inp    = document.getElementById("msgInput");
  const disc   = document.getElementById("disconnectBtn");
  markBtn = document.getElementById("markEmailBtn");

  /* optional audio ping */
  const banner   = document.getElementById("soundBanner");
  const enableBt = document.getElementById("enableAudioBtn");
  const ping     = new Audio("/chat/static/audio/new_chat.mp3");
  enableBt?.addEventListener("click", () =>
    ping.play().then(()=>{ ping.pause(); banner?.remove(); }).catch(()=>{}));

  lists = {
    live : document.getElementById("visitorList"),
    new  : document.getElementById("newChatList"),
    prev : document.getElementById("afterHoursList"),
  };

  /* -------------------------------------------------------------- */
  /* socket listeners                                               */
  /* -------------------------------------------------------------- */
  socket.on("visitor_msg", d => {
  removeTypingBubble(d.sid);
  renderLine(d, messagesPane);
});
  socket.on("rep_msg",     d => renderLine(d, messagesPane));
  socket.on("system",      d => renderLine(d, messagesPane));

  /* ---- visitor presence ---------------------------------------- */
  socket.on("visitor_online",  ({ sid, username }) => addRow("live", sid, username));
  socket.on("visitor_offline", ({ sid }) => dropRow(sid));

  /* ---- new chat inside office hours ---------------------------- */
  socket.on("new_chat", ({ sid, username }) => {
    addRow("new", sid, username);
    ping.currentTime = 0; ping.play().catch(()=>{});
  });
  socket.on("new_chat_remove", ({ sid }) => dropRow(sid));
  socket.on("prev_chat_remove", ({ chat_id }) =>
  document.querySelectorAll(`li[data-id="${chat_id}"]`).forEach(el => el.remove()));

  /* ---- previous-day chats -------------------------------------- */
  socket.on("after_hours_chat",
  ({ chat_id, username, email, preview }) => addRow("prev", chat_id, username, preview, "prev", email));
      
  /* ---- typing indicator from visitor --------------------------- */
  socket.on("typing", ({ sid, is_typing }) => {        
    if (sid !== liveSID) return;
    if (is_typing) {
      if (!typingDots.has(sid)) {
        const dot = document.createElement("div");
        dot.className = "msg visitor";
        dot.innerHTML = '<p class="bubble">…</p>';
        messagesPane.appendChild(dot);
        typingDots.set(sid, dot);
        messagesPane.scrollTop = messagesPane.scrollHeight;
      }
    } else {
      typingDots.get(sid)?.remove();
      typingDots.delete(sid);
    }
  });

  /* ---- historical side-panel ----------------------------------- */
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
    if (!liveSID) {
      renderLine({ body:"Select a live visitor first.",
                   author:"system", ts:Date.now() }, messagesPane);
      return;
    }
    const txt = inp.value.trim();
    if (!txt) return;
    socket.emit("rep_msg", txt);
    renderLine({ body:txt, author:"rep", ts:Date.now() }, messagesPane);
    socket.emit("rep_typing", { is_typing: false });
    typingState = false;
    removeTypingBubble(liveSID);
    inp.value = "";
  };

  inp.oninput = () => {
  if (!liveSID) return;
  const hasText = inp.value.trim().length > 0;

  if (hasText && !typingState) {
    socket.emit("rep_typing", { is_typing: true });
    typingState = true;
  } else if (!hasText && typingState) {
    socket.emit("rep_typing", { is_typing: false });
    typingState = false;
  }
};

  disc.onclick = () => {
    if (!liveSID) return;
    socket.emit("leave_visitor", { sid: liveSID });
    liveSID = null;
    messagesPane.innerHTML = "";
    hideTranscript();
    historyList.innerHTML = "";
  };

  markBtn.onclick = () => {
  const chatId = markBtn.dataset.chatId;
  if (!chatId) return;

  socket.emit("mark_replied", { chat_id: chatId });
  messagesPane.innerHTML =
    '<p class="text-sm text-slate-500">Marked as replied via e-mail.</p>';
  markBtn.classList.add("hidden");
};

  /* ---- list row click (event delegation) ----------------------- */
  document.addEventListener("click", e => {
    const li = e.target.closest("li[data-id]");
    if (li) openChat(li);
  });
 });

/* ---------------- helper funcs ------------------------------------ */

/* create or update a <li> row */
function addRow(listKey, id, username, preview = "", type = "live", email = "") {
  document.querySelectorAll(`li[data-id="${id}"]`).forEach(el => el.remove());

  const li = document.createElement("li");
  li.dataset.id    = id;
  li.dataset.type  = type;
  li.dataset.email = email;
  li.className     = "px-2 py-1 cursor-pointer hover:bg-gray-100";

  li.innerHTML =
    `<strong>${username ?? "(anon)"}</strong>
     ${email ? `<span class="block text-xs text-slate-400">${email}</span>` : ""}
     ${preview ? `<span class="block text-xs text-slate-500 truncate">${preview}</span>` : ""}`;

  lists[listKey].appendChild(li);
}

/* drop row by id */
function dropRow(id){
  document.querySelectorAll(`li[data-id="${id}"]`).forEach(el => el.remove());
}

/* open either a live chat or an after-hours transcript */
function openChat(li) {
  const isPrev = li.dataset.type === "prev";
  const payload = isPrev
                    ? { chat_id: li.dataset.id }
                    : { sid:     li.dataset.id };

  liveSID = isPrev ? null : li.dataset.id;
  messagesPane.innerHTML = "";
  hideTranscript();
  historyList.innerHTML = "";
  setLiveUI(!isPrev);

  socket.emit("join_visitor", payload);

  // store current chat_id on the button for later
  markBtn.dataset.chatId = li.dataset.id;
}

/* transcript panel */
function showTranscript(){
  pastPane.classList.remove("hidden");
  pastPane.innerHTML = "";
}
function hideTranscript(){
  pastPane.classList.add("hidden");
  pastPane.innerHTML =
    '<p class="text-center text-slate-500">Select a chat ↑</p>';
}

function removeTypingBubble(sid) {
  typingDots.get(sid)?.remove();
  typingDots.delete(sid);
}

function setLiveUI(isLive) {
  document.getElementById("chatForm").classList.toggle("hidden", !isLive);
  markBtn.classList.toggle("hidden",  isLive);
}

/* add a previous session row */
function addHistoryRow({ chat_id, label, opened }){
  const li = document.createElement("li");
  li.dataset.chat = chat_id;
  li.className = "px-2 py-1 cursor-pointer hover:bg-gray-100";
  li.textContent = `Chat ${label} • ${opened.slice(0,10)}`;
  li.onclick = () => viewOldChat(chat_id);
  historyList.appendChild(li);
}
function viewOldChat(id){
  historyList.querySelectorAll("li").forEach(li =>
    li.classList.toggle("bg-blue-50", li.dataset.chat == id));
  showTranscript();
  socket.emit("history_request", { chat_id: id });
}