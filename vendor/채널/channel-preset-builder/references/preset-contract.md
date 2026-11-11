# 프리셋 → 기존 제작기 계약 v0.1

이 문서는 연결 계약이다. 현재 사용자 프로젝트가 자막형/나레이션형으로 개편 중이므로 실제 엔진의 진입점과 지원 기능을 확인한 후 어댑터를 구현한다. JSON만 만들고 완성영상 생성이 연결됐다고 보고하지 않는다.

## 프리셋 필수 영역

- identity: schema_version, preset_id, reference_channel, output_language, production_mode(subtitle/narration), sample_scope, evidence_revision.
- evidence: 영상별 수집시점/해시/관찰표, 모든 규칙의 observed/inferred/proposed/unknown 근거와 표본수.
- material_policy: 채택/제외 조건, 소스 검색어/탐색 순서, 원본 검증, 맥락/사용허용 근거, 중복 확인.
- story_transformation: 원본 맥락→새 설정 변환, 역할/목표/걸림돌, 정보 공개 순서, 줄별 궁금증 변화, 회수 관계, retained/reordered/emphasized/interpreted/fictionalized/unresolved 구분.
- narrative_recipes: 입력 장면 조건, 설정 발상법, 전개, 문장역할, 장면배치, 회수, 적용 제외, 지지/반례. [이야기 변환 분석](story-transformation.md) 참조.
- narrative: 사건/감정 전개, 훅 약속·보상, 정보 공개 순서, 문장역할, 길이 분포, 어미/어휘, 금지 추론, 엔딩, 반례.
- titles: upload_title, on_screen_title, thumbnail_text 각각의 규칙; 없는 층은 null.
- writing: 승인된 script/title/meme 프롬프트 경로·해시, 언어, 조건별 분량.
- edit: 줄/사건별 source 구간과 output timeline, crop/speed/transition, 자막과 컷의 관계.
- audio: original/narration/music/sfx의 파일 또는 해결 대기 항목, 권한, 타임라인, gain/duck/fade. 원본 음원 미확인은 임의 곡명으로 채우지 않는다.
- layout: base_template 해시, 추가 층 layout.json 경로, 좌표 기준·변환, 각 엔진 지원 여부. 기존 층 수정 금지.
- runtime: requested_model/actual_model, dispatch/response/receipt 해시, 비용, 캐시, Gemini 호출 제거 검사.
- validation: 기준별 tolerances, 실제 측정, 불일치, 제작 승인과 최초 CapCut 열기 상태.

## 제작 입력/출력

입력: 승인된 프리셋, 새 원본 목록(파일·해시·길이·출처), 승인된 script/title, line_to_source_map, layout.json, audio_plan.json, output_type(capcut/mp4/both).

어댑터는 지원 불가능한 필드, 없는 음원/글꼴, 누락된 원본구간, 시간 범위 오류, 요청표 없는 에이전트 답을 먼저 거부한다. 기존 렌더러가 style.json을 읽지 않는다면 연결 코드를 구현하기 전까지 해당 설정은 지원 안 됨으로 보고한다.

출력: CapCut 프로젝트 또는 MP4, manifest, 실제 timeline, dependency hashes, QA report. 컷눈이 정한 source 구간을 렌더러가 실제로 사용했는지 출력 timeline을 대조한다.

## 에이전트 응답

`evidence_gate.py` 응답 JSON 필드:

```json
{
  "task_id": "발행된 요청 ID",
  "actual_model": "실제로 실행된 모델 ID",
  "opened_evidence_hashes": ["요청표의 모든 파일 해시"],
  "findings": [{
    "basis": "observed",
    "claim": "타임코드와 화면 위치를 포함한 관찰",
    "evidence_hashes": ["해당 근거 해시"]
  }]
}
```

요청표를 발행한 뒤 실제 런타임에 전달하고 답을 기다린다. receipt는 형식/출처 확인까지만 뜻하며 승인이나 내용 정확성을 보증하지 않는다. 다른 에이전트가 같은 원본을 보고 주장을 검증한다. 응답 수락 후에도 제작 직전에 해시를 재검증한다.

## 출하 검수

1. 실제 사실·해석·창작 설정의 구분이 맞는지, 원본 요약으로 퇴행하지 않았는지, 줄마다 전개가 진전되는지, 훅과 마지막 회수가 이어지는지 검수. 실제 대사 번역으로 표기한 부분은 원음을 별도 대조.
2. 완성영상 전체를 듣고 본다. 검수 도구가 화면/소리를 재생하지 못하면 해당 검수를 미완료로 남긴다.
3. 레퍼런스와 결과의 대응 사건(도입/전환/끝) 3장을 나란히 비교. 같은 재생초를 억지로 맞추지 않고 각각 타임코드 표시.
4. 글자수, 컷 간격, 자막 읽기시간, 위치 px, 원본-완성 구간, 음향 시작점 차이를 수치로 보고. 다른 소재에서 일부 차이는 의도한 편집인지 설명.
5. 자막 잘림/빈 프레임/음성 끊김/없는 미디어·글꼴, 추가 트랙 존재, 원본 템플릿 불변 해시 검사.
6. Gemini 실제 호출 0건 검사와 실제 에이전트 사용 내역. 정적 검색과 실행 결과를 구분.
7. 첫 CapCut 프로젝트는 사용자 열기 확인 대기. 이 단계 전에는 검수 완료로 표시하지 않는다.

## 최종 완료

이 계약의 분석 JSON은 analysis_draft 단계다. [전용 스킬 마무리](finalization.md)에 따라 이름 있는 스킬로 규칙·제작 코드 연결·역할을 묶고, 한 편 제작과 실제 화면/음향 검수 및 설치가 끝나야 completed다. 사용자가 확정한 뒤에는 분석 결과 설명만 하고 종료하지 않는다.
