from aws_cdk import (
    core,
    aws_logs,
    aws_dynamodb as ddb,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigw
)
from aws_cdk.core import Duration
from aws_cdk.aws_dynamodb import Attribute, AttributeType
from pathlib import Path

class SmartnumbersTestStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.prefix = ('infra-smartnumbers').lower()
        self.root_dir = str(Path(__file__).parents[1])
        print(self.root_dir)
        self.log_retention = aws_logs.RetentionDays.ONE_WEEK
        
        # ////////////////////////////////////////////////////////////////////////////////////////////
        """ S3 Buckets """

        # output bucket
        bucket_name = self.prefix + '-output-bucket'
        output_bucket = s3.Bucket(self, bucket_name,
                                bucket_name=bucket_name,
                                removal_policy=core.RemovalPolicy.DESTROY
                                )
                                
        # ////////////////////////////////////////////////////////////////////////////////////////////
        """ Dynamo Tables """
        self.tables = []

        calls_table_name = self.prefix + '-calls'
        calls_table = ddb.Table(
            self, calls_table_name,
            table_name=calls_table_name,
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            sort_key=Attribute(name="number", type=AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY,
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )
        self.tables.append(calls_table_name)

        operators_table_name = self.prefix + '-operators'
        operators_table = ddb.Table(
            self, operators_table_name,
            table_name=operators_table_name,
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            sort_key=Attribute(name="prefix", type=AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY,
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST
        )
        self.tables.append(operators_table_name)

        # ////////////////////////////////////////////////////////////////////////////////////////////
        """ Lambdas """
        self.lambdas = []

        api_receiver_lambda = create_lambda(self, 'api_receiver')
        self.lambdas.append(api_receiver_lambda)
        calls_table.grant_read_write_data(api_receiver_lambda)
        operators_table.grant_read_write_data(api_receiver_lambda)

        matcher_call_operator_lambda = create_lambda(self, 'matcher_call_operator')
        self.lambdas.append(matcher_call_operator_lambda)
        calls_table.grant_read_write_data(matcher_call_operator_lambda)
        operators_table.grant_read_data(matcher_call_operator_lambda)
        output_bucket.grant_read_write(matcher_call_operator_lambda)

        # ////////////////////////////////////////////////////////////////////////////////////////////
        """ API Gateways """

        api_endpoint = apigw.LambdaRestApi(self, self.prefix + '-gateway',
                                           handler=api_receiver_lambda,
                                           proxy=False)

        apigateway_integration_input = apigw.LambdaIntegration(api_receiver_lambda)
        apigateway_endpoint_input = api_endpoint.root.add_resource('input_data')
        apigateway_endpoint_input.add_method('POST', apigateway_integration_input)

        apigateway_integration_input = apigw.LambdaIntegration(matcher_call_operator_lambda)
        apigateway_endpoint_trigger = api_endpoint.root.add_resource('event_trigger')
        apigateway_endpoint_trigger.add_method('POST', apigateway_integration_input)



def create_lambda(self, lambda_folder_name, function_name_override=None, timeout_seconds=60, memory_size=128, handler_override=None, description=None, log_retention=None):
    function_name = function_name_override or lambda_folder_name
    lambda_name = function_name+'-lambda'
    new_lambda = _lambda.Function(
        self, lambda_name,
        runtime=_lambda.Runtime.PYTHON_3_7,
        code=_lambda.Code.asset(self.root_dir + '/lambdas/' + lambda_folder_name),
        function_name=self.prefix + '-' + lambda_name,
        handler=handler_override or function_name + '.handler',  # set to handler to avoid aws default
        log_retention=log_retention or self.log_retention,
        description=description or lambda_folder_name + ' Lambda Function',
        timeout=Duration.seconds(timeout_seconds),
        memory_size=memory_size
    )
    return new_lambda
