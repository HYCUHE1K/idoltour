# idoltour
아이돌성지순례

## 영화 정보 에이전트
Scrapy 기반의 CLI 에이전트가 추가되어, 영화 제목을 입력하면 웹에서 관련 정보를 수집하고 정확도 점수가 가장 높은 상위 3개 결과만 보여줍니다. IMDb, TVMaze, Wikipedia 공개 엔드포인트를 활용하며, 제목 유사도(rapidfuzz)를 통해 정확도를 산출합니다.

### 설치
```bash
python3 -m pip install -e .
```

### 사용 방법
```bash
python3 -m movie_agent.cli "Interstellar"
```

선택적으로 다음 옵션을 지정할 수 있습니다.
- `--top`: 출력할 순위 개수 (기본 3)
- `--limit`: 소스별로 유지할 후보 개수 (기본 5)
- `--sources`: `imdb tvmaze wikipedia` 중 일부만 선택해 조회
- `--output`: `table` 또는 `json`
- `--verbose`: Scrapy 로그를 자세히 확인

### 동작 개요
1. 사용자 입력 정규화 → 소스별 요청 생성
2. Scrapy Spider가 병렬로 정보를 수집 후 `MovieItem`으로 정형화
3. `TopKPipeline`이 유사도 점수 기준 정렬 → 상위 3개만 남김
4. CLI가 결과를 표 혹은 JSON으로 출력
