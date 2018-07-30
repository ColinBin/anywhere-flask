from constants import SUCCESS, FAILURE, code_desc
import json


def gen_json_success(data=None):
    result = dict()
    result["status"] = SUCCESS
    result["data"] = data
    return json.dumps(result)


def gen_json_failure(err_code):
    result = dict()
    result['status'] = FAILURE
    result['data'] = {"err_code": err_code, "err_msg": code_desc[err_code]}
    return json.dumps(result)
