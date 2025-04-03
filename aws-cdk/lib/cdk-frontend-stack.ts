import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';


import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as cloudfront_origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';

import { execSync } from 'child_process';

export class CdkFrontendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    try {
      const backend = require("../backend.json")
      console.log(`cd ../adiutor/client && npm i && export VITE_API_URL=${backend.CdkBackendStack.ApiUrl} && export VITE_ENV=prod && npm run build-only`, backend)
      execSync(`cd ../adiutor/client && npm i && export VITE_API_URL=${backend.CdkBackendStack.ApiUrl} && export VITE_ENV=prod && npm run build-only`, { stdio: 'inherit' })
      execSync("pwd", { stdio: 'inherit' })
    } catch (error) {
      return
    }


    // S3 Bucket for hosting the Vue.js application
    const siteBucket = new s3.Bucket(this, 'VueHostingBucket', {
      websiteIndexDocument: 'index.html',
      publicReadAccess: true,
      autoDeleteObjects: true,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: false,
        blockPublicPolicy: false,
        ignorePublicAcls: false,
        restrictPublicBuckets: false
      }),
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      versioned: true,
    });

    // CloudFront distribution for serving content
    const distribution = new cloudfront.Distribution(this, 'VueDistribution', {
      defaultBehavior: {
        origin: new cloudfront_origins.S3Origin(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      defaultRootObject: 'index.html',
    });

    new s3deploy.BucketDeployment(this, 'UploadVueSource', {
      sources: [s3deploy.Source.asset('../adiutor/client/dist')], // Upload local folder
      destinationBucket: siteBucket,
      distribution: distribution,
      distributionPaths: ["/*"]
    });


    // Define the bucket policy
    const bucketPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      principals: [new iam.AnyPrincipal()], // Allows access from anyone
      actions: ['s3:*'], // Grants all actions on the bucket
      resources: [
        siteBucket.bucketArn,
        `${siteBucket.bucketArn}/*`,
      ],
      conditions: {
        Bool: {
          'aws:SecureTransport': true
        },
      },
    });

    // Attach the policy to the bucket
    siteBucket.addToResourcePolicy(bucketPolicy);


    // Output CloudFront URL
    new cdk.CfnOutput(this, 'CloudFrontURL', {
      value: distribution.domainName,
    });
  }


}
