const tbody = document.querySelector('#processTable tbody');
function addProcess(pid, arrival, burst, priority){
  const n = tbody.children.length + 1;
  const row = document.createElement('tr');
  row.innerHTML = `
    <td><input value="${pid || 'P'+n}"></td>
    <td><input type="number" min="0" value="${arrival ?? n-1}"></td>
    <td><input type="number" min="1" value="${burst ?? [5,3,8,6,4][(n-1)%5]}"></td>
    <td><input type="number" min="1" value="${priority ?? [2,1,3,2,1][(n-1)%5]}"></td>
    <td><button class="delete" onclick="this.closest('tr').remove()">Delete</button></td>`;
  tbody.appendChild(row);
}
['P1','P2','P3','P4','P5'].forEach((p,i)=>addProcess(p,i,[5,3,8,6,4][i],[2,1,3,2,1][i]));

function readProcesses(){
  return [...tbody.querySelectorAll('tr')].map(tr=>{
    const v = tr.querySelectorAll('input');
    return {pid:v[0].value, arrival:+v[1].value, burst:+v[2].value, priority:+v[3].value};
  });
}
async function post(url, data){
  const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  return await res.json();
}
function metric(label, value){ return `<div class="metric"><span>${label}</span><b>${value}</b></div>`; }
async function runCPU(){
  const data = await post('/api/cpu',{processes:readProcesses(), algorithm:document.getElementById('cpuAlgo').value, quantum:+document.getElementById('quantum').value});
  const gantt = document.getElementById('gantt');
  gantt.innerHTML = data.gantt.map(g=>`<div class="gantt-block"><div>${g.pid}</div><small>${g.start} - ${g.end}</small></div>`).join('');
  document.getElementById('cpuMetrics').innerHTML = metric('Average Waiting Time', data.avg_waiting) + metric('Average Turnaround Time', data.avg_turnaround) + metric('Total Processes', data.rows.length);
}

async function runPage(){
  const data = await post('/api/page',{algorithm:document.getElementById('pageAlgo').value, frames:+document.getElementById('frames').value, reference:document.getElementById('reference').value});
  document.getElementById('pageStats').innerHTML = metric('Page Faults', data.faults) + metric('Hits', data.hits) + metric('Fault Rate', data.fault_rate+'%') + metric('Hit Rate', data.hit_rate+'%');
  document.getElementById('frameView').innerHTML = data.history.map((h,i)=>`<div class="frame-card"><h4>Ref ${h.page}</h4>${h.frames.map(f=>`<div class="frame-box">${f}</div>`).join('')}<p class="${h.status==='Fault'?'fault':'hit'}">${h.status}</p></div>`).join('');
}
function parseMatrix(text){return text.trim().split('\n').map(r=>r.trim().split(/\s+/).map(Number));}
async function runBanker(){
  const data = await post('/api/banker',{available:document.getElementById('available').value.trim().split(/\s+/).map(Number), maximum:parseMatrix(document.getElementById('maximum').value), allocation:parseMatrix(document.getElementById('allocation').value)});
  document.getElementById('bankerResult').innerHTML = `<h3 class="${data.safe?'safe':'unsafe'}">${data.safe?'System is in Safe State':'System is Not Safe / Deadlock Possible'}</h3><p>Safe Sequence:</p><div class="sequence">${data.sequence.map(p=>`<span>${p}</span>`).join('')}</div>`;
}
runCPU(); runPage(); runBanker();
