"""
가격 예측 모듈 테스트
====================

테스트 실행:
```bash
pytest backend/tests/test_price_prediction.py -v
```
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPricePredictionModel:
    """PricePredictionModel 테스트"""
    
    @pytest.fixture
    def model(self):
        from backend.modules.price_prediction.predictor import PricePredictionModel
        return PricePredictionModel()
    
    @pytest.fixture
    def sample_history(self):
        """테스트용 가격 이력"""
        import numpy as np
        
        base_price = 720000
        history = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            # 약간의 하락 추세 시뮬레이션
            price = base_price - (i * 500) + np.random.randint(-3000, 3000)
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": max(650000, int(price))
            })
        
        return history
    
    def test_model_initialization(self, model):
        """모델 초기화 테스트"""
        assert model is not None
        assert model.model_type == "simple"
    
    def test_predict_with_history(self, model, sample_history):
        """가격 이력 기반 예측 테스트"""
        result = model.predict(
            component_id="gpu_rtx4070",
            component_name="RTX 4070",
            category="gpu",
            current_price=700000,
            price_history=sample_history,
            prediction_days=30,
        )
        
        assert result is not None
        assert len(result.predictions) == 30
        assert result.trend is not None
        assert result.buy_recommendation is not None
    
    def test_predict_without_history(self, model):
        """가격 이력 없이 예측 테스트"""
        result = model.predict(
            component_id="gpu_test",
            component_name="Test GPU",
            category="gpu",
            current_price=700000,
            price_history=[],
            prediction_days=14,
        )
        
        assert result is not None
        assert len(result.predictions) == 14
    
    def test_prediction_structure(self, model, sample_history):
        """예측 결과 구조 테스트"""
        result = model.predict(
            component_id="test",
            component_name="Test",
            category="gpu",
            current_price=700000,
            price_history=sample_history,
            prediction_days=7,
        )
        
        # 예측 포인트 구조 확인
        pred = result.predictions[0]
        assert pred.date is not None
        assert pred.price > 0
        assert pred.lower <= pred.price <= pred.upper
    
    def test_trend_analysis(self, model, sample_history):
        """추세 분석 테스트"""
        result = model.predict(
            component_id="test",
            component_name="Test",
            category="gpu",
            current_price=700000,
            price_history=sample_history,
            prediction_days=30,
        )
        
        trend = result.trend
        assert trend.direction is not None
        assert 0 <= trend.strength <= 1
    
    def test_buy_recommendation(self, model, sample_history):
        """구매 추천 테스트"""
        result = model.predict(
            component_id="test",
            component_name="Test",
            category="gpu",
            current_price=700000,
            price_history=sample_history,
            prediction_days=30,
        )
        
        rec = result.buy_recommendation
        assert rec.action is not None
        assert 0 <= rec.confidence <= 1
        assert rec.reasoning is not None


class TestPriceDataCollector:
    """PriceDataCollector 테스트"""
    
    @pytest.fixture
    def collector(self):
        from backend.modules.price_prediction.data_collector import PriceDataCollector
        return PriceDataCollector()
    
    def test_collector_initialization(self, collector):
        """수집기 초기화 테스트"""
        assert collector is not None
        assert collector.data_dir is not None
    
    def test_collect_price(self, collector):
        """가격 수집 테스트 (manual 모드)"""
        record = collector.collect_price("RTX 4070", "gpu")
        
        assert record is not None
        assert record.component_name == "RTX 4070"
        assert record.category == "gpu"
        assert record.min_price > 0
    
    def test_add_and_get_history(self, collector):
        """가격 기록 추가 및 조회 테스트"""
        from backend.modules.price_prediction.data_collector import PriceRecord
        
        record = PriceRecord(
            component_id="test_comp",
            component_name="Test Component",
            category="gpu",
            date="2024-01-15",
            min_price=500000,
            avg_price=550000,
            max_price=600000,
            source="manual"
        )
        
        collector.add_price_record(record)
        history = collector.get_price_history("test_comp", days=30)
        
        assert len(history) == 1
        assert history[0].component_id == "test_comp"


class TestPriceFeatureExtractor:
    """PriceFeatureExtractor 테스트"""
    
    @pytest.fixture
    def extractor(self):
        from backend.modules.price_prediction.features import PriceFeatureExtractor
        return PriceFeatureExtractor()
    
    @pytest.fixture
    def sample_history(self):
        """테스트용 가격 이력"""
        import numpy as np
        
        history = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            price = 700000 + np.random.randint(-10000, 10000)
            history.append({"date": date.strftime("%Y-%m-%d"), "price": int(price)})
        
        return history
    
    def test_extractor_initialization(self, extractor):
        """추출기 초기화 테스트"""
        assert extractor is not None
    
    def test_extract_features(self, extractor, sample_history):
        """특성 추출 테스트"""
        features = extractor.extract(sample_history)
        
        assert features is not None
        assert features.ma_7 is not None
        assert features.volatility is not None
    
    def test_moving_average(self, extractor, sample_history):
        """이동평균 계산 테스트"""
        features = extractor.extract(sample_history)
        
        if len(sample_history) >= 7:
            assert features.ma_7 is not None
            assert features.ma_7 > 0
    
    def test_to_array(self, extractor, sample_history):
        """배열 변환 테스트"""
        features = extractor.extract(sample_history)
        arr = extractor.to_array(features)
        
        assert arr is not None
        assert len(arr) > 0


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
