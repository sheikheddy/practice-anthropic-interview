import bisect as b,hashlib
hash=lambda k:int(hashlib.md5(k.encode()).hexdigest()[:16],16)
I=lambda r,c:b.bisect_left(r,(hash(c),))%len(r)
class HashRing:
 def __init__(s):s._ring=[]
 def add_server(s,x):
  if(e:=(hash(x),x))in s._ring:return 0
  b.insort(s._ring,e);return 1
 def remove_server(s,x):
  if(e:=(hash(x),x))not in s._ring:return 0
  s._ring.remove(e);return 1
 def get_server(s,c):
  if not s._ring:raise ValueError
  return s._ring[I(s._ring,c)][1]
class HashRingVirtual:
 def __init__(s):s._ring=[];s.s=s._servers=set();s.servers=s.s
 def add_server(s,x,c=1):
  assert c>0
  if x in s.s:return 0
  s.s.add(x)
  for i in range(c):b.insort(s._ring,(hash(f'{x}:{i}'),0,x))
  return 1
 def remove_server(s,x):
  if x not in s.s:return 0
  s.s.remove(x);s._ring=[e for e in s._ring if e[2]!=x];return 1
 def get_server(s,c):
  if not s._ring:raise ValueError
  return s._ring[I(s._ring,c)][2]
class O:
 def __init__(s,a,b=''):s.chat_id=s.success=a;s.last_timestamp=s.llm_reply=b
ChatResponse=ChatData=O
def post_fn(*a):raise Exception
o=lambda d:min(d.values(),key=lambda z:z.last_timestamp,default=0)
class ChatClient(HashRingVirtual):
 def __init__(s):super().__init__();s.ring=s;s.h=s.chat_to_server={}
 def remove_server(s,x):
  if not super().remove_server(x):return 0
  h={c:v for c,v in s.h.items()if v!=x};s.h=s.chat_to_server=h;return 1
 def _iter_ring_servers(s,c):
  if s._ring:
   r=s._ring;i=I(r,c)
   for v in dict.fromkeys(e[2]for e in r[i:]+r[:i]):yield v
 def send_chat_message(s,c,m):
  if not s._ring:raise RuntimeError
  h=s.h;a=h.get(c);p=post_fn
  if a in s.s and(r:=p(a,c,m)).success:return r.llm_reply
  for v in s._iter_ring_servers(c):
   if v!=a and(r:=p(v,c,m)).success:h[c]=v;return r.llm_reply
  h.pop(c,None);raise RuntimeError
 def get_current_server(s,c):
  h=s.h;a=h.get(c)
  if a in s.s:return a
  if a!=None:h.pop(c,None)
  return s.get_server(c)
class Server:
 def __init__(s,max_vram_chats,max_ram_chats):
  assert max_vram_chats>1<max_ram_chats
  s.max_vram_chats,s.max_ram_chats=max_vram_chats,max_ram_chats;s.num_cache_hits=s.num_cache_misses=0;s.is_online=1;s.vram_chats={};s.ram_chats={}
 @property
 def total_chats(s):return len(s.vram_chats)+len(s.ram_chats)
 def has_chat(s,c):return c in s.vram_chats|s.ram_chats
 def remove_chat(s,c):return s.vram_chats.pop(c,None)or s.ram_chats.pop(c,None)
 def shutdown(s):
  if not s.is_online:raise RuntimeError
  s.is_online=0;s.vram_chats.clear();s.ram_chats.clear()
 def handle_request(s,c,t,m):
  if not s.is_online:return O(0)
  v=s.vram_chats;r=s.ram_chats;M,N=s.max_vram_chats,s.max_ram_chats
  if c in v:s.num_cache_hits+=1;v[c].last_timestamp=t;return O(1)
  if c in r:
   s.num_cache_hits+=1;x=r.pop(c);x.last_timestamp=t
   if len(v)>=M:
    if len(r)>=N-1 and(y:=o(r)):del r[y.chat_id]
    if(y:=o(v)):del v[y.chat_id];r[y.chat_id]=y
   v[c]=x;return O(1)
  s.num_cache_misses+=1;x=O(c,t)
  if len(v)>=M:
   if len(r)>=N and(y:=o(r)):del r[y.chat_id]
   if(y:=o(v)):del v[y.chat_id];r[y.chat_id]=y
  v[c]=x;return O(1)
