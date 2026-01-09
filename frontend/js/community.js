// Mock Data for Popular Builds
const POPULAR_BUILDS = [
    { id: 1, title: "200만원대 게이밍 끝판왕", author: "GameMaster", cpu: "Ryzen 7 7800X3D", gpu: "RTX 4070 Ti", price: "2,350,000" },
    { id: 2, title: "입문용 가성비 롤/피파", author: "NewbieHelper", cpu: "Core i5-12400F", gpu: "RTX 3060", price: "850,000" },
    { id: 3, title: "화이트 감성 데스크테리어", author: "WhiteLover", cpu: "Ryzen 5 7600", gpu: "RTX 4060 White", price: "1,100,000" },
    { id: 4, title: "최고사양 작업용 워크스테이션", author: "ProEditor", cpu: "Core i9-14900K", gpu: "RTX 4090", price: "5,200,000" },
    { id: 5, title: "검은 신화 오공 풀옵션", author: "MonkeyKing", cpu: "Ryzen 7 7800X3D", gpu: "RTX 4080 Super", price: "3,100,000" },
    { id: 6, title: "대학생 과제/롤 겸용", author: "Student", cpu: "Ryzen 5 5600", gpu: "RX 6600", price: "700,000" },
    { id: 7, title: "디자이너를 위한 맥 스타일", author: "Artist", cpu: "Core i7-13700", gpu: "RTX 4060 Ti", price: "1,500,000" },
    { id: 8, title: "배틀그라운드 국민옵션", author: "PUBGPlayer", cpu: "Core i5-13400F", gpu: "RTX 4060", price: "1,050,000" },
    { id: 9, title: "스트리밍 송출용 서브", author: "Streamer", cpu: "Ryzen 7 5700X", gpu: "GTX 1660 Super", price: "600,000" },
    { id: 10, title: "사이버펑크 2077 레이트레이싱", author: "NightCity", cpu: "Core i7-14700K", gpu: "RTX 4080", price: "3,500,000" },
    { id: 11, title: "미니 ITX 귀여운 PC", author: "SmallSize", cpu: "Ryzen 5 7600", gpu: "RTX 4060 LP", price: "1,200,000" },
    { id: 12, title: "영상편집 입문 견적", author: "EditorBeginner", cpu: "Core i5-13500", gpu: "RTX 3060 12GB", price: "1,150,000" },
    { id: 13, title: "개발자용 리눅스 머신", author: "DevOps", cpu: "Ryzen 9 7900", gpu: "iGPU", price: "900,000" },
    { id: 14, title: "로스트아크 QHD 풀옵", author: "MokoKo", cpu: "Core i5-13600K", gpu: "RTX 4070", price: "1,800,000" },
    { id: 15, title: "300만원 화이트 풀세트", author: "RichBoy", cpu: "Ryzen 7 7800X3D", gpu: "RTX 4070 Ti Super", price: "2,950,000" },
];

export function showPopularBuilds() {
    // 간단한 모달이나 alert로 띄우거나, DOM 요소를 생성해서 보여줌
    // 여기서는 화면 중앙에 오버레이 리스트를 띄우는 방식으로 구현

    // 기존 오버레이가 있다면 제거
    const existingOverlay = document.getElementById('community-overlay');
    if (existingOverlay) existingOverlay.remove();

    const overlay = document.createElement('div');
    overlay.id = 'community-overlay';
    Object.assign(overlay.style, {
        position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
        backgroundColor: 'rgba(0,0,0,0.8)', zIndex: 9999,
        display: 'flex', justifyContent: 'center', alignItems: 'center'
    });

    const container = document.createElement('div');
    Object.assign(container.style, {
        width: '600px', maxHeight: '80vh', backgroundColor: '#1a1a1a',
        borderRadius: '12px', padding: '20px', overflowY: 'auto',
        border: '1px solid #333', color: '#fff', boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
    });

    const header = document.createElement('div');
    header.innerHTML = '<h2 style="margin:0 0 20px 0; font-size: 24px;">🔥 인기 AI 추천 빌드</h2>';

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '닫기';
    Object.assign(closeBtn.style, {
        float: 'right', background: 'transparent', border: 'none', color: '#888',
        cursor: 'pointer', fontSize: '16px'
    });
    closeBtn.onclick = () => overlay.remove();
    header.insertBefore(closeBtn, header.firstChild);

    const list = document.createElement('ul');
    list.style.listStyle = 'none';
    list.style.padding = 0;

    POPULAR_BUILDS.forEach(build => {
        const item = document.createElement('li');
        Object.assign(item.style, {
            padding: '15px', borderBottom: '1px solid #333', display: 'flex',
            justifyContent: 'space-between', alignItems: 'center', gap: '10px'
        });

        item.innerHTML = `
            <div>
                <div style="font-weight:bold; font-size:16px;">${build.title}</div>
                <div style="font-size:12px; color:#888;">by ${build.author} | ${build.cpu} + ${build.gpu}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#00e676; font-weight:bold;">₩${build.price}</div>
                <button class="view-btn" style="background:#333; color:#fff; border:none; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer; margin-top:4px;">상세보기</button>
            </div>
        `;
        list.appendChild(item);
    });

    // 이벤트 위임으로 상세보기 클릭 처리 (Mock)
    list.addEventListener('click', (e) => {
        if (e.target.classList.contains('view-btn')) {
            alert('이 빌드의 상세 내용을 불러옵니다... (Mock Data)');
        }
    });

    container.appendChild(header);
    container.appendChild(list);
    overlay.appendChild(container);
    document.body.appendChild(overlay);
}

export function saveCurrentBuild(parts) {
    if (!parts || parts.length === 0) {
        alert("저장할 부품이 없습니다. 먼저 견적을 완성해주세요.");
        return;
    }
    // TODO: 실제로는 DB에 저장해야 함
    console.log("Saving build:", parts);

    // 성공 시뮬레이션
    setTimeout(() => {
        alert("✅ 내 견적이 성공적으로 저장되었습니다!\n(나중에 '내 보관함'에서 확인할 수 있습니다 - Mock)");
    }, 500);
}

export function shareCurrentBuild() {
    // 공유 링크 복사 시뮬레이션
    const mockLink = `https://spckit.xyz/share/build-${Math.floor(Math.random() * 10000)}`;

    navigator.clipboard.writeText(mockLink).then(() => {
        alert(`🔗 공유 링크가 복사되었습니다!\n${mockLink}`);
    }).catch(() => {
        alert(`🔗 공유 링크: ${mockLink}`);
    });
}
