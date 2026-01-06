"""
하드웨어 및 벤치마크 정보 수집기
================================

[목표]
------
1. HardwareCollector: 다양한 소스에서 하드웨어 정보 수집 및 정규화
2. BenchmarkCollector: 벤치마크 점수 데이터베이스 관리

[HardwareCollector 기능]
----------------------
- 사용자 입력 파싱 (자연어, JSON, 시스템 정보)
- 하드웨어 이름 정규화 (다양한 표기법 통일)
- 누락된 스펙 추론/보완

[BenchmarkCollector 기능]
-----------------------
- 벤치마크 점수 데이터베이스 로드
- 점수 조회 및 캐싱
- 데이터베이스 업데이트

[데이터 소스]
-----------
- 사용자 직접 입력
- 프론트엔드 자동 감지 (navigator.userAgentData 등)
- 외부 벤치마크 API (선택적)

[구현 가이드]
-----------
1. 다양한 CPU/GPU 이름 표기법을 정규화
   예: "i5 12400f", "Intel Core i5-12400F", "12400F" → "i5-12400f"
2. 벤치마크 DB는 JSON/CSV 파일로 관리
3. 정기적으로 벤치마크 데이터 업데이트 프로세스 필요

[TODO]
-----
- [ ] 하드웨어 이름 정규화 정규식 구현
- [ ] 벤치마크 데이터 JSON 파일 생성
- [ ] 외부 API 연동 (UserBenchmark, PassMark 등)
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import re
from loguru import logger


# ============================================================================
# 하드웨어 정보 수집기
# ============================================================================

class HardwareCollector:
    """
    하드웨어 정보 수집 및 정규화
    
    다양한 형식의 입력을 받아 표준화된 형태로 변환.
    
    사용법:
    ```python
    collector = HardwareCollector()
    
    # 자연어 입력
    specs = collector.parse_natural_language(
        "i5 12400f, RTX 3060, 램 16기가, SSD 512GB"
    )
    
    # 딕셔너리 입력 정규화
    normalized = collector.normalize_specs({
        "cpu": "Intel Core i5-12400F",
        "gpu": "GeForce RTX 3060"
    })
    ```
    """
    
    # CPU 이름 정규화 패턴
    CPU_PATTERNS = {
        # Intel 패턴
        r"(i[3579])[- ]?(\d{4,5})[kfKF]*": r"i\1-\2",  # i5-12400, i5 12400F → i5-12400
        r"intel.*core.*?(i[3579])[- ]?(\d{4,5})": r"i\1-\2",
        
        # AMD 패턴
        r"ryzen\s*(\d)\s*(\d{4})[xX3]*": r"ryzen \1 \2x",
        r"amd.*ryzen.*?(\d)\s*(\d{4})": r"ryzen \1 \2",
    }
    
    # GPU 이름 정규화 패턴
    GPU_PATTERNS = {
        # NVIDIA RTX
        r"(?:geforce\s*)?rtx\s*(\d{4})(?:\s*(ti|super))?": r"rtx \1 \2",
        r"nvidia.*rtx\s*(\d{4})": r"rtx \1",
        
        # NVIDIA GTX
        r"(?:geforce\s*)?gtx\s*(\d{4})(?:\s*(ti|super))?": r"gtx \1 \2",
        
        # AMD Radeon
        r"(?:radeon\s*)?rx\s*(\d{4})(?:\s*(xt|xtx))?": r"rx \1 \2",
    }
    
    def __init__(self):
        logger.info("HardwareCollector 초기화")
    
    def normalize_cpu_name(self, cpu_name: str) -> str:
        """
        CPU 이름 정규화
        
        다양한 표기법을 통일된 형식으로 변환.
        
        Args:
            cpu_name: 원본 CPU 이름
            
        Returns:
            정규화된 CPU 이름
        """
        normalized = cpu_name.lower().strip()
        
        for pattern, replacement in self.CPU_PATTERNS.items():
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                # 정규식 그룹으로 교체
                result = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
                return result.strip()
        
        return normalized
    
    def normalize_gpu_name(self, gpu_name: str) -> str:
        """
        GPU 이름 정규화
        
        Args:
            gpu_name: 원본 GPU 이름
            
        Returns:
            정규화된 GPU 이름
        """
        normalized = gpu_name.lower().strip()
        
        for pattern, replacement in self.GPU_PATTERNS.items():
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                result = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
                return result.strip()
        
        return normalized
    
    def parse_natural_language(self, text: str) -> Dict[str, Any]:
        """
        자연어 입력에서 하드웨어 정보 추출
        
        Args:
            text: 자연어 텍스트
                예: "i5 12400f, RTX 3060, 램 16기가, SSD 512GB"
                
        Returns:
            추출된 하드웨어 정보 딕셔너리
        """
        specs = {}
        text_lower = text.lower()
        
        # CPU 추출
        cpu_match = re.search(
            r"(i[3579][- ]?\d{4,5}[kfKF]*|ryzen\s*\d\s*\d{4}[xX3]*)",
            text_lower
        )
        if cpu_match:
            specs["cpu"] = {"name": self.normalize_cpu_name(cpu_match.group())}
        
        # GPU 추출
        gpu_match = re.search(
            r"(rtx\s*\d{4}(?:\s*(?:ti|super))?|gtx\s*\d{4}(?:\s*ti)?|rx\s*\d{4}(?:\s*xt)?)",
            text_lower
        )
        if gpu_match:
            specs["gpu"] = {"name": self.normalize_gpu_name(gpu_match.group())}
        
        # 메모리 추출
        memory_match = re.search(r"(?:램|ram|메모리)\s*(\d+)\s*(?:기가|gb|g)?", text_lower)
        if memory_match:
            specs["memory"] = {"capacity": int(memory_match.group(1))}
        
        # 메모리 용량만 있는 경우
        if "memory" not in specs:
            memory_match = re.search(r"(\d+)\s*(?:기가|gb)\s*(?:램|ram|메모리)?", text_lower)
            if memory_match:
                specs["memory"] = {"capacity": int(memory_match.group(1))}
        
        # 스토리지 추출
        storage_match = re.search(
            r"(ssd|hdd|nvme)[,\s]*(\d+)\s*(?:gb|기가|tb|테라)?",
            text_lower
        )
        if storage_match:
            storage_type = storage_match.group(1).upper()
            capacity = int(storage_match.group(2))
            if "tb" in text_lower or "테라" in text_lower:
                capacity *= 1024
            specs["storage"] = {"type": storage_type, "capacity": capacity}
        
        return specs
    
    def normalize_specs(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """
        스펙 딕셔너리 정규화
        
        Args:
            specs: 원본 스펙 딕셔너리
            
        Returns:
            정규화된 스펙 딕셔너리
        """
        normalized = {}
        
        # CPU 정규화
        if "cpu" in specs:
            if isinstance(specs["cpu"], str):
                normalized["cpu"] = {"name": self.normalize_cpu_name(specs["cpu"])}
            elif isinstance(specs["cpu"], dict):
                normalized["cpu"] = specs["cpu"].copy()
                if "name" in normalized["cpu"]:
                    normalized["cpu"]["name"] = self.normalize_cpu_name(normalized["cpu"]["name"])
        
        # GPU 정규화
        if "gpu" in specs:
            if isinstance(specs["gpu"], str):
                normalized["gpu"] = {"name": self.normalize_gpu_name(specs["gpu"])}
            elif isinstance(specs["gpu"], dict):
                normalized["gpu"] = specs["gpu"].copy()
                if "name" in normalized["gpu"]:
                    normalized["gpu"]["name"] = self.normalize_gpu_name(normalized["gpu"]["name"])
        
        # 나머지 복사
        for key in ["memory", "storage"]:
            if key in specs:
                normalized[key] = specs[key].copy() if isinstance(specs[key], dict) else specs[key]
        
        return normalized


# ============================================================================
# 벤치마크 데이터 수집기
# ============================================================================

class BenchmarkCollector:
    """
    벤치마크 점수 데이터베이스 관리
    
    JSON/CSV 파일에서 벤치마크 점수를 로드하고 조회.
    
    사용법:
    ```python
    collector = BenchmarkCollector()
    
    # 점수 조회
    cpu_score = collector.get_cpu_score("i5-12400f")
    gpu_score = collector.get_gpu_score("rtx 3060")
    
    # 데이터베이스 업데이트
    collector.update_database("cpu", {"i5-14600k": 75})
    ```
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        auto_load: bool = True,
    ):
        """
        Args:
            data_dir: 벤치마크 데이터 디렉토리
            auto_load: 초기화 시 자동 로드 여부
        """
        self.data_dir = data_dir or Path(__file__).parent / "data"
        self.cpu_benchmarks: Dict[str, int] = {}
        self.gpu_benchmarks: Dict[str, int] = {}
        
        if auto_load:
            self._load_default_data()
        
        logger.info(f"BenchmarkCollector 초기화: CPU {len(self.cpu_benchmarks)}개, GPU {len(self.gpu_benchmarks)}개")
    
    def _load_default_data(self):
        """기본 벤치마크 데이터 로드"""
        json_path = self.data_dir / "benchmark_scores.json"
        
        if json_path.exists():
            try:
                data = self.load_from_file(json_path)
                self.cpu_benchmarks = data.get("cpu", {})
                self.gpu_benchmarks = data.get("gpu", {})
                logger.info(f"벤치마크 데이터 로드됨: {json_path}")
            except Exception as e:
                logger.error(f"벤치마크 파일 로드 중 오류: {e}")
                self.cpu_benchmarks = {}
                self.gpu_benchmarks = {}
        else:
            logger.warning(f"벤치마크 파일 없음: {json_path}")
            # Fallback (optional) or empty
            self.cpu_benchmarks = {}
            self.gpu_benchmarks = {}
    
    def load_from_file(self, filepath: Path) -> Dict[str, Any]:
        """
        파일에서 벤치마크 데이터 로드
        
        Args:
            filepath: JSON 파일 경로
            
        Returns:
            로드된 데이터
        """
        if not filepath.exists():
            logger.warning(f"벤치마크 파일 없음: {filepath}")
            return {}
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data
    
    def save_to_file(self, filepath: Path, data: Dict[str, Any]):
        """
        벤치마크 데이터를 파일로 저장
        
        Args:
            filepath: 저장 경로
            data: 저장할 데이터
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"벤치마크 데이터 저장: {filepath}")
    
    def get_cpu_score(self, cpu_name: str) -> Optional[int]:
        """
        CPU 벤치마크 점수 조회
        
        Args:
            cpu_name: CPU 이름 (정규화된 형태 권장)
            
        Returns:
            벤치마크 점수 또는 None
        """
        normalized = cpu_name.lower().strip()
        
        # 정확한 매칭
        if normalized in self.cpu_benchmarks:
            return self.cpu_benchmarks[normalized]
        
        # 부분 매칭
        for key, score in self.cpu_benchmarks.items():
            if key in normalized or normalized in key:
                return score
        
        return None
    
    def get_gpu_score(self, gpu_name: str) -> Optional[int]:
        """
        GPU 벤치마크 점수 조회
        
        Args:
            gpu_name: GPU 이름 (정규화된 형태 권장)
            
        Returns:
            벤치마크 점수 또는 None
        """
        normalized = gpu_name.lower().strip()
        
        # 정확한 매칭
        if normalized in self.gpu_benchmarks:
            return self.gpu_benchmarks[normalized]
        
        # 부분 매칭
        for key, score in self.gpu_benchmarks.items():
            if key in normalized or normalized in key:
                return score
        
        return None
    
    def update_database(
        self,
        component_type: str,
        scores: Dict[str, int],
    ):
        """
        벤치마크 데이터베이스 업데이트
        
        Args:
            component_type: "cpu" 또는 "gpu"
            scores: 추가/업데이트할 점수 딕셔너리
        """
        if component_type == "cpu":
            self.cpu_benchmarks.update(scores)
        elif component_type == "gpu":
            self.gpu_benchmarks.update(scores)
        else:
            raise ValueError(f"지원하지 않는 타입: {component_type}")
        
        logger.info(f"{component_type} 벤치마크 업데이트: {len(scores)}개 항목")
    
    def search(self, query: str, component_type: str = "all") -> List[Dict[str, Any]]:
        """
        벤치마크 데이터 검색
        
        Args:
            query: 검색어
            component_type: "cpu", "gpu", 또는 "all"
            
        Returns:
            매칭되는 항목 리스트
        """
        results = []
        query_lower = query.lower()
        
        if component_type in ["cpu", "all"]:
            for name, score in self.cpu_benchmarks.items():
                if query_lower in name:
                    results.append({"type": "cpu", "name": name, "score": score})
        
        if component_type in ["gpu", "all"]:
            for name, score in self.gpu_benchmarks.items():
                if query_lower in name:
                    results.append({"type": "gpu", "name": name, "score": score})
        
        # 점수 내림차순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # HardwareCollector 테스트
    hw_collector = HardwareCollector()
    
    # 자연어 파싱 테스트
    test_texts = [
        "i5 12400f, RTX 3060, 램 16기가, SSD 512GB",
        "Intel Core i5-12400F CPU에 GeForce RTX 3060 그래픽카드",
        "라이젠 5 5600x, RX 6700XT, 메모리 32GB",
    ]
    
    for text in test_texts:
        result = hw_collector.parse_natural_language(text)
        print(f"입력: {text}")
        print(f"결과: {result}\n")
    
    # BenchmarkCollector 테스트
    bm_collector = BenchmarkCollector()
    
    print(f"i5-12400f 점수: {bm_collector.get_cpu_score('i5-12400f')}")
    print(f"RTX 3060 점수: {bm_collector.get_gpu_score('rtx 3060')}")
    print(f"검색 결과: {bm_collector.search('rtx 40')}")
