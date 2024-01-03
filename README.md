# A simple program to determine server status from logs (a tested from Fixpoint)

## Test Environment(動作環境)
- Python 3.10.9 64-bit

## How to use(使用方法)

Simply run the log monitor with the following command.

```
python3 RunlogMonitor.py
```
And run the log generator with the following command.
```
python3 RunlogGenerator.py
```

### Note(注意)

This program is divided into two parts. One is the log generator, and the other is the log monitor.
The config.json is for the log generator. And the monitor_config.json is for the log monitor.

### Config(設定)

The config.json is for the log generator.
```
{
    "ip_addresses": [
        {
            "ip": "10.20.30.1",
            "expected_ping": 20,
            "packet_loss": 85
        }
    ],
    "interval": {
        "generate": 10,
        "store": 100
    },
    "timeout_switch": {
        "10.20.30.0": false
    }
}
```
At here, interval is the interval of generating logs. And the unit is second.
It is worth mentioning that the log generator would automatically close after 10 minutes

The monitor_config.json is for the log monitor.
```
{
    "runtime_parameter":{
        "timeout_times_threshold": 10,
        "timeout_ping_threshold": 100
    },
    "dat_file": "./log_timeout.dat",
    "output":{
        "path": "./output/",
        "filename": "monitorlog.dat"
    }
}
```
Except for the parameters listed here, other parameter functions are not implemented.

## Examples and results(例と結果)

The log file can be extended forever. The example results use the log_timeout.dat file.
The output files have been stored in ./output/

## Design ideas(設計のアイデア)

At first, I wanted to use multiple threads to simultaneously simulate log generation and detect timeouts in real time, but found that the amount of work was too large and finally focused on completing the initial functions.

I have the same idea as above in question 123. Record the log content through a dictionary list, and then judge it one by one. If a timeout occurs, record it temporarily until the IP is restored and clear the record.

Question 4 is more complicated. I used a tricky method. Assuming that the log content is coherent in time, then I will only record the number and time when the time changes and the content with the same IP prefix appears. In this way, no matter how many subnets there are Each IP record can be used to determine whether the entire subnet has timed out.

And all of this is based on the fact that I did not take the initiative to sort the contents of the log. That is to say, if the log itself needs to be re-sorted, other functions may need to be introduced.