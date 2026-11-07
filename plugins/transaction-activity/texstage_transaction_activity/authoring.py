# SPDX-License-Identifier: Apache-2.0
"""Prepare public exercises, private reference facts and consistent TeX editions."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from . import model

PROVIDER = 'io.github.stefanjdecker.transactionactivity'
TYPE = PROVIDER + '.schedule'
ENGINE = 'io.github.stefanjdecker.transactionengine.schedule'
ROOT = Path(__file__).resolve().parent
LESSON = Draft202012Validator(json.loads((ROOT/'schemas/lesson-v1.json').read_text(encoding='utf-8')))


def localized(value, language):
    return value['de' if language.startswith('de') else 'en']


def operation_label(op):
    if op['kind'] == 'commit':
        return 'commit'
    if op['kind'] == 'read':
        return f"read {op['object']}"
    value = op['value']
    expression = str(value['constant']) if 'constant' in value else f"{value['read']} {value['add']:+d}"
    return f"{op['object']} := {expression}"


def fragment(exercise, worked, language, solutions):
    de = language.startswith('de')
    esc = latex_escape
    rows = [r'\begingroup\raggedright\footnotesize',
            r'\textbf{'+esc(localized(exercise['title'], language))+r'}\par\smallskip']
    if not solutions:
        rows += [esc(localized(exercise['prompt'], language))+r'\par\smallskip',
                 esc(('Anfangswerte: ' if de else 'Initial values: ')+', '.join(f'{k} = {v}' for k,v in exercise['initial'].items()))+r'\par\smallskip']
        width = '.31' if len(exercise['transactions']) == 3 else '.47'
        for transaction in exercise['transactions']:
            rows += [r'\begin{minipage}[t]{'+width+r'\linewidth}\scriptsize',
                     r'\textbf{'+esc(transaction['id'])+r'}\par']
            rows += [esc(f"{op['id']}: {operation_label(op)}")+r'\par' for op in transaction['operations']]
            rows.append(r'\end{minipage}\hfill')
        rows += [r'\par\medskip\textbf{'+('Ablauf' if de else 'Schedule')+r'}\par\ttfamily\scriptsize',
                 esc(' '.join(exercise['schedule']))+r'\par\normalfont\smallskip',
                 esc('Vorhersagen, untersuchen, Konflikte erklären, Ablauf reparieren.' if de else
                     'Predict, inspect, explain conflicts, then repair the schedule.')+r'\par']
    else:
        original = worked['original']
        facts = model.analyze(exercise)
        # The maximum exercise has fifteen rows and long operation identifiers.
        # Keep it on one slide with a consistent, readable six-point table.
        size = r'\fontsize{6}{7}\selectfont' if len(facts['trace']) > 10 else r'\scriptsize'
        rows += [r'\textbf{'+('Geprüfte Lösungen' if de else 'Checked solutions')+r'}\par\smallskip',
                 r'\begin{minipage}[t]{.40\linewidth}\vspace{0pt}'+size+r'\begin{tabular}{rll}',
                 ('Schritt & Op. & Wert' if de else 'Step & Op. & Value')+r'\\\hline']
        rows += [f"{i} & {esc(step['operation'])} & {step.get('value', '--')}"+r'\\' for i,step in enumerate(facts['trace'],1)]
        rows += [r'\end{tabular}\end{minipage}\hfill\begin{minipage}[t]{.56\linewidth}\vspace{0pt}\raggedright'+size,
                 esc(('Endwerte: ' if de else 'Final values: ')+', '.join(f'{k} = {v}' for k,v in original['final'].items()))+r'\par\smallskip']
        for edge in original['diagnosis']['edges']:
            a,b=edge['witness']
            rows.append(esc(f"{edge['from']} -> {edge['to']} ({a}, {b})")+r'\par')
        cert=original['diagnosis']['certificate']
        rows += [esc(('Zyklus: ' if de else 'Cycle: ') if cert['kind']=='cycle' else ('Serielle Ordnung: ' if de else 'Serial order: '))+esc(' -> '.join(cert['vertices']))+r'\par\smallskip']
        for i,repair in enumerate(worked['repairs'],1):
            rows += [esc(('Reparatur ' if de else 'Repair ')+str(i)+':')+r'\par\ttfamily',
                     esc(' '.join(repair['order']))+r'\par\normalfont']
        rows += [r'\smallskip '+esc(localized(worked['explanation'],language))+r'\par\end{minipage}']
    rows.append(r'\endgroup')
    return '\n'.join(rows)


def prepare_lesson(source, context):
    source=copy.deepcopy(source)
    LESSON.validate(source)
    exercise=model.validate(source['exercise'])
    original=model.analyze(exercise)
    repairs=[]
    for order in source['worked_repairs']:
        facts=model.analyze(exercise,order)
        model.require(facts['acyclic'],'worked-repair-cyclic')
        repairs.append({'order':facts['order'],'final':facts['final'], 'serial_order':facts['serial_order']})
    model.require(len({model.canonical(r['order']) for r in repairs})==len(repairs),'worked-repair-duplicate')
    diagnosis={'edges':[{'from':e['from'],'to':e['to'],'witness':e['witnesses'][0]} for e in original['edges']],
               'certificate':{'kind':'serial' if original['acyclic'] else 'cycle',
                              'vertices':original['serial_order'] if original['acyclic'] else original['cycle']}}
    worked={'original':{'final':original['final'],'diagnosis':diagnosis},
            'repairs':repairs,'explanation':source['explanation']}
    language=context.get('language','en')
    return PreparedAuthoring(
        PreparedItem(public={'format':1,'exercise':exercise},
                     private={'original':original,'worked':worked},
                     evaluations={'analysis':{'seed':json.dumps(exercise,ensure_ascii=False,separators=(',',':')),
                                               'options':{},'references':[]}}),
        {edition:fragment(exercise,worked,language,edition=='solutions') for edition in ('exercise','solutions')})
