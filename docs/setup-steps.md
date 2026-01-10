# SmartVault Backup – Setup Guide

This document walks through the full deployment process for the SmartVault automated EC2 backup system.

---

## 1. Create the Lambda Function

1. Open AWS Console → Lambda → Create Function  
2. Use:
   - Name: `smart-vault-backup`
   - Runtime: Python 3.12+
3. Create IAM Execution Role with least-privilege policy (see iam-policy.json)
4. Paste the Lambda code into the function
5. Deploy

---

## 2. Add Environment Variables

Inside Lambda → Configuration → Environment variables:

| Key            | Value |
|----------------|-------|
| SNS_TOPIC_ARN  | arn:aws:sns:REGION:ACCOUNT_ID:smartvault-backup-alerts |
| RETENTION_DAYS | 7     |

Click **Save**.

---

## 3. Create SNS Topic

1. Go to SNS → Create topic  
2. Name: `smartvault-backup-alerts`  
3. Create subscription:
   - Protocol: Email
   - Endpoint: your email  
4. Confirm subscription in your inbox

---

## 4. Tag EC2 Instances for Backup

Go to EC2 → Instances → Select instance → Tags:

| Key     | Value |
|---------|--------|
| Backup  | true   |

Only instances with this tag will be backed up.

---

## 5. Create EventBridge Scheduled Rule

1. Go to **EventBridge → Rules → Create Rule**
2. Name: `smart-vault-daily-backup`
3. Type: **Schedule**
4. Schedule pattern (daily at UTC 1 AM): cron(0 1 * * ? *)
5. Add target → Lambda function → choose `smart-vault-backup`
6. Create rule

---

## 6. Test the System

### Manual Test
In Lambda → Test: {
"action": "manual-trigger"
}


Click **Test**.

### Verify Results:
- Snapshots appear in EC2 → Snapshots
- SNS email sends summary
- CloudWatch logs show details

---

## 7. Automatic Cleanup

Snapshots older than the configured RETENTION_DAYS are removed automatically in the Lambda script.

---

## 8. Monitoring

- CloudWatch Logs → `/aws/lambda/smart-vault-backup`
- SNS Emails for:
  - Success
  - No instances found
  - Errors
- EventBridge rule shows last trigger time

---

## 9. Cleanup (to avoid AWS charges)

If you want to turn off everything:

- Delete EventBridge rule
- Delete Lambda function
- Delete SNS topic + subscriptions
- Delete IAM execution role
- Delete EBS snapshots
- Delete CloudWatch log group

---

SmartVault is now fully deployed! 🚀




