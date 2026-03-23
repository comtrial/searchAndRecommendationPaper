# Search Engine & Recommend

대학-기업 간 연구 협업 증대를 위한 검색 엔진 및 추천 시스템입니다.

## 주요 기능

- **논문/연구자/기업 검색**: Whoosh 기반 전문 검색 엔진 (한국어 형태소 분석 + 영어 Stemming)
- **기업 → 논문 추천**: 기업의 업종/분야와 매칭되는 연구 논문 추천
- **논문 유사도 추천**: 특정 논문과 유사한 논문 탐색 (content-based)
- **연구자 기반 추천**: 연구 분야 기반 유사 연구자 및 관련 기업 추천
- **상호작용 기반 가중치**: 기업의 열람 이력을 반영한 점수 조정
- **최신 콘텐츠 정렬**: 이미지 유무 + 날짜 기반 정렬

## 기술 스택

| 분류 | 기술 |
|------|------|
| Backend | Flask, Flask-RESTful |
| Search Engine | Whoosh (inverted index) |
| NLP | KoNLPy (꼬꼬마 형태소 분석기) |
| Database | MariaDB (PyMySQL) |
| Language | Python 3.7+ |

## 프로젝트 구조

```
Searchengine-Recommend/
├── __init__.py                          # Flask 앱 & API 라우팅
├── Research_Recommend/
│   ├── utils.py                         # 공용 유틸 (DB 연결, 형태소 분석, 경로 설정)
│   ├── duplicated_index.py              # 인덱싱 (논문, 학과, 기업)
│   └── searcher.py                      # 검색 & 추천 로직
└── requirements.txt
```

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 환경 변수

DB 및 인덱스 경로를 환경 변수로 설정합니다:

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=your_database
export INDEX_BASE_DIR=/path/to/index/directory
```

## 실행

```bash
# 인덱싱 (최초 1회 또는 데이터 갱신 시)
# GET /test/indexing/request 호출 또는 직접 실행

# 서버 시작
python __init__.py
```

## API 엔드포인트

### 1. 검색 결과 목록

```
GET /test/result_list?input_word={검색어}&page_num={페이지}&data_count={개수}&type={타입}
```

- `input_word`: 검색어 (빈 문자열이면 최신 콘텐츠 반환)
- `page_num`: 페이지 번호
- `data_count`: 페이지당 결과 수
- `type` (선택): 콘텐츠 타입 필터 (쉼표 구분, 예: `1,2`)

### 2. 기업 기반 추천

```
GET /test/recommend/by_company?company_idx={기업ID}&page_num={페이지}&data_count={개수}&type={타입}
```

### 3. 논문 유사도 추천

```
GET /test/recommend/by_content_idx?content_idx={논문ID}&data_count={개수}
```

### 4. 연구자 기반 추천

```
GET /test/recommend/by_researcher?researcher_idx={연구자ID}&data_count={개수}
```

**응답**: 유사 연구자 목록 (`researcher_data`) + 관련 기업 목록 (`company_data`)

### 5. 인덱싱 요청

```
GET /test/indexing/request
```

## 인덱싱 구조

| 인덱스 | 대상 | 주요 필드 |
|--------|------|-----------|
| `db_to_index_duplicate` | 논문 (중복 제거) | title, content, department, research_field, english_name |
| `department_index` | 학과-분야 매핑 | department, sector |
| `company_index` | 기업 | name, ceo, sector, industry |

---

## 검색 엔진 아키텍처 상세

### 왜 KoNLPy (꼬꼬마)인가?

논문 데이터는 한국어 제목/초록 + 영어 논문명이 혼합된 형태입니다. 단순 키워드 매칭(문자열 일치)으로는 다음 문제를 해결할 수 없습니다:

| 문제 | 예시 | 단순 매칭 결과 |
|------|------|---------------|
| 조사/어미 불일치 | "인공지능**의** 활용" vs "인공지능 활용" | 불일치 |
| 복합 명사 분리 | "딥러닝기반음성인식" → "딥러닝", "음성인식" | 검색 불가 |
| 한영 혼합 | "BERT 기반 자연어처리" | 한쪽만 매칭 |

**꼬꼬마(Kkma)**를 선택한 이유:

1. **명사 추출 정확도**: 꼬꼬마는 세종 코퍼스 기반으로 학습되어, 학술 용어의 명사 추출이 비교적 정확합니다
2. **복합 명사 분리**: "음성인식시스템" → `["음성", "인식", "시스템"]`으로 분리하여 부분 매칭 가능
3. **불용어 자동 제거**: 명사만 추출하므로 조사("의", "을", "에서")가 자연히 제거됩니다

### 이중 언어 분석 파이프라인

```python
def kkma_analyze(input_word):
    kkma = Kkma()
    stem = StemmingAnalyzer()
    hangul = re.compile('[^ ㄱ-ㅣ가-힣]+')
    english = ' '.join(hangul.findall(input_word))

    return ' '.join(kkma.nouns(input_word)) + ' '.join([token.text for token in stem(english)])
```

하나의 입력 텍스트를 **한국어 경로**와 **영어 경로**로 분리하여 처리합니다:

```
입력: "BERT 기반의 한국어 자연어처리 연구"
        │
        ├─ 한국어 경로 (Kkma.nouns)
        │   → ["기반", "한국어", "자연어", "처리", "연구"]
        │
        └─ 영어 경로 (StemmingAnalyzer)
            → ["bert"]  (소문자화 + 어간 추출)

최종 인덱싱 토큰: "기반 한국어 자연어 처리 연구 bert"
```

- **한국어**: `Kkma.nouns()` — 형태소 분석 후 명사만 추출
- **영어**: Whoosh의 `StemmingAnalyzer` — 소문자 변환 + Porter Stemming (예: "processing" → "process")
- **분리 기준**: 정규표현식 `[^ ㄱ-ㅣ가-힣]+`로 한글이 아닌 부분을 영어로 판별

이 방식으로 "BERT based NLP" 검색이 "BERT 기반 자연어처리" 논문과도 매칭됩니다.

### 검색 품질 향상 기법

#### 1. Field Boosting (필드 가중치)

모든 필드를 동일하게 취급하지 않고, 검색 의도에 맞는 필드에 높은 가중치를 부여합니다:

```python
schema = Schema(
    title       = KEYWORD(field_boost=7.5),    # 제목 일치 → 최고 우선
    english_name = KEYWORD(field_boost=7.5),   # 영문 제목도 동일 가중
    content     = KEYWORD(field_boost=1.5),    # 본문 일치 → 보조
    research_field = KEYWORD(field_boost=1.2), # 연구 분야 → 약한 보조
    department  = KEYWORD(field_boost=1.1),    # 학과명 → 최소 보조
)
```

**효과**: "딥러닝"을 검색하면, 제목에 "딥러닝"이 있는 논문이 본문에만 언급된 논문보다 **5배** 높은 점수를 받습니다.

#### 2. Multi-Field OR 검색

```python
MultifieldParser(
    ['title', 'content', 'department', 'researcher_name', 'research_field', 'english_name'],
    schema,
    group=qparser.OrGroup  # 핵심: AND가 아니라 OR
).parse(query)
```

6개 필드를 동시에 검색하되 `OrGroup`을 사용합니다:
- **OR**: 하나의 필드라도 매칭되면 결과에 포함 (recall 극대화)
- **BM25 스코어링**: Whoosh 기본 스코어링이 매칭된 필드 수 + boost에 따라 순위를 자동 결정

#### 3. 중복 논문 제거 (Deduplication)

동일 연구자가 제출한 유사 논문을 인덱싱 단계에서 제거합니다:

```python
# 1) 연구자별로 그룹핑
data_list.sort(key=lambda x: x[researcher_idx])

# 2) 같은 연구자의 논문끼리 제목 유사도 비교
score = SequenceMatcher(None, title_a, title_b).ratio()

# 3) 97% 이상 유사하면 중복으로 판정 → 인덱스에서 제외
if score >= 0.97:
    remove(title_b)
```

**왜 97%?**: 동일 논문의 버전 차이(오타 수정, 부제 변경 등)를 잡되, 실제로 다른 논문(후속 연구 등)은 보존하기 위한 임계값입니다.

#### 4. Recency Scoring (최신성 가점)

최근 논문에 가산점을 부여하여 오래된 논문이 상위에 고정되는 것을 방지합니다:

```python
days_old = (now - publish_date).days
recency_bonus = 0.2 - (days_old / 20000)
final_score = relevance_score + recency_bonus
```

| 논문 발행일 | days_old | recency_bonus |
|------------|----------|---------------|
| 오늘 | 0 | +0.200 |
| 1년 전 | 365 | +0.182 |
| 5년 전 | 1825 | +0.109 |
| 10년 전 | 3650 | +0.018 |
| 15년+ | 5475+ | -0.074 (감점) |

#### 5. Image Priority (이미지 우선 정렬)

검색 결과를 최종 정렬할 때 이미지 보유 여부를 1차 정렬 키로 사용합니다:

```python
results.sort(key=lambda x: (-image_count, -score))
```

이미지가 있는 논문 = 시각 자료가 풍부한 연구 → 기업 입장에서 이해도가 높으므로 우선 노출합니다.

#### 6. Interaction-based Re-ranking (상호작용 기반 재정렬)

기업의 과거 열람 이력을 반영하여 추천 점수를 조정합니다:

```
기업 A의 최근 열람 이력 (최대 10건)
    │
    ├─ 이미 열람한 논문 → score -= 0.2  (중복 노출 감소)
    │
    └─ 열람한 논문의 연구자가 쓴 다른 논문 → score += 0.1  (관심 연구자 부스트)
```

이 방식으로 같은 검색어에도 기업마다 다른 결과 순위가 생깁니다.

#### 7. Cross-Index Department Matching (학과-업종 교차 매칭)

기업 → 논문 추천 시 단순 키워드 매칭이 아니라 3단계 교차 검색을 수행합니다:

```
기업의 industry + sector
    │
    ① department_index 검색: 업종 → 관련 학과 목록 추출
    │   예: "반도체" → ["전자공학과", "재료공학과", "물리학과"]
    │
    ② 논문 인덱스 검색: 업종 키워드로 전문 검색
    │
    ③ 필터링: ①에서 나온 학과 소속 연구자의 논문만 남김
```

이렇게 하면 "반도체" 기업에게 전자공학과 논문은 추천하되, 키워드만 우연히 겹치는 경영학과 논문은 제외됩니다.

### 검색 파이프라인 전체 흐름

```
사용자 검색어 입력
    │
    ▼
[1] kkma_analyze(): 한국어 명사 추출 + 영어 Stemming
    │
    ▼
[2] MultifieldParser (6개 필드, OrGroup): Whoosh BM25 스코어링
    │
    ▼
[3] filter_by_type(): 콘텐츠 타입 필터 (논문/특허 등)
    │
    ▼
[4] Pagination: offset 기반 페이지네이션
    │
    ▼
[5] result_list(): DB에서 원본 데이터 조회 → JSON 응답 구성
```

```
기업 기반 추천 파이프라인
    │
    ▼
[1] 기업 industry/sector 조회
    │
    ▼
[2] department_index에서 관련 학과 추출 (Cross-Index Matching)
    │
    ▼
[3] 논문 인덱스 Multi-field 검색 + 학과 필터링
    │
    ▼
[4] Score Normalization: 최고 점수 기준 0~1 정규화
    │
    ▼
[5] InteractionRecommend: 열람 이력 기반 점수 조정
    │
    ▼
[6] sort_by_date(): 최신성 가점 적용
    │
    ▼
[7] filter_by_type() → 이미지 우선 정렬 → 페이지네이션
```

## License

MIT
