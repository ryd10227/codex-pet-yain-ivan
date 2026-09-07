# 야인이반 (Yain Ivan)

뮤지컬 《브라더스 까라마조프》의 이반에서 영감을 받아 만든 비공식 Codex 데스크톱용 픽셀 모에 펫입니다.

- 검은 롱코트, 회색 체크 조끼, 와인색 넥타이와 둥근 안경
- 냉소적이고 반항적인 표정, 단정하고 정적인 태도
- 책을 읽는 idle, 고정 자세의 필기 running, 16방향 시선 반응을 포함한 v2 스프라이트
- 8열 × 11행, 1536 × 2288 WebP

## 상황별 애니메이션

| 상태 | 미리보기 | 상태 | 미리보기 |
| --- | --- | --- | --- |
| 독서 중 (`idle`) | ![책을 읽는 idle 애니메이션](preview-idle.gif) | 작업 중 (`running`) | ![책상에서 글을 쓰는 running 애니메이션](preview-running.gif) |
| 오른쪽 이동 (`running-right`) | ![오른쪽으로 이동하는 애니메이션](preview-running-right.gif) | 왼쪽 이동 (`running-left`) | ![왼쪽으로 이동하는 애니메이션](preview-running-left.gif) |
| 인사 (`waving`) | ![손을 들어 인사하는 애니메이션](preview-waving.gif) | 대기 (`waiting`) | ![대기하는 애니메이션](preview-waiting.gif) |
| 점프 (`jumping`) | ![팔을 올리며 정면을 노려보는 jumping 애니메이션](preview-jumping.gif) | 실패 (`failed`) | ![실패 상태 애니메이션](preview-failed.gif) |
| 검토 (`review`) | ![검토 중인 애니메이션](preview-review.gif) | 시선 반응 (`look`) | ![16방향 시선 반응 애니메이션](preview-look.gif) |

## 설치

저장소를 내려받거나 압축 파일을 푼 뒤, 아래 방법 중 하나를 사용하세요.

### Windows

PowerShell에서 저장소 폴더로 이동한 다음 실행합니다.

```powershell
.\install.ps1
```

### macOS / Linux

터미널에서 저장소 폴더로 이동한 다음 실행합니다.

```bash
chmod +x install.sh
./install.sh
```

수동 설치를 원하면 `pet.json`과 `spritesheet.webp`를 함께 아래 폴더에 복사하면 됩니다.

```text
~/.codex/pets/yain-ivan/
```

설치 후 Codex 데스크톱 앱의 펫 선택 화면을 새로고침하고 **야인이반**을 선택하세요. 이미 앱이 열려 있었다면 재시작이 필요할 수 있습니다.

## 파일

- `pet.json` — Codex 펫 메타데이터
- `spritesheet.webp` — 실제 v2 애니메이션 스프라이트
- `preview-*.gif` — 상황별 애니메이션 미리보기
- `contact-sheet.png` — 전체 상태 확인용 시트
- `validation.json` — v2 구조 검증 결과
- `SHA256SUMS.txt` — 배포 파일 무결성 확인값
- `scripts/` — jumping 얼굴 보정 및 미리보기 재생성 스크립트

## 안내

이 저장소는 개인적·비상업적 팬 작업입니다. 배우 임강성, 공연 제작사, 원작 및 관련 권리자, OpenAI와 공식적인 관련이나 후원 관계가 없습니다. 원본 배우 사진은 저장소에 포함하지 않았습니다.

사용 조건은 [LICENSE.md](LICENSE.md), 권리 관련 안내는 [NOTICE.md](NOTICE.md)를 확인해 주세요.

---

## English

Yain Ivan is an unofficial pixel-moe pet for the Codex desktop app, inspired by Ivan from the musical *The Brothers Karamazov*.

To install, run `install.ps1` on Windows or `install.sh` on macOS/Linux. You may also copy `pet.json` and `spritesheet.webp` together into `~/.codex/pets/yain-ivan/`, refresh the pet picker, and select **야인이반**.

The table above previews every animation state, including movement, jumping, waiting, failure, review, and the 16-direction look response.

This is a personal, non-commercial fan work. It is not affiliated with or endorsed by actor Lim Kang-sung, the musical production, the original work or its rightsholders, or OpenAI. No source photographs are included.
