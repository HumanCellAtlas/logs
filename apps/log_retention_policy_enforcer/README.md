# Log retention policy enforcer

Add cron lambda that enforces log retention policy.

This lambda runs every two days and checks the retention policies of all
log groups. If the log group retention policy is not specified in the
lambda's configuration file, it sets it to a default TTL of 90 days. If
the log group retention policy is specified, it sets it to that TTL.
