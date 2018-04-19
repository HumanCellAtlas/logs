from itertools import chain
from lib.firehose_record import FirehoseRecord


def from_docs(doc_stream):
    return _flatten_records(
        _select_data_records(
            _docs_to_records(doc_stream)
        )
    )


def _docs_to_records(doc_stream):
    for doc in doc_stream:
        yield FirehoseRecord(doc)


def _select_data_records(record_stream):
    for record in record_stream:
        if record.message_type == 'DATA_MESSAGE':
            yield record


def _flatten_records(records):
    return chain.from_iterable(
        [r.transform_and_extract_from_log_events_in_record() for r in records]
    )
