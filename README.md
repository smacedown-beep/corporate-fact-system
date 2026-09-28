# Corporate Investment FACT & Provenance System (Next Generation)

> **"이 숫자가 왜 맞다고 믿어야 하는가?"** — 모든 투자 수치에 대한 사법적(Forensic) 원천 역추적 및 불변 증거 시스템

## 1. 개요
본 시스템은 하남전기㈜ / 뉴모텍㈜ 등의 기업 유휴자금 투자(1~2년 Horizon)를 위해 구축된 엄격한 FACT 기반 데이터 인프라입니다. AI의 주관적 추정이나 가공된 2차 뉴스를 배제하고, 공식 원천(Level 1~4)에서 수집된 불변 증거(Immutable Evidence)만을 기반으로 독립 검증된 공인 FACT를 산출합니다.

## 2. 핵심 원칙
1. **FACT FIRST**: 뉴스, 리서치, AI 해석(Level 5~7)은 FACT 원천으로 사용 불가.
2. **AI PASS를 맹신하지 않음**: 문자열 "PASS"가 아닌 실체적 암호화 증거(SHA-256, XML 태그 좌표) 검증.
3. **Multi-Attribute Identity 교차검증**: 접수번호 단독 신뢰 금지 (`rcept_no` + `corp_code` + `stock_code` + `company_name` + `report_name` + `period`).
4. **Append-Only Immutability**: 원천 관측치(`raw_observation`), 수집 로그, 감사 로그에 대한 `UPDATE`/`DELETE` 원천 금지 (DB 트리거 및 코드 가드).
5. **Point-in-Time (PIT) 준수**: 공표 시점(`availability_date`)이 투자 판단일(`decision_date`)보다 미래인 데이터는 `LOOKAHEAD_BIAS`로 전면 차단.
6. **Hard Migration Stop**: 8대 선행 조건(오염 검토, reconciliation, 테스트 통과, 인간 승인) 충족 전까지 마이그레이션 및 자동 덮어쓰기 금지.

## 3. 실행 방법
```bash
# 감사 대시보드 렌더링
python -m corporate_invest_system_next.src.cli.main report

# 현대자동차(HMC) 종합 포렌식 감사 보고서 렌더링
python -m corporate_invest_system_next.src.cli.main report --type hmc

# 전체 테스트 슈트 실행 (52종 테스트 전건 검증)
python corporate_invest_system_next/tests/run_all_tests.py
```
