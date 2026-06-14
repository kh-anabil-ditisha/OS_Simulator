from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------------- CPU Scheduling Algorithms ----------------
def cpu_scheduling(processes, algorithm='FCFS', quantum=2):
    processes = [dict(p) for p in processes]
    for p in processes:
        p['pid'] = str(p.get('pid', '')).strip() or 'P'
        p['arrival'] = int(p.get('arrival', 0))
        p['burst'] = int(p.get('burst', 1))
        p['priority'] = int(p.get('priority', 1))
        p['remaining'] = p['burst']

    gantt = []
    time = 0
    completed = 0
    n = len(processes)
    finish = {}
    algorithm = algorithm.upper()

    if algorithm == 'FCFS':
        for p in sorted(processes, key=lambda x: (x['arrival'], x['pid'])):
            if time < p['arrival']:
                gantt.append({'pid': 'Idle', 'start': time, 'end': p['arrival']})
                time = p['arrival']
            gantt.append({'pid': p['pid'], 'start': time, 'end': time + p['burst']})
            time += p['burst']
            finish[p['pid']] = time

    elif algorithm == 'SJF':
        while completed < n:
            available = [p for p in processes if p['arrival'] <= time and p['remaining'] > 0]
            if not available:
                next_time = min(p['arrival'] for p in processes if p['remaining'] > 0)
                gantt.append({'pid': 'Idle', 'start': time, 'end': next_time})
                time = next_time
                continue
            p = min(available, key=lambda x: (x['burst'], x['arrival']))
            gantt.append({'pid': p['pid'], 'start': time, 'end': time + p['burst']})
            time += p['burst']
            p['remaining'] = 0
            finish[p['pid']] = time
            completed += 1

    elif algorithm == 'PRIORITY':
        while completed < n:
            available = [p for p in processes if p['arrival'] <= time and p['remaining'] > 0]
            if not available:
                next_time = min(p['arrival'] for p in processes if p['remaining'] > 0)
                gantt.append({'pid': 'Idle', 'start': time, 'end': next_time})
                time = next_time
                continue
            p = min(available, key=lambda x: (x['priority'], x['arrival']))
            gantt.append({'pid': p['pid'], 'start': time, 'end': time + p['burst']})
            time += p['burst']
            p['remaining'] = 0
            finish[p['pid']] = time
            completed += 1

    elif algorithm == 'RR':
        quantum = max(1, int(quantum))
        queue = []
        arrived = set()
        while completed < n:
            for p in sorted(processes, key=lambda x: x['arrival']):
                if p['arrival'] <= time and p['pid'] not in arrived:
                    queue.append(p)
                    arrived.add(p['pid'])
            if not queue:
                next_time = min(p['arrival'] for p in processes if p['remaining'] > 0 and p['pid'] not in arrived)
                gantt.append({'pid': 'Idle', 'start': time, 'end': next_time})
                time = next_time
                continue
            p = queue.pop(0)
            run = min(quantum, p['remaining'])
            gantt.append({'pid': p['pid'], 'start': time, 'end': time + run})
            time += run
            p['remaining'] -= run
            for np in sorted(processes, key=lambda x: x['arrival']):
                if np['arrival'] <= time and np['pid'] not in arrived:
                    queue.append(np)
                    arrived.add(np['pid'])
            if p['remaining'] > 0:
                queue.append(p)
            else:
                finish[p['pid']] = time
                completed += 1
    else:
        return {'error': 'Invalid algorithm'}

    rows = []
    total_wait = total_turn = 0
    for p in processes:
        tat = finish[p['pid']] - p['arrival']
        wt = tat - p['burst']
        total_wait += wt
        total_turn += tat
        rows.append({'pid': p['pid'], 'arrival': p['arrival'], 'burst': p['burst'], 'priority': p['priority'], 'waiting': wt, 'turnaround': tat})
    return {'gantt': gantt, 'rows': rows, 'avg_waiting': round(total_wait/n, 2), 'avg_turnaround': round(total_turn/n, 2)}

# ---------------- Page Replacement Algorithms ----------------
def page_replacement(reference, frames_count, algorithm='FIFO'):
    refs = [int(x) for x in reference]
    frames = []
    history = []
    faults = 0
    hits = 0
    algorithm = algorithm.upper()

    for i, page in enumerate(refs):
        status = 'Hit'
        if page in frames:
            hits += 1
        else:
            faults += 1
            status = 'Fault'
            if len(frames) < frames_count:
                frames.append(page)
            else:
                if algorithm == 'FIFO':
                    frames.pop(0)
                elif algorithm == 'LRU':
                    last_used = []
                    for f in frames:
                        previous = refs[:i]
                        last_used.append(previous[::-1].index(f) if f in previous else 9999)
                    victim_index = last_used.index(max(last_used))
                    frames.pop(victim_index)
                elif algorithm == 'OPTIMAL':
                    next_use = []
                    future = refs[i+1:]
                    for f in frames:
                        next_use.append(future.index(f) if f in future else 9999)
                    victim_index = next_use.index(max(next_use))
                    frames.pop(victim_index)
                frames.append(page)
        history.append({'page': page, 'frames': frames.copy(), 'status': status})
    total = len(refs) or 1
    return {'history': history, 'faults': faults, 'hits': hits, 'fault_rate': round(faults/total*100, 2), 'hit_rate': round(hits/total*100, 2)}

# ---------------- Banker's Algorithm ----------------
def bankers(available, maximum, allocation):
    n = len(maximum)
    m = len(available)
    need = [[maximum[i][j] - allocation[i][j] for j in range(m)] for i in range(n)]
    work = available[:]
    finish = [False] * n
    sequence = []
    changed = True
    while changed:
        changed = False
        for i in range(n):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(m)):
                for j in range(m):
                    work[j] += allocation[i][j]
                finish[i] = True
                sequence.append(f'P{i}')
                changed = True
    return {'safe': all(finish), 'sequence': sequence, 'need': need, 'work': work}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cpu', methods=['POST'])
def api_cpu():
    data = request.json
    return jsonify(cpu_scheduling(data['processes'], data.get('algorithm','FCFS'), data.get('quantum',2)))

@app.route('/api/page', methods=['POST'])
def api_page():
    data = request.json
    refs = [x for x in data['reference'].replace(',', ' ').split() if x.strip()]
    return jsonify(page_replacement(refs, int(data.get('frames',3)), data.get('algorithm','FIFO')))

@app.route('/api/banker', methods=['POST'])
def api_banker():
    data = request.json
    return jsonify(bankers(data['available'], data['maximum'], data['allocation']))

if __name__ == '__main__':
    app.run(debug=True)
