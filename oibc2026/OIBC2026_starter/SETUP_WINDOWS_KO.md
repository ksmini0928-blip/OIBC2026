# OIBC 2026 Windows + VS Code 환경구축 가이드

## 0. 시작하기 전에

- Python **3.11 (64비트)** 권장.
- VS Code의 **Python** 확장 설치.
- 프로젝트 경로 예시: `C:\oibc2026`. 한글/공백/OneDrive 경로를 꼭 피해야 하는 건 아니지만 문제 발생 가능성을 줄이기 위해 짧은 영문 경로 추천.
- `baseline.py` 원본은 수정 없이 첨부함.
- `scoring.py`와 문제정의서는 현재 업로드되지 않았으므로 별도로 확보하면 좋음.

## 1. 파일 준비

1. 이 ZIP의 압축을 `C:\oibc2026`에 풉니다.
2. 사용자가 전달받은 대회 원본 데이터 10개 파일을 **같은 폴더** `C:\oibc2026`에 복사합니다.
3. VS Code에서 **File > Open Folder > `C:\oibc2026`** 선택.
4. **Terminal > New Terminal** 에서 PowerShell 열기.

## 2. 가상환경 만들기 / 의존성 설치

PowerShell에서 한 줄씩 실행:

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`py -3.11 --version`에서 해당 버전이 없다고 나오면 먼저 64비트 Python 3.11을 설치하거나 설치된 버전에 맞게 `py -3.12` 등을 사용합니다. VS Code 오른쪽 아래 Python 인터프리터는 `.venv\Scripts\python.exe`로 선택합니다.

PowerShell 실행 정책 때문에 가상환경 Activate가 막혀도 위처럼 **.venv의 python.exe를 직접 실행**하면 됩니다.

## 3. 학습/평가 파일 자동 배치

```powershell
.\.venv\Scripts\python.exe prepare_data.py --source . --dry-run
.\.venv\Scripts\python.exe prepare_data.py --source .
```

별도 데이터 폴더에 원본이 있다면 `--source "C:\Data\oibc_raw"` 형태로 지정하면 됩니다.

### 최종 구조

```text
C:\oibc2026\
  baseline.py
  prepare_data.py
  verify_env.py
  requirements.txt
  README.md
  benchmark_2025.csv
  sites.csv
  smp.csv                      <- 평가 데이터 (8,760행)
  train\
    generation.parquet
    forecast_wa.parquet       <- 원본 forecast_wa(1).parquet
    forecast_wb.parquet       <- 원본 forecast_wb(1).parquet
    observed_wa.parquet
    observed_wb.parquet
    smp.csv                   <- 원본 smp(1).csv
  test\
    forecast_wa.parquet       <- 원본 forecast_wa.parquet
    forecast_wb.parquet       <- 원본 forecast_wb.parquet
```

## 4. 환경 정상인지 검증

```powershell
.\.venv\Scripts\python.exe verify_env.py
```

성공하면 `[SUCCESS] Ready to run the official baseline.`이 표시됩니다.

## 5. 첫 기본 모델 실행

**환경 검사 성공 이후에만** 실행합니다.

```powershell
.\.venv\Scripts\python.exe baseline.py --sites-out site_forecast.parquet
```

예상 산출물:
- `composition.csv`: 발전소 253개 그룹 지정 (헤더 포함 254행)
- `forecast.csv`: 두 그룹 x 평가 8,760시간 = 17,520 예측행 (헤더 포함 17,521행)
- `site_forecast.parquet`: 발전소별 예측, 그룹 재구성을 위한 중간결과

**유의:** `baseline.py` 로그에 찍히는 `train MAE`는 학습한 데이터에서 계산한 설비이용률 오차이며, 지난해 1등 팀의 MAE 44.51과 직접 비교하면 안 됩니다. 추후 시간 분할 검증, 그룹별 kWh 기반 MAE 및 공식 정산식 평가를 구현해야 합니다.

## 6. 대회 규정 주요 사항

- 총 253개 발전소를 **평가 기간 전체에서 고정된 G1/G2**로 배치.
- 그룹별 합산 설비용량은 **20,000 kW 이상**.
- 최종 예측은 전일 17시까지 알 수 있는 정보만 활용.
- 공식 정산식: `S = Σ(SMP * 실제) - 0.10 * Σ(SMP * k * |예측 - 실제|)`.
- 평가 구간의 실제 발전량은 제공되지 않으므로 기본 모델의 진짜 성능을 알려면 학습구간에서 시간 순서대로 검증 분리 필요.
