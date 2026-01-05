import torch
import torch.nn.functional as F
from loguru import logger
from pathlib import Path
import os
from .graph_builder import PCComponentGraph
from .models import RecommendationGNN, GNNConfig

def train_gnn():
    logger.info("성능 목표 달성을 위한 GNN 학습을 시작합니다.")
    
    builder = PCComponentGraph()
    builder.load_from_json()
    data = builder.to_pyg()
    
    if data is None: return

    config = GNNConfig()
    model = RecommendationGNN(config=config, metadata=data.metadata())
    
    save_path = Path("backend/modules/recommendation/model_weights.pt")
    if save_path.exists():
        logger.warning("가중치 규격 불일치를 방지하기 위해 기존 파일을 삭제하고 새로 학습합니다.")
        os.remove(save_path)

    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    model.train()

    rel = ('component', 'synergy', 'component')
    edge_index = data[rel].edge_index
    num_nodes = data['component'].num_nodes

    # BPR Loss 기반 학습
    epochs = 200 
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()
        
        z_dict = model(data.x_dict, data.edge_index_dict)
        z = z_dict['component']
        
        pos_scores = (z[edge_index[0]] * z[edge_index[1]]).sum(dim=-1)
        neg_dst = torch.randint(0, num_nodes, (edge_index.size(1),), device=z.device)
        neg_scores = (z[edge_index[0]] * z[neg_dst]).sum(dim=-1)
        
        loss = -torch.mean(F.logsigmoid(pos_scores - neg_scores))
        
        loss.backward()
        optimizer.step()
        
        if epoch % 20 == 0:
            logger.info(f"Epoch {epoch:03d}/{epochs} | Loss: {loss.item():.6f}")

    torch.save(model.state_dict(), save_path)
    logger.success(f"학습 완료! 저장됨: {save_path}")

if __name__ == "__main__":
    train_gnn()