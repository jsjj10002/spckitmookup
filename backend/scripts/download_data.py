import os
import sys
import shutil
import zipfile
from pathlib import Path
from google.cloud import storage
from loguru import logger

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    logger.info(f"Downloaded storage object {source_blob_name} from bucket {bucket_name} to {destination_file_name}.")

def main():
    # 환경 변수 확인
    use_gcs = os.getenv("USE_GCS_DATA", "false").lower() == "true"
    if not use_gcs:
        logger.info("Skipping GCS download (USE_GCS_DATA is not true)")
        return

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME environment variable is not set")
        sys.exit(1)

    zip_filename = "chroma_db.zip"
    download_path = Path("/tmp") / zip_filename
    extract_path = Path("/tmp/chroma_db")
    
    # 다운로드 디렉토리 생성
    download_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Starting download from GCS bucket: {bucket_name}")
        download_blob(bucket_name, zip_filename, str(download_path))
        
        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {download_path} to {extract_path}")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        logger.success("Data download and extraction complete.")
        
        # 압축 파일 삭제 (공간 절약)
        download_path.unlink()
        
    except Exception as e:
        logger.error(f"Failed to download or extract data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 로깅 설정
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    main()
