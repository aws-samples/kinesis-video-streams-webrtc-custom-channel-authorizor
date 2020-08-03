######################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
######################################################################################
import boto3
import json


def lambda_handler(event, context):
    sts = boto3.client('sts')

    kvs_channel_name = event['pathParameters']['channelName']
    account_id = event['requestContext']['accountId']

    viewer_role_name = kvs_channel_name + '-viewer'
    viewer_role_arn = 'arn:aws:iam::' + \
        account_id + ':role/' + viewer_role_name

    viewer_assume_role = sts.assume_role(RoleArn=viewer_role_arn,
                                         RoleSessionName='temp', DurationSeconds=900)
    acessKeyId = viewer_assume_role['Credentials']['AccessKeyId']
    secretAccessKey = viewer_assume_role['Credentials']['SecretAccessKey']
    sessionToken = viewer_assume_role['Credentials']['SessionToken']
    return {
        "statusCode": 200,
        "body": json.dumps({
            "viewerRoleArn": viewer_role_arn,
            "channelName": kvs_channel_name,
            "acessKeyId": acessKeyId,
            "secretAccessKey": secretAccessKey,
            "sessionToken": sessionToken
        }),
    }
