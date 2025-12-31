# PC 사양 진단 모듈 데이터

> 벤치마크 점수, 게임 권장사양, 용도별 기준 데이터

---

## 목차

1. [필요 데이터 목록](#1-필요-데이터-목록)
2. [데이터 수집 방법](#2-데이터-수집-방법)
3. [데이터 형식](#3-데이터-형식)
4. [데이터 갱신 주기](#4-데이터-갱신-주기)

---

## 1. 필요 데이터 목록

| 파일명 | 설명 | 우선순위 | 상태 |
|--------|------|----------|------|
| `cpu_benchmarks.json` | CPU 벤치마크 점수 | 필수 | 미수집 |
| `gpu_benchmarks.json` | GPU 벤치마크 점수 | 필수 | 미수집 |
| `game_requirements.json` | 게임별 권장 사양 | 권장 | 미수집 |
| `purpose_specs.json` | 용도별 권장 스펙 | 권장 | 미수집 |
| `bottleneck_rules.json` | 병목 판단 규칙 | 권장 | 미수집 |

---

## 2. 데이터 수집 방법

### 2.1 CPU 벤치마크 (cpu_benchmarks.json)

**데이터 출처:**
- [PassMark CPU Benchmark](https://www.cpubenchmark.net/)
- [Cinebench R23 Scores](https://www.cgdirector.com/cinebench-r23-scores/)
- [Geekbench Browser](https://browser.geekbench.com/processor-benchmarks)
- [UserBenchmark](https://cpu.userbenchmark.com/)

**수집 방법:**

```python
# 방법 1: 수동 수집 (권장)
# PassMark 상위 500개 CPU 데이터 엑셀 다운로드 후 JSON 변환

# 방법 2: 웹 스크래핑 (주의: 이용약관 확인)
import requests
from bs4 import BeautifulSoup

def scrape_passmark_cpu():
    url = "https://www.cpubenchmark.net/cpu_list.php"
    # 주의: robots.txt 및 이용약관 확인 필요
    # 상업적 사용 시 API 라이선스 구매 권장
    pass
```

**필요 필드:**
- `name`: CPU 이름 (정규화된 형식)
- `passmark_score`: PassMark 점수
- `cinebench_single`: Cinebench R23 싱글코어
- `cinebench_multi`: Cinebench R23 멀티코어
- `geekbench_single`: Geekbench 6 싱글코어
- `geekbench_multi`: Geekbench 6 멀티코어
- `tdp`: 열설계전력 (W)
- `cores`: 코어 수
- `threads`: 스레드 수
- `release_date`: 출시일

### 2.2 GPU 벤치마크 (gpu_benchmarks.json)

**데이터 출처:**
- [PassMark GPU Benchmark](https://www.videocardbenchmark.net/)
- [3DMark Scores](https://benchmarks.ul.com/hardware/best-gpus)
- [TechPowerUp GPU Database](https://www.techpowerup.com/gpu-specs/)
- [Tom's Hardware GPU Hierarchy](https://www.tomshardware.com/reviews/gpu-hierarchy,4388.html)

**수집 방법:**

```python
# TechPowerUp GPU 스펙 페이지에서 데이터 수집
# 주의: 이용약관 확인 필요

def collect_gpu_data():
    # 방법 1: GPU-Z 내보내기 파일 활용
    # 방법 2: 공개 API 활용 (있는 경우)
    # 방법 3: 수동 입력 (정확도 높음)
    pass
```

**필요 필드:**
- `name`: GPU 이름
- `passmark_score`: PassMark G3D Mark
- `timespy_score`: 3DMark Time Spy 점수
- `firestrike_score`: 3DMark Fire Strike 점수
- `vram`: VRAM 용량 (GB)
- `memory_type`: 메모리 타입 (GDDR6, GDDR6X 등)
- `tdp`: TDP (W)
- `release_date`: 출시일

### 2.3 게임 권장사양 (game_requirements.json)

**데이터 출처:**
- [Steam 스토어 페이지](https://store.steampowered.com/)
- [PC Gaming Wiki](https://www.pcgamingwiki.com/)
- [Can You Run It](https://www.systemrequirementslab.com/)

**수집 방법:**

```python
# Steam API 활용
import requests

def get_steam_requirements(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    data = response.json()
    
    if data[str(app_id)]['success']:
        requirements = data[str(app_id)]['data'].get('pc_requirements', {})
        return requirements
    return None

# 인기 게임 app_id 목록
POPULAR_GAMES = {
    "PUBG": 578080,
    "GTA V": 271590,
    "Cyberpunk 2077": 1091500,
    "Elden Ring": 1245620,
    # ...
}
```

**필요 필드:**
- `name`: 게임 이름
- `steam_app_id`: Steam App ID
- `minimum`: 최소 사양 (CPU, GPU, RAM)
- `recommended`: 권장 사양
- `ultra_4k`: 울트라/4K 사양 (있는 경우)
- `release_date`: 출시일

### 2.4 용도별 권장 스펙 (purpose_specs.json)

**데이터 출처:**
- 전문가 가이드 문서
- 하드웨어 리뷰 사이트
- 소프트웨어 공식 요구사양

**수동 작성:**

```json
{
  "gaming_1080p": {
    "description": "1080p 60fps 게이밍",
    "cpu_score_min": 15000,
    "gpu_score_min": 10000,
    "ram_min_gb": 16,
    "storage_type": "SSD"
  },
  "gaming_1440p": {
    "description": "1440p 144fps 게이밍",
    "cpu_score_min": 25000,
    "gpu_score_min": 18000,
    "ram_min_gb": 32,
    "storage_type": "NVMe"
  },
  "video_editing_4k": {
    "description": "4K 영상 편집",
    "cpu_score_min": 30000,
    "gpu_score_min": 15000,
    "ram_min_gb": 64,
    "storage_type": "NVMe"
  }
  // ...
}
```

---

## 3. 데이터 형식

### cpu_benchmarks.json

```json
{
  "version": "1.0.0",
  "updated_at": "2024-12-31",
  "source": ["PassMark", "Cinebench", "Geekbench"],
  "data": [
    {
      "id": "intel_i9_14900k",
      "name": "Intel Core i9-14900K",
      "brand": "Intel",
      "generation": 14,
      "socket": "LGA1700",
      "cores": 24,
      "threads": 32,
      "base_clock_ghz": 3.2,
      "boost_clock_ghz": 6.0,
      "tdp_w": 125,
      "release_date": "2023-10-17",
      "benchmarks": {
        "passmark": 60195,
        "cinebench_r23_single": 2283,
        "cinebench_r23_multi": 40616,
        "geekbench6_single": 2998,
        "geekbench6_multi": 19847
      },
      "tier": "enthusiast"
    }
  ]
}
```

### gpu_benchmarks.json

```json
{
  "version": "1.0.0",
  "updated_at": "2024-12-31",
  "source": ["PassMark", "3DMark", "TechPowerUp"],
  "data": [
    {
      "id": "nvidia_rtx4090",
      "name": "NVIDIA GeForce RTX 4090",
      "brand": "NVIDIA",
      "architecture": "Ada Lovelace",
      "vram_gb": 24,
      "memory_type": "GDDR6X",
      "memory_bus_bit": 384,
      "tdp_w": 450,
      "release_date": "2022-10-12",
      "benchmarks": {
        "passmark_g3d": 39227,
        "timespy": 36688,
        "firestrike": 57257
      },
      "tier": "enthusiast",
      "msrp_usd": 1599
    }
  ]
}
```

### game_requirements.json

```json
{
  "version": "1.0.0",
  "updated_at": "2024-12-31",
  "data": [
    {
      "name": "Cyberpunk 2077",
      "steam_app_id": 1091500,
      "genre": ["RPG", "Action"],
      "release_date": "2020-12-10",
      "requirements": {
        "minimum": {
          "cpu": "Intel Core i5-3570K",
          "cpu_score": 6500,
          "gpu": "GTX 970",
          "gpu_score": 9000,
          "ram_gb": 8,
          "storage_gb": 70
        },
        "recommended": {
          "cpu": "Intel Core i7-6700",
          "cpu_score": 8500,
          "gpu": "RTX 2060",
          "gpu_score": 15000,
          "ram_gb": 16,
          "storage_gb": 70
        },
        "ultra_4k": {
          "cpu": "Intel Core i9-12900K",
          "cpu_score": 40000,
          "gpu": "RTX 4090",
          "gpu_score": 39000,
          "ram_gb": 32,
          "storage_gb": 70
        }
      }
    }
  ]
}
```

---

## 4. 데이터 갱신 주기

| 데이터 | 갱신 주기 | 트리거 |
|--------|----------|--------|
| CPU 벤치마크 | 월 1회 | 신제품 출시, 분기별 정기 |
| GPU 벤치마크 | 월 1회 | 신제품 출시, 분기별 정기 |
| 게임 권장사양 | 필요 시 | 인기 신작 출시 |
| 용도별 스펙 | 분기 1회 | 하드웨어 세대 교체 |

---

## 5. 데이터 검증

```python
# data_validator.py
import json
from pathlib import Path

def validate_cpu_benchmarks(filepath: str) -> bool:
    """CPU 벤치마크 데이터 유효성 검사"""
    with open(filepath) as f:
        data = json.load(f)
    
    required_fields = ['id', 'name', 'benchmarks']
    benchmark_fields = ['passmark', 'cinebench_r23_single']
    
    for cpu in data['data']:
        for field in required_fields:
            if field not in cpu:
                print(f"Missing field: {field} in {cpu.get('name', 'unknown')}")
                return False
        
        for bm in benchmark_fields:
            if bm not in cpu['benchmarks']:
                print(f"Missing benchmark: {bm} in {cpu['name']}")
                return False
    
    return True
```

---

## 6. 초기 데이터 시드

최소한의 동작을 위해 다음 데이터를 우선 수집:

1. **CPU**: Intel 12~14세대, AMD Ryzen 5000~7000 시리즈 (약 50개)
2. **GPU**: NVIDIA RTX 30/40 시리즈, AMD RX 6000/7000 시리즈 (약 30개)
3. **게임**: 인기 게임 상위 20개

---

## 담당자 체크리스트

- [ ] CPU 벤치마크 50개 이상 수집
- [ ] GPU 벤치마크 30개 이상 수집
- [ ] 게임 권장사양 20개 이상 수집
- [ ] 용도별 스펙 기준 5개 이상 정의
- [ ] 데이터 검증 스크립트 실행
- [ ] 모듈 코드와 연동 테스트
