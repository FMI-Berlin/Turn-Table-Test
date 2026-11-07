"""Shared dataset configuration and repository paths (standard library only)."""
from dataclasses import dataclass
import datetime as dt
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / 'datasets' / '2026-11-03'


@dataclass(frozen=True)
class Dataset:
    directory: Path
    identifier: str
    date: str
    receivers: list
    max_gap_s: float
    assessment: Path | None

    @property
    def results(self):
        return ROOT / 'results' / self.identifier


def load_dataset(path=DEFAULT_DATASET):
    path = Path(path).resolve()
    config_path = path / 'dataset.json' if path.is_dir() else path
    config = json.loads(config_path.read_text())
    directory = config_path.parent
    identifier = config['id']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', identifier):
        raise ValueError('Dataset id must contain only letters, digits, underscores and hyphens')
    date = dt.date.fromisoformat(config['date']).isoformat()
    receivers = config['receivers']
    names = [r['name'] for r in receivers]
    if len(receivers) < 3 or len(set(names)) != len(receivers):
        raise ValueError('A reference and at least two outage receivers with unique names are required')
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', name) for name in names):
        raise ValueError('Receiver names must be safe filename stems')
    reference = config['reference_receiver']
    if reference not in names:
        raise ValueError('reference_receiver must name one of the configured receivers')
    receivers = sorted(receivers, key=lambda r: r['name'] != reference)
    files = []
    for receiver in receivers:
        file = (directory / receiver['file']).resolve()
        if not file.is_file():
            raise FileNotFoundError(f'Missing receiver input: {file}')
        if receiver['color'] not in ('red', 'green', 'blue') and not re.fullmatch(r'#[0-9a-fA-F]{6}', receiver['color']):
            raise ValueError('Receiver colors must be red, green, blue or a six-digit hex color')
        files.append((receiver['name'], file, receiver['color']))
    gap = float(config.get('analysis', {}).get('max_gap_s', 3))
    if not math.isfinite(gap) or gap <= 0:
        raise ValueError('max_gap_s must be finite and positive')
    assessment = config.get('assessment')
    assessment = (directory / assessment).resolve() if assessment else None
    if assessment is not None and not assessment.is_file():
        raise FileNotFoundError(f'Missing assessment: {assessment}')
    return Dataset(directory, identifier, date, files, gap, assessment)
