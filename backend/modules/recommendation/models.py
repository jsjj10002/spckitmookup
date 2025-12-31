"""
GNN 추천 모델
=============

[목표]
------
PyTorch Geometric 기반 GNN 모델 구현.
GraphSAGE, GAT 등 다양한 아키텍처 지원.

[모델 아키텍처]
--------------
1. GraphSAGE: 이웃 샘플링 + 집계
2. GAT (Graph Attention Network): 어텐션 기반 집계
3. HeteroGNN: 이종 그래프용

[학습 방법]
----------
- Link Prediction: 부품 간 추천 관계 예측
- Node Classification: 부품 적합도 분류
- Contrastive Learning: 유사 부품 임베딩 학습

[참고]
-----
- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/
- GraphSAGE 논문: https://arxiv.org/abs/1706.02216
- GAT 논문: https://arxiv.org/abs/1710.10903

[TODO]
-----
- [ ] PyTorch Geometric 설치
- [ ] 모델 학습 파이프라인
- [ ] 모델 평가 메트릭
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

# TODO: PyTorch Geometric 설치 후 주석 해제
# import torch
# import torch.nn as nn
# import torch.nn.functional as F
# from torch_geometric.nn import SAGEConv, GATConv, HeteroConv
# from torch_geometric.data import HeteroData


# ============================================================================
# 모델 설정
# ============================================================================

@dataclass
class GNNConfig:
    """GNN 모델 설정"""
    # 임베딩 차원
    embedding_dim: int = 64
    hidden_dim: int = 128
    output_dim: int = 64
    
    # 레이어 설정
    num_layers: int = 2
    dropout: float = 0.3
    
    # 어텐션 설정 (GAT용)
    num_heads: int = 4
    
    # 학습 설정
    learning_rate: float = 0.001
    weight_decay: float = 1e-5


# ============================================================================
# GNN 모델 (Placeholder)
# ============================================================================

class RecommendationGNN:
    """
    PC 부품 추천용 GNN 모델
    
    PyTorch Geometric 기반 그래프 신경망.
    부품 간 관계를 학습하여 개인화 추천에 활용.
    
    사용법:
    ```python
    config = GNNConfig(embedding_dim=64, num_layers=2)
    model = RecommendationGNN(config)
    
    # 학습
    model.train(graph_data, epochs=100)
    
    # 추론
    embeddings = model.get_embeddings(component_ids)
    scores = model.predict_link(component1_id, component2_id)
    ```
    
    [모델 구조]
    ----------
    1. 노드 임베딩 레이어
    2. GraphSAGE/GAT 집계 레이어 x N
    3. 출력 레이어 (링크 예측 또는 노드 분류)
    
    [학습 목표]
    ----------
    - 호환되는 부품 쌍의 임베딩을 가깝게
    - 비호환 부품 쌍의 임베딩을 멀게
    - 시너지 있는 부품 쌍에 높은 점수
    """
    
    def __init__(
        self,
        config: Optional[GNNConfig] = None,
        model_type: str = "sage",  # sage, gat
    ):
        """
        Args:
            config: 모델 설정
            model_type: 모델 타입 (sage, gat)
        """
        self.config = config or GNNConfig()
        self.model_type = model_type
        
        # TODO: 실제 PyTorch 모델 초기화
        # self._build_model()
        
        logger.info(f"RecommendationGNN 초기화: type={model_type}")
    
    def _build_model(self):
        """
        모델 구조 빌드
        
        TODO: PyTorch Geometric 설치 후 구현
        """
        # GraphSAGE 예시:
        #
        # class GraphSAGEModel(nn.Module):
        #     def __init__(self, in_channels, hidden_channels, out_channels, num_layers):
        #         super().__init__()
        #         self.convs = nn.ModuleList()
        #         self.convs.append(SAGEConv(in_channels, hidden_channels))
        #         for _ in range(num_layers - 2):
        #             self.convs.append(SAGEConv(hidden_channels, hidden_channels))
        #         self.convs.append(SAGEConv(hidden_channels, out_channels))
        #
        #     def forward(self, x, edge_index):
        #         for conv in self.convs[:-1]:
        #             x = conv(x, edge_index)
        #             x = F.relu(x)
        #             x = F.dropout(x, p=0.3, training=self.training)
        #         x = self.convs[-1](x, edge_index)
        #         return x
        #
        # self.model = GraphSAGEModel(...)
        pass
    
    def train(
        self,
        graph_data: Any,
        epochs: int = 100,
        batch_size: int = 256,
    ):
        """
        모델 학습
        
        Args:
            graph_data: 학습용 그래프 데이터
            epochs: 학습 에폭 수
            batch_size: 배치 크기
        """
        logger.info(f"모델 학습 시작: {epochs} epochs")
        
        # TODO: 실제 학습 루프 구현
        #
        # optimizer = torch.optim.Adam(
        #     self.model.parameters(),
        #     lr=self.config.learning_rate,
        #     weight_decay=self.config.weight_decay
        # )
        #
        # for epoch in range(epochs):
        #     self.model.train()
        #     total_loss = 0
        #
        #     for batch in data_loader:
        #         optimizer.zero_grad()
        #         out = self.model(batch.x, batch.edge_index)
        #         loss = self._compute_loss(out, batch)
        #         loss.backward()
        #         optimizer.step()
        #         total_loss += loss.item()
        #
        #     logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}")
        
        logger.info("모델 학습 완료 (placeholder)")
    
    def _compute_loss(self, embeddings: Any, batch: Any) -> float:
        """
        손실 함수 계산
        
        Link Prediction 손실:
        - Positive edges: 호환/시너지 부품 쌍
        - Negative edges: 랜덤 샘플링된 부품 쌍
        """
        # TODO: 실제 손실 함수 구현
        # pos_score = (embeddings[pos_edge_index[0]] * embeddings[pos_edge_index[1]]).sum(dim=1)
        # neg_score = (embeddings[neg_edge_index[0]] * embeddings[neg_edge_index[1]]).sum(dim=1)
        # loss = F.binary_cross_entropy_with_logits(pos_score, ones) + \
        #        F.binary_cross_entropy_with_logits(neg_score, zeros)
        return 0.0
    
    def get_embeddings(
        self,
        node_ids: List[str],
    ) -> Dict[str, List[float]]:
        """
        노드 임베딩 조회
        
        Args:
            node_ids: 노드 ID 리스트
            
        Returns:
            노드별 임베딩 벡터 딕셔너리
        """
        # TODO: 실제 임베딩 추출
        # self.model.eval()
        # with torch.no_grad():
        #     embeddings = self.model(data.x, data.edge_index)
        #     return {node_id: embeddings[idx].tolist() for node_id, idx in node_mapping.items()}
        
        # Placeholder: 랜덤 임베딩 반환
        import random
        return {
            node_id: [random.random() for _ in range(self.config.embedding_dim)]
            for node_id in node_ids
        }
    
    def predict_link(
        self,
        source_id: str,
        target_id: str,
    ) -> float:
        """
        링크 예측 (두 노드 간 관계 강도)
        
        Args:
            source_id: 소스 노드 ID
            target_id: 타겟 노드 ID
            
        Returns:
            예측 점수 (0-1)
        """
        embeddings = self.get_embeddings([source_id, target_id])
        
        # 코사인 유사도 계산
        emb1 = embeddings[source_id]
        emb2 = embeddings[target_id]
        
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a ** 2 for a in emb1) ** 0.5
        norm2 = sum(a ** 2 for a in emb2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # 0-1 범위로 정규화
        return (similarity + 1) / 2
    
    def recommend(
        self,
        selected_ids: List[str],
        candidate_ids: List[str],
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        추천 부품 순위 생성
        
        Args:
            selected_ids: 이미 선택한 부품 ID들
            candidate_ids: 후보 부품 ID들
            top_k: 상위 K개 반환
            
        Returns:
            (부품 ID, 점수) 튜플 리스트
        """
        if not selected_ids:
            # 선택된 부품 없으면 랜덤 순위
            import random
            return [(cid, random.random()) for cid in candidate_ids[:top_k]]
        
        scores = []
        
        for candidate_id in candidate_ids:
            # 선택된 모든 부품과의 평균 점수
            avg_score = 0
            for selected_id in selected_ids:
                avg_score += self.predict_link(selected_id, candidate_id)
            avg_score /= len(selected_ids)
            
            scores.append((candidate_id, avg_score))
        
        # 점수 순 정렬
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def save(self, path: str):
        """모델 저장"""
        logger.info(f"모델 저장: {path}")
        # torch.save({
        #     'model_state_dict': self.model.state_dict(),
        #     'config': self.config,
        # }, path)
    
    @classmethod
    def load(cls, path: str) -> "RecommendationGNN":
        """모델 로드"""
        logger.info(f"모델 로드: {path}")
        # checkpoint = torch.load(path)
        # model = cls(config=checkpoint['config'])
        # model.model.load_state_dict(checkpoint['model_state_dict'])
        # return model
        return cls()


# ============================================================================
# 모델 평가 메트릭
# ============================================================================

class GNNEvaluator:
    """
    GNN 모델 평가기
    
    추천 성능 평가 메트릭:
    - Hit Rate @ K
    - NDCG @ K
    - MRR (Mean Reciprocal Rank)
    """
    
    @staticmethod
    def hit_rate_at_k(
        predictions: List[str],
        ground_truth: List[str],
        k: int = 5,
    ) -> float:
        """
        Hit Rate @ K
        
        상위 K개 예측 중 정답이 포함된 비율.
        """
        top_k = set(predictions[:k])
        truth_set = set(ground_truth)
        
        hits = len(top_k & truth_set)
        return hits / min(k, len(ground_truth)) if ground_truth else 0.0
    
    @staticmethod
    def ndcg_at_k(
        predictions: List[str],
        ground_truth: List[str],
        k: int = 5,
    ) -> float:
        """
        NDCG @ K (Normalized Discounted Cumulative Gain)
        
        순위를 고려한 추천 품질 평가.
        """
        import math
        
        truth_set = set(ground_truth)
        
        dcg = 0.0
        for i, pred in enumerate(predictions[:k]):
            if pred in truth_set:
                dcg += 1 / math.log2(i + 2)  # i+2 because log2(1) = 0
        
        # Ideal DCG
        idcg = sum(1 / math.log2(i + 2) for i in range(min(k, len(ground_truth))))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def mrr(
        predictions: List[str],
        ground_truth: List[str],
    ) -> float:
        """
        MRR (Mean Reciprocal Rank)
        
        첫 번째 정답의 순위 역수.
        """
        truth_set = set(ground_truth)
        
        for i, pred in enumerate(predictions):
            if pred in truth_set:
                return 1.0 / (i + 1)
        
        return 0.0


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # 모델 테스트
    config = GNNConfig(embedding_dim=32, num_layers=2)
    model = RecommendationGNN(config)
    
    # 임베딩 테스트
    node_ids = ["cpu_i5_14600k", "mb_asus_z790", "gpu_rtx4070"]
    embeddings = model.get_embeddings(node_ids)
    
    print("임베딩:")
    for node_id, emb in embeddings.items():
        print(f"  {node_id}: dim={len(emb)}")
    
    # 링크 예측 테스트
    score = model.predict_link("cpu_i5_14600k", "mb_asus_z790")
    print(f"\n링크 예측 (CPU-MB): {score:.4f}")
    
    # 추천 테스트
    recommendations = model.recommend(
        selected_ids=["cpu_i5_14600k"],
        candidate_ids=["mb_asus_z790", "mb_msi_b650", "gpu_rtx4070"],
        top_k=3
    )
    
    print("\n추천 결과:")
    for comp_id, score in recommendations:
        print(f"  {comp_id}: {score:.4f}")
