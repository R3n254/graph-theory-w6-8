import random, networkx as nx
from cpp_solver import solve_directed_cpp, solve_undirected_cpp

# 1. slide example (undirected) = 69
g = nx.MultiGraph()
for a,b,w in [("A","C",6),("C","B",12),("B","D",7),("B","E",17),("D","E",18),("A","D",2)]:
    g.add_edge(a,b,length=w)
assert solve_undirected_cpp(g,"A")["total_m"] == 69

# 2. random strongly connected digraphs: route must use every edge, be closed, start at base
def check(H, base):
    r = solve_directed_cpp(H, base)
    steps = r["route"]
    assert steps[0]["from"] == base and steps[-1]["to"] == base
    for a,b in zip(steps, steps[1:]):
        assert a["to"] == b["from"]
    need = {(u,v) for u,v,_ in H.edges(keys=True)}
    got = {(s["from"], s["to"]) for s in steps}
    assert need <= got
    assert r["total_m"] >= r["required_m"] - 1e-6
    return r

random.seed(1)
for t in range(200):
    n = random.randint(3,12)
    H = nx.MultiDiGraph()
    nodes = list(range(n))
    for i in nodes:  # cycle guarantees strong connectivity
        H.add_edge(i,(i+1)%n,length=random.randint(1,50))
    for _ in range(random.randint(0,3*n)):
        a,b = random.sample(nodes,2)
        H.add_edge(a,b,length=random.randint(1,50))
    check(H, 0)

# 3. already balanced graph -> no repeats
C = nx.MultiDiGraph()
for i in range(5): C.add_edge(i,(i+1)%5,length=10)
r = check(C,0); assert r["repeated_m"] == 0 and r["total_m"] == 50

# 4. optimality vs LP on small cases
from scipy.optimize import linprog
import numpy as np
for t in range(60):
    n = random.randint(3,7)
    H = nx.MultiDiGraph()
    for i in range(n): H.add_edge(i,(i+1)%n,length=random.randint(1,20))
    for _ in range(random.randint(0,2*n)):
        a,b = random.sample(range(n),2); H.add_edge(a,b,length=random.randint(1,20))
    edges = list(H.edges(keys=True,data=True))
    # extra traversals x_e >= 0 integer on each edge, balance in=out
    A = np.zeros((n,len(edges)))
    for j,(u,v,k,d) in enumerate(edges):
        A[u,j]-=1; A[v,j]+=1   # inflow - outflow of extra
    b_eq = np.array([H.out_degree(i)-H.in_degree(i) for i in range(n)],float)
    res = linprog([d["length"] for *_,d in edges],A_eq=A,b_eq=b_eq,bounds=(0,None))
    req = sum(d["length"] for *_,d in edges)
    assert abs(solve_directed_cpp(H,0)["total_m"] - (req+res.fun)) < 1e-6
print("ALL TESTS PASSED")
