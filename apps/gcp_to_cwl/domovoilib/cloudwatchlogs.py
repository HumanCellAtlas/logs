import boto3
from botocore.exceptions import ClientError


class LogStatus:

    def __init__(self, log_group, log_stream):
        self.log_group = log_group
        self.log_stream = log_stream
        self.log_group_exists = None
        self.log_stream_exists = None
        self.upload_token = None


class CloudWatchLogs:

    def __init__(self, client=boto3.client('logs')):
        self.client = client

    def put_log_events(self, request, sequence_token_cache):
        try:
            return self._put_log_events(request, sequence_token_cache)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != 'ResourceNotFoundException':
                raise e
            self.prepare(request['logGroupName'], request['logStreamName'])
            return self._put_log_events(request, sequence_token_cache)

    def _put_log_events(self, request, sequence_token_cache):
        cache_key = f"{request['logGroupName']}.{request['logStreamName']}"
        try:
            if cache_key in sequence_token_cache:
                sequence_token = sequence_token_cache[cache_key]
                response = self.client.put_log_events(
                    logGroupName=request['logGroupName'],
                    logStreamName=request['logStreamName'],
                    logEvents=request['logEvents'],
                    sequenceToken=sequence_token
                )
            else:
                response = self.client.put_log_events(
                    logGroupName=request['logGroupName'],
                    logStreamName=request['logStreamName'],
                    logEvents=request['logEvents'],
                )
            print(f"{request['logGroupName']}: put {len(request['logEvents'])} log events, next sequence token is {response['nextSequenceToken']}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code not in {'InvalidSequenceTokenException', 'DataAlreadyAcceptedException'}:
                raise e
            correct_sequence_token = str(e).split(' ')[-1]
            print(f"{request['logGroupName']}: handling {error_code}, new token is {correct_sequence_token}.")
            if correct_sequence_token != 'null':
                sequence_token_cache[cache_key] = correct_sequence_token
            else:
                sequence_token_cache.pop(cache_key, None)
            response = self._put_log_events(request, sequence_token_cache)

        sequence_token_cache[cache_key] = response['nextSequenceToken']
        return response

    def prepare(self, log_group, log_stream):
        status = LogStatus(log_group=log_group, log_stream=log_stream)
        status = self._get_upload_token_if_possible(status)
        status = self._create_log_group_if_needed(status)
        status = self._create_log_stream_if_needed(status)
        return status.upload_token

    def _get_upload_token_if_possible(self, status):
        if status.upload_token:
            return status
        return self._update_status(status)

    def _create_log_group_if_needed(self, status):
        if status.log_group_exists:
            print(f"Log group/stream exists, obtained sequence token: ${status.upload_token}")
            return status
        self.client.create_log_group(logGroupName=status.log_group)
        return status

    def _create_log_stream_if_needed(self, status):
        if status.log_stream_exists:
            return status
        try:
            self.client.create_log_stream(
                logGroupName=status.log_group,
                logStreamName=status.log_stream,
            )
            status.log_stream_exists = True
            status.upload_token = None
            return status
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != 'ResourceAlreadyExistsException':
                raise e
            print(f"${status.log_stream}: stream already existed, retrieving sequence token.")
            return self._update_status(status)

    def _update_status(self, status):
        try:
            pages = self.client.get_paginator('describe_log_streams').paginate(
                logGroupName=status.log_group,
                logStreamNamePrefix=status.log_stream
            )
            for page in pages:
                for stream in page:
                    if stream['logStreamName'] == status.log_stream:
                        status.log_group_exists = True
                        status.log_stream_exists = True
                        status.upload_token = stream['uploadSequenceToken']
                        return status
            print(f"{status.log_group}: Log group/stream exists!")
            return status
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != 'ResourceNotFoundException':
                raise e
            print(f"{status.log_group}: Log group/stream does not exist!")
            status.log_group_exists = False
            status.log_stream_exists = False
            return status
