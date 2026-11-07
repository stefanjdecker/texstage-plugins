# SPDX-License-Identifier: Apache-2.0
"""Prepare one FD lesson source for live, exercise and solution editions."""
import copy

from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from . import model

ENGINE = 'io.github.stefanjdecker.fdlab.dependencies'
TYPE = 'io.github.stefanjdecker.fdlab.exercise'


def localized(value, language):
    return value['de' if language.startswith('de') else 'en']


def _set(seed, mask):
    names = [latex_escape(name) for i, name in enumerate(seed['attributes']) if mask & (1 << i)]
    return r'\(\varnothing\)' if not names else r'\{' + ', '.join(names) + r'\}'


def _fragment(public, worked, language, solutions):
    seed, mode, answer = public['seed'], public['mode'], worked['answer']
    task = seed['task']
    de = language.startswith('de')
    label = lambda en, german: german if de else en
    rows = [r'\begingroup\raggedright\small',
            r'\textbf{' + latex_escape(localized(public['title'], language)) + r'}\par',
            latex_escape(localized(public['prompt'], language)) + r'\par\smallskip']
    if public['points']:
        rows.append(label('Maximum points', 'Maximale Punkte') + ': ' + str(public['points']) + r'\par')
    if mode != 'keys':
        start = task['start' if mode == 'closure' else 'lhs']
        rows.append(r'\textbf{' + label('Starting set', 'Startmenge') + '}: ' + _set(seed, start) + r'\par')
        if mode == 'implication':
            rows.append(r'\textbf{' + label('Target FD', 'Ziel-FD') + '}: ' + _set(seed, task['lhs']) +
                        r' \(\rightarrow\) ' + _set(seed, task['rhs']) + r'\par')
    else:
        rows.append(label('Find one candidate key.' if task['require'] == 'one' else 'Find all candidate keys.',
                          'Finden Sie einen Kandidatenschlüssel.' if task['require'] == 'one' else 'Finden Sie alle Kandidatenschlüssel.') + r'\par')
    rows.append(r'\smallskip')
    if solutions:
        rows.append(r'\textbf{' + label('One worked answer', 'Eine mögliche Lösung') + r'}\par\smallskip')
        if mode == 'keys':
            for key in answer['keys']:
                rows.append(label('Candidate key', 'Kandidatenschlüssel') + ': ' + _set(seed, key) + r'\par')
        elif mode == 'implication' and not answer['implied']:
            rows.append(label('Does not follow: a two-row counterexample.', 'Folgt nicht: ein Gegenbeispiel mit zwei Zeilen.') + r'\par')
            rows += [r'\begin{tabular}{@{}lll@{}}', label('Attribute & Row 1 & Row 2', 'Attribut & Zeile 1 & Zeile 2') + r'\\\hline']
            for i, name in enumerate(seed['attributes']):
                rows.append(latex_escape(name) + ' & 0 & ' + ('0' if answer['agree'] & (1 << i) else '1') + r'\\')
            rows.append(r'\end{tabular}\par')
        else:
            rows += [r'\begin{tabular}{@{}p{.08\linewidth}p{.15\linewidth}p{.68\linewidth}@{}}',
                     label('Step & FD & Known attributes', 'Schritt & FD & Bekannte Attribute') + r'\\\hline',
                     '0 & -- & ' + _set(seed, start) + r'\\']
            reached = start
            for index, fd_index in enumerate(answer['steps'], 1):
                fd = seed['fds'][fd_index]
                reached |= fd['rhs']
                rows.append(f'{index} & ' + latex_escape(fd['id']) + ' & ' + _set(seed, reached) + r'\\')
            rows.append(r'\end{tabular}\par\smallskip')
            rows.append((label('Complete closure', 'Attributabschluss') + ': ' + _set(seed, answer['closure']) if mode == 'closure'
                         else label('The target follows from the given FDs.', 'Die Ziel-FD folgt aus den gegebenen FDs.')) + r'\par')
        rows += [r'\smallskip', latex_escape(localized(worked['explanation'], language)) + r'\par']
    else:
        rows.append(r'\begin{tabular}{@{}p{.08\linewidth}p{.83\linewidth}@{}}')
        for fd in seed['fds']:
            rows.append(latex_escape(fd['id']) + ' & ' + _set(seed, fd['lhs']) + r' \(\rightarrow\) ' + _set(seed, fd['rhs']) + r'\\')
        if not seed['fds']:
            rows.append('-- & ' + label('No FDs given.', 'Keine FDs gegeben.') + r'\\')
        instruction = {'closure': label('Show your FD steps and final set.', 'Zeigen Sie Ihre FD-Schritte und die endgültige Menge.'),
                       'keys': label('A candidate key determines every attribute and has no removable member.', 'Ein Kandidatenschlüssel bestimmt alle Attribute und hat kein entfernbares Mitglied.'),
                       'implication': label('Give a derivation, or two rows satisfying every given FD but violating the target.', 'Geben Sie eine Herleitung oder zwei Zeilen an, die alle gegebenen FDs erfüllen und die Ziel-FD verletzen.')}[mode]
        rows += [r'\end{tabular}\par\smallskip', latex_escape(instruction) + r'\par\medskip',
                 r'\rule{.95\linewidth}{.3pt}\par\medskip\rule{.95\linewidth}{.3pt}\par']
    rows.append(r'\endgroup')
    return '\n'.join(rows)


def prepare_lesson(source, context):
    source = model.normalize(source)
    seed, answer = model.compile_lesson(source)
    facts = model.analyze(seed, answer)
    public = {k: copy.deepcopy(source['exercise'][k]) for k in ('id', 'title', 'prompt', 'attributes')}
    public.update(mode=seed['task']['mode'], seed=seed, feedback=source['feedback'], sharing_notice={
        'en': 'The presenter can share a saved answer with the class without your name.',
        'de': 'Die Lehrperson kann eine gespeicherte Antwort ohne Ihren Namen mit der Gruppe teilen.'})
    public['points'] = source.get('points', 0)
    worked = {'answer': answer, 'explanation': copy.deepcopy(source['explanation'])}
    private = {'exercise': facts['exercise'], 'worked': worked}
    if public['mode'] == 'keys':
        private.update(table=model.closure_table(seed), candidate_keys=facts['facts']['candidate_keys'])
    else:
        private['closure'] = facts['facts']['closure']
        if public['mode'] == 'implication':
            private['implied'] = facts['facts']['implied']
    language = context.get('language', 'en')
    diagnostics = []
    seen = set()
    for fd in seed['fds']:
        key = (fd['lhs'], fd['rhs'])
        if key in seen:
            diagnostics.append('Repeated dependency retained: ' + fd['id'])
        seen.add(key)
    return PreparedAuthoring(
        PreparedItem(public=public, private=private,
                     evaluations={},
                     diagnostics=diagnostics),
        {edition: _fragment(public, worked, language, edition == 'solutions')
         for edition in ('exercise', 'solutions')})
