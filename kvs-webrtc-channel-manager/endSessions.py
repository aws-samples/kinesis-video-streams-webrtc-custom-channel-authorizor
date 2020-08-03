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
import botocore
import os
from datetime import timezone
import datetime
import time


def lambda_handler(event, context):
    iam = boto3.client('iam')
    kvs_channel_name = event['pathParameters']['channelName']

    revoke_access_policy_file = os.environ['LAMBDA_TASK_ROOT'] + \
        os.environ['REVOKE_POLICY_KEY']

    revoke_access_policy = None
    with open(revoke_access_policy_file, 'r') as myfile:
        revoke_access_policy = myfile.read()

    dt = datetime.datetime.now()
    utc_time = dt.replace(tzinfo=timezone.utc)

    revoke_access_policy = revoke_access_policy.replace(
        '[policy creation time]', utc_time.isoformat()[:-9] + 'Z')

    master_role_name = kvs_channel_name + '-master'
    viewer_role_name = kvs_channel_name + '-viewer'
    revoke_policy_name = 'AWSRevokeOlderSessions'

    try:
        # Update the master and the viewer roles with the inline policy
        iam.put_role_policy(
            RoleName=master_role_name,
            PolicyName=revoke_policy_name,
            PolicyDocument=revoke_access_policy
        )
        iam.put_role_policy(
            RoleName=viewer_role_name,
            PolicyName=revoke_policy_name,
            PolicyDocument=revoke_access_policy
        )
    except botocore.exceptions.ClientError as err:
        print(err)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "All sessions prior to " + utc_time.isoformat() + " revoked for master and viewer for channel : " + kvs_channel_name,
        }),
    }
