"""Knowledge network: sources, equations, facts, properties, methods, oils and citations."""
import json, glob, os, re
import numpy as np
import pandas as pd
import networkx as nx
from modules.paths import KNOWLEDGE, MASTER
from modules.measurement import map_method


class KnowledgeNetwork:
    def __init__(self):
        self.G = None

    def build(self, out_dir=os.path.join(KNOWLEDGE, "graph")):
        G = nx.MultiDiGraph()
        def norm_doi(s):
            m = re.search(r"10\.\d{4,9}/[^\s?#&\"]+", str(s or ""))
            return m.group(0).rstrip(").,;").lower() if m else None
        def src_node(cit, doi, url):
            d = norm_doi(doi) or norm_doi(url)
            nid = "doi:" + d if d else ("url:" + str(url) if url else "cit:" + str(cit)[:80])
            if nid not in G: G.add_node(nid, type="source", label=str(cit)[:160], doi=d or "", url=str(url or ""))
            return nid
        PROP = {"api": "API", "sg": "API", "density": "density", "rho": "density", "pour": "pour_point", "pp": "pour_point",
                "wax": "wax_content", "cp": "wax_content", "visc": "viscosity", "nu": "viscosity", "v100": "viscosity", "mu": "viscosity",
                "tb": "boiling_point", "mw": "molar_mass", "m": "molar_mass", "p": "pressure", "gor": "GOR", "rate": "cooling_rate",
                "wat": "WAT", "t": "temperature", "x1": "composition", "x2": "composition", "x3": "composition", "x4": "composition",
                "z": "composition", "asph": "asphaltenes", "ca": "asphaltenes", "cr": "resins"}
        def prop_of(name):
            s = str(name).lower()
            for k, v in PROP.items():
                if s == k or s.startswith(k): return v
            return "other"
        ALIAS = {"API": "density_API", "density": "density_API", "cloud_point": "WAT"}
        def pnode(p):
            p = ALIAS.get(p, p)
            nid = "property:" + p
            if nid not in G: G.add_node(nid, type="property", label=p)
            return nid
        # equations
        for f in glob.glob(os.path.join(KNOWLEDGE, "*", "models.jsonl")):
            ag = os.path.basename(os.path.dirname(f))
            for line in open(f):
                if not line.strip(): continue
                d = json.loads(line); mid = "model:" + d["id"]
                G.add_node(mid, type="equation", label=d.get("name", ""), agent=ag, target=d.get("target", ""), access=d.get("access", ""),
                           confidence=d.get("confidence", ""), python=d.get("python", "")[:500], validity=json.dumps(d.get("validity", {}))[:300])
                s = src_node(d.get("citation"), d.get("doi"), d.get("url")); G.add_edge(s, mid, rel="provides_equation")
                G.add_edge(mid, pnode(d.get("target") or "other"), rel="predicts")
                for i in d.get("inputs", []) or []:
                    G.add_edge(pnode(prop_of(i.get("symbol") or i.get("name"))), mid, rel="input_to")
        # facts
        for f in glob.glob(os.path.join(KNOWLEDGE, "*", "facts.jsonl")):
            ag = os.path.basename(os.path.dirname(f))
            for line in open(f):
                if not line.strip(): continue
                d = json.loads(line); fid = "fact:" + d["id"]
                G.add_node(fid, type="fact", label=str(d.get("magnitude", ""))[:200], agent=ag, relation=d.get("relation", ""),
                           low=str(d.get("value_low")), high=str(d.get("value_high")), unit=str(d.get("unit")), confidence=d.get("confidence", ""))
                s = src_node(d.get("citation"), d.get("doi"), d.get("url")); G.add_edge(s, fid, rel="states_fact")
                G.add_edge(pnode(str(d.get("subject"))), fid, rel="subject_of"); G.add_edge(fid, pnode(str(d.get("object"))), rel="affects")
        # real oils and methods
        m = pd.read_csv(MASTER)
        for _, r in m.iterrows():
            oid = "oil:" + str(r.oil_group)
            if oid not in G: G.add_node(oid, type="oil", label=str(r.oil_name)[:100], country=str(r.country_basin))
            s = src_node(r.source, None, r.source_url); G.add_edge(s, oid, rel="measures", row=str(r.row_id), tier=str(r.tier), wat=str(r.wat_c))
            mm = map_method(r.wat_method) or "other"
            G.add_node("method:" + mm, type="method", label=mm); G.add_edge(oid, "method:" + mm, rel="wat_by", row=str(r.row_id))
        # citation network from the network agent, if present
        for f in glob.glob(os.path.join(KNOWLEDGE, "network", "edges.csv")):
            e = pd.read_csv(f, dtype=str)
            for _, r in e.iterrows():
                a, b = str(r.src_id), str(r.dst_id)
                for x, t in [(a, r.src_type), (b, r.dst_type)]:
                    if x not in G: G.add_node(x, type=str(t), label=x)
                G.add_edge(a, b, rel=str(r.rel), evidence=str(r.get("evidence", "")))
        for f in glob.glob(os.path.join(KNOWLEDGE, "network", "nodes.csv")):
            n = pd.read_csv(f, dtype=str)
            for _, r in n.iterrows():
                if r.id in G: G.nodes[r.id].update({k: str(v) for k, v in r.items() if k != "id" and isinstance(v, str)})
        os.makedirs(out_dir, exist_ok=True)
        nx.write_graphml(G, os.path.join(out_dir, "wat_knowledge_graph.graphml"))
        pd.DataFrame([dict(id=k, **v) for k, v in G.nodes(data=True)]).to_csv(os.path.join(out_dir, "nodes.csv"), index=False)
        pd.DataFrame([dict(src=a, dst=b, **d) for a, b, d in G.edges(data=True)]).to_csv(os.path.join(out_dir, "edges.csv"), index=False)
        types = pd.Series([d.get("type") for _, d in G.nodes(data=True)]).value_counts()
        rels = pd.Series([d.get("rel") for _, _, d in G.edges(data=True)]).value_counts()
        print(f"✓ Knowledge graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        self.G = G
        return G
