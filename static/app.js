let deferredPrompt;

const installBtn=document.getElementById("installBtn");

window.addEventListener("beforeinstallprompt",(e)=>{

e.preventDefault();

deferredPrompt=e;

installBtn.style.display="flex";

});

installBtn.addEventListener("click",async()=>{

installBtn.style.display="none";

deferredPrompt.prompt();

const result=await deferredPrompt.userChoice;

deferredPrompt=null;

});

window.addEventListener("appinstalled",()=>{

console.log("Installed");

});