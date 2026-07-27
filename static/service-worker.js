const CACHE_NAME="radhu-v1";

const urls=[

"/",

"/offline.html",

"/static/icon/192.png",

"/static/icon/512.png"

];

self.addEventListener("install",(event)=>{

event.waitUntil(

caches.open(CACHE_NAME)

.then(cache=>cache.addAll(urls))

);

self.skipWaiting();

});

self.addEventListener("activate",(event)=>{

event.waitUntil(

caches.keys()

.then(keys=>Promise.all(

keys.filter(key=>key!==CACHE_NAME)

.map(key=>caches.delete(key))

))

);

});

self.addEventListener("fetch",(event)=>{

event.respondWith(

fetch(event.request)

.catch(()=>{

return caches.match(event.request)

.then(res=>{

return res || caches.match("/offline.html");

});

})

);

});