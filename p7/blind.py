"""Préparer deux ordres de lecture et une clé séparée pour les évaluateurs humains."""

import argparse
import json
from pathlib import Path
import random

from p7.benchmark import code_for, data
from pedagogy.catalogue import EXERCISES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--traces', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True, help='Graine connue uniquement du coordinateur.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    scenarios = {dialogue['id']: dialogue for dialogue in data()}
    entries = {}
    for profile in 'ABCD':
        for line in (args.traces / f'{profile}.jsonl').read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            if row['repetition'] != 1:
                continue
            response = row['reponse'] or {}
            key = profile, row['dialogue']
            exercise = EXERCISES[row['famille']]
            entry = entries.setdefault(key, {'famille': row['famille'], 'niveau': exercise['level'],
                                            'enonce': exercise['statement'], 'tours': []})
            entry['tours'].append({'eleve': row['attendu']['text'],
                                   'code': code_for(scenarios[row['dialogue']], bool(row['attendu'].get('code'))),
                                   'reponse': [response[field] for field in ('feedback', 'indice', 'question') if response.get(field)]})
    rng = random.Random(args.seed)
    keys = list(entries)
    rng.shuffle(keys)
    blind = {f'D{i:03}': key for i, key in enumerate(keys, 1)}
    for teacher in (1, 2):
        order = list(blind)
        rng.shuffle(order)
        deck = [{'id': key} | entries[blind[key]] for key in order]
        (args.output / f'enseignant-{teacher}.json').write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.output / 'cle-coordinateur.json').write_text(json.dumps(blind, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
