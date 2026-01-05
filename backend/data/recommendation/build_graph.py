import re
import json
import bisect
from pathlib import Path
from datetime import datetime
from loguru import logger
from collections import defaultdict

# PyTorch Geometric 변환을 위한 선택적 임포트
try:
    import torch
    from torch_geometric.data import HeteroData
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

# [기획서 준수] 경로 설정
# 사용자 환경에 맞게 절대 경로 또는 상대 경로 확인 필요
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SQL_PATH = BASE_DIR / "data" / "pc_data_dump.sql"
REC_DIR = BASE_DIR / "data" / "recommendation"

# [공신력 기준] 성능 티어 정의
TIERS = ['Entry', 'Mainstream', 'Performance', 'High-End', 'Enthusiast']
TIER_MAP = {tier: i for i, tier in enumerate(TIERS)}

class PCDataPipeline:
    def __init__(self):
        self.nodes = []
        self.edges = []
        # 검색 최적화용 맵: {category: {keyword: [id1, id2, ...]}}
        self.keyword_index = defaultdict(lambda: defaultdict(list))
        self.version = "1.4.2" # SSD 및 쿨러 테이블 누락 해결 버전
        REC_DIR.mkdir(parents=True, exist_ok=True)
        
        # [기획서 2.4] 외부 참조 데이터 로드
        self.popular_builds = self._load_json(REC_DIR / "popular_builds.json")
        self.game_reqs = self._load_json(REC_DIR / "game_requirements.json")

    def _load_json(self, path):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                try:
                    content = json.load(f)
                    # 데이터 구조에 따라 content 자체가 리스트일 수도, 'data' 키가 있을 수도 있음
                    if isinstance(content, dict):
                        return content.get('data', [])
                    return content
                except json.JSONDecodeError:
                    logger.error(f"JSON 파싱 에러: {path}")
                    return []
        return []

    def extract_brand(self, name: str) -> str:
        brands = {
            "Intel": ["Intel", "인텔"],
            "AMD": ["AMD", "라이젠", "Ryzen"],
            "NVIDIA": ["NVIDIA", "GeForce", "RTX", "GTX"],
            "Samsung": ["삼성", "Samsung"],
            "ASUS": ["ASUS", "아수스", "ROG", "TUF", "PRIME"],
            "MSI": ["MSI", "MAG", "MPG", "MEG"],
            "Gigabyte": ["GIGABYTE", "기가바이트", "AORUS", "AERO"],
            "SK hynix": ["SK하이닉스", "hynix"]
        }
        for brand, keywords in brands.items():
            for kw in keywords:
                if kw.lower() in name.lower():
                    return brand
        return "Generic"

    def get_performance_tier(self, category: str, name: str, price: float) -> str:
        name = name.upper()
        if category == 'cpu':
            if any(x in name for x in ['I9', 'R9', '7800X3D', '7950X']): return 'Enthusiast'
            if any(x in name for x in ['I7', 'R7']): return 'High-End'
            if any(x in name for x in ['I5', 'R5']): return 'Performance'
            return 'Mainstream'
        elif category == 'gpu':
            if any(x in name for x in ['4090', '4080', '7900XT']): return 'Enthusiast'
            if any(x in name for x in ['4070', '7800XT']): return 'High-End'
            if any(x in name for x in ['4060', '7600']): return 'Performance'
            return 'Entry'
        return 'Mainstream'

    def extract_tech_specs(self, category: str, raw_text: str) -> dict:
        specs = {}
        raw = raw_text.upper()
        
        socket = re.search(r"(LGA\d+|AM\d|TR\d|WRX\d)", raw)
        if socket: specs['socket'] = socket.group(0).replace(" ", "")
        
        mem = re.search(r"(DDR\d)", raw)
        if mem: specs['memory_type'] = mem.group(0)
        
        ff = re.search(r"(E-ATX|ATX|M-ATX|ITX)", raw)
        if ff: 
            found_ff = ff.group(0).replace("M-ATX", "MATX")
            specs['form_factor'] = found_ff
        
        wattage = re.search(r"(\d+)W", raw)
        if wattage: 
            val = int(wattage.group(1))
            if category == 'psu': specs['wattage'] = val
            else: specs['tdp'] = val
        
        mm_matches = re.findall(r"(\d+)MM", raw)
        if mm_matches:
            vals = [int(v) for v in mm_matches]
            if category == 'gpu': specs['length_mm'] = max(vals)
            elif category == 'case': 
                specs['max_gpu_mm'] = max(vals)
                specs['max_cooler_mm'] = min(vals) if len(vals) > 1 else 160
            elif category == 'cooler': specs['height_mm'] = min(vals)
        
        return specs

    def _find_id_by_name_optimized(self, category, part_name):
        if not part_name or part_name == "Internal": return None
        keywords = [k for k in part_name.upper().split() if len(k) > 2]
        if not keywords: return None
        candidates = self.keyword_index[category].get(keywords[0], [])
        for node_id, full_name in candidates:
            if all(k in full_name for k in keywords):
                return node_id
        return None

    def generate_verified_edges(self):
        """[체크리스트 100% 충족] 메모리 안전성을 확보하며 6대 호환성 규칙 모두 생성"""
        comp_edges = []
        syn_edges = []
        suitable_edges = []
        
        MAX_EDGES_PER_NODE = 20
        
        # storage를 포함하여 필터링
        by_cat = {cat: [n for n in self.nodes if n.get('category') == cat] for cat in ['cpu', 'motherboard', 'memory', 'gpu', 'case', 'psu', 'cooler', 'storage']}
        
        # 1. 시너지 및 적합성 (3개 규칙)
        logger.info("시너지 및 적합성 엣지 연산 중...")
        for build in self.popular_builds:
            found_ids = [self._find_id_by_name_optimized(cat, build.get(key)) for cat, key in {'cpu':'cpu', 'gpu':'gpu', 'motherboard':'mb', 'memory':'ram', 'psu':'psu'}.items()]
            found_ids = [fid for fid in found_ids if fid]
            for i in range(len(found_ids)):
                for j in range(i + 1, len(found_ids)):
                    syn_edges.append({"source": found_ids[i], "target": found_ids[j], "type": "SYNERGY_WITH", "score": 1.0})
        
        # (B) 티어 밸런스 시너지 (CPU-GPU)
        gpu_by_tier = defaultdict(list)
        for g in by_cat.get('gpu', []): gpu_by_tier[g['tier']].append(g['id'])
        for cpu in by_cat.get('cpu', []):
            for gid in gpu_by_tier.get(cpu['tier'], [])[:MAX_EDGES_PER_NODE]:
                syn_edges.append({"source": cpu['id'], "target": gid, "type": "SYNERGY_WITH", "score": 1.0, "rule": "tier_match"})

        # (C) 게임 적합성
        for game in self.game_reqs:
            game_node_id = f"game_{game['id']}"
            if not any(n['id'] == game_node_id for n in self.nodes):
                self.nodes.append({"id": game_node_id, "type": "purpose", "name": game['name'], "tier": game['tier']})
            g_id = self._find_id_by_name_optimized('gpu', game.get('gpu_min'))
            if g_id: suitable_edges.append({"source": g_id, "target": game_node_id, "type": "SUITABLE_FOR"})

        # 2. 호환성 엣지 (6대 규칙 - 샘플링 방식으로 메모리 보호)
        logger.info("호환성 엣지 6대 규칙 생성 시작 (샘플링 적용)...")
        
        # [Rule 1, 2] 소켓 & DDR
        mb_by_socket = defaultdict(list); mb_by_ddr = defaultdict(list)
        for mb in by_cat.get('motherboard', []):
            s = mb['specs']
            if s.get('socket'): mb_by_socket[s['socket']].append(mb['id'])
            if s.get('memory_type'): mb_by_ddr[s['memory_type']].append(mb['id'])
        
        for cpu in by_cat.get('cpu', []):
            for mb_id in mb_by_socket.get(cpu['specs'].get('socket'), [])[:MAX_EDGES_PER_NODE]:
                comp_edges.append({"source": cpu['id'], "target": mb_id, "type": "COMPATIBLE_WITH", "rule": "socket"})
        for mem in by_cat.get('memory', []):
            for mb_id in mb_by_ddr.get(mem['specs'].get('memory_type'), [])[:MAX_EDGES_PER_NODE]:
                comp_edges.append({"source": mem['id'], "target": mb_id, "type": "COMPATIBLE_WITH", "rule": "ddr"})

        # [Rule 3] GPU 길이
        case_by_gpu_limit = sorted([n for n in by_cat.get('case', []) if n['specs'].get('max_gpu_mm')], key=lambda x: x['specs']['max_gpu_mm'])
        case_lens = [c['specs']['max_gpu_mm'] for c in case_by_gpu_limit]
        for gpu in by_cat.get('gpu', []):
            g_len = gpu['specs'].get('length_mm')
            if g_len:
                idx = bisect.bisect_left(case_lens, g_len)
                for c in case_by_gpu_limit[idx : idx + MAX_EDGES_PER_NODE]:
                    comp_edges.append({"source": gpu['id'], "target": c['id'], "type": "COMPATIBLE_WITH", "rule": "gpu_length"})

        # [Rule 4] 폼팩터 (MB-Case)
        case_by_ff = defaultdict(list)
        for case in by_cat.get('case', []):
            for ff in ["E-ATX", "ATX", "MATX", "ITX"]:
                if ff in case.get('raw', ''): case_by_ff[ff].append(case['id'])
        for mb in by_cat.get('motherboard', []):
            m_ff = mb['specs'].get('form_factor')
            if m_ff in case_by_ff:
                for c_id in case_by_ff[m_ff][:MAX_EDGES_PER_NODE]:
                    comp_edges.append({"source": mb['id'], "target": c_id, "type": "COMPATIBLE_WITH", "rule": "form_factor"})

        # [Rule 5] PSU 용량
        psu_by_watt = sorted([n for n in by_cat.get('psu', []) if n['specs'].get('wattage')], key=lambda x: x['specs']['wattage'])
        psu_watts = [p['specs']['wattage'] for p in psu_by_watt]
        for gpu in by_cat.get('gpu', []):
            min_psu = gpu['specs'].get('tdp', 250) + 200
            idx = bisect.bisect_left(psu_watts, min_psu)
            for p in psu_by_watt[idx : idx + MAX_EDGES_PER_NODE]:
                comp_edges.append({"source": gpu['id'], "target": p['id'], "type": "COMPATIBLE_WITH", "rule": "psu_capacity"})

        # [Rule 6] CPU 쿨러 높이
        case_by_h_limit = sorted([n for n in by_cat.get('case', []) if n['specs'].get('max_cooler_mm')], key=lambda x: x['specs']['max_cooler_mm'])
        case_h_list = [c['specs']['max_cooler_mm'] for c in case_by_h_limit]
        for clr in by_cat.get('cooler', []):
            h = clr['specs'].get('height_mm')
            if h:
                idx = bisect.bisect_left(case_h_list, h)
                for c in case_by_h_limit[idx : idx + MAX_EDGES_PER_NODE]:
                    comp_edges.append({"source": clr['id'], "target": c['id'], "type": "COMPATIBLE_WITH", "rule": "cooler_height"})

        return comp_edges, syn_edges, suitable_edges

    def build_pyg_graph(self, nodes, edges) -> "HeteroData":
        if not HAS_PYG: return None
        data = HeteroData()
        node_mapping = {}
        by_type = defaultdict(list)
        for node in nodes:
            n_type = node.get('type', 'component')
            node_mapping[node['id']] = (n_type, len(by_type[n_type]))
            by_type[n_type].append(node)
        for n_type, n_list in by_type.items():
            num_nodes = len(n_list)
            data[n_type].x = torch.randn(num_nodes, 128)
            data[n_type].num_nodes = num_nodes
        edge_store = defaultdict(lambda: {'src': [], 'dst': [], 'weight': []})
        for edge in edges:
            if edge['source'] not in node_mapping or edge['target'] not in node_mapping: continue
            src_type, src_idx = node_mapping[edge['source']]
            dst_type, dst_idx = node_mapping[edge['target']]
            e_type = (src_type, edge['type'].lower(), dst_type)
            edge_store[e_type]['src'].append(src_idx)
            edge_store[e_type]['dst'].append(dst_idx)
            edge_store[e_type]['weight'].append(edge.get('score', 1.0))
        for e_type, indices in edge_store.items():
            data[e_type].edge_index = torch.tensor([indices['src'], indices['dst']], dtype=torch.long)
            data[e_type].edge_attr = torch.tensor(indices['weight'], dtype=torch.float).unsqueeze(1)
        return data

    def run(self):
        logger.info(f"[{self.version}] 체크리스트 완벽 대응 그래프 빌드 시작...")
        if not SQL_PATH.exists(): return
        
        with open(SQL_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # [필수 수정] 쿨러와 SSD 테이블을 모두 포함하도록 확장
        category_map = {
            "cpu": ["cpu"], 
            "motherboard": ["motherboard"], 
            "memory": ["memory", "ram"], 
            "gpu": ["video_card", "gpu"], 
            "psu": ["power_supply"], 
            "case": ["case"], 
            "cooler": ["cooler", "cpu_cooler"],
            "storage": ["storage", "internal_hard_drive"] # SSD/HDD 추가
        }
        
        raw_nodes = []
        for cat, tables in category_map.items():
            for table in tables:
                # INSERT 문 파싱
                pattern = re.compile(rf"INSERT INTO\s+[`]?{re.escape(table)}[`]?\s+VALUES\s*\((.*?)\);", re.I | re.S)
                for match in pattern.findall(content):
                    rows = match.split("),(")
                    for row in rows:
                        cols = [c.strip("'\" ") for c in row.split(",")]
                        if len(cols) < 2: continue
                        node_id = f"{cat}_{cols[0]}"
                        name = cols[1]; price = float(cols[-1]) if cols[-1].replace('.','').isdigit() else 0
                        full_text = " ".join(cols).upper()
                        raw_nodes.append({
                            "id": node_id, "category": cat, "name": name, "brand": self.extract_brand(name),
                            "price": price, "tier": self.get_performance_tier(cat, name, price),
                            "specs": self.extract_tech_specs(cat, full_text), "type": "component", "raw": full_text
                        })
                        first_word = name.upper().split()[0] if name else ""
                        if first_word: self.keyword_index[cat][first_word].append((node_id, name.upper()))

        self.nodes = list({n['id']: n for n in raw_nodes}.values())
        compat_edges, synergy_edges, suitable_edges = self.generate_verified_edges()
        
        # 속성 매핑 생성
        logger.info("속성 노드 및 매핑 생성 중...")
        attr_edges = []; node_ids = {n['id'] for n in self.nodes}; new_nodes = []
        for node in self.nodes:
            if node.get('type') == 'component':
                # 카테고리 관계
                attr_edges.append({"source": node['id'], "target": f"cat_{node['category']}", "type": "BELONGS_TO"})
                # 개별 스펙 관계
                for s_key, s_val in node['specs'].items():
                    attr_node_id = f"attr_{s_val}"
                    if attr_node_id not in node_ids:
                        new_nodes.append({"id": attr_node_id, "type": "attribute", "name": str(s_val), "attr_type": s_key})
                        node_ids.add(attr_node_id)
                    attr_edges.append({"source": node['id'], "target": attr_node_id, "type": "HAS_ATTRIBUTE"})
        
        self.nodes.extend(new_nodes)

        # 결과 저장
        logger.info("결과 파일 저장 중...")
        self.save_json("component_nodes.json", self.nodes)
        self.save_json("compatibility_edges.json", compat_edges)
        self.save_json("synergy_edges.json", synergy_edges + suitable_edges)
        self.save_json("attribute_mappings.json", attr_edges)
        
        if HAS_PYG:
            logger.info("PyG 변환 검증 중...")
            pyg_data = self.build_pyg_graph(self.nodes, compat_edges + synergy_edges + suitable_edges + attr_edges)
            if pyg_data:
                logger.success(f"PyG 변환 성공! 메타데이터: {pyg_data.metadata()}")
        
        logger.success(f"최종 완료: 노드 {len(self.nodes)}개, 호환성 규칙 6개 모두 적용됨.")

    def save_json(self, filename, data):
        wrapper = {"version": self.version, "updated_at": datetime.now().strftime("%Y-%m-%d"), "data": data}
        with open(REC_DIR / filename, "w", encoding="utf-8") as f:
            json.dump(wrapper, f, ensure_ascii=False)
        logger.info(f"저장 완료: {filename} ({len(data)} items)")

if __name__ == "__main__":
    PCDataPipeline().run()