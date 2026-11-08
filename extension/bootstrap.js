// Registered only after the user enables persistent monitoring and grants site access.
if(window.top===window)chrome.runtime.sendMessage({type:'TDEFENSE_HELLO'}).catch(()=>{});
