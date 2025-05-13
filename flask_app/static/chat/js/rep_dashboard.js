(() => {
  const listVis  = document.getElementById("visitorList");
  const listNew  = document.getElementById("newChatList");
  const win   = document.getElementById("chatWindow");
  const head  = document.getElementById("chatHeading");
  const form  = document.getElementById("repForm");
  const input = document.getElementById("repInput");

  let currentVisitor = null;
  const socket = io();
  socket.on("connect", () => socket.emit("iam_rep"));

  /* ── sync lists from server ───────────────────────────── */
  socket.on("visitor_online",  ({ sid }) => addLI(listVis, sid));
  socket.on("visitor_offline", ({ sid }) => {
  removeLI(sid);                           // already exists
  if (currentVisitor === sid) {            // you were chatting with them
    head.textContent = "Chat";
    win.innerHTML = "";
    currentVisitor = null;
  }
});
  socket.on("new_chat",        ({ sid }) => {
    removeLI(sid);                    // move from visitors →
    addLI(listNew, sid);              //               → new-chats
  });
  socket.on("new_chat_remove", ({ sid }) => removeLI(sid));
  
  const short = sid => sid.slice(0, 8);

  function addLI(ul, sid) {
    if (sid === socket.id || document.getElementById(sid)) return;
    const li = document.createElement("li");
    li.id = sid;
    li.textContent = short(sid);
    li.className = "cursor-pointer underline text-blue-600";
    li.onclick = () => selectVisitor(sid);
    ul.appendChild(li);
  }

  function removeLI(sid) {
    const li = document.getElementById(sid);
    li && li.remove();
  }

  /* ── selecting a visitor ────────── */
  function selectVisitor(sid) {
    head.textContent = `Now chatting with: ${short(sid)}`;
    win.innerHTML = "";
    removeLI(sid);                         // from whichever list
    currentVisitor = sid;
    socket.emit("join_visitor", { sid });
  }
  
  /* ── disconnect flow ─────────────────────────────── */
document.getElementById("disconnectBtn").onclick = () => {
  if (!currentVisitor) {
    alert("You’re not chatting with anyone.");
    return;
  }

  if (!confirm("End this chat?")) return;      // native Yes/No modal

  socket.emit("leave_visitor", { sid: currentVisitor });

  // UI reset
  head.textContent = "Chat";
  currentVisitor = null;
  win.innerHTML = "";
};

  /* ── chat flow ──────────────────── */
  form.addEventListener("submit", e => {
    e.preventDefault();
    if (!currentVisitor) return alert("Pick a visitor first!");
    socket.emit("rep_msg", input.value);
    append("me", input.value);
    input.value = "";
  });

  socket.on("visitor_msg", t => append("them", t));
  socket.on("system",      t => append("sys",  t));

  function append(who, text) {
    const div = document.createElement("div");
    div.className = `my-0.5 ${ who === "me" ? "text-right" :
                               who === "sys" ? "italic text-gray-500 text-center" :
                               ""}`;
    div.textContent = text;
    win.appendChild(div);
    win.scrollTop = win.scrollHeight;
  }
})();