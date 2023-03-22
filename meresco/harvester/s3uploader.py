from xml.etree.ElementTree import tostring

import boto3
from botocore.exceptions import ClientError
from .virtualuploader import VirtualUploader, UploaderException, \
    InvalidComponentException, InvalidDataException


class S3Uploader(VirtualUploader):
    def __init__(self, target, eventlogger, collection="ignored"):
        super().__init__(eventlogger)
        self.endpoint_url = target.baseurl
        self.access_key = target.accessKey
        self.secret_key = target.secretKey
        self.path = target.path
        self.bucket_name = target.bucket
        self.s3 = boto3.client('s3',
                               endpoint_url=self.endpoint_url,
                               aws_access_key_id=self.access_key,
                               aws_secret_access_key=self.secret_key)

    def send(self, anUpload):
        try:
            file_name = anUpload.id.replace('/', '_')
            serialized_xml = tostring(anUpload.record)
            self.s3.put_object(Bucket=self.bucket_name,
                               Key=self.path + '/' + file_name,
                               Body=serialized_xml)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise InvalidComponentException(anUpload.id, 'Bucket does not exist.')
            else:
                raise UploaderException(anUpload.id, e)

    def delete(self, anUpload):
        try:
            self.s3.delete_object(Bucket=self.bucket_name,
                                  Key=anUpload.id)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise InvalidComponentException(anUpload.id, 'Bucket does not exist.')
            elif error_code == 'NoSuchKey':
                raise InvalidDataException(anUpload.id, 'Key does not exist in bucket.')
            else:
                raise UploaderException(anUpload.id, e)

    def info(self):
        try:
            response = self.s3.head_bucket(Bucket=self.bucket_name)
            return {'bucket': self.bucket_name, 'status': response['ResponseMetadata']['HTTPStatusCode']}
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise InvalidComponentException(self.bucket_name, 'Bucket does not exist.')
            else:
                raise UploaderException(self.bucket_name, e)
