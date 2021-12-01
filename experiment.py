from collections import defaultdict

result = (
1, [(1, 'Feature2', 3, 0, 1), (3, 'Group3', 2, -1, 1), (2, 'Group2', 1, -2, 1), (1, 'Group1', None, -3, 1)], 1,
'Function4', 1)
heritage = [(1, 'Feature2', 3, 0, 1), (3, 'Group3', 2, -1, 1), (2, 'Group2', 1, -2, 1), (1, 'Group1', None, -3, 1)]
heritage2 = [(33, 'Feature33', 3, 0, 1), (3, 'Group3', 2, -1, 1), (2, 'Group2', 1, -2, 1), (1, 'Group1', None, -3, 1)]
heritage3 = [(44, 'Feature44', 3, 0, 1), (2, 'Group2', 1, -2, 1), (1, 'Group1', None, -3, 1)]


def build_tree(result, array, pointer=-1):

    id, name = array[pointer][:2]
    if id not in result:
        result[id] = {"name": name, "subgroup": {}, "features": {}}

    if -pointer == len(array) - 1:
        feature_id, feature_name = array[0]
        result[id]["features"].update({feature_id: {"name": feature_name}})
        return result[id]["features"][feature_id]

    return build_tree(result[id]["subgroup"], array, pointer-1)


res = {}

feature_id, hierarchy, functions = (
    1, [(1, 'Feature2'), (3, 'Group3'), (2, 'Group2'), (1, 'Group1')], [(1, 'Function4'), (2, 'Function22')]
)
s = build_tree(res, hierarchy)

s["functions"] = {}
for func_id, func_name in functions:
    s["functions"].update({func_id: {"name": func_name}})

# s = build_tree(res, heritage2)
# s = build_tree(res, heritage3)
print(s)

import json
print(json.dumps(res, indent=4))