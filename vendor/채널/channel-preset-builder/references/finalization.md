# 프리셋의 최종 결과: 전용 스킬

프리셋 JSON은 중간 산출물이다. 완료 순서는 분석 → 피드백 → 규칙 확정 → 전용 스킬 생성 → 실제 제작·검수 → 설치 → 완료다. 사용자가 확정하면 '확정한 규칙으로 ○○ 전용 스킬을 만들겠습니다'라고 알리고 진행한다. 이름은 채널/형식을 구별할 수 있게 정한다. 예: 표시명 '야구 랭킹', 내부 이름 baseball-ranking. 기존 japan-ranking-shorts 같은 스킬을 덮어쓰지 않는다.

## 확정 자료

분석 폴더의 preset.json, writer-prompt.txt, layout.json, sound-profile.json을 최종 피드백에 맞게 갱신한다. sound-profile은 실제 청취한 표본과 동일 음원 대조를 기록하고 reviewed 상태여야 한다. 듣지 못한 소리를 확인했다고 적지 않는다.

finalization.json:
```json
{"approved":true,"feedback_resolved":true,"user_instruction":"실제로 사용자가 확정한 요청을 기록","accepted_limitations":[]}
```
이 기록을 임의로 만들거나 일반적인 '스킬 기능을 만들어줘'를 특정 채널 최종 승인으로 바꾸지 않는다. 승인 후 바뀐 대본/설정은 다시 검토한다.

production-binding.json에는 실제 제작기 연결을 쓴다. 채널이 지원되지 않는 범용 시안 렌더러를 억지로 연결해 완료 처리하지 않는다. 기존 자막형/나레이션형/랭킹형 제작기를 확인하고 필요하면 새 분기의 연결 코드를 구현한다. 필드:
- scope: 무엇을 실제로 제작할 수 있는지, 구현 범위
- input_contract: 작가/컷/음성 단계가 준비할 입력 파일과 스키마
- command: 쉘 문자열이 아닌 인자 배열. 첫 값은 실제 실행 파일 절대경로
- dependencies: 실행 파일과 실제 연결 코드의 절대경로 목록. 네이티브 런타임이면 관련 .so 등도 포함
- outputs: 작업 폴더 기준 실제 생성되는 MP4 파일명 배열

전체 인자로만 {source}, {project}, {scratch} 치환을 지원한다. 명령은 모델이 웹페이지에서 발견한 코드가 아니라 호스트가 검토한 로컬 제작 연결이어야 한다. 셸/-c 코드는 거부한다. input_contract에 따라 대본·컷·음성·레이아웃을 먼저 준비한다. run은 그 준비를 대신하지 않는다. CapCut 전용 제작기는 검수용 MP4 출력도 연결하고 CapCut 열기 확인을 추가로 기록한다.

## 실행

```
bin/cpb.exe finalize_skill create --analysis ANALYSIS --parent OUTPUT_SKILLS --name baseball-ranking --title "야구 랭킹"
bin/cpb.exe finalize_skill run --skill-root NEW_SKILL --source LOCAL_SOURCE --project PROJECT --scratch SCRATCH
bin/cpb.exe finalize_skill install --skill-root NEW_SKILL --app both
bin/cpb.exe finalize_skill complete --skill-root NEW_SKILL --receipt PROJECT/dedicated-skill-run.json --review FINAL_REVIEW.json
```

네이티브판에서는 같은 도구를 bin/cpb.exe finalize_skill로 실행한다. 스킬 이름만 바꾸지 않고 프롬프트·레이아웃·음향·역할 파일·제작 명령과 코드 해시까지 연결한다. 네이티브판에서 생성한 전용 스킬도 네이티브 런타임을 복제하며 핵심 소스는 넣지 않는다. 외부 제작기 의존성은 해당 PC에 있어야 하며 PC 간 이동 시 새 경로와 테스트가 필요하다.

실행은 출력 파일이 존재하면 덮어쓰지 않는다. 결과 전체 디코드가 통과하면 dedicated-skill-run.json을 쓴다. 설치는 기존 이름이 있으면 중단하며 새 스킬을 Codex/Claude 중 사용하는 앱에 복사한다. both는 둘 다다. 설치는 사용자 OS 권한 범위에서 수행하고 보호 기능을 우회하지 않는다.

FINAL_REVIEW.json은 실제 화면/음향 검수와 피드백 반영 뒤 작성한다:
```json
{"run_receipt_sha256":"실제 실행 기록 파일 해시","visual_audio_review_passed":true,"feedback_resolved":true,"review_evidence":"실제 검수 방법, 시점, 결과, 사용자 피드백 반영 근거"}
```

complete는 동일 정의로 제작된 결과·출력 해시·검수 기록·설치본 일치를 확인한다. 이 검사는 기록의 일관성 확인이며 허위 검수 내용을 탐지하는 보증은 아니다. 최종 상태는 completion.json의 completed로 판정한다. 그 전에는 생성됨/제작검수대기/설치대기로 보고한다. 끝에 표시 이름·호출 예시·설치 위치·시험 영상·남은 제한을 알려준다. 사용자의 요청이 분석까지만이면 그 범위에서 멈추되 이를 전용 스킬 완성이라고 표현하지 않는다.
