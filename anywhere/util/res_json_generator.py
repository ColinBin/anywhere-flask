import json

from constants import SUCCESS, FAILURE, error_desc


def gen_json_success(data=None):
    result = dict()
    result["status"] = SUCCESS
    result["data"] = data
    return json.dumps(result)


def gen_json_failure(err_code):
    result = dict()
    result['status'] = FAILURE
    result['data'] = {"err_code": err_code, "err_msg": error_desc[err_code]}
    return json.dumps(result)
