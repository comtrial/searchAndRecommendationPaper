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

## License

MIT
