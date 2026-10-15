import os
from src.configs import settings
from collections import defaultdict

# def get_list_model_by_provider():
#     res = {}
#     for model in settings.chat_models:
#         res[model['provider']]=[]
#     for model in settings.chat_models:
#         res[model['provider']].append(model['name'])
#     return res
def get_list_model_by_provider():
    res = {}
    for model in settings.chat_models:
        if model['provider'] not in res:
            res[model['provider']]=[]
            res[model['provider']].append(model['name'])
        else:
            res[model['provider']].append(model['name'])
    return res
# def get_list_model_by_provider():
#     res = defaultdict(list)
#     for model in settings.chat_models:
#         res[model['provider']].append(model['name'])
#     return res

if __name__ == "__main__":
    print(get_list_model_by_provider())