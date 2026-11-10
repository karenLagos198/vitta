const $ = s => document.querySelector(s);
const money = n => "$" + Number(n).toLocaleString("es-CO");
// Datos de ejemplo en memoria (sin backend por ahora)
const tareas = [{t:"Entregar guía de Taller de Programación",p:"Alta",f:"2026-11-12",ok:false},{t:"Estudiar para parcial",p:"Media",f:"2026-11-15",ok:true}];
const movs = [{d:"Mesada",m:500000,tipo:"ingreso",c:"Otros"},{d:"Almuerzo",m:15000,tipo:"gasto",c:"Comida"},{d:"Pasaje bus",m:12000,tipo:"gasto",c:"Transporte"}];
const recs = [{t:"Pagar internet",f:"2026-11-20"}];

$("#fecha").textContent = new Date().toLocaleDateString("es-CO",{weekday:"long",day:"numeric",month:"long"});

function render(){
  $("#lista-tareas").innerHTML = tareas.map((x,i)=>`<li class="${x.ok?'hecha':''}"><span>${x.t} · ${x.p} ${x.f||''}</span><span><button data-ok="${i}">✓</button> <button data-del="${i}">✕</button></span></li>`).join("");
  $("#lista-mov").innerHTML = movs.map(x=>`<li><span>${x.d} · ${x.c}</span><b>${x.tipo==='gasto'?'-':'+'}${money(x.m)}</b></li>`).join("");
  $("#lista-rec").innerHTML = recs.map(x=>`<li><span>${x.t}</span><span>${x.f}</span></li>`).join("");
  const pend = tareas.filter(x=>!x.ok).length;
  const saldo = movs.reduce((s,x)=>s+(x.tipo==='gasto'?-x.m:x.m),0);
  $("#kpi-tareas").textContent = pend; $("#kpi-saldo").textContent = money(saldo); $("#kpi-rec").textContent = recs.length;
  const pct = tareas.length ? Math.round((tareas.length-pend)/tareas.length*100) : 0;
  $("#progreso").style.width = pct+"%"; $("#progreso-txt").textContent = pct+"% completado";
  const por = {}; movs.filter(x=>x.tipo==='gasto').forEach(x=>por[x.c]=(por[x.c]||0)+x.m);
  const max = Math.max(1,...Object.values(por));
  $("#grafico").innerHTML = Object.entries(por).map(([c,v])=>`<div class="bar-row"><span class="lbl">${c}</span><div class="b" style="width:${v/max*60}%"></div><span>${money(v)}</span></div>`).join("") || "<small>Sin gastos aún</small>";
}
document.addEventListener("click",e=>{
  if(e.target.dataset.ok!==undefined){tareas[e.target.dataset.ok].ok=!tareas[e.target.dataset.ok].ok;render();}
  if(e.target.dataset.del!==undefined){tareas.splice(e.target.dataset.del,1);render();}
});
$("#form-tarea").onsubmit = e=>{e.preventDefault();tareas.push({t:$("#t-texto").value,p:$("#t-prio").value,f:$("#t-fecha").value,ok:false});e.target.reset();render();};
$("#form-mov").onsubmit = e=>{e.preventDefault();movs.push({d:$("#m-desc").value,m:+$("#m-monto").value,tipo:$("#m-tipo").value,c:$("#m-cat").value});e.target.reset();render();};
$("#form-rec").onsubmit = e=>{e.preventDefault();recs.push({t:$("#r-texto").value,f:$("#r-fecha").value});e.target.reset();render();};

// Navegación
const titulos={resumen:"Resumen del día",tareas:"Tareas",finanzas:"Finanzas",recordatorios:"Recordatorios",asistente:"Asistente IA"};
function ir(){
  const id=(location.hash||"#resumen").slice(1);
  document.querySelectorAll(".view").forEach(v=>v.classList.toggle("hidden",v.id!==id));
  document.querySelectorAll("nav a").forEach(a=>a.classList.toggle("active",a.getAttribute("href")==="#"+id));
  $("#titulo").textContent=titulos[id]||"Vitta";
}
window.addEventListener("hashchange",ir);

// Asistente IA
$("#ia-btn").onclick=()=>{
  const r=predecir($("#ia-texto").value);
  $("#ia-res").innerHTML = r ? r.map(x=>`<div class="ia-item"><span style="width:90px">${x.cat}</span><div class="b" style="width:${x.p*60}%"></div><span>${(x.p*100).toFixed(0)}%</span></div>`).join("")
    : "<small>No reconozco esas palabras, prueba con otras.</small>";
};
render(); ir();
