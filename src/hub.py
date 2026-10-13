import json,os,html,re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','out'))
flags=json.load(open('preview-flags.json'))
pages=[]
for dp,dn,fn in os.walk('preview'):
  for f in fn:
    if f=='index.html':
      p=os.path.join(dp,f); t=re.search(r'<title>(.*?)</title>',open(p).read()).group(1)
      pages.append((os.path.relpath(p,'preview'),html.unescape(t)))
pages.sort()
main=[p for p in pages if not p[0].startswith('glossary/') or p[0]=='glossary/index.html']
terms=[p for p in pages if p[0].startswith('glossary/') and p[0]!='glossary/index.html']
def link(p,t): return f'<li><a href="site/{p}">{html.escape(t.replace(" | Nashional Investments",""))}</a><span>/{p.replace("index.html","")}</span></li>'
fl=''.join(f'<li><b>{html.escape(f[0])}</b>{html.escape(f[1])}</li>' for f in flags) or '<li>Nothing open.</li>'
hub=open('../src/hub_template.html').read().format(n=len(pages),nt=len(terms),pages=''.join(link(p,t) for p,t in main),flags=fl,terms=''.join(link(p,t) for p,t in terms))
open('hub.html','w').write(hub)
files={('site/'+os.path.relpath(os.path.join(dp,f),'preview')):os.path.relpath(os.path.join(dp,f),'.') for dp,dn,fn in os.walk('preview') for f in fn}
json.dump(files,open('files.json','w'))
print(len(files),len(flags))
