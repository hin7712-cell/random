# 랜덤프리셋 HANDOFF

일본 쇼츠용 "랜덤 순서 랭킹" 영상(1080×1920 MP4)을 만드는 Claude 전용 스킬 `random-preset`(표시명 **랜덤프리셋**)을 다른 Windows PC에 설치하고 쓰는 방법이다.
레퍼런스 채널 Polar Ranks(https://www.youtube.com/@polarranks)를 분석한 뒤 사용자 피드백 2회를 반영해 2026-11-11에 확정했다.

> **Claude에게:** 사용자가 "랜덤프리셋 HANDOFF.md 읽어줘"라고 하면 이 문서를 위에서부터 순서대로 실행한다.
> - 각 단계의 결과를 사용자에게 한국어로 보고한다.
> - 로그인, 글꼴 설치, 청취 확인처럼 사용자만 할 수 있는 일은 안내만 하고 기다린다.
> - 키, 토큰, 쿠키, .env 값은 요구하지 않는다.
> - 앱 세션 안에서 다른 `claude -p`를 중첩 실행하지 않는다. 작가와 검수는 현재 세션의 네이티브 서브에이전트로 수행한다.
> - 이미 설치된 스킬이나 기존 파일은 덮어쓰지 않는다.

## 0. 이 저장소에 들어 있는 것 / 없는 것

| 경로 | 내용 |
|---|---|
| `preset/polarranks/` | 확정 규칙(`preset.json`, `writer-prompt.txt`, `layout.json`, `sound-profile.json`, `finalization.json`, `production-binding.json`) |
| `preset/polarranks/production/` | 제작 코드: `produce_random_ranking.py`(진입점), `render_ranking.py`, `mix_user_sfx.py`, `layout_ja_v2.json`, `setup_random_preset.py` |
| `preset/polarranks/production/example/` | 확정 시험작의 대본 `story_ja.json`과 컷 노트 (영상은 없음) |
| `preset/polarranks/sound-analysis/assets/` | 효과음 2개: Myinstants VINE BOOM, FAAAH (사용 권리는 확인 안 됨) |
| `vendor/채널/` | channel-preset-builder 설치 패키지 (cpb.exe 네이티브 런타임) |

**들어 있지 않은 것:**
- 레퍼런스 채널 영상, 시험 원본 영상, 완성 MP4
- 쇼치클로 패키지
- 개인 설정과 키

## 1. 준비물 (사용자가 직접)

1. **기기:** Windows 10/11 x64, Claude 데스크톱 앱(Code 탭), 본인 Claude 로그인.
2. **Python:** Python 3.12(3.10 이상이면 됨). `py -3.12 --version`으로 확인하고, 없으면 python.org에서 설치한다.
3. **ffmpeg:** `winget install Gyan.FFmpeg`로 설치하고, 새 터미널에서 `ffmpeg -version`과 `ffprobe -version`이 되는지 확인한다.
4. **글꼴:**
   - **Pretendard:** `Pretendard-Black.ttf`가 필요하다. 반드시 "모든 사용자용으로 설치"해서 `C:\Windows\Fonts`에 들어가야 한다.
   - **Yu Gothic Bold(`YuGothB.ttc`)와 Segoe UI Emoji(`seguiemj.ttf`):** Windows에 기본으로 들어 있다.

## 2. channel-preset-builder 설치

새 대화에서 다음과 같이 요청한다(경로는 이 저장소의 실제 위치로 바꾼다).

```
<저장소>\vendor\채널 에 있는 채널 프리셋 빌더를 설치해줘. SKILL.md를 읽고 필요한 도구와 설정을 확인해줘.
기존 파일과 개인 설정은 보존하고, 내가 직접 해야 하는 로그인만 안내해줘.
```

설치가 끝나면 `%USERPROFILE%\.claude\skills\channel-preset-builder\bin\cpb.exe doctor`가 통과해야 한다.
랜덤프리셋은 음성인식을 쓰지 않으므로 `prepare-speech` 단계는 선택이다.

## 3. Python 가상환경

저장소 폴더에서 다음을 실행한다.

```bash
py -3.12 -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. 스킬 생성과 설치

먼저 점검만 한다.

```bash
.venv\Scripts\python.exe -I preset\polarranks\production\setup_random_preset.py --check
```

`problems`가 빈 목록이면 설치를 실행한다.

```bash
.venv\Scripts\python.exe -I preset\polarranks\production\setup_random_preset.py
```

이 스크립트가 하는 일:
1. `production-binding.json`을 이 PC의 경로로 다시 쓴다. 이전 파일은 `.prev.json`으로 남긴다.
2. `finalize_skill create`로 `build\random-preset`을 만든다.
3. `finalize_skill install --app claude`로 `%USERPROFILE%\.claude\skills\random-preset`에 설치한다.

같은 이름의 스킬이 이미 설치되어 있으면 멈춘다. 지울지는 사용자가 결정한다.

## 5. 첫 시험 제작 · 검수 · 완료 (Claude가 수행)

설치만으로는 `created_pending_test` 상태다. 아래를 끝내야 `completed`가 된다.

1. **원본 준비:** 사용자에게 시험할 원본 영상(로컬 MP4, 720×1280 권장)을 받는다.
   - 확정 시험작과 같은 원본을 쓰면 `example/story_ja.json`을 그대로 쓸 수 있다.
   - 같은 원본인지는 파일명 `snaptik_7671195624213056798_v3.mp4`와 sha256 `b813477462d6d385f240b8bad963f17fb69b6b11139b8285c02d55fc04376386`으로 확인한다.
   - 다른 원본이면 `writer-prompt.txt`를 따르는 네이티브 작가 서브에이전트가 원본 화면을 직접 보고 새 `story.json`을 쓴다.
2. **프로젝트 폴더:** 새 프로젝트 폴더를 만들고 `story.json`을 넣는다.
3. **제작 실행:**
   ```
   %USERPROFILE%\.claude\skills\random-preset\bin\cpb.exe finalize_skill run --skill-root <build\random-preset 절대경로> --source <원본> --project <프로젝트> --scratch <임시폴더>
   ```
4. **검수:**
   - 6개 클립마다 앞·중간·끝 프레임을 뽑아 직접 본다. 빈 띠, 잘린 얼굴·몸, 원본에 박힌 글자, 제목·목록 잘림이 없는지 확인한다.
   - 전체를 디코드하고 `blackdetect` 결과가 0인지 확인한다.
   - 사용자에게 완성 MP4를 들어 보게 하고, 들었다는 답을 받는다. Claude가 직접 듣지 못했으면 그렇게 적는다.
5. **검수 기록:** `<프로젝트>\final-review.json`을 쓴다. `run_receipt_sha256`는 `dedicated-skill-run.json`의 sha256이다.
6. **완료 판정:**
   ```
   ...cpb.exe finalize_skill complete --skill-root <build\random-preset> --receipt <프로젝트>\dedicated-skill-run.json --review <프로젝트>\final-review.json
   ```
   결과가 `"status": "completed"`이면 끝이다.

## 6. 평소 사용법

새 대화에서 다음처럼 요청한다.

```
랜덤프리셋 <원본 영상 경로 또는 URL>
```

진행 순서: 원본 확인 → 작가가 `story.json` 작성(일본어와 한국어 뜻) → `finalize_skill run` → 프레임과 소리 검수 → MP4 전달.

## 7. 확정 규칙 요약 (자세한 내용은 `writer-prompt.txt`, `preset.json`)

- **언어:** 일본어 라벨과 제목. 사용자에게는 한국어 뜻을 따로 알려 준다.
- **순서:** 카운트다운이 아니라 섞은 순서다(예: 4→3→5→6→2→1). 마지막은 반드시 2위→1위다.
- **제목:** 2줄, Yu Gothic Bold 100px, 한 줄 9자 이하. 1줄은 형용사(노랑)+ランキング, 2줄은 주제(파랑)+분류.
- **순위 목록:** 영상 왼쪽 위(x 40, y 400~800, 줄 간격 80px)에 둔다. 지금 나오는 라벨만 선명하고, 이전 라벨과 이모지는 40% 투명도, 번호는 항상 선명하다.
- **클립:** 2.3~7.8초, 하드 컷, 3:4 크롭으로 원본 글자를 제거한다.
- **vine boom:** 하위·중위 순위 0~2개의 충돌 프레임에 넣는다(0.5초, −3 dB, 채널 믹서). 1위에는 넣지 않는다.
- **FAAAH:** 모든 순위 전환 직전 0.6초에 넣는다(0 dB, 원본 −6 dB 덕킹). 채널 음원이 아니라 사용자가 확정한 규칙이다.
- **마스터:** −2 dB에 리미터 0.89.
- 규칙 위반 대본은 `produce_random_ranking.py`가 제작 전에 거부한다.

## 8. 알려진 한계

- **Windows 전용:** cpb.exe, Yu Gothic, `C:/Windows/Fonts` 경로를 쓰므로 맥에서는 동작하지 않는다.
- **MP4만 출력:** CapCut 출력은 없다.
- **소리 확인 범위:** 효과음은 원래 PC에서 사용자가 청취 확인했다(2026-11-11, "Listened, all OK"). 새 PC에서 만든 결과물도 사용자가 다시 들어 봐야 한다.
- **사용 권리:** FAAAH와 VINE BOOM 음원의 권리는 확인되지 않았다(Myinstants 공개 페이지).
- **음량:** vine boom이 클립 소리에 묻힐 수 있다. 리미터를 걸어도 0 dB를 아주 조금 넘는 부분이 남을 수 있다.
- **레퍼런스 근거:** 레퍼런스 채널 영상과 분석용 원본 근거 자료는 저장소에 없다. 규칙의 근거 기록(`preset.json`, `sound-profile.json`)만 있다.
