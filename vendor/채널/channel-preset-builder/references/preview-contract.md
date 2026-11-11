# MP4 시안 계약

이 렌더러는 중앙 영상 띠와 상단 자막이 있는 시안용이다. CapCut 어댑터가 아니고 모든 채널 화면을 지원하지 않는다. 현재 macOS Hiragino 글꼴과 Pillow, ffmpeg/ffprobe가 필요하다.

- story.json: segments 배열. 각 줄 narration_ja, caption_ja, meaning_ko, story_function, source_start/end(초), emphasis(불리언). 대본은 실제 작가 요청·응답 근거를 통과해야 한다.
- layout.json: reference_background_rgb [R,G,B], reference_video_y_range_normalized1080 [y0,y1], source_crop [x,y,w,h], source_credit, voice_credit. 실제 측정과 시안 선택을 구분해서 기록한다.
- voice/00.mp3부터 줄 순서대로 음성. 외부 기존 TTS 부품으로 생성하며 텍스트와 해시를 함께 보관한다.
- 원본 소리를 끄고 저음량 자체 리듬과 전환음을 더한다. 레퍼런스 음악 재현으로 보고하지 않는다.
- 속도는 음성 길이에 맞추되 0.65~1.5 범위를 벗어나면 멈춘다. 이를 억지로 늘리지 말고 작가/컷 검토로 돌아간다.
- 배경·영상 위치는 JSON을 읽는다. 글꼴·스타일은 이 제한된 시안 렌더러의 기본값이며 정식 포맷의 보존을 보증하지 않는다.

출력 preview.mp4, timeline.json을 직접 디코드 검증하고 장면표를 별도 검수자에게 제공한다. 채널 소재와 시험 원본이 맞지 않으면 각색 시안이라는 사실을 눈에 띄게 보고한다.
