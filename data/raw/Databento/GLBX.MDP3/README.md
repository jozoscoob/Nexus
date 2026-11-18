# Databento GLBX.MDP3 — CBOT 대두 복합체(ZL 대두유 · ZM 대두박 · ZS 대두)

승인자 포털 다운로드(2026-11-17~18, parent 심볼 `ZL.FUT`·`ZM.FUT`·`ZS.FUT`)를 상품별로 정리한 폴더.
정리 스크립트: `scripts/build_databento_products.py`(러너 컨테이너에서 재실행 시 동일 결과).

> ⚠️ **데이터 파일은 로컬 전용**(2026-11-19 승인자 결정 B): 공개 저장소이고 CME 시장 데이터(Databento 경유)는
> 재배포 라이선스 대상이므로 정리본·정의·통계 CSV/xlsx는 커밋하지 않는다. 저장소에는 스크립트·제거 로그·질의 메타데이터만 둔다.
> 원본 포털 파일을 이 폴더에 두고 스크립트를 실행하면 아래 산출물이 재생성된다.

## 구조

| 경로 | 내용 | 저장소 |
|---|---|---|
| `OHLCV-1d/{ZL,ZM,ZS}/clean/*_ohlcv-1d_outright_*.csv`(+xlsx) | 단일 월물 일봉(UTC 일자) — 스프레드·콤보·연속 심볼·일요일 조각 제거 | 로컬 전용 |
| `OHLCV-1d/{X}/clean/*_front_by_prior_volume.csv` | 전일 거래량 1~3위 월물·롤 플래그·동일 월물 수익률(사후 정보 없음) | 로컬 전용 |
| `OHLCV-1d/{X}/clean/removal_log.md` | 제거한 열·심볼 유형별 사유와 행 수 | 커밋 |
| `Definitions/{X}/*_definitions_outright.csv` | 월물별 정의 1행(만기·활성일·호가단위·승수) | 로컬 전용 |
| `Statistics/{X}/*_statistics_daily_outright.csv` | 거래일×월물 **CME 공식 정산가**·미결제약정·청산 거래량(+원천 stat_flags) | 로컬 전용 |
| `OHLCV-1d/ZL/ZL_ohlcv-1d_2010-06-06_2026-08-12.csv` | 구 `ZL.c.0` 연속 계열(세션 종가 검증기 입력 — 2026-08부터 이미 공개 저장소에 존재) | 커밋(이동) |
| 원본 포털 파일(xlsx·csv·일별 `.csv.zst` 배치 폴더 `GLBX-*`·`manifest.json`) | 원시 다운로드 | 로컬 전용(.gitignore) |

## 판독 규칙

- **정산가 정본은 Statistics(stat_type 3)**. OHLCV 일봉 종가는 UTC 일자 마지막 체결가로 정산가와 다르다.
- Yahoo `ZL=F` 종가 = **최근월(만기 최근접) 월물의 CME 공식 정산가**와 2010~2026 전 구간 일치(4,125일 100%) —
  인도월 저유동성 구간을 포함하는 달력 롤 계열이다.
- 연속 계열이 필요하면 `front_by_prior_volume`(거래량 1위, 전일 기준)을 쓰고, 수익률은 같은 월물끼리만 계산한다(롤일 결측).
- 착유 마진(Board Crush)은 상품별 1위 월물을 섞지 말고 인도월을 맞춘 조합(예: ZSX6 · ZMZ6 · ZLZ6)으로 계산한다.
- 정산가 `settlement_flags` bit0=최종(final). 같은 거래일·월물은 최종 정산 우선, 그다음 최신 레코드를 채택했다.
- `*_date_from_ts_event=True` 행은 원천 `ts_ref`(거래일)가 비어 수신 일자로 대체한 값 — 초기 연도 미결제약정에 집중.
