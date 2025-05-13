document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll(".logo-wrapper svg path")
    .forEach((p,i)=>{
      const len=p.getTotalLength();
      p.style.strokeDasharray=len;
      p.style.strokeDashoffset=len;
      p.style.animationDelay=`${i*0.06}s`;  // stagger
    });
});