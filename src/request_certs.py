import boto3
import yaml
from time import sleep


def get_data():
    with open('data.yaml') as f:
        data = yaml.load(f)
    return data


def request_certificate(data, region):
    acm_conn = boto3.client('acm',
                          region_name=region)
    response = acm_conn.request_certificate(
        DomainName=data['domains'][0],
        ValidationMethod='DNS',
        SubjectAlternativeNames=data['domains'][1:]
        )
    return response


def get_cert_data(region, cert_arn):
    acm_conn = boto3.client('acm',
                          region_name=region)
    response = acm_conn.describe_certificate(
        CertificateArn=cert_arn
        )
    return response


def set_route53_record(region, domain, record_name, record_value):
    print (region, domain, record_name, record_value)
    route53_conn = boto3.client('route53')
    response = route53_conn.list_hosted_zones_by_name(
        DNSName='infra.stylight.net')
    zone_id = response['HostedZones'][0]['Id'].split('/hostedzone/')[1]
    route53_conn = boto3.client('route53')
    route53_conn.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            'Comment': 'Create DNS Validation for AWS SSL Certificate',
            'Changes': [
                {
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': 'CNAME',
                        'TTL': 300,
                        'ResourceRecords': [
                            {
                                'Value': record_value
                            }
                        ]
                    }
                }
            ]
        }
    )


def get_pending_certs(region):
    acm_conn = boto3.client('acm',
                          region_name=region)
    reponse = acm_conn.list_certificates(
        CertificateStatuses=['PENDING_VALIDATION']
    )
    return reponse


def main(data=get_data()):
    for region in data['regions']:
        cert_request = request_certificate(data, region)
        sleep(5)
        cert_data = get_cert_data(region, cert_arn=cert_request['CertificateArn'])
        for domain in cert_data['Certificate']['DomainValidationOptions']:
            set_route53_record(region, domain['DomainName'], domain['ResourceRecord']['Name'], domain['ResourceRecord']['Value'])
    # for region in data['regions']:
    #     pending_certs = get_pending_certs(region)
    # print (pending_certs)


if __name__ == "__main__":
    main()
