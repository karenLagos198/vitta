// Red neuronal pequeña (1 capa oculta) entrenada en el navegador para
// clasificar la categoría de un gasto a partir de su texto.
const DATOS = [
 ["pasaje bus","Transporte"],["taxi al trabajo","Transporte"],["gasolina moto","Transporte"],["transmilenio recarga","Transporte"],["uber","Transporte"],
 ["almuerzo","Comida"],["pizza","Comida"],["mercado supermercado","Comida"],["hamburguesa","Comida"],["cafe panaderia","Comida"],
 ["netflix","Ocio"],["cine","Ocio"],["videojuego","Ocio"],["concierto","Ocio"],["spotify","Ocio"],
 ["recibo luz","Servicios"],["agua acueducto","Servicios"],["internet","Servicios"],["plan celular","Servicios"],["gas natural","Servicios"]
];
const CATS = ["Comida","Transporte","Ocio","Servicios"];
const tok = t => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").split(/[^a-z]+/).filter(Boolean);
const VOCAB = [...new Set(DATOS.flatMap(d=>tok(d[0])))];
const H = 8;
const rnd = () => (Math.random()-.5)*.6;
const W1 = Array.from({length:H},()=>VOCAB.map(rnd)), b1 = Array(H).fill(0);
const W2 = Array.from({length:CATS.length},()=>Array(H).fill(0).map(rnd)), b2 = Array(CATS.length).fill(0);
const vec = t => { const s=new Set(tok(t)); return VOCAB.map(w=>s.has(w)?1:0); };
const sig = x => 1/(1+Math.exp(-x));
function softmax(z){const m=Math.max(...z),e=z.map(v=>Math.exp(v-m)),s=e.reduce((a,b)=>a+b);return e.map(v=>v/s);}
function forward(x){
  const h=W1.map((w,i)=>sig(w.reduce((s,wj,j)=>s+wj*x[j],b1[i])));
  const o=softmax(W2.map((w,k)=>w.reduce((s,wj,j)=>s+wj*h[j],b2[k])));
  return {h,o};
}
function entrenar(epocas=600,lr=.5){
  for(let e=0;e<epocas;e++){
    for(const [t,c] of DATOS){
      const x=vec(t),y=CATS.map(k=>k===c?1:0),{h,o}=forward(x);
      const dO=o.map((v,k)=>v-y[k]);
      const dH=h.map((hv,j)=>hv*(1-hv)*dO.reduce((s,d,k)=>s+d*W2[k][j],0));
      W2.forEach((w,k)=>{w.forEach((_,j)=>w[j]-=lr*dO[k]*h[j]);b2[k]-=lr*dO[k];});
      W1.forEach((w,j)=>{w.forEach((_,i)=>w[i]-=lr*dH[j]*x[i]);b1[j]-=lr*dH[j];});
    }
  }
}
entrenar();
function predecir(texto){
  const x=vec(texto);
  if(!x.some(v=>v)) return null;
  return forward(x).o.map((p,k)=>({cat:CATS[k],p})).sort((a,b)=>b.p-a.p);
}
