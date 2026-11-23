"""Ablations sur situations P7 inédites et candidats gelés par tour."""

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import random

from p5.contract import Situation
from p5.jepa import load
from p5.orchestration import Experiment
from p7.benchmark import interval


TUPLES = ('faits', 'reponses_precedentes', 'acquis', 'erreurs', 'interventions')


def evaluate(trace, model, *, seed):
    rows = []
    for raw in trace:
        if raw['repetition'] != 1 or not raw['reponse']:
            continue
        state = raw['reponse'].get('pedagogie', {})
        decision = state.get('experience_jepa')
        if not decision:
            continue
        case = decision['situation']
        situation = Situation(**(case | {key: tuple(case[key]) for key in TUPLES}))
        rows.append((raw, situation, decision['classement_regles']))
    if len(rows) < 2:
        raise ValueError('Au moins deux situations admissibles sont nécessaires.')
    rng = random.Random(seed)
    # Permutation circulaire d’un ordre aléatoire, avec bijection et sans point fixe.
    order = list(range(len(rows)))
    rng.shuffle(order)
    donors = {left + 1: rows[right][1] for left, right in zip(order, order[1:] + order[:1], strict=True)}
    for index, (raw, situation, options) in enumerate(rows, 1):
        modes = {mode: Experiment(mode, model if mode in ('c', 'melange') else None,
                                  donors=donors if mode == 'melange' else None) for mode in ('b', 'c', 'neutralise', 'melange')}
        output = {}
        for mode, experiment in modes.items():
            ranked, source, scores = experiment.rank(situation, options, index)
            output[mode] = {'source': source, 'scores': scores, 'classement': ranked, 'retenue': ranked[0],
                            'change': ranked[0] != options[0]}
        yield {'dialogue': raw['dialogue'], 'tour': raw['tour'], 'modele': model.identity, 'graine': seed,
               'situation': asdict(situation), 'melange': asdict(donors[index]), 'decisions': output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    trace = [json.loads(line) for line in args.trace.read_text(encoding='utf-8').splitlines()]
    result = {}
    with args.output.open('x', encoding='utf-8') as stream:
        for seed in (17, 43, 97):
            rows = list(evaluate(trace, load(args.models / f'fixe-24-{seed}'), seed=seed))
            for row in rows:
                print(json.dumps(row, ensure_ascii=False), file=stream)
            result[str(seed)] = {}
            for mode in ('b', 'c', 'neutralise', 'melange'):
                changes = sum(row['decisions'][mode]['change'] for row in rows)
                actions = Counter(row['decisions'][mode]['retenue'][0] for row in rows)
                result[str(seed)][mode] = {'reclassements': changes, 'n': len(rows), 'actions': actions,
                                           'wilson95_taux_reclassement': interval(changes, len(rows))}
    args.output.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
