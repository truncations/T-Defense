// Browser-local database. No raw message text, field values or full URLs are stored.
const TrustStore=(()=>{
  let database;
  const open=()=>database || (database=new Promise((resolve,reject)=>{
    const request=indexedDB.open('t-defense-element-trust',1);
    request.onupgradeneeded=()=>{const store=request.result.createObjectStore('elements',{keyPath:'fingerprint'});store.createIndex('origin','origin');};
    request.onsuccess=()=>resolve(request.result);request.onerror=()=>{database=null;reject(new Error('Local trust database is unavailable.'));};
  }));
  async function read(origin=null){const db=await open();return new Promise((resolve,reject)=>{const tx=db.transaction('elements','readonly');const store=tx.objectStore('elements');const request=origin?store.index('origin').getAll(origin):store.getAll();request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(new Error('Could not read local trust decisions.'));});}
  async function add(record){
    if(!/^[0-9a-f]{64}$/.test(record.fingerprint) || !['message','link','form'].includes(record.kind))throw new Error('Invalid exact-element trust decision.');
    const origin=new URL(record.origin).origin;if(origin!==record.origin || !/^https?:/.test(origin))throw new Error('Invalid trust scope.');
    const db=await open();return new Promise((resolve,reject)=>{const tx=db.transaction('elements','readwrite');const store=tx.objectStore('elements');let full=false;
      const count=store.count();count.onsuccess=()=>{const existing=store.get(record.fingerprint);existing.onsuccess=()=>{if(count.result>=5000 && !existing.result){full=true;tx.abort();return;}store.put({fingerprint:record.fingerprint,origin,kind:record.kind,createdAt:Date.now()});};};
      tx.oncomplete=()=>resolve();tx.onabort=()=>reject(new Error(full?'Trust database is full. Remove old entries before adding more.':'Could not save this local trust decision.'));tx.onerror=()=>{};
    });
  }
  async function remove(fingerprint){if(!/^[0-9a-f]{64}$/.test(fingerprint))throw new Error('Invalid trust entry.');const db=await open();return new Promise((resolve,reject)=>{const tx=db.transaction('elements','readwrite');tx.objectStore('elements').delete(fingerprint);tx.oncomplete=()=>resolve();tx.onabort=()=>reject(new Error('Could not remove trust.'));});}
  async function clear(){const db=await open();return new Promise((resolve,reject)=>{const tx=db.transaction('elements','readwrite');tx.objectStore('elements').clear();tx.oncomplete=()=>resolve();tx.onabort=()=>reject(new Error('Could not clear trust.'));});}
  return {read,add,remove,clear};
})();
