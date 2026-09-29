abc = {  
             'security': {'priority': 3, 'agent': 'security', 'dependencies': ['repository']},
             'repository' : {'priority': 1, 'agent': 'abc', 'dependencies': ['repository']}
}
abc = sorted(abc.values(), key = lambda x : x ['priority'])
for agent in abc:
    print(agent[""])