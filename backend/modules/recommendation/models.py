import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Any, List
from dataclasses import dataclass
from torch_geometric.nn import SAGEConv, to_hetero

@dataclass
class GNNConfig:
    embedding_dim: int = 128
    hidden_dim: int = 256
    output_dim: int = 128
    num_layers: int = 2
    dropout: float = 0.2

class RecommendationGNN(nn.Module):
    def __init__(self, config: Optional[GNNConfig] = None, metadata: Any = None):
        super().__init__()
        self.config = config or GNNConfig()
        if metadata:
            self._build_model(metadata)

    def _build_model(self, metadata):
        class GNNLayer(nn.Module):
            def __init__(self, in_c, out_c, dropout):
                super().__init__()
                self.conv = SAGEConv(in_c, out_c)
                self.dropout = nn.Dropout(dropout)
            def forward(self, x, edge_index):
                x = self.conv(x, edge_index)
                return self.dropout(F.relu(x))

        self.encoder = to_hetero(GNNLayer(-1, self.config.hidden_dim, self.config.dropout), metadata)
        self.projection = to_hetero(GNNLayer(self.config.hidden_dim, self.config.output_dim, 0.0), metadata)

    def forward(self, x_dict, edge_index_dict):
        x_dict = self.encoder(x_dict, edge_index_dict)
        x_dict = {k: F.relu(x) for k, x in x_dict.items() if x is not None}
        x_dict = self.projection(x_dict, edge_index_dict)
        return x_dict

class GNNEvaluator:
    """추천 성능 평가를 위한 유틸리티 클래스 (__init__.py 참조용)"""
    @staticmethod
    def hit_rate_at_k(predictions: List[str], ground_truth: List[str], k: int = 5) -> float:
        if not ground_truth: return 0.0
        hits = len(set(predictions[:k]) & set(ground_truth))
        return hits / len(ground_truth)

    @staticmethod
    def mrr(predictions: List[str], ground_truth: List[str]) -> float:
        for i, p in enumerate(predictions):
            if p in ground_truth:
                return 1.0 / (i + 1)
        return 0.0