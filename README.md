# 🚀 SmartVault – Automated EC2 Backup System on AWS  
A fully serverless, tag-based EC2 backup automation using **AWS Lambda**, **EBS Snapshots**, **EventBridge Schedules**, **SNS Alerts**, and **CloudWatch Logging**.

SmartVault automatically:  
✔ Scans for EC2 instances tagged with `Backup=true`  
✔ Creates EBS snapshots  
✔ Tags snapshots with metadata  
✔ Cleans up old snapshots (retention policy)  
✔ Sends success/failure notifications to SNS  
✔ Runs daily via EventBridge  

---

## 🏗 Architecture

SmartVault’s architecture includes:

- AWS Lambda → Executes the backup logic  
- Amazon EC2 → Instances marked for backup using tags  
- Amazon EBS Snapshots → Incremental backups  
- EventBridge Rule → Daily scheduling  
- SNS Topic → Alerts sent to email  
- CloudWatch Logs → Monitor success/failure  

(Place your architecture diagram here if available)

---

## 📌 Features

- 🏷 Tag-based automation (`Backup=true`)  
- 💾 Incremental EBS snapshots  
- 🔁 Automatic cleanup of old snapshots  
- 🔔 SNS email notifications  
- 🕒 Runs on a customizable schedule  
- ☁️ Fully serverless — no servers required  
- 🔐 Least-privilege IAM permission model

---



---

## 🧠 How It Works

1. EventBridge triggers Lambda daily  
2. Lambda searches for instances with:  
   `Backup = true`  
3. For each instance:  
   - Creates a snapshot  
   - Tags snapshot with metadata  
4. Deletes snapshots older than retention period  
5. Sends an SNS email summarizing:  
   - Created snapshots  
   - Deleted snapshots  
   - Errors or skipped events  

---

## 📝 Lambda Code (Place inside lambda/lambda_function.py)

```python
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

```
---
##🔧 IAM Policy (Least Privilege)

Place this inside docs/iam-policy.json

{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["ec2:DescribeInstances"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["ec2:CreateSnapshot","ec2:DeleteSnapshot","ec2:DescribeSnapshots","ec2:CreateTags"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["sns:Publish"], "Resource": "*" }
  ]
}
---

##📅 EventBridge Schedule

Example cron to run every day at 1 AM UTC:

cron(0 1 * * ? *)
---

##📨 SNS Alerts

Alerts sent include:

Snapshot creation success

No instances found (backup skipped)

Cleanup of old snapshots

Any unexpected errors
---

##🧪 Test Event

Use this test event in the Lambda console:

{
  "action": "manual-trigger"
}

---


##🧹 Cleanup & Cost Control

To avoid charges, delete:

Lambda function

EventBridge rule

SNS topic

Snapshots

CloudWatch Log Group

IAM role
