#! /usr/bin/env python3

"""A JSON document will be a three-level dictionary. We care about
barcode, sample, and reference.
"""

import argparse
from collections import Counter
import json
import os
import sys
from pathlib import Path
from subprocess import run, DEVNULL, PIPE


def main():
    args = parse_args()
    run(args.json_path_stream, args.add_references, args.add_json_path)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('json_path_stream',
                        nargs='?',
                        type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('--add-references', '-r', action='store_true')
    parser.add_argument('--add-json-path', '-j', action='store_true')
    args = parser.parse_args()
    return args


def run(json_path_stream, add_references, add_json_path):
    references = set()
    for merge in parse_merge_definitions(json_path_stream):
        references.add(merge.reference)
        for s in merge.sequencing_events:
            row = [s.barcode, s.sample_name, merge.id]
            if add_references:
                row.append(merge.reference)
            if add_json_path:
                row.append(merge.json_path)
            print(*row, sep='\t')
    if len(references) > 1 and not add_references:
        print('Multiple references:', *sorted(references), file=sys.stderr)


def parse_merge_definitions(json_path_stream):
    """Generator of Merge objects. The input is a stream of JSON file paths."""
    for line in json_path_stream:
        json_path = line.rstrip('\n')
        merge = Merge(json_path)
        yield merge


class Merge:
    """Contains global data about a merge and a list of SequencingEvent."""
    def __init__(self, json_path):
        self.json_path = json_path
        json_path = Path(json_path)
        if json_path.name == 'event.json':
            self._load_hgv_19(json_path)
        else:
            self._load_hgv_legacy(json_path)
        self.get_sequencing_events_data(json_path)

    def _load_hgv_19(self, json_path):
        self.json_path = json_path
        with open(str(json_path)) as fin:
            merge_definition_dict = json.load(fin)
        self.id = merge_definition_dict['event_id']
        self.lib_name = merge_definition_dict['library_name']
        ses = merge_definition_dict['sequencing_events']
        self.sequencing_events = [
            SequencingEvent(key, json_path, json_data)
            for key, json_data in ses.items()
        ]

    def _load_hgv_legacy(self, json_path):
        self.json_path = json_path
        with open(str(json_path)) as fin:
            merge_definition_dict = json.load(fin)
        self.num_sequencing_events = merge_definition_dict['seNum']
        self.id = merge_definition_dict['eventId']
        self.lib_name = merge_definition_dict['libName']
        ses = merge_definition_dict['seqEvents']
        self.sequencing_events = [
            SequencingEvent(key, json_path, json_data)
            for key, json_data in ses.items()
        ]
        # no equivalent in _load_hgv_19
        assert len(self.sequencing_events) == self.num_sequencing_events, (
            json_path, len(self.sequencing_events), self.num_sequencing_events
        )

    def get_sequencing_events_data(self, json_path):
        c = Counter(se.sample_name for se in self.sequencing_events)
        assert len(c) == 1, json_path
        self.sample_name = c.most_common(1)[0][0]
        r = Counter(se.reference for se in self.sequencing_events)
        assert len(r) == 1, json_path
        self.reference = r.most_common(1)[0][0]


class SequencingEvent:
    """Represents everything about a single sequencing event"""
    def __init__(self, key, json_path, json_data):
        self.json_path = json_path
        json_path = Path(json_path)
        if json_path.name == 'event.json':
            self._load_hgv_19_se(key, json_data)
        else:
            self._load_hgv_legacy_se(key, json_data)

    def _load_hgv_19_se(self, key, json_data):
        self.barcode = json_data['event_id']
        assert self.barcode == key, key
        self.sample_name = json_data['sample_name']
        self.reference = json_data['reference']

    def _load_hgv_legacy_se(self, key, json_data):
        self.barcode = json_data['eventId']
        assert self.barcode == key, key
        self.sample_name = json_data['sampleName']
        self.reference = json_data['reference']


if __name__ == '__main__':
    main()
