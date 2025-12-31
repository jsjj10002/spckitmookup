# 호환성 검사 모듈 데이터

> 소켓 매핑, 폼팩터, 전력 요구량, 물리적 치수 데이터

---

## 목차

1. [필요 데이터 목록](#1-필요-데이터-목록)
2. [데이터 수집 방법](#2-데이터-수집-방법)
3. [데이터 형식](#3-데이터-형식)
4. [호환성 규칙 정의](#4-호환성-규칙-정의)

---

## 1. 필요 데이터 목록

| 파일명 | 설명 | 우선순위 | 상태 |
|--------|------|----------|------|
| `cpu_socket_map.json` | CPU 소켓-메인보드 매핑 | 필수 | 미수집 |
| `memory_compatibility.json` | DDR 세대별 호환 정보 | 필수 | 미수집 |
| `form_factor_map.json` | 케이스-메인보드 폼팩터 | 필수 | 미수집 |
| `psu_requirements.json` | 부품별 전력 요구량 | 필수 | 미수집 |
| `physical_dimensions.json` | GPU 길이, 쿨러 높이 등 | 필수 | 미수집 |
| `pcie_compatibility.json` | PCIe 버전/레인 호환성 | 권장 | 미수집 |
| `storage_interfaces.json` | M.2/SATA 인터페이스 정보 | 권장 | 미수집 |

---

## 2. 데이터 수집 방법

### 2.1 CPU 소켓 매핑 (cpu_socket_map.json)

**데이터 출처:**
- Intel ARK (https://ark.intel.com/)
- AMD Product Specifications (https://www.amd.com/en/products/specifications/)
- Wikipedia CPU 소켓 목록

**수동 정리 (정확도 높음):**

```json
{
  "version": "1.0.0",
  "updated_at": "2024-12-31",
  "sockets": {
    "LGA1700": {
      "brand": "Intel",
      "supported_generations": [12, 13, 14],
      "supported_cpus": [
        "Intel Core i9-14900K",
        "Intel Core i9-14900KF",
        "Intel Core i7-14700K",
        "Intel Core i7-14700KF",
        "Intel Core i5-14600K",
        "Intel Core i5-14600KF",
        "Intel Core i9-13900K",
        "Intel Core i9-13900KF",
        "Intel Core i7-13700K",
        "Intel Core i5-13600K",
        "Intel Core i9-12900K",
        "Intel Core i7-12700K",
        "Intel Core i5-12600K"
      ],
      "compatible_chipsets": ["Z790", "Z690", "B760", "B660", "H770", "H670"],
      "cooler_mounting": "LGA1700",
      "note": "일부 LGA1200 쿨러 호환 (마운팅 킷 필요)"
    },
    "LGA1200": {
      "brand": "Intel",
      "supported_generations": [10, 11],
      "supported_cpus": [
        "Intel Core i9-11900K",
        "Intel Core i7-11700K",
        "Intel Core i5-11600K",
        "Intel Core i9-10900K",
        "Intel Core i7-10700K",
        "Intel Core i5-10600K"
      ],
      "compatible_chipsets": ["Z590", "Z490", "B560", "B460", "H570", "H470"],
      "cooler_mounting": "LGA1200"
    },
    "AM5": {
      "brand": "AMD",
      "supported_generations": ["Ryzen 7000", "Ryzen 9000"],
      "supported_cpus": [
        "AMD Ryzen 9 7950X3D",
        "AMD Ryzen 9 7950X",
        "AMD Ryzen 9 7900X3D",
        "AMD Ryzen 9 7900X",
        "AMD Ryzen 7 7800X3D",
        "AMD Ryzen 7 7700X",
        "AMD Ryzen 5 7600X",
        "AMD Ryzen 5 7600"
      ],
      "compatible_chipsets": ["X670E", "X670", "B650E", "B650"],
      "cooler_mounting": "AM5",
      "note": "AM4 쿨러 대부분 호환 (마운팅 홀 동일)"
    },
    "AM4": {
      "brand": "AMD",
      "supported_generations": ["Ryzen 1000", "Ryzen 2000", "Ryzen 3000", "Ryzen 5000"],
      "supported_cpus": [
        "AMD Ryzen 9 5950X",
        "AMD Ryzen 9 5900X",
        "AMD Ryzen 7 5800X3D",
        "AMD Ryzen 7 5800X",
        "AMD Ryzen 5 5600X",
        "AMD Ryzen 5 5600"
      ],
      "compatible_chipsets": ["X570", "X470", "X370", "B550", "B450", "B350", "A520", "A320"],
      "cooler_mounting": "AM4"
    }
  }
}
```

### 2.2 메모리 호환성 (memory_compatibility.json)

```json
{
  "version": "1.0.0",
  "memory_types": {
    "DDR5": {
      "voltage": 1.1,
      "pin_count": 288,
      "min_speed_mhz": 4800,
      "max_speed_mhz": 8400,
      "compatible_platforms": {
        "Intel": ["LGA1700 (Z690/B660 이상)", "LGA1851"],
        "AMD": ["AM5"]
      },
      "note": "DDR4와 물리적 호환 불가 (핀 배열 다름)"
    },
    "DDR4": {
      "voltage": 1.2,
      "pin_count": 288,
      "min_speed_mhz": 2133,
      "max_speed_mhz": 5333,
      "compatible_platforms": {
        "Intel": ["LGA1700 (일부)", "LGA1200", "LGA1151"],
        "AMD": ["AM4"]
      },
      "note": "DDR5와 물리적 호환 불가"
    }
  },
  "speed_compatibility": {
    "explanation": "메인보드가 지원하는 최대 속도까지만 인식",
    "examples": [
      {
        "memory": "DDR5-6000",
        "motherboard_max": "DDR5-5600",
        "result": "DDR5-5600으로 동작",
        "is_compatible": true
      },
      {
        "memory": "DDR5-6000",
        "motherboard_max": "DDR5-7200",
        "result": "DDR5-6000으로 동작 (XMP/EXPO 활성화)",
        "is_compatible": true
      }
    ]
  },
  "capacity_limits": {
    "consumer_desktop": {
      "max_per_slot_gb": 64,
      "typical_slots": [2, 4],
      "max_total_gb": 256
    }
  }
}
```

### 2.3 폼팩터 매핑 (form_factor_map.json)

```json
{
  "version": "1.0.0",
  "motherboard_form_factors": {
    "E-ATX": {
      "dimensions_mm": {"width": 305, "height": 330},
      "compatible_cases": ["Full Tower", "E-ATX Mid Tower"],
      "typical_pcie_slots": 7,
      "typical_ram_slots": 8
    },
    "ATX": {
      "dimensions_mm": {"width": 244, "height": 305},
      "compatible_cases": ["Full Tower", "Mid Tower", "일부 Mini Tower"],
      "typical_pcie_slots": 7,
      "typical_ram_slots": 4
    },
    "Micro-ATX": {
      "dimensions_mm": {"width": 244, "height": 244},
      "compatible_cases": ["Full Tower", "Mid Tower", "Mini Tower", "Micro-ATX 케이스"],
      "typical_pcie_slots": 4,
      "typical_ram_slots": 4
    },
    "Mini-ITX": {
      "dimensions_mm": {"width": 170, "height": 170},
      "compatible_cases": ["모든 케이스", "ITX 케이스", "SFF 케이스"],
      "typical_pcie_slots": 1,
      "typical_ram_slots": 2
    }
  },
  "case_form_factors": {
    "Full Tower": {
      "supported_motherboards": ["E-ATX", "ATX", "Micro-ATX", "Mini-ITX"],
      "typical_gpu_clearance_mm": 400,
      "typical_cooler_clearance_mm": 185
    },
    "Mid Tower": {
      "supported_motherboards": ["ATX", "Micro-ATX", "Mini-ITX"],
      "typical_gpu_clearance_mm": 350,
      "typical_cooler_clearance_mm": 165
    },
    "Mini Tower": {
      "supported_motherboards": ["Micro-ATX", "Mini-ITX"],
      "typical_gpu_clearance_mm": 300,
      "typical_cooler_clearance_mm": 155
    },
    "ITX Case": {
      "supported_motherboards": ["Mini-ITX"],
      "typical_gpu_clearance_mm": 280,
      "typical_cooler_clearance_mm": 70
    }
  }
}
```

### 2.4 PSU 전력 요구량 (psu_requirements.json)

```json
{
  "version": "1.0.0",
  "component_tdp": {
    "cpu": {
      "Intel Core i9-14900K": {"tdp": 125, "peak": 253},
      "Intel Core i7-14700K": {"tdp": 125, "peak": 253},
      "Intel Core i5-14600K": {"tdp": 125, "peak": 181},
      "AMD Ryzen 9 7950X": {"tdp": 170, "peak": 230},
      "AMD Ryzen 7 7800X3D": {"tdp": 120, "peak": 162},
      "AMD Ryzen 5 7600X": {"tdp": 105, "peak": 142}
    },
    "gpu": {
      "NVIDIA RTX 4090": {"tdp": 450, "peak": 600, "pcie_power": "1x16pin or 3x8pin"},
      "NVIDIA RTX 4080": {"tdp": 320, "peak": 400, "pcie_power": "1x16pin or 2x8pin"},
      "NVIDIA RTX 4070 Ti": {"tdp": 285, "peak": 350, "pcie_power": "1x16pin or 2x8pin"},
      "NVIDIA RTX 4070": {"tdp": 200, "peak": 250, "pcie_power": "1x8pin"},
      "AMD RX 7900 XTX": {"tdp": 355, "peak": 450, "pcie_power": "2x8pin"},
      "AMD RX 7800 XT": {"tdp": 263, "peak": 330, "pcie_power": "2x8pin"}
    }
  },
  "system_base_power": {
    "motherboard": 50,
    "memory_per_stick": 5,
    "ssd_nvme": 7,
    "ssd_sata": 3,
    "hdd": 10,
    "fans_per_unit": 3,
    "rgb_lighting": 10
  },
  "psu_recommendations": {
    "formula": "총 TDP * 1.5 ~ 2.0 권장",
    "tiers": [
      {"min_wattage": 0, "max_wattage": 400, "recommended_psu": 550},
      {"min_wattage": 400, "max_wattage": 550, "recommended_psu": 750},
      {"min_wattage": 550, "max_wattage": 700, "recommended_psu": 850},
      {"min_wattage": 700, "max_wattage": 900, "recommended_psu": 1000},
      {"min_wattage": 900, "max_wattage": 1200, "recommended_psu": 1200}
    ]
  },
  "efficiency_ratings": {
    "80+ Bronze": {"typical_efficiency": 0.85, "recommended_for": "budget"},
    "80+ Gold": {"typical_efficiency": 0.90, "recommended_for": "mainstream"},
    "80+ Platinum": {"typical_efficiency": 0.92, "recommended_for": "high-end"},
    "80+ Titanium": {"typical_efficiency": 0.94, "recommended_for": "enthusiast"}
  }
}
```

### 2.5 물리적 치수 (physical_dimensions.json)

```json
{
  "version": "1.0.0",
  "gpu_dimensions": {
    "NVIDIA RTX 4090": {
      "length_mm": 336,
      "width_mm": 140,
      "slots": 3.5,
      "weight_g": 2180
    },
    "NVIDIA RTX 4080": {
      "length_mm": 304,
      "width_mm": 137,
      "slots": 3,
      "weight_g": 1650
    },
    "NVIDIA RTX 4070 Ti": {
      "length_mm": 285,
      "width_mm": 122,
      "slots": 2.5,
      "weight_g": 1200
    },
    "NVIDIA RTX 4070": {
      "length_mm": 240,
      "width_mm": 115,
      "slots": 2,
      "weight_g": 900
    },
    "AMD RX 7900 XTX": {
      "length_mm": 287,
      "width_mm": 123,
      "slots": 2.5,
      "weight_g": 1350
    }
  },
  "cpu_cooler_dimensions": {
    "Noctua NH-D15": {
      "height_mm": 165,
      "width_mm": 150,
      "depth_mm": 161,
      "ram_clearance_mm": 32,
      "supported_sockets": ["LGA1700", "LGA1200", "AM5", "AM4"]
    },
    "be quiet! Dark Rock Pro 4": {
      "height_mm": 163,
      "width_mm": 136,
      "depth_mm": 145,
      "ram_clearance_mm": 40,
      "supported_sockets": ["LGA1700", "LGA1200", "AM5", "AM4"]
    },
    "Noctua NH-L9i": {
      "height_mm": 37,
      "width_mm": 95,
      "depth_mm": 95,
      "ram_clearance_mm": "무제한",
      "supported_sockets": ["LGA1700", "LGA1200"],
      "note": "로우프로파일 ITX용"
    }
  },
  "aio_radiator_sizes": {
    "120mm": {"mounting": "120mm", "recommended_tdp_max": 100},
    "240mm": {"mounting": "2x120mm", "recommended_tdp_max": 180},
    "280mm": {"mounting": "2x140mm", "recommended_tdp_max": 200},
    "360mm": {"mounting": "3x120mm", "recommended_tdp_max": 280}
  }
}
```

---

## 3. 데이터 형식

### 통합 스키마

```python
"""
호환성 데이터 스키마 정의
"""
from pydantic import BaseModel
from typing import List, Optional, Dict

class SocketInfo(BaseModel):
    brand: str
    supported_generations: List[str]
    supported_cpus: List[str]
    compatible_chipsets: List[str]
    cooler_mounting: str
    note: Optional[str] = None

class MemoryType(BaseModel):
    voltage: float
    pin_count: int
    min_speed_mhz: int
    max_speed_mhz: int
    compatible_platforms: Dict[str, List[str]]

class FormFactor(BaseModel):
    dimensions_mm: Dict[str, int]
    supported_motherboards: List[str]
    typical_gpu_clearance_mm: int
    typical_cooler_clearance_mm: int

class ComponentPower(BaseModel):
    tdp: int
    peak: int
    pcie_power: Optional[str] = None

class PhysicalDimension(BaseModel):
    length_mm: int
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    slots: Optional[float] = None
    weight_g: Optional[int] = None
```

---

## 4. 호환성 규칙 정의

### 규칙 우선순위

| 순위 | 검사 항목 | 심각도 | 설명 |
|------|----------|--------|------|
| 1 | CPU-메인보드 소켓 | Critical | 불일치 시 장착 불가 |
| 2 | 메모리-메인보드 DDR | Critical | 불일치 시 장착 불가 |
| 3 | GPU-케이스 길이 | Critical | 초과 시 장착 불가 |
| 4 | 메인보드-케이스 폼팩터 | Critical | 불일치 시 장착 불가 |
| 5 | CPU 쿨러-케이스 높이 | Warning | 초과 시 측판 장착 불가 |
| 6 | PSU 용량 | Warning | 부족 시 시스템 불안정 |
| 7 | 메모리 속도 | Info | 오버클럭 지원 여부 |

### 규칙 코드

```python
"""
backend/modules/compatibility/rules.py에서 사용하는 규칙 데이터
"""

COMPATIBILITY_RULES = [
    {
        "id": "cpu_mb_socket",
        "name": "CPU-메인보드 소켓 호환",
        "severity": "critical",
        "check": lambda cpu, mb: cpu['socket'] == mb['socket'],
        "message_pass": "CPU 소켓 호환됨",
        "message_fail": "CPU 소켓({cpu_socket})과 메인보드 소켓({mb_socket})이 다릅니다"
    },
    {
        "id": "memory_mb_type",
        "name": "메모리-메인보드 DDR 타입",
        "severity": "critical",
        "check": lambda mem, mb: mem['type'] == mb['memory_type'],
        "message_pass": "메모리 타입 호환됨",
        "message_fail": "메모리({mem_type})와 메인보드({mb_type})의 DDR 타입이 다릅니다"
    },
    {
        "id": "gpu_case_length",
        "name": "GPU-케이스 길이",
        "severity": "critical",
        "check": lambda gpu, case: gpu['length_mm'] <= case['max_gpu_length'],
        "message_pass": "GPU 길이 적합",
        "message_fail": "GPU 길이({gpu_length}mm)가 케이스 최대({case_max}mm)를 초과합니다"
    },
    {
        "id": "mb_case_form",
        "name": "메인보드-케이스 폼팩터",
        "severity": "critical",
        "check": lambda mb, case: mb['form_factor'] in case['supported_form_factors'],
        "message_pass": "폼팩터 호환됨",
        "message_fail": "메인보드({mb_form})가 케이스({case_forms})에 맞지 않습니다"
    },
    {
        "id": "cooler_case_height",
        "name": "CPU 쿨러-케이스 높이",
        "severity": "warning",
        "check": lambda cooler, case: cooler['height_mm'] <= case['max_cooler_height'],
        "message_pass": "쿨러 높이 적합",
        "message_fail": "쿨러 높이({cooler_height}mm)가 케이스({case_max}mm)를 초과할 수 있습니다"
    },
    {
        "id": "psu_capacity",
        "name": "PSU 용량",
        "severity": "warning",
        "check": lambda total_tdp, psu: total_tdp * 1.3 <= psu['wattage'],
        "message_pass": "PSU 용량 충분",
        "message_fail": "권장 PSU 용량({recommended}W)보다 낮습니다 (현재: {psu_wattage}W)"
    }
]
```

---

## 5. 데이터 갱신

### 갱신 주기

| 데이터 | 주기 | 트리거 |
|--------|------|--------|
| 소켓 매핑 | 연 2회 | 신규 플랫폼 출시 |
| 메모리 호환성 | 연 1회 | DDR 신세대 출시 |
| 폼팩터 | 거의 없음 | 표준 변경 시 |
| 전력 요구량 | 월 1회 | 신제품 출시 |
| 물리적 치수 | 월 1회 | 신제품 출시 |

---

## 담당자 체크리스트

- [ ] CPU 소켓 매핑 완료 (Intel/AMD 최근 3세대)
- [ ] 메모리 DDR4/DDR5 호환성 정리
- [ ] 폼팩터 매핑 완료 (ATX/mATX/ITX)
- [ ] PSU 전력 계산 규칙 정의
- [ ] 주요 GPU 30개 치수 데이터 수집
- [ ] 주요 쿨러 20개 치수 데이터 수집
- [ ] 호환성 규칙 코드 연동 테스트
