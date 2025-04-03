import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {
  DockerImageFunction,
  DockerImageCode,
  FunctionUrlAuthType,
  Architecture,
  HttpMethod,
} from "aws-cdk-lib/aws-lambda";
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';

export class CdkBackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);



    // Lambda function (image) to crawl web sites
    const crawlerImageCode = DockerImageCode.fromImageAsset("../adiutor/crawl4ai", {
      cmd: ["src.app.handler"],
    });
    const crawlerFunction = new DockerImageFunction(this, "CrawlerFunction", {
      code: crawlerImageCode,
      memorySize: 1024,
      timeout: cdk.Duration.seconds(180)
    });
    


    // Function to handle the API requests
    const apiImageCode = DockerImageCode.fromImageAsset("../adiutor/server", {
      cmd: ["src.app.handler"],
    });

    const apiFunction = new DockerImageFunction(this, "ApiFunction", {
      code: apiImageCode,
      memorySize: 1024,
      timeout: cdk.Duration.seconds(360),
      architecture: Architecture.X86_64,
      environment: {
        BUCKET_NAME: "backend-denspa",
        BACKEND_ENV: "prod",
        CRAWLER_LAMBDA_NAME: crawlerFunction.functionName,
      },
    });

    apiFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: ['*'], // Allows invoking any Bedrock model
    }));

    const bucket = new s3.Bucket(this, 'BackendDenspa', {
      bucketName: 'backend-denspa',
    })

    bucket.grantReadWrite(apiFunction)
    crawlerFunction.grantInvoke(apiFunction);

    // Public URL for the API function.
    const apiFunctionUrl = apiFunction.addFunctionUrl({
      authType: FunctionUrlAuthType.NONE,
      cors: {
        allowedHeaders: ["*"],
        allowedMethods: [HttpMethod.ALL],
        allowedOrigins: ["*"],
        exposedHeaders: ["*"]
      }
    });


    // Output the URL for the API function.
    new cdk.CfnOutput(this, "ApiUrl", {
      value: apiFunctionUrl.url,
    });

  }

}
