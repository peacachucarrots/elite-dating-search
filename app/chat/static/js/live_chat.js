/* ----------------------------------------------------------------------
   live_chat.js  (loaded from every page that includes the widget)
---------------------------------------------------------------------- */
import { io }            from "https://cdn.socket.io/4.7.5/socket.io.esm.min.js";
import { renderLine }    from "/static/js/chat_common.js";

(() => {
  const chatBox = document.getElementById("chatbox");
  if (!chatBox) return;                 // page doesn’t include widget

  const messagesPane = document.getElementById("messages");
  const form   = document.getElementById("chatForm");
  const input  = document.getElementById("msgInput");
  const ratingBox  = document.getElementById("ratingBox");
  const toggleBtn = chatBox.querySelector('header .toggle');
  const starBtns = document.querySelectorAll("#ratingBox .rate-btn");

  /* open / collapse */
  const updateIcon = () => {
    toggleBtn.textContent = chatBox.classList.contains('collapsed') ? '▲' : '▼';
  };
  updateIcon();
  toggleBtn.addEventListener('click', () => {
    chatBox.classList.toggle('collapsed');
    updateIcon();
  });

  /* Socket.IO ------------------------------------------------------ */
  const socket = io({ path:"/socket.io", query:{ role:"visitor" } });

  /* quick-reply menu ----------------------------------------------- */
  let quickBox = null, currentOptions=[];
  function buildMenu(opts){
    currentOptions = opts;
    if (quickBox) quickBox.remove();
    quickBox = document.createElement("div");
    opts.forEach(opt => {
      const btn = Object.assign(document.createElement("button"), {
        textContent: opt.label,
        className: "mr-2 mb-2 px-3 py-1 rounded bg-slate-200 hover:bg-slate-300"
      });
      btn.onclick = () => {
        socket.emit("visitor_msg", `__faq__:${opt.id}`);
        quickBox.remove();
        if (opt.id === "human") currentOptions = [];     // stop redraws
      };
      quickBox.appendChild(btn);
    });
    messagesPane.appendChild(quickBox);
    messagesPane.scrollTop = messagesPane.scrollHeight;
  }

  /* incoming ------------------------------------------------------- */
  socket.on("quick_options", ({ options }) => buildMenu(options));

  socket.on("visitor_msg", d => {
    renderLine(d, messagesPane);
    if (d.author === "assistant" && currentOptions.length)
      buildMenu(currentOptions);
  });
 socket.on("rep_msg", d => {
  if (repDot) { repDot.remove(); repDot = null; }
  renderLine(d, messagesPane);
});
  socket.on("system",   d => renderLine(d, messagesPane));
  socket.on("disconnect", () =>
    renderLine({ author:"system", body:"Chat disconnected…", ts:Date.now() }, messagesPane)
  );
  socket.on("chat_closed", () => {
  form.style.display = "none";      // hide input
  ratingBox.classList.remove("hidden");   // show ★-rating
});

  /* typing bubbles from rep --------------------------------------- */
  let repDot=null;
  socket.on("rep_typing", ({ is_typing }) => {
    if (is_typing) {
      if (!repDot){
        repDot = document.createElement("div");
        repDot.className = "msg rep";
        repDot.innerHTML = '<p class="bubble">…</p>';
        messagesPane.appendChild(repDot);
        messagesPane.scrollTop = messagesPane.scrollHeight;
      }
    } else if (repDot){
      repDot.remove();
      repDot=null;
    }
  });

  /* outgoing visitor line ----------------------------------------- */
  form.onsubmit = e => {
    e.preventDefault();
    const txt=input.value.trim();
    if(!txt) return;
    socket.emit("visitor_msg", txt);
    renderLine({author:"visitor",body:txt,ts:Date.now()}, messagesPane);
    socket.emit("typing", { is_typing: false });  // tell visitor
		typingState = false;
    input.value="";
  };

  document.querySelectorAll(".rate-btn").forEach(btn => {
  btn.onclick = () => {
    const score = +btn.dataset.score;           // 1-5
    socket.emit("satisfaction", { score });     // send to server

    ratingBox.innerHTML = "<p>Thanks for your feedback!</p>";
    
    const newBtn = document.createElement("button");
    newBtn.textContent = "Start new chat";
    newBtn.className = "mt-2 px-3 py-1 rounded bg-blue-600 text-white";
    newBtn.onclick = () => window.location.reload();
    ratingBox.appendChild(newBtn);
  };
});

starBtns.forEach(btn => {
  const setFill = idx => {
    starBtns.forEach((b, i) => {
      b.style.color = i < idx ? "var(--brand-gold)" : "#cbd5e1";
    });
  };

  btn.addEventListener("mouseenter", () => setFill(+btn.dataset.score));
  btn.addEventListener("mouseleave", () => setFill(0));

  btn.addEventListener("click", () => setFill(+btn.dataset.score));
});

let typingState = false;
input.oninput = () => {
  const hasText = input.value.trim().length > 0;

  if (hasText && !typingState) {                 // started typing
    socket.emit("typing", { is_typing: true });
    typingState = true;
  } else if (!hasText && typingState) {          // cleared box
    socket.emit("typing", { is_typing: false });
    typingState = false;
  }
};
})();