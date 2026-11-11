# Myinstants 효과음 선택과 적용

채널 프리셋을 만들 때 레퍼런스 영상의 실제 오디오를 먼저 조사한다. 영상 제작 시에는 그 채널의 sound-profile.json에 등록된 효과음만 사용한다. 모든 채널에 동일한 효과음을 배정하지 않는다. channel_pipeline.py 단독 실행에는 이 판단 단계가 없다. 스킬의 제작 단계에서 수행한다.

1. 레퍼런스에서 효과음의 역할과 밀도를 먼저 확인한다. 반전 강조, 실패 반응, 전환, 정적 해소 등을 구분한다. 청취하지 못했으면 미확인으로 적고 신규 편집 제안과 구분한다.
2. 확정 타임라인에서 넣을 장면과 목적을 먼저 정한다. 매 컷에 기계적으로 넣지 않는다. 횟수·길이·음량·삽입 위치는 해당 채널에서 관찰한 값을 따른다. 관찰하지 못하면 unknown으로 두고 공통 기본값으로 채우지 않는다.
3. 레퍼런스에서 들은 소리의 특징·이름·언어로 동일 음원 후보를 먼저 찾는다. 장면의 역할만 보고 새로운 음원을 고르지 않는다. 예: 짧은 반전=dun dun / dramatic boom, 실패=fail / sad trombone, 전환=whoosh. 예시는 고정 선택 목록이 아니다. 한국 트렌드 페이지를 일본 채널의 인기 효과음 근거로 쓰지 않는다.
4. 아래 search 도구로 1페이지 최대10개를 수집하고 후보 2–3개를 비교한다. 이름만으로 실제 소리를 판정하지 않는다. 청취 가능한 도구가 없으면 상태를 not_listened로 유지하고 미리듣기와 믹스 시안을 사용자에게 제공한다. Jev는 이미 관찰한 텍스트 후보 분류에만 선택적으로 사용하며 소리를 들었다고 대신 판단하지 않는다.
5. 선택한 후보를 fetch로 받는다. 이름/원본 페이지/MP3 주소/해시/길이/권리 확인/청취 상태를 보관한다. 다운로드 가능 여부는 상업 이용 허가 증명이 아니다. 확인되지 않은 권리는 unknown으로 유지한다. 수강생 배포 ZIP에 음원 파일은 넣지 않는다.
6. 최종 렌더의 시간 기준으로 sfx-plan.json을 만들고 mix한다. 문장과 중요한 원음이 묻히지 않게 짧고 낮게 시작한다. 음량값은 출발점이며 실제 믹스를 들어 조정한다. 영상 구간 변경 뒤에는 시간표도 갱신한다.
7. 출처와 적용 시점을 보고서에 남긴다. CapCut은 기존 조립기의 별도 오디오 트랙으로 연결해야 하며 이 도구는 MP4 믹스만 한다.

## 실행 (호스트 에이전트용)

스킬 폴더 기준 절대경로로 실행한다. 학생에게 터미널 명령을 직접 입력하게 하는 것이 기본 UX가 아니다.

```
bin/cpb.exe myinstants_sfx search "SEARCH TERMS" --output WORK/search
bin/cpb.exe myinstants_sfx fetch WORK/search/RESULT.json --index 0 --output WORK/assets
bin/cpb.exe myinstants_sfx mix --video PREVIEW.mp4 --plan WORK/sfx-plan.json --output PREVIEW-sfx.mp4
```

## 채널별 오디오 근거

분석 파이프라인은 sound-profile.json을 pending_audio_review 상태로 만든다. ASR이나 화면을 봤다는 이유만으로 완료 처리하지 않는다. 실제 오디오를 들을 수 있는 환경에서 각 표본을 검토하고 다음을 기록한다.
- reviewed_video_ids: 실제 검토한 표본 ID
- observations: id, video_id, start/end(초), role, listening_evidence(검토자·원본 파일 해시·청취 방법·소리 특징)
- assets: id, observation_ids, match_status(exact_verified/probable/similar/unidentified), comparison_evidence(원본 구간과 후보 음원의 실제 대조 근거), sha256
- usage_rules: 해당 채널의 빈도·길이·대사 대비 음량·반복·삽입 시점

확인된 동일 음원만 기본 적용한다. 유사 후보나 미확인 음원은 자동 대체하지 않는다. 사용자가 대체를 명시적으로 요청한 경우에만 asset.substitution_approval에 그 요청을 기록한다. 청취 불가면 미확인으로 보고한다. 효과음이 없는 채널은 실제 청취 범위와 무효과음 관찰을 남긴다. 모델의 자기 보고나 해시 존재만으로 정확한 식별을 보증하지 않는다.

큐 파일과 sound-profile.json 및 assets/는 같은 프로젝트 폴더 안에 둔다. 각 cue는 profile_asset_id와 asset_sha256을 포함한다. 다른 채널의 프로필과 연결하면 믹서가 거부한다.

sfx-plan.json 예시:
```json
{"channel_url":"CHANNEL_URL","sound_profile":"sound-profile.json","events":[{"profile_asset_id":"VERIFIED_CHANNEL_ASSET_ID","asset_sha256":"MATCHING_ASSET_SHA256","asset_manifest":"assets/DOWNLOAD.json","start":15.5,"trim_start":0,"duration":0.8,"gain_db":-12,"reason":"반복의 규칙을 깨닫는 자막의 첫 박자 강조"}]}
```

실제 manifest 경로와 음원 길이에 맞춘다. 예시 파일명을 그대로 쓰지 않는다. 출력은 원본과 다른 파일이다. 입력에 오디오 트랙이 있어야 한다. 1–12개 큐, 개당 최대10초, 최대60초/10MiB 음원만 지원한다. 원본은 보존한다.

공식 API는 익명 사용자 분당10회 제한을 안내한다. 검색은 순차 실행하고 캐시를 재사용한다. 다운로드/다른 프로그램 호출도 고려해 요청량을 늘리지 않는다. 403/429나 인증 요구 시 중단하고 자동 반복/프록시 우회를 하지 않는다. 도구는 OS 프록시도 사용하지 않는다.

출처: https://www.myinstants.com/api/v1/
