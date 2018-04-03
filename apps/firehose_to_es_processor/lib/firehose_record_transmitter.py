import boto3
from time import sleep

class FirehoseRecordTransmitter():

    def __init__(self, region, stream_name):
        self.stream_name = stream_name
        self.client = boto3.client('firehose', region_name=region)

    def transmit(self, records):
        record_chunks = self._chunk_records(records=records)
        for record_chunk in record_chunks:
            print('Reingesting %s records into firehose.' % (str(len(record_chunk))))
            self._transmit_record_chunk(record_chunk)

    def _transmit_record_chunk(self, record_chunk, attempts_made=0, max_attempts=20):
        """Put record chunk to delivery stream with built in retry"""
        failed_records = []
        try:
            response = self.client.put_record_batch(DeliveryStreamName=self.stream_name, Records=record_chunk)
        except:
            failed_records = record_chunk

        # if there are no failed_records (put_record_batch succeeded), iterate over the response to gather ind failures
        if not failed_records and response['FailedPutCount'] > 0:
            for idx, res in enumerate(response['RequestResponses']):
                if res.get('ErrorCode'):
                    failed_records.append(record_chunk[idx])

        if len(failed_records) > 0:
            if attempts_made + 1 < max_attempts:
                print('Some records failed while calling put_record_chunk, retrying')
                sleep(1)
                self._transmit_record_chunk(failed_records, attempts_made + 1, max_attempts)
            else:
                raise RuntimeError('Could not put records after %s attempts.' % (str(max_attempts)))

    def _chunk_records(self, chunk_size=450, records=[]):
        """Yield successive chunks from records."""
        record_chunks = []
        for i in range(0, len(records), chunk_size):
            record_chunk = records[i:i + chunk_size]
            record_chunks.append(record_chunk)
        return record_chunks
