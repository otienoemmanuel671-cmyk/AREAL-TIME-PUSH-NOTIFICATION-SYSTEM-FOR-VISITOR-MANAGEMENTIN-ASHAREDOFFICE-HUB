import os, sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, redirect, url_for, flash, session, g, abort, Response, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
BASE=os.path.dirname(os.path.abspath(__file__)); DB=os.path.join(BASE,'visitor_hub.db')
app=Flask(__name__); app.config['SECRET_KEY']=os.environ.get('SECRET_KEY','emmanuel-visitor-hub-2026')
CSS='''body{margin:0;font-family:Inter,Arial,sans-serif;background:#f4f7fb;color:#172033}.shell{display:grid;grid-template-columns:280px 1fr;min-height:100vh}.side{background:#0d1b2a;color:white;padding:26px}.brand{font-weight:900;font-size:20px;margin-bottom:26px}.brand span{display:block;color:#9fb0c6;font-size:13px;margin-top:5px}nav a{display:block;color:#e8eef8;text-decoration:none;padding:12px 14px;border-radius:12px;margin:6px 0}nav a:hover{background:#19324d}.main{padding:30px}.top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px}h1{font-size:32px;letter-spacing:-.04em;margin:0}.sub{color:#66758f}.pill{background:#e8f7f4;color:#0f766e;padding:10px 14px;border-radius:999px;font-weight:800}.card,.kpi{background:white;border:1px solid #e6ebf2;border-radius:22px;box-shadow:0 18px 45px rgba(23,32,51,.08);padding:22px}.grid{display:grid;gap:20px}.two{grid-template-columns:1fr 1fr}.three{grid-template-columns:repeat(3,1fr)}table{width:100%;border-collapse:collapse}td,th{padding:12px 8px;border-bottom:1px solid #e6ebf2;text-align:left}th{font-size:12px;color:#66758f;text-transform:uppercase}input,select,textarea{width:100%;height:44px;border:1px solid #dfe6f0;border-radius:12px;padding:0 12px;background:white}textarea{height:80px;padding-top:10px}label{display:grid;gap:6px;font-weight:700;margin-bottom:12px}.btn,button{border:0;border-radius:12px;background:#e9eef6;padding:11px 15px;font-weight:800;text-decoration:none;color:#172033;cursor:pointer}.primary{background:linear-gradient(135deg,#123c69,#1c5d99)!important;color:white}.danger{color:#b42318;font-weight:800}.success{color:#0f766e;font-weight:800}.flash{padding:12px;border-radius:12px;background:#eef4ff;margin-bottom:10px}.login{min-height:100vh;display:grid;place-items:center;background:linear-gradient(rgba(5,12,22,.56),rgba(5,12,22,.72)),url('/static/project_reference.jpg') center/cover no-repeat fixed}.login .card{width:min(440px,92vw);background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.45)}.actions{display:flex;gap:8px;flex-wrap:wrap}.audit p{border-bottom:1px solid #e6ebf2;padding-bottom:9px}.system-photo{width:100%;height:220px;object-fit:cover;border-radius:18px;border:1px solid #e5e7eb;box-shadow:0 14px 34px rgba(23,32,51,.12);margin:0 0 18px}.login-photo{width:100%;height:190px;object-fit:cover;border-radius:20px;margin:0 0 18px;border:1px solid rgba(255,255,255,.35)}.hero-card{overflow:hidden}.hero-card p{margin-top:0}
@media(max-width:900px){.shell,.two,.three{grid-template-columns:1fr}}'''
def conn():
    if 'db' not in g: g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row
    return g.db
@app.teardown_appcontext
def close(e):
    d=g.pop('db',None)
    if d: d.close()
def q(sql,args=(),one=False):
    c=conn().execute(sql,args); r=c.fetchall(); c.close(); return (r[0] if r else None) if one else r
def ex(sql,args=()):
    c=conn().execute(sql,args); conn().commit(); return c.lastrowid
def user(): return q('select * from users where id=?',(session.get('uid'),),one=True) if session.get('uid') else None
def need(fn):
    @wraps(fn)
    def w(*a,**k):
        if not user(): flash('Please log in first.'); return redirect(url_for('login'))
        return fn(*a,**k)
    return w
def role(*roles):
    def deco(fn):
        @wraps(fn)
        def w(*a,**k):
            u=user()
            if not u: return redirect(url_for('login'))
            if u['role'] not in roles: abort(403)
            return fn(*a,**k)
        return w
    return deco
def log(text): ex('insert into audit_logs(user_id,action,created_at) values(?,?,?)',(session.get('uid'),text,datetime.now().isoformat(timespec='seconds')))
def init_db():
    os.makedirs(BASE,exist_ok=True); db=sqlite3.connect(DB); c=db.cursor(); c.executescript('''
    create table if not exists tenants(id integer primary key,name text,office text,active integer default 1);
    create table if not exists users(id integer primary key,username text unique,password_hash text,full_name text,role text,tenant_id integer,phone text,push_enabled integer default 1,sms_enabled integer default 1,active integer default 1);
    create table if not exists visitors(id integer primary key,visitor_name text,phone text,id_number text,purpose text,tenant_id integer,host_id integer,checked_in_by integer,checkin_time text,checkout_time text,status text default 'Waiting');
    create table if not exists notifications(id integer primary key,visitor_id integer,host_id integer,channel text,status text,sent_at text,ack_at text,fallback_sent_at text,message text);
    create table if not exists audit_logs(id integer primary key,user_id integer,action text,created_at text);
    ''')
    if c.execute('select count(*) from tenants').fetchone()[0]==0:
        c.executemany('insert into tenants(name,office) values(?,?)',[('Nairobi Legal Partners','A-12'),('Savannah Tech Labs','B-04'),('Afya Med Consultancy','C-08')])
    if c.execute('select count(*) from users').fetchone()[0]==0:
        tenants={r[1]:r[0] for r in c.execute('select id,name from tenants')}
        users=[('admin',generate_password_hash('Admin@2026'),'Hub Administrator','Administrator',None,'0700000001'),('reception',generate_password_hash('Reception@2026'),'Front Desk Receptionist','Receptionist',None,'0700000002'),('otieno',generate_password_hash('Host@2026'),'Brian Otieno','Host',tenants['Savannah Tech Labs'],'0712345678'),('amina',generate_password_hash('Host@2026'),'Amina Wanjiku','Host',tenants['Nairobi Legal Partners'],'0722000000'),('david',generate_password_hash('Host@2026'),'David Mwangi','Host',tenants['Afya Med Consultancy'],'0733000000')]
        c.executemany('insert into users(username,password_hash,full_name,role,tenant_id,phone) values(?,?,?,?,?,?)',users)
    db.commit(); db.close()
def layout(title,sub,body):
    u=user(); nav=''; who=''
    if u:
        nav=f'<nav><a href="{url_for("dashboard")}">Dashboard</a><a href="{url_for("checkin")}">Visitor Check-In</a><a href="{url_for("visitors")}">Visitor Log</a><a href="{url_for("host_panel")}">Host Notifications</a>'
        if u['role']=='Administrator': nav+=f'<a href="{url_for("admin")}">Admin / Reports</a>'
        nav+=f'<a href="{url_for("logout")}">Logout</a></nav>'; who=f'<p>{u["full_name"]}<br><span>{u["role"]}</span></p>'
    flashes=''.join([f'<div class="flash">{m}</div>' for m in get_flashes()])
    return render_template_string(f'<!doctype html><html><head><title>{title}</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet"><style>{CSS}</style></head><body><div class="shell"><aside class="side"><div class="brand">Shared Office Hub<span>Real-Time Visitor Alerts</span></div>{nav}{who}</aside><main class="main"><div class="top"><div><h1>{title}</h1><p class="sub">{sub}</p></div><div class="pill">Push + SMS fallback simulation</div></div>{flashes}{body}</main></div></body></html>')
def get_flashes():
    from flask import get_flashed_messages
    return get_flashed_messages()
@app.route('/')
def index(): return redirect(url_for('dashboard') if user() else url_for('login'))
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=q('select * from users where username=? and active=1',(request.form['username'],),one=True)
        if u and check_password_hash(u['password_hash'],request.form['password']): session.clear(); session['uid']=u['id']; log(f'{u["username"]} logged in'); return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template_string(f'<html><head><title>Login</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>{CSS}</style></head><body class="login"><div class="card"><h1>Visitor Hub Login</h1><p class="sub">Instant host alerts for shared-office visitors.</p><form method="post"><label>Username<input name="username"></label><label>Password<input type="password" name="password"></label><button class="btn primary">Login</button></form><p class="sub">admin/Admin@2026 · reception/Reception@2026 · otieno/Host@2026</p></div></body></html>')
@app.route('/logout')
@need
def logout(): log('User logged out'); session.clear(); return redirect(url_for('login'))
@app.route('/dashboard')
@need
def dashboard():
    today=datetime.now().date().isoformat(); waiting=q('select count(*) c from visitors where status="Waiting"',one=True)['c']; done=q('select count(*) c from visitors where status="Checked Out"',one=True)['c']; nots=q('select status,count(*) c from notifications group by status')
    nrows=''.join([f'<tr><td>{r["status"]}</td><td>{r["c"]}</td></tr>' for r in nots]) or '<tr><td colspan=2>No notifications yet</td></tr>'
    recent=q('select v.*,u.full_name host,t.name tenant from visitors v join users u on u.id=v.host_id join tenants t on t.id=v.tenant_id order by v.id desc limit 8')
    rows=''.join([f'<tr><td>{r["visitor_name"]}</td><td>{r["tenant"]}</td><td>{r["host"]}</td><td>{r["status"]}</td></tr>' for r in recent])
    return layout('Operations Dashboard','Monitor visitor waiting time, host alerts and notification delivery.',f'<section class="grid three"><div class="kpi"><span>Waiting</span><h1>{waiting}</h1></div><div class="kpi"><span>Checked Out</span><h1>{done}</h1></div><div class="kpi"><span>Today</span><h1>{today}</h1></div></section><section class="grid two"><div class="card hero-card"><img class="system-photo" src="/static/project_reference.jpg" alt="Shared office reception reference"><h2>Shared office reception reference</h2><p class="sub">Visual reference for the reception desk where visitors check in before host notification.</p></div><div class="card"><h2>Recent Visitors</h2><table><tr><th>Visitor</th><th>Tenant</th><th>Host</th><th>Status</th></tr>{rows}</table></div><div class="card"><h2>Notification Delivery</h2><table><tr><th>Status</th><th>Count</th></tr>{nrows}</table></div></section>')
@app.route('/checkin',methods=['GET','POST'])
@need
@role('Receptionist','Administrator')
def checkin():
    hosts=q('select u.*,t.name tenant from users u join tenants t on t.id=u.tenant_id where u.role="Host" and u.active=1')
    if request.method=='POST':
        host=q('select * from users where id=?',(request.form['host_id'],),one=True); msg=f'Visitor {request.form["visitor_name"]} has arrived at reception.'
        vid=ex('insert into visitors(visitor_name,phone,id_number,purpose,tenant_id,host_id,checked_in_by,checkin_time,status) values(?,?,?,?,?,?,?,?,?)',(request.form['visitor_name'],request.form.get('phone',''),request.form.get('id_number',''),request.form.get('purpose',''),host['tenant_id'],host['id'],session['uid'],datetime.now().isoformat(timespec='seconds'),'Waiting'))
        ex('insert into notifications(visitor_id,host_id,channel,status,sent_at,message) values(?,?,?,?,?,?)',(vid,host['id'],'Push','Sent',datetime.now().isoformat(timespec='seconds'),msg)); log(f'Checked in visitor {request.form["visitor_name"]} and pushed alert to {host["full_name"]}'); flash('Visitor checked in and push notification sent instantly.'); return redirect(url_for('visitors'))
    opts=''.join([f'<option value="{h["id"]}">{h["full_name"]} — {h["tenant"]}</option>' for h in hosts])
    form=f'<div class="card"><form method="post"><label>Visitor Name<input name="visitor_name" required></label><label>Phone<input name="phone"></label><label>ID / Passport No.<input name="id_number"></label><label>Host<select name="host_id">{opts}</select></label><label>Purpose<textarea name="purpose"></textarea></label><button class="btn primary">Check In & Notify Host</button></form></div>'
    return layout('Reception Visitor Check-In','Record visitor details and trigger instant host notification.',form)
@app.route('/visitors')
@need
def visitors():
    rows=q('select v.*,u.full_name host,t.name tenant from visitors v join users u on u.id=v.host_id join tenants t on t.id=v.tenant_id order by v.id desc')
    trs=''.join([f'<tr><td>{r["visitor_name"]}</td><td>{r["tenant"]}</td><td>{r["host"]}</td><td>{r["checkin_time"]}</td><td>{r["status"]}</td><td><div class="actions"><a class="btn small" href="{url_for("host_ack",visitor_id=r["id"])}">Acknowledge</a><a class="btn small" href="{url_for("fallback",visitor_id=r["id"])}">SMS Fallback</a><a class="btn small" href="{url_for("checkout",visitor_id=r["id"])}">Check Out</a></div></td></tr>' for r in rows])
    return layout('Visitor Log','Live reception log with acknowledgement, SMS fallback and checkout controls.',f'<div class="card"><table><tr><th>Visitor</th><th>Tenant</th><th>Host</th><th>Check-In</th><th>Status</th><th>Action</th></tr>{trs}</table></div>')
@app.route('/host')
@need
def host_panel():
    u=user(); extra='and n.host_id=?' if u['role']=='Host' else ''; args=(u['id'],) if u['role']=='Host' else ()
    rows=q(f'select n.*,v.visitor_name,v.purpose from notifications n join visitors v on v.id=n.visitor_id where 1=1 {extra} order by n.id desc',args)
    trs=''.join([f'<tr><td>{r["visitor_name"]}</td><td>{r["message"]}</td><td>{r["status"]}</td><td>{r["sent_at"]}</td><td><a class="btn small primary" href="{url_for("host_ack",visitor_id=r["visitor_id"])}">Acknowledge</a></td></tr>' for r in rows])
    return layout('Host Live Notifications','Hosts see arrival alerts and acknowledge visitors from this panel.',f'<div class="card"><table><tr><th>Visitor</th><th>Message</th><th>Status</th><th>Sent</th><th></th></tr>{trs}</table></div>')
@app.route('/ack/<int:visitor_id>')
@need
def host_ack(visitor_id):
    ex('update notifications set status="Acknowledged", ack_at=? where visitor_id=?',(datetime.now().isoformat(timespec='seconds'),visitor_id)); ex('update visitors set status="Host Acknowledged" where id=? and status="Waiting"',(visitor_id,)); log(f'Acknowledged visitor #{visitor_id}'); flash('Host acknowledgement recorded.'); return redirect(request.referrer or url_for('host_panel'))
@app.route('/fallback/<int:visitor_id>')
@need
def fallback(visitor_id):
    ex('update notifications set status="SMS Fallback Sent", fallback_sent_at=?, channel="Push + SMS" where visitor_id=?',(datetime.now().isoformat(timespec='seconds'),visitor_id)); log(f'SMS fallback triggered for visitor #{visitor_id}'); flash('SMS fallback simulated and recorded.'); return redirect(request.referrer or url_for('visitors'))
@app.route('/checkout/<int:visitor_id>')
@need
def checkout(visitor_id):
    ex('update visitors set status="Checked Out", checkout_time=? where id=?',(datetime.now().isoformat(timespec='seconds'),visitor_id)); log(f'Checked out visitor #{visitor_id}'); flash('Visitor checked out.'); return redirect(url_for('visitors'))
@app.route('/admin')
@need
@role('Administrator')
def admin():
    tenants=q('select * from tenants'); hosts=q('select u.*,t.name tenant from users u left join tenants t on t.id=u.tenant_id order by u.role,u.full_name'); logs=q('select a.*,u.username from audit_logs a left join users u on u.id=a.user_id order by a.id desc limit 30')
    t=''.join([f'<tr><td>{x["name"]}</td><td>{x["office"]}</td></tr>' for x in tenants]); h=''.join([f'<tr><td>{x["full_name"]}</td><td>{x["role"]}</td><td>{x["tenant"] or "Hub"}</td><td>{x["phone"]}</td></tr>' for x in hosts]); l=''.join([f'<p><b>{x["created_at"]}</b><br>{x["username"] or "System"} · {x["action"]}</p>' for x in logs])
    return layout('Admin / Reports','Tenant, host, delivery and audit views for hub management.',f'<p><a class="btn ghost" href="{url_for("export_csv")}">Export Visitor CSV</a></p><section class="grid two"><div class="card"><h2>Tenants</h2><table>{t}</table><h2>Hosts & Staff</h2><table>{h}</table></div><div class="card audit"><h2>Audit Log</h2>{l}</div></section>')
@app.route('/export.csv')
@need
@role('Administrator')
def export_csv():
    rows=q('select v.visitor_name,t.name tenant,u.full_name host,v.status,v.checkin_time,v.checkout_time from visitors v join tenants t on t.id=v.tenant_id join users u on u.id=v.host_id')
    lines=['Visitor,Tenant,Host,Status,CheckIn,CheckOut']+[f'{r["visitor_name"]},{r["tenant"]},{r["host"]},{r["status"]},{r["checkin_time"]},{r["checkout_time"] or ""}' for r in rows]
    return Response('\n'.join(lines), mimetype='text/csv')
init_db()

if __name__=='__main__':
    port = int(os.environ.get('PORT', 5052))
    app.run(debug=True, host='0.0.0.0', port=port)
