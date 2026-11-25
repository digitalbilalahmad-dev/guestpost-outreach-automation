import argparse, csv, json, pathlib, sys
from core import db_open,import_domains,research,extract_prices,record_offer
p=argparse.ArgumentParser();p.add_argument('--db',default='data/outreach.db');sub=p.add_subparsers(dest='command',required=True)
a=sub.add_parser('import-csv');a.add_argument('file')
sub.add_parser('status')
a=sub.add_parser('research');a.add_argument('--limit',type=int,default=10)
a=sub.add_parser('parse-reply');a.add_argument('--website-id',type=int,required=True);a.add_argument('--file',required=True)
args=p.parse_args();db=db_open(args.db)
if args.command=='import-csv':
    with open(args.file,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);headers=reader.fieldnames or []
        col=next((x for x in headers if x.lower().strip() in ('website','domain','url')),None)
        if not col: sys.exit('CSV must contain Website, Domain, or URL header')
        print('Imported:',import_domains(db,(r[col] for r in reader if r.get(col))))
elif args.command=='status':
    for row in db.execute('SELECT status,count(*) n FROM websites GROUP BY status'):print(dict(row))
elif args.command=='research':
    for row in db.execute("SELECT id,domain FROM websites WHERE status='NEW' LIMIT ?",(args.limit,)):
        result=research(row['domain']);db.execute('UPDATE websites SET status=?,contact_email=?,source_url=? WHERE id=?',(result['status'],result['email'],result['source_url'],row['id']));db.commit();print(row['domain'],result)
elif args.command=='parse-reply':
    reply=pathlib.Path(args.file).read_text(encoding='utf-8');parsed=extract_prices(reply)
    if not db.execute('SELECT 1 FROM websites WHERE id=?',(args.website_id,)).fetchone():sys.exit('Unknown website ID')
    record_offer(db,args.website_id,reply,parsed);print(json.dumps(parsed,indent=2))
