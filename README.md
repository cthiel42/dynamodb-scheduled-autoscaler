# DynamoDB Scheduled Autoscaler

### Overview & Use Cases
This is not a full blown replacement for DynamoDB autoscaling, but something that can be paired with DynamoDB autoscaling to greatly enhance it's functionality. In its current state, this Lambda can be used to adjust the Minimum and Maximum Read/Write unit capacities for DynamoDB on a set schedule. This is somewhat similar to Autoscaling Scheduled Actions, but allows you to specify your scaling rules in a live configuration file.

The most common use case for this would be when you have a very predictable spike in read/writes, and you want to scale up prior to that spike so you don't get any throttled requests. In this case, you might create an interval where the minimum capacity units greatly increase to handle the burst, and then sometime after the burst or even during the burst, you can end that interval to let the capacities go back to their default. Since this is best if it's paired with DynamoDB's autoscaling, reducing capacities before the burst is over won't cause provisioned capacities to be reduced, as they'll continue to track the target utilization specified in the autoscaling settings.

### Setup & Configuration
This can be run as a Lambda function with an EventBridge rule as the trigger. My recommendation would be to not run the Lambda any more frequently than every 5 minutes. DynamoDB tables can take several minutes to update with new autoscale settings, so it's not useful to be running on a more frequent interval than roughly 5 minutes. The Lambda will also need `application-autoscaling:DescribeScalableTargets` and `application-autoscaling:RegisterScalableTarget` permissions to update table capacities.

The configuration file takes in a JSON array of settings. Each setting is for a specific table or index, and can contain several different scaling intervals. All times in the configuration file should be specified in UTC time. See the included config file for examples and a template.

Configurations that need to be included in a setting:
- type: table|index (str)
- resource: scaling policy resource (str)
- defaultReadMin: minimum read capacity to default to if no intervals are active (int)
- defaultReadMax: maximum read capacity to default to if no intervals are active (int)
- defaultWriteMin: minimum write capacity to default to if no intervals are active (int)
- defaultWriteMax: maximum write capacity to default to if no intervals are active (int)
- intervals
  - timeStart: time the interval settings should take effect in UTC and format of HH:MM:SS (str)
  - timeEnd: time the interval settings should discontinue taking effect in UTC and format of HH:MM:SS (str)
  - readMin: (Optional) minimum read capacity to set while interval is in effect (int)
  - readMax: (Optional) maximum read capacity to set while interval is in effect (int)
  - writeMin: (Optional) minimum write capacity to set while interval is in effect (int)
  - writeMax: (Optional) maximum write capacity to set while interval is in effect (int)
