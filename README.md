# API specs for Nutanix Objects

The API JSON is copied over from AWS S3 API specs
https://github.com/aws/aws-sdk-cpp/blob/1.11.485/tools/code-generation/api-descriptions/s3-2006-03-01.normal.json

Further, any unspecified operations and fileds have been marked with `"isNtnxSupported":false` so that to exclude them from the documentation. The fields aren't deleted to support the future plan of using the same JSON to generate the custom SDK for Nutanix Objects, so that any client using those unsupported fields will not get compile-time/link-time errors. Any unsupported fields reaching to the backend will be either invite errors from the Nutanix Objects server or simply ignored.

Tests performed:
1. Custom AWS C++ SDK generation using the JSON using AWS's code generation tool.
2. Compilation of the generated SDK with thirdparty and poseidon.
3. s3_api_test UT execution with the custom SDK generated.
4. AWS CLI model generation using the JSON.
5. aws_nutanix_test UI execution with the custom AWS CLI model.
