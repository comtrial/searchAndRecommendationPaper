import csv
import os
import random

from difflib import SequenceMatcher
from whoosh.index import create_in
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import *

from Research_Recommend.utils import (
    kkma_analyze, connect_db,
    DUPLICATE_INDEX_DIR, DEPARTMENT_INDEX_DIR, COMPANY_INDEX_DIR, SECTOR_CSV_PATH,
)


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def duplicate():
    curs, conn = connect_db()

    num_list = list()
    data_list = list()
    duplicate_list = list()

    curs.execute('Select idx, title, researcher_idx from tbl_data')
    rows = curs.fetchall()

    for row in rows:
        detail = [row[0], row[1], row[2]]
        duplicate_list.append(row[0])
        data_list.append(detail)

    data_list.sort(key=lambda x: x[2])

    for i in range(len(data_list) - 1):
        j = i + 1
        while data_list[i][2] == data_list[j][2]:
            score = similarity(data_list[i][1], data_list[j][1])
            if score >= 0.97 and data_list[j][0] not in num_list:
                num_list.append(data_list[j][0])

            j += 1
            if j > len(data_list) - 1:
                break

    for i in num_list:
        duplicate_list.remove(i)

    conn.close()
    return duplicate_list


class DuplicatedIndexing:

    def indexing(self):
        curs, conn = connect_db()

        curs.execute('Select target_idx, target_type_code from tbl_data_image')
        image = curs.fetchall()
        image_list = list()

        for i in image:
            if i[1] == 1 and i[0] not in image_list:
                image_list.append(i[0])

        indexdir = DUPLICATE_INDEX_DIR
        duplicate_list = duplicate()

        data_idx = list()
        english_title = list()

        curs.execute("Select data_idx, english_name from tbl_paper_data")
        paper_data = curs.fetchall()

        for row in paper_data:
            data_idx.append(row[0])
            english_title.append(row[1])

        if not os.path.exists(indexdir):
            os.makedirs(indexdir)

        schema = Schema(
            idx=ID(stored=True),
            title=KEYWORD(field_boost=7.5),
            content=KEYWORD(field_boost=1.5),
            researcher_name=TEXT(),
            researcher_idx=ID(stored=True),
            department=KEYWORD(stored=True, field_boost=1.1),
            research_field=KEYWORD(field_boost=1.2),
            english_name=KEYWORD(field_boost=7.5),
            date=TEXT(stored=True),
            image_num=NUMERIC(stored=True),
            start_date=DATETIME(stored=True),
            type_code=NUMERIC(stored=True),
            weight=NUMERIC(stored=True),
        )

        ix = create_in(indexdir, schema)
        wr = ix.writer()

        for idx in duplicate_list:
            curs.execute(
                "Select title, content, researcher_idx, start_date, data_type_code from tbl_data where idx =%s", idx
            )
            data = curs.fetchall()

            curs.execute(
                "Select name, department, research_field from tbl_researcher_data where idx = %s", data[0][2]
            )
            researcher_data = curs.fetchall()

            title = str(data[0][0])
            content = str(data[0][1])
            researcher_name = researcher_data[0][0]
            researcher_idx = str(data[0][2])
            department = researcher_data[0][1]
            research_field = researcher_data[0][2]
            weight = random.randrange(-5, 6)
            date = data[0][3]
            type_code = data[0][4]

            if date is None:
                date = '1-1-1'
            else:
                date = date.strftime('%Y-%m-%d')

            if idx in image_list:
                curs.execute('Select idx from tbl_data_image where target_idx = %s', idx)
                image = curs.fetchall()
                if len(image) >= 2:
                    image_num = 2
                else:
                    image_num = 1
            else:
                image_num = 0

            if idx in data_idx and english_title[data_idx.index(idx)] is not None:
                wr.add_document(
                    idx=str(idx),
                    title=kkma_analyze(title),
                    content=kkma_analyze(content),
                    researcher_name=kkma_analyze(researcher_name),
                    researcher_idx=researcher_idx,
                    department=kkma_analyze(department),
                    research_field=kkma_analyze(research_field),
                    english_name=english_title[data_idx.index(idx)],
                    date=date,
                    image_num=image_num,
                    type_code=type_code,
                    weight=weight,
                )
            else:
                wr.add_document(
                    idx=str(idx),
                    title=kkma_analyze(title),
                    content=kkma_analyze(content),
                    researcher_name=kkma_analyze(researcher_name),
                    researcher_idx=researcher_idx,
                    department=kkma_analyze(department),
                    research_field=kkma_analyze(research_field),
                    date=date,
                    image_num=image_num,
                    type_code=type_code,
                    weight=weight,
                )
        wr.commit()
        conn.close()


class DepartmentIndexing:

    def indexing(self):
        indexdir = DEPARTMENT_INDEX_DIR

        if not os.path.exists(indexdir):
            os.makedirs(indexdir)

        f = open(SECTOR_CSV_PATH, 'r', encoding='utf-8')
        rdr = csv.reader(f)
        data = list()
        result = list()

        for line in rdr:
            data.append(line)

        for i in range(2, len(data) - 1):
            if data[i][0] != '':
                department = data[i][0]
                info = department + ' ' + data[i][1], data[i][2]
            else:
                info = department + ' ' + data[i][1], data[i][2]

            result.append(info)

        schema = Schema(
            department=TEXT(stored=True),
            sector=KEYWORD(stored=True, analyzer=StemmingAnalyzer()),
        )

        ix = create_in(indexdir, schema)
        wr = ix.writer()

        for line in result:
            wr.add_document(department=line[0], sector=kkma_analyze(line[1]))
        wr.commit()


class CompanyIndexing:

    def indexing(self):
        curs, conn = connect_db()

        indexdir = COMPANY_INDEX_DIR

        if not os.path.exists(indexdir):
            os.makedirs(indexdir)

        curs.execute("Select idx, name, ceo, sector, industry from tbl_company")
        company_data = curs.fetchall()

        schema = Schema(
            company_number=ID(stored=True),
            name=TEXT(),
            ceo=TEXT(),
            sector=KEYWORD(),
            industry=KEYWORD(),
        )

        company_ix = create_in(indexdir, schema)
        wr = company_ix.writer()

        for row in company_data:
            wr.add_document(
                company_number=str(row[0]),
                name=row[1],
                ceo=row[2],
                sector=kkma_analyze(str(row[3])),
                industry=kkma_analyze(str(row[4])),
            )
        wr.commit()
        conn.close()
