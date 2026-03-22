from flask import Flask, make_response, jsonify, request
from flask_restful import Api

from Research_Recommend.searcher import SearchEngine, Recommend, ResearcherSearch, RecentContent
from Research_Recommend.duplicated_index import DuplicatedIndexing, DepartmentIndexing, CompanyIndexing

app = Flask(__name__)
api = Api(app)


@app.route('/test/recommend/by_company', methods=['GET'])
def by_company_idx():
    parameter_dict = request.args.to_dict()

    company_idx = parameter_dict['company_idx']
    page_num = parameter_dict['page_num']
    data_count = parameter_dict['data_count']

    if len(parameter_dict) == 4:
        data_type = parameter_dict['type']
        data_type = list(map(int, data_type.split(sep=',')))
    else:
        data_type = [0]

    engine_recommend = Recommend()
    data = engine_recommend.recommend_by_company(company_idx, int(page_num), int(data_count), data_type)

    response = make_response(
        jsonify({
            "message": 'OK',
            "data": data["results"],
            "data_count": data_count,
            "data_total_count": data["data_total_count"],
        }),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/test/result_list', methods=['GET'])
def result_list():
    parameter_dict = request.args.to_dict()

    input_word = parameter_dict['input_word']
    page_num = parameter_dict['page_num']
    data_count = parameter_dict['data_count']

    if len(parameter_dict) == 4:
        data_type = parameter_dict['type']
        data_type = list(map(int, data_type.split(sep=',')))
    else:
        data_type = [0]

    if len(input_word) == 0:
        engine = RecentContent()
        data = engine.recent(int(page_num), int(data_count), data_type)
    else:
        engine = SearchEngine()
        data = engine.searching(input_word, int(page_num), int(data_count), data_type)

    response = make_response(
        jsonify({
            "message": 'OK',
            "data_count": data_count,
            "data_total_count": data["data_total_count"],
            "data": data["results"],
            "page_num": page_num,
        }),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/test/recommend/by_content_idx', methods=['GET'])
def by_content_idx():
    parameter_dict = request.args.to_dict()

    content_idx = parameter_dict['content_idx']
    data_count = parameter_dict['data_count']

    engine_recommend = Recommend()
    recommend_results = engine_recommend.more_like_idx(content_idx, int(data_count))

    response = make_response(
        jsonify({
            "message": 'OK',
            "data": recommend_results["results"],
            "data_total_count": recommend_results["data_total_count"],
            "data_count": data_count,
        }),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/test/recommend/by_researcher', methods=['GET'])
def recommend_for_researcher():
    parameter_dict = request.args.to_dict()

    researcher_idx = parameter_dict['researcher_idx']
    data_count = parameter_dict['data_count']

    engine_recommend = ResearcherSearch()
    researcher_data = engine_recommend.recommend_by_researcher(researcher_idx, int(data_count))
    company_data = engine_recommend.recommend_company_to_researcher(researcher_idx, int(data_count))

    response = make_response(
        jsonify({
            "message": 'OK',
            "researcher_data": researcher_data["results"],
            "company_data": company_data["results"],
            "data_count": data_count,
            "researcher_data_total_count": researcher_data["data_total_count"],
            "company_data_total_count": company_data["data_total_count"],
        }),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/test/indexing/request', methods=['GET'])
def indexing_request():
    DuplicatedIndexing().indexing()
    DepartmentIndexing().indexing()
    CompanyIndexing().indexing()

    response = make_response(
        jsonify({"message": 'Done'}),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response


if __name__ == "__main__":
    app.run(use_reloader=False, debug=True)
