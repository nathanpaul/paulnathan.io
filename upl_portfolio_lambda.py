import boto3
import StringIO
from botocore.client import Config
import zipfile

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:092746047212:deploy_portfolio_topic')
    try:
        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        portfolio_bucket = s3.Bucket('portfolio.paulnathan.io')
        build_bucket = s3.Bucket('portfoliobuild.paulnathan.io')

        portfolio_zip = StringIO.StringIO()

        build_bucket.download_fileobj('portfoliobuild.zip', portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm)
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print "Hello world"
        topic.publish(Subject="Portfolio Deployed", Message="Portfolio deployed!")
    except:
        topic.publish(Subject="FAILURE", Message="You fucked up a-aron")
        raise

    return "Welcome to Lambda!"
