"""
GNN 기반 추천 시스템 모듈 테스트
================================

테스트 실행:
```bash
pytest backend/tests/test_recommendation.py -v
```
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestGNNRecommendationEngine:
    """GNNRecommendationEngine 테스트"""
    
    @pytest.fixture
    def engine(self):
        from backend.modules.recommendation.engine import GNNRecommendationEngine
        return GNNRecommendationEngine()
    
    def test_engine_initialization(self, engine):
        """엔진 초기화 테스트"""
        assert engine is not None
        assert engine._compatibility_rules is not None
    
    def test_recommend_motherboard(self, engine):
        """메인보드 추천 테스트"""
        result = engine.recommend(
            selected_components=[
                {"category": "cpu", "name": "Intel Core i5-14600K"}
            ],
            target_category="motherboard",
            budget=300000,
            purpose="gaming",
        )
        
        assert result is not None
        assert len(result.recommendations) > 0
        
        # 첫 번째 추천 검증
        first_rec = result.recommendations[0]
        assert first_rec.rank == 1
        assert first_rec.scores.compatibility == 1.0  # 호환되는 것만
    
    def test_recommend_with_preferences(self, engine):
        """선호 설정 적용 추천 테스트"""
        result = engine.recommend(
            selected_components=[
                {"category": "cpu", "name": "Intel Core i5-14600K"}
            ],
            target_category="motherboard",
            budget=300000,
            preferences={"brand": "ASUS", "priority": "quality"},
        )
        
        # ASUS 브랜드가 더 높은 점수
        asus_recs = [r for r in result.recommendations if "ASUS" in r.name]
        if asus_recs:
            assert asus_recs[0].scores.relevance > 0.8
    
    def test_recommendation_result_structure(self, engine):
        """추천 결과 구조 테스트"""
        result = engine.recommend(
            selected_components=[],
            target_category="gpu",
            budget=800000,
        )
        
        assert hasattr(result, 'recommendations')
        assert hasattr(result, 'graph_context')
        assert hasattr(result, 'processing_time_ms')
        
        if result.recommendations:
            rec = result.recommendations[0]
            assert hasattr(rec, 'scores')
            assert hasattr(rec, 'reasons')


class TestPCComponentGraph:
    """PCComponentGraph 테스트"""
    
    @pytest.fixture
    def graph(self):
        from backend.modules.recommendation.graph_builder import PCComponentGraph
        return PCComponentGraph()
    
    def test_graph_initialization(self, graph):
        """그래프 초기화 테스트"""
        # 기본 카테고리/목적 노드가 생성됨
        assert len(graph.nodes) > 0
    
    def test_add_component(self, graph):
        """부품 추가 테스트"""
        graph.add_component(
            component_id="cpu_test",
            name="Test CPU",
            category="cpu",
            attributes={"socket": "LGA1700", "brand": "Intel"}
        )
        
        assert "cpu_test" in graph.nodes
        assert graph.nodes["cpu_test"].name == "Test CPU"
    
    def test_load_components(self, graph):
        """부품 로드 테스트"""
        components = [
            {"id": "cpu_1", "name": "CPU 1", "category": "cpu"},
            {"id": "gpu_1", "name": "GPU 1", "category": "gpu"},
        ]
        
        initial_count = len(graph.nodes)
        graph.load_components_from_dict(components)
        
        assert len(graph.nodes) > initial_count
    
    def test_get_stats(self, graph):
        """통계 조회 테스트"""
        stats = graph.get_stats()
        
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "node_counts" in stats


class TestRecommendationGNN:
    """RecommendationGNN 테스트"""
    
    @pytest.fixture
    def model(self):
        from backend.modules.recommendation.models import RecommendationGNN, GNNConfig
        config = GNNConfig(embedding_dim=32, num_layers=2)
        return RecommendationGNN(config)
    
    def test_model_initialization(self, model):
        """모델 초기화 테스트"""
        assert model is not None
        assert model.config.embedding_dim == 32
    
    def test_get_embeddings(self, model):
        """임베딩 조회 테스트"""
        node_ids = ["node1", "node2", "node3"]
        embeddings = model.get_embeddings(node_ids)
        
        assert len(embeddings) == 3
        for node_id in node_ids:
            assert node_id in embeddings
            assert len(embeddings[node_id]) == model.config.embedding_dim
    
    def test_predict_link(self, model):
        """링크 예측 테스트"""
        score = model.predict_link("node1", "node2")
        
        assert 0 <= score <= 1
    
    def test_recommend(self, model):
        """추천 테스트"""
        recommendations = model.recommend(
            selected_ids=["selected_1"],
            candidate_ids=["cand_1", "cand_2", "cand_3"],
            top_k=2
        )
        
        assert len(recommendations) == 2
        # 점수 내림차순 정렬 확인
        assert recommendations[0][1] >= recommendations[1][1]


class TestGNNEvaluator:
    """GNNEvaluator 테스트"""
    
    def test_hit_rate_at_k(self):
        """Hit Rate @ K 테스트"""
        from backend.modules.recommendation.models import GNNEvaluator
        
        predictions = ["a", "b", "c", "d", "e"]
        ground_truth = ["b", "d"]
        
        hit_rate = GNNEvaluator.hit_rate_at_k(predictions, ground_truth, k=3)
        
        # b가 상위 3개에 있음
        assert hit_rate > 0
    
    def test_mrr(self):
        """MRR 테스트"""
        from backend.modules.recommendation.models import GNNEvaluator
        
        # 첫 번째가 정답인 경우
        predictions = ["a", "b", "c"]
        ground_truth = ["a"]
        
        mrr = GNNEvaluator.mrr(predictions, ground_truth)
        assert mrr == 1.0
        
        # 두 번째가 정답인 경우
        predictions = ["a", "b", "c"]
        ground_truth = ["b"]
        
        mrr = GNNEvaluator.mrr(predictions, ground_truth)
        assert mrr == 0.5


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
