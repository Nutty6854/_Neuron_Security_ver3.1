# _Neuron_Security_ver3.1 — 신경 신호 열화 감지 (단일 주제)

이 폴더는 한 주제만 다룬다.

> 신경 신호가 서서히 망가지는 상황(진폭 감소·잡음 증가·뉴런 소실·기준선 드리프트)을, 생물 뉴런 모델 + ANN이 작고 가벼운 구조로 감지할 수 있는가?

- 설계와 판정 기준: [coordination/GrokBot_다음주제_신호열화감지_정리_20261109_1745.md](coordination/GrokBot_다음주제_신호열화감지_정리_20261109_1745.md). 문서 끝 '변경 기록'이 본문보다 우선한다.
- 상태: 제안(DRAFT). 숫자(열화 강도, 창 길이, 기록 수, seed)는 아직 고정 전이다. 실행은 하루 승인 후에만 한다.
- 판정은 성공 또는 실패만 쓴다.

## 구성

- `coordination/`: 설계 문서와 에이전트 기록
- `reference/izhikevich.py`: ver3 `claude_izhikevich/claude_izhikevich_encoder_types/izhikevich.py`의 복사본(표준 라이브러리만 사용)
- `reference/encoder_types_config.json`: 같은 폴더의 설정 복사본(RS·LTS·FS·TC 파라미터 포함)

## 원본과의 관계

- ver3(`../_Neuron_Security_ver3/`)는 수정하지 않는다. 필요한 파일은 복사해서 쓴다.
- ver3의 지난 결과(ECG 1·2차, 45 nm 에너지 비교)는 반복하지 않는다.
