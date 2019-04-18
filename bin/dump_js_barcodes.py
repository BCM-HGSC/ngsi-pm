#! /usr/bin/env python3

"""A JSON document will be a three-level dictionary. We care about
barcode, sample, and reference.
"""

import argparse
from collections import Counter
import json
from logging import error
import os
from pathlib import Path
from subprocess import run, DEVNULL, PIPE
import sys

MESSAGE = "THE KEY MISSING"


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
        self.id = merge_definition_dict.get('event_id', MESSAGE)
        if self.id == MESSAGE:
            error("key 'event_id' in Merge is missing; %r", json_path)
        self.lib_name = merge_definition_dict.get('library_name', MESSAGE)
        if self.lib_name == MESSAGE:
            error("key 'library_name' in Merge is missing; %r", json_path)
        ses = merge_definition_dict.get('sequencing_events', MESSAGE)
        if ses == MESSAGE:
            error("key 'sequencing_events' in Merge is missing; %r", json_path)
        else:
            self.sequencing_events = [
                SequencingEvent(key, json_path, json_data)
                for key, json_data in ses.items()
            ]

    def _load_hgv_legacy(self, json_path):
        self.json_path = json_path
        with open(str(json_path)) as fin:
            merge_definition_dict = json.load(fin)
        self.num_sequencing_events = merge_definition_dict.get('seNum', MESSAGE)
        self.id = merge_definition_dict.get('eventId', MESSAGE)
        self.lib_name = merge_definition_dict.get('libName', MESSAGE)
        ses = merge_definition_dict.get('seqEvents', MESSAGE)
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
        if len(c) == 1:
            self.sample_name = c.most_common(1)[0][0]
        else:
            # breakpoint()
            error(
                'count: %r; sample names: %r; json: %r', len(c), c, json_path
            )

        r = Counter(se.reference for se in self.sequencing_events)
        if len(r) == 1:
            self.reference = r.most_common(1)[0][0]
        else:
            error(
                'references: %r; count is %r; json: %r', r, len(r), json_path
            )


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
        self.barcode = json_data.get('event_id', MESSAGE)
        # assert self.barcode == key, key
        if self.barcode == MESSAGE:
            error("key 'event_id' in SE is missing; %r", key)
        self.sample_name = json_data.get('sample_name', MESSAGE)
        if self.sample_name == MESSAGE:
            error("key 'sample_name' in SE is missing; %r", key)
        self.reference = json_data.get('reference', MESSAGE)

    def _load_hgv_legacy_se(self, key, json_data):
        self.barcode = json_data.get('eventId', MESSAGE)
        # assert self.barcode == key, key
        if self.barcode == MESSAGE:
            error("key 'eventId' in SE is missing; %r", key)
        self.sample_name = json_data.get('sampleName', MESSAGE)
        if self.sample_name == MESSAGE:
            error("key 'sampleName' in SE is missing; %r", key)
        self.reference = json_data.get('reference', MESSAGE)


if __name__ == '__main__':
    main()
