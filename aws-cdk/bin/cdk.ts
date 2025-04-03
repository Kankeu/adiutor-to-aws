#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { CdkBackendStack } from '../lib/cdk-backend-stack';
import { CdkFrontendStack } from '../lib/cdk-frontend-stack';

const app = new cdk.App();
new CdkBackendStack(app, 'CdkBackendStack', {});

new CdkFrontendStack(app, 'CdkFrontendStack', {});
