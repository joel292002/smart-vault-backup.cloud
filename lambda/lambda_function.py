import boto3
import os
from datetime import datetime, timedelta

ec2 = boto3.client("ec2")
sns = boto3.client("sns")

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", 7))

def lambda_handler(event, context):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # 1. Find instances with Backup=true
    instances = ec2.describe_instances(
        Filters=[{"Name": "tag:Backup", "Values": ["true"]}]
    )["Reservations"]

    if not instances:
        send_sns("No instances found with Backup=true — skipping snapshot.")
        return {"message": "No instances to back up."}

    created = []
    deleted = []

    for reservation in instances:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]

            snap = ec2.create_snapshot(
                VolumeId=instance["BlockDeviceMappings"][0]["Ebs"]["VolumeId"],
                Description=f"SmartVault snapshot of {instance_id}"
            )

            ec2.create_tags(
                Resources=[snap["SnapshotId"]],
                Tags=[{"Key": "CreatedOn", "Value": today}]
            )

            created.append(snap["SnapshotId"])

    # 2. Cleanup old snapshots
    old_snaps = ec2.describe_snapshots(
        OwnerIds=["self"],
        Filters=[{"Name": "tag:CreatedOn", "Values": ["*"]}]
    )["Snapshots"]

    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)

    for snap in old_snaps:
        created_on = datetime.strptime(
            next(t["Value"] for t in snap["Tags"] if t["Key"] == "CreatedOn"),
            "%Y-%m-%d"
        )

        if created_on < cutoff:
            ec2.delete_snapshot(SnapshotId=snap["SnapshotId"])
            deleted.append(snap["SnapshotId"])

    # 3. SNS Summary
    email = f"""
SmartVault Backup Summary
-------------------------
Created snapshots: {created}
Deleted old snapshots: {deleted}
"""

    send_sns(email)
    return {"created": created, "deleted": deleted}

def send_sns(message):
    sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="SmartVault Backup Notification")
