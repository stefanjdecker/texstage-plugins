# SPDX-License-Identifier: Apache-2.0
"""Generate distinct valid FD submissions and independently calculated grades."""
import itertools
import json
from pathlib import Path
import sys
from texstage_fd_lab import model


def cases(lesson, count, diverse=False):
    seed, worked = model.compile_lesson(lesson)
    task = seed['task']; mode=task['mode']; masks=range(1 << len(seed['attributes']))
    def candidates():
        yield worked
        if mode=='keys':
            for size in (1,2,3):
                for keys in itertools.combinations(masks,size):
                    yield {'format':1,'mode':mode,'keys':list(keys)}
        else:
            if mode=='implication':
                for agree in masks: yield {'format':1,'mode':mode,'implied':False,'agree':agree}
            for length in range(9):
                for steps in itertools.product(range(len(seed['fds'])),repeat=length):
                    if mode=='closure':
                        for closure in masks: yield {'format':1,'mode':mode,'steps':list(steps),'closure':closure}
                    else:yield {'format':1,'mode':mode,'implied':True,'steps':list(steps)}
    result=[];seen=set()
    for value in candidates():
        # Wire validation and the independent Python engine, not browser claims.
        try:
            answer=model.answer_for(seed,value)
        except (model.InputError, model.ResourceLimit):
            continue  # Some modes allow only one key or a smaller proof budget.
        key=model.canonical(answer)
        if key in seen:continue
        seen.add(key);facts=model.analyze(seed,answer)['facts']
        if mode=='keys':
            correct=all(k in facts['candidate_keys'] for k in answer['keys']) and (
                task['require']=='one' or set(answer['keys'])==set(facts['candidate_keys']))
        elif mode=='closure':
            correct=facts['trace']['error'] is None and answer['closure']==facts['closure']==facts['trace']['reached']
        elif answer['implied']:
            correct=facts['proof']['error'] is None and task['rhs'] & ~facts['proof']['reached']==0
        else:
            correct=not facts['proof']['violated_fds'] and facts['proof']['violates_target']
        result.append({'answer':answer,'correct':correct})
        if not diverse:return result*count
        if len(result)==count:return result
    raise ValueError('Not enough distinct answers for this exercise')


if __name__=='__main__':
    print(json.dumps(cases(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')),
                           int(sys.argv[2]), sys.argv[3]=='1')))
