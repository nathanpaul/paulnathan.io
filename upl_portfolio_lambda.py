import boto3
import StringIO
from botocore.client import Config
import zipfile
import mimetypes

def lambda_handler(event, context):
    mimetypes.init()
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:092746047212:deploy_portfolio_topic')
    location = {
        "bucketName": 'portfoliobuild.paulnathan.io',
        "objectKey": 'portfoliobuild.zip'
    }

    try:
        job = event.get("CodePipeline.job")
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        portfolio_bucket = s3.Bucket('portfolio.paulnathan.io')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = StringIO.StringIO()

        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                if nm.endswith('DS_Store'):
                    continue
                obj = myzip.open(nm)
                if nm.endswith('eot'):
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': 'application/vnd.ms-fontobject'})
                elif nm.endswith('woff2'):
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': 'font/woff2'})
                elif nm.endswith('otf'):
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': 'font/otf'})
                elif nm.endswith('woff'):
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': 'font/woff'})
                elif nm.endswith('less'):
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': 'text/css'})
                elif nm.endswith('ttf'):
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': 'application/octet-stream'})
                else:
                    print nm
                    portfolio_bucket.upload_fileobj(obj, nm,
                        ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0] })

                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print "Hello world"
        topic.publish(Subject="Portfolio Deployed", Message="Portfolio deployed!")
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="FAILURE", Message="You fucked up a-aron")
        raise

    return "Welcome to Lambda!"
