/**
 * 빌드 스크립트
 * frontend의 파일들을 dist 폴더로 복사한다
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const sourceDir = path.join(__dirname, '..', 'frontend');
const distDir = path.join(__dirname, '..', 'dist');

/**
 * 디렉토리 재귀 복사
 */
function copyDirectory(src, dest) {
  // 대상 디렉토리 생성
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  // 소스 디렉토리의 모든 항목 읽기
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    // 제외할 파일/폴더
    if (entry.name === 'node_modules' || entry.name === '.git' || 
        entry.name.endsWith('.md') || entry.name.startsWith('.')) {
      continue;
    }

    if (entry.isDirectory()) {
      // 디렉토리면 재귀 복사
      copyDirectory(srcPath, destPath);
    } else {
      // 파일이면 복사
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

/**
 * 빌드 실행
 */
function build() {
  console.log('🚀 빌드 시작...');

  // dist 폴더가 있으면 삭제
  if (fs.existsSync(distDir)) {
    console.log('📦 기존 dist 폴더 삭제 중...');
    fs.rmSync(distDir, { recursive: true, force: true });
  }

  // frontend 폴더를 dist로 복사
  console.log('📁 파일 복사 중...');
  copyDirectory(sourceDir, distDir);

  console.log('✅ 빌드 완료!');
  console.log(`📂 결과물: ${distDir}`);
}

// 빌드 실행
build();

