"""
ChromaDB를 사용한 벡터 데이터베이스 관리
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from .config import CHROMA_PERSIST_DIRECTORY, CHROMA_COLLECTION_NAME
from .embedder import GeminiEmbedder


class PCComponentVectorStore:
    """PC 부품 정보를 저장하고 검색하는 벡터 데이터베이스"""

    def __init__(
        self,
        persist_directory: str = CHROMA_PERSIST_DIRECTORY,
        collection_name: str = CHROMA_COLLECTION_NAME,
        embedder: Optional[GeminiEmbedder] = None,
    ):
        """
        Args:
            persist_directory: ChromaDB 저장 디렉토리
            collection_name: 컬렉션 이름
            embedder: 임베딩 생성기 (None이면 자동 생성)
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedder = embedder or GeminiEmbedder()

        # ChromaDB 클라이언트 초기화
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        # 컬렉션 가져오기 또는 생성
        self.collection = self._get_or_create_collection()

        logger.info(
            f"PCComponentVectorStore 초기화 완료: "
            f"collection={collection_name}, "
            f"items={self.collection.count()}"
        )

    def _get_or_create_collection(self):
        """컬렉션 가져오기 또는 생성"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"기존 컬렉션 로드: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # 코사인 유사도 사용
            )
            logger.info(f"새 컬렉션 생성: {self.collection_name}")

        return collection

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 500,
    ) -> None:
        """
        문서들을 벡터 데이터베이스에 추가

        Args:
            documents: 문서 리스트 (각 문서는 'text'와 'metadata' 키 포함)
            batch_size: 배치 크기
        """
        logger.info(f"{len(documents)}개의 문서를 추가 중...")

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            
            # 텍스트 추출
            texts = [doc["text"] for doc in batch]
            
            # 메타데이터 정제: None 값 제거
            cleaned_metadatas = []
            for doc in batch:
                metadata = {}
                for k, v in doc["metadata"].items():
                    # None 값 또는 빈 값 건너뛰기
                    if v is None or v == "":
                        continue
                    # 지원되는 타입만 추가 (bool, int, float, str)
                    if isinstance(v, (bool, int, float)):
                        metadata[k] = v
                    else:
                        # 기타 타입은 문자열로 변환
                        metadata[k] = str(v)
                cleaned_metadatas.append(metadata)
            
            # ID 생성 (카테고리 + 인덱스)
            ids = [
                f"{doc['metadata'].get('category', 'unknown')}_{doc['metadata'].get('id', i + j)}"
                for j, doc in enumerate(batch)
            ]

            # 임베딩 생성
            logger.debug(f"배치 {i // batch_size + 1}: 임베딩 생성 중...")
            embeddings = self.embedder.embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")

            # ChromaDB에 추가
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=cleaned_metadatas,
            )

            logger.info(
                f"진행: {min(i + batch_size, len(documents))}/{len(documents)} "
                f"({(min(i + batch_size, len(documents)) / len(documents) * 100):.1f}%)"
            )

        logger.info(f"문서 추가 완료. 총 아이템 수: {self.collection.count()}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 문서 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            filter_metadata: 메타데이터 필터 (예: {"category": "cpu"})

        Returns:
            검색 결과 리스트
        """
        # 쿼리 임베딩 생성
        query_embedding = self.embedder.embed_query(query)

        # 검색 수행
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        # 결과 포맷팅
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # 코사인 거리 -> 유사도
                }
            )

        logger.info(f"검색 완료: '{query}' -> {len(formatted_results)}개 결과")
        return formatted_results

    def get_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        특정 카테고리의 부품 조회

        Args:
            category: 부품 카테고리 (예: "cpu", "gpu")
            limit: 최대 결과 수

        Returns:
            부품 리스트
        """
        results = self.collection.get(
            where={"category": category},
            limit=limit,
            include=["documents", "metadatas"],
        )

        formatted_results = []
        for i in range(len(results["ids"])):
            formatted_results.append(
                {
                    "id": results["ids"][i],
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
            )

        return formatted_results

    def delete_collection(self) -> None:
        """컬렉션 삭제 (데이터 초기화)"""
        self.client.delete_collection(name=self.collection_name)
        logger.warning(f"컬렉션 삭제됨: {self.collection_name}")
        self.collection = self._get_or_create_collection()

    def get_stats(self) -> Dict[str, Any]:
        """
        벡터 데이터베이스 통계 조회

        Returns:
            통계 정보 딕셔너리
        """
        total_count = self.collection.count()
        
        # 카테고리별 카운트 (샘플링)
        sample_results = self.collection.get(limit=1000, include=["metadatas"])
        categories = {}
        for metadata in sample_results["metadatas"]:
            cat = metadata.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_documents": total_count,
            "collection_name": self.collection_name,
            "persist_directory": str(self.persist_directory),
            "categories_sample": categories,
        }

