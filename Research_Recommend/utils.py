import os
import re
import pymysql

from konlpy.tag import Kkma
from whoosh.analysis import StemmingAnalyzer

# Base directory for index files (override with INDEX_BASE_DIR env var)
INDEX_BASE_DIR = os.environ.get('INDEX_BASE_DIR', os.path.join(os.path.dirname(__file__)))

DUPLICATE_INDEX_DIR = os.path.join(INDEX_BASE_DIR, 'db_to_index_duplicate')
DEPARTMENT_INDEX_DIR = os.path.join(INDEX_BASE_DIR, 'department_index')
COMPANY_INDEX_DIR = os.path.join(INDEX_BASE_DIR, 'company_index')
SECTOR_CSV_PATH = os.path.join(INDEX_BASE_DIR, 'sector.csv')


def kkma_analyze(input_word):
    """Apply Kkma noun extraction for Korean and stemming for English."""
    kkma = Kkma()
    stem = StemmingAnalyzer()
    hangul = re.compile('[^ ㄱ-ㅣ가-힣]+')
    english = ' '.join(hangul.findall(input_word))

    return ' '.join(kkma.nouns(input_word)) + ' '.join([token.text for token in stem(english)])


def connect_db():
    """Create a database connection. Configure via env vars or PyMySQL defaults."""
    conn = pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', ''),
        charset='utf8mb4',
    )
    curs = conn.cursor()
    return curs, conn
