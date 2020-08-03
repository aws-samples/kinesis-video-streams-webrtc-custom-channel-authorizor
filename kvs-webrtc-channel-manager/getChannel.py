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
import json
import sys
import botocore
import boto3
import calendar
import time
import io
import os


def lambda_handler(event, context):
    # boto3 clients
    ddb = boto3.client('dynamodb')
    kvs = boto3.client('kinesisvideo')
    iam = boto3.client('iam')

    # Constants
    ddb_table_name = os.environ['TOKEN_TABLE']
    kvs_channel_name_prefix = os.environ['KVS_CHANNEL_NAME_PREFIX']
    master_policy_file = os.environ['LAMBDA_TASK_ROOT'] + \
        os.environ['MASTER_POLICY_KEY']
    viewer_policy_file = os.environ['LAMBDA_TASK_ROOT'] + \
        os.environ['VIEWER_POLICY_KEY']
    trust_policy_file = os.environ['LAMBDA_TASK_ROOT'] + \
        os.environ['TRUST_POLICY_KEY']

    # Dervived constants
    epoch_time = str(int(time.time()))
    kvs_channel_name = kvs_channel_name_prefix + epoch_time
    account_id = event['requestContext']['accountId']

    # Initialization
    channel_arn = None

    # 1. Get all channel entries from DDB table
    # TODO - This should be changed to query by timestamp based on business logic, will need to modify table with proper indices
    response = ddb.scan(TableName=ddb_table_name)
    channels = response['Items']

    if not channels:
        print("No channels available.. creating new channel")
        # Create signalling channel if none existing are eligible
        kvs_response = kvs.create_signaling_channel(ChannelName=kvs_channel_name,
                                                    ChannelType='SINGLE_MASTER',
                                                    SingleMasterConfiguration={
                                                        'MessageTtlSeconds': 60
                                                    })
        channel_arn = kvs_response['ChannelARN']
    else:
        kvs_channel_name = channels[0]['channel_name']['S']
        channel_arn = channels[0]['channel_arn']['S']
        print("Channel" + kvs_channel_name +
              " already exists.. Not creating a new channel")

    # 2. Make enrty in DDB Table - TODO - KVS channel selection logic has to be improved
    ddb.put_item(TableName=ddb_table_name, Item={
                 'channel_name': {'S': kvs_channel_name}, 'channel_arn': {'S': channel_arn}})

    # 3. Check IAM if master and viewer policies are created, if not create
    master_policy_name = kvs_channel_name + '-master'
    master_policy_arn = 'arn:aws:iam::' + \
        account_id + ':policy/' + master_policy_name
    viewer_policy_name = kvs_channel_name + '-viewer'
    viewer_policy_arn = 'arn:aws:iam::' + \
        account_id + ':policy/' + viewer_policy_name
    master_role_name = master_policy_name
    viewer_role_name = viewer_policy_name

    try:
        iam.get_policy(PolicyArn=master_policy_arn)

    except botocore.exceptions.ClientError as err:
        print('No policy.. creating policy' + str(err))
        master_policy_json = None
        with open(master_policy_file, 'r') as myfile:
            master_policy_json = myfile.read()
        master_policy_json = master_policy_json.replace(
            "{channel_arn}", channel_arn)
        iam.create_policy(PolicyName=master_policy_name,
                          PolicyDocument=master_policy_json)

    # This is identical to the above block and can be refactored
    try:
        iam.get_policy(
            PolicyArn=viewer_policy_arn)

    except botocore.exceptions.ClientError as err:
        print('No policy.. creating policy' + str(err))
        viewer_policy_json = None
        with open(viewer_policy_file, 'r') as myfile:
            viewer_policy_json = myfile.read()
        viewer_policy_json = viewer_policy_json.replace(
            "{channel_arn}", channel_arn)
        iam.create_policy(PolicyName=viewer_policy_name,
                          PolicyDocument=viewer_policy_json)

    # 4. Check if roles exists - may be need to reverse this logic to check for role first
    role_policy_json = None
    with open(trust_policy_file, 'r') as myfile:
        role_policy_json = myfile.read()
    role_policy_json = role_policy_json.replace('{accountId}', account_id)
    try:
        iam.get_role(
            RoleName=master_role_name)

    except botocore.exceptions.ClientError as err:
        print('No role.. creating role' + str(err))
        iam.create_role(RoleName=master_role_name,
                        AssumeRolePolicyDocument=role_policy_json)
        iam.attach_role_policy(
            RoleName=master_role_name,
            PolicyArn=master_policy_arn
        )

    try:
        iam.get_role(
            RoleName=viewer_role_name)

    except botocore.exceptions.ClientError as err:
        print('No role.. creating role' + str(err))
        iam.create_role(RoleName=viewer_role_name,
                        AssumeRolePolicyDocument=role_policy_json)
        iam.attach_role_policy(
            RoleName=viewer_role_name,
            PolicyArn=viewer_policy_arn
        )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "channelName": kvs_channel_name,
        }),
    }
