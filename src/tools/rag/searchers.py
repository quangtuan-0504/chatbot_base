from collections import defaultdict
from typing import Tuple, List
def merge_strings(lst)-> str:
    if not lst:
        return ""
    
    result = lst[0]  # Bắt đầu với chuỗi đầu tiên
    
    for i in range(1, len(lst)):
        current = lst[i]  # Chuỗi hiện tại
        prev = lst[i-1]   # Chuỗi trước đó
        
        # Tìm độ dài phần trùng lặp
        overlap = 0
        for j in range(len(prev), 0, -1):
            if current.startswith(prev[-j:]):
                overlap = j
                break
        
        # Thêm phần không trùng lặp của chuỗi hiện tại
        result += current[overlap:]
    
    return result
def union_overlab(dict_doc_texts : dict[str,list]) -> str: 
    total_text_retrieved = ""
    for file_name, lst_text in dict_doc_texts.items():
        text_join_of_file = merge_strings(lst_text)
        total_text_retrieved += text_join_of_file + f"\nthe above information is taken from file : {file_name}\n\n"   
    return  total_text_retrieved
def vicinity_search(
    client ,
    query_vector : list[float] ,
    collection_name : str ,
    limit : int = 5,
    file_names : list = [] ,
    metric_type : str = "COSINE",
    offset : int = 0,
    upper_bound : int = 2,
    lower_bound : int =2
) -> Tuple[str,List]:
    expr = "file_name in {list_file}" if file_names else None
    filter_params = {"list_file": file_names} if file_names else None
    res = client.search(
        collection_name = collection_name,
        data=[query_vector],
        limit=limit,
        filter=expr,
        filter_params=filter_params,
        output_fields=["text","file_name", "chunk_index_in_file"],
        search_params = {
            "metric_type": metric_type, 
            "offset": offset ,# The records to skip
            # "params": {
            #     "radius": 0.4,
            #     "range_filter": 0.6
            # }
        }
        
    )
    lst_file_relevant = []
    dic_doc_texts_relevant = defaultdict(list)
    for hits in res:
        for hit in hits:
            vicinities_range=[hit['entity']['chunk_index_in_file'] - x for x in range(lower_bound,0,-1)] \
                        + [hit['entity']['chunk_index_in_file'] + x for x in range(0,upper_bound+1)]
            file_name = hit["entity"]["file_name"]
            expr = f'file_name == "{file_name}" && chunk_index_in_file in {vicinities_range}' if vicinities_range else None # expression
            res_vicinities = client.query(
                collection_name=collection_name,
                filter=expr,
                output_fields=["text","file_name", "chunk_index_in_file"],
            )
            for vicinities in res_vicinities:
                dic_doc_texts_relevant[vicinities['file_name']].append(vicinities['text'])
                if vicinities["file_name"] not in lst_file_relevant:
                    lst_file_relevant.append(vicinities["file_name"])
    # for k,v in dic_doc_texts_relevant.items():
    #             res_retrieval += "\n".join(v) + f"\nthe above information is taken from file : {k}\n\n"
    total_text_retrieved = union_overlab(dict_doc_texts=dic_doc_texts_relevant)
    return total_text_retrieved , lst_file_relevant