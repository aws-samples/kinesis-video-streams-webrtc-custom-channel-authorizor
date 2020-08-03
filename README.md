# Amazon Kinesis Video Streams WebRTC Custom Authorizor with AWS Security Token Service(STS)

## Summary

[Amazon Kinesis Video Streams for WebRTC](https://docs.aws.amazon.com/kinesisvideostreams-webrtc-dg/latest/devguide/kvswebrtc-how-it-works.html) is a fully managed AWS service that supports thousands of simultaneous video chats, and frees developers from having to procure, set up and maintain their own media servers. This solution allows you to build a basic browser-based video chat application.

## Description

This sample demonstrates how to build a custom authorizor solution which can be used to control access to signalling channels and build a channel re-use pattern for Amazon Kinesis Video Streams for WebRTC using a serverless [AWS SAM](https://aws.amazon.com/serverless/sam/) application consisting of resources built using Amazon API Gateway, AWS Lambda, Amazon Cognito, Amazon DynamoDB and AWS Security Token Service(STS).

Kinesis Video Streams WebRTC signalling channels are [priced](https://aws.amazon.com/kinesis/video-streams/pricing/) on the Active signaling channels (per channel per month) dimension.

For use-cases which require a dedicated channel for only a short duration with ephemeral users for instance Know Your Customer(KYC) for Fintech companies, game streaming or any short lived video chat use case, re-using signalling channels can lead to a significant cost benefit.

The project consists of a REST API using API Gateway with four endpoints:

- **/getChannel -** This endpoint can be used to get a channel name and build re-use logic based on the business application for channel re-use

Response:

```
{ "channelName": "kvs-signalling-channel-1595838155" }
```

- **/getMasterCredentials/{channelName} -** Given the channel name get temporary credentials scoped to the signalling channel with minimum access required to establish connection as master. The temporary credentials are valid for 900 seconds and can be changed as per requirement. This method will need to be updated to accept a pre-defined shared id between the master and viewer to discover the same signalling channel or the channel name will need to be shared externally using some application mechanism

Response:

```
{
  "masterRoleArn": "arn:aws:iam::**********:role/kvs-signalling-channel-1595838155-master",
  "channelName": "kvs-signalling-channel-1595838155",
  "acessKeyId": "**********",
  "secretAccessKey": "******************",
  "sessionToken": "******************"
}
```

- **/getViewerCredentials/{channelName} -** Given the channel name get temporary credentials scoped to the signalling channel with minimum access required to establish connection as viewer. The temporary credentials are valid for 900 seconds and can be changed as per requirement

Response:

```
{
  "masterRoleArn": "arn:aws:iam::**********:role/kvs-signalling-channel-1595838155-viewer",
  "channelName": "kvs-signalling-channel-1595838155",
  "acessKeyId": "**********",
  "secretAccessKey": "******************",
  "sessionToken": "******************"
}
```

- **/endSessions/{channelName} -** uses the STS [rovoke temporary security credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_revoke-sessions.html) mechanism to revoke access to previously distributed tokens

```
{
  "message": "All sessions prior to 2020-07-27T08:45:42.083464+00:00 revoked for master and viewer for channel : kvs-signalling-channel-1595838155"
}
```

## TO DO

- API Gateway security using Cognito/lambda authorizor
- Re-use logic for DynamoDB

## Deploy the application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools.

- SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3 installed](https://www.python.org/downloads/)
- Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided --capabilities CAPABILITY_NAMED_IAM
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

- **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
- **AWS Region**: The AWS region you want to deploy your app to.
- **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
- **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modified IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
- **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

## Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

```bash
app$ sam build --use-container
```

The SAM CLI installs dependencies defined in `kvs-webrtc-channel-manager/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
app$ sam local invoke GetChannelFunction --event events/event.json
```

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

```bash
sam-app$ sam local start-api
sam-app$ curl http://localhost:3000/
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. The `Events` property on each function's definition includes the route and method for each path.

```yaml
Events:
  HelloWorld:
    Type: Api
    Properties:
      Path: /getChannel
      Method: get
```

## Add a resource to your application

The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam-app$ sam logs -n HelloWorldFunction --stack-name kvs-webrtc-channel-manager --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Unit tests

Tests are defined in the `tests` folder in this project. Use PIP to install the [pytest](https://docs.pytest.org/en/latest/) and run unit tests.

```bash
sam-app$ pip install pytest pytest-mock --user
sam-app$ python -m pytest tests/ -v
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name kvs-webrtc-channel-manager
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
