# OVOS-utils

collection of simple utilities for use across the mycroft ecosystem

## Install

```bash
pip install ovos_utils
```

## Commandline scripts
### ovos-logs
 Small helper tool to quickly navigate the logs, create slices and quickview errors  

---------------
- **ovos-logs slice [options]**

  **Slice logs of a given time period. Defaults on the last service start (`-s`) until now (`-u`)**

  _Different logs can be picked using the `-l` option. All logs will be included if not specified._  
  _Optionally the directory where the logs are stored (`-p`) and the file where the slices should be dumped (`-f`) can be specified._
    

  _[ex: `ovos-logs slice`]_  
  <sup>_Slice all logs from service start up until now._</sup>
  
  _[ex: `ovos-logs slice -s 17:05:20 -u 17:05:25`]_  
  <sup>_Slice all logs from 17:05:20 until 17:05:25._</sup>    
  <sup>_**no logs in that timeframe in other present logs_</sup>
  <img width="1898" alt="Screenshot 2023-12-25 185004" src="https://github.com/emphasize/ovos-utils/assets/25036977/c7918bd6-0e13-46af-8016-55486b9a786e">  
   
  _[ex: `ovos-logs slice -s 17:05:20 -u 17:05:25 -l skills`]_  
  <sup>_Slice skills.log from 17:05:20 until 17:05:25._</sup>
  
  _[ex: `ovos-logs slice -s 17:05:20 -u 17:05:25 -f ~/testslice.log`]_  
  <sup>_Slice the logs from 17:05:20 until 17:05:25 on all log files and dump the slices in the file ~/testslice.log (default: `~/slice_<timestamp>.log`)._</sup>
  <img width="1246" alt="Screenshot 2023-12-25 190732" src="https://github.com/emphasize/ovos-utils/assets/25036977/dda99d8a-2739-4872-b81a-f44902b43d7d">
--------------

- **ovos-logs list [-e|-w|-d|-x] [options]**

  **List logs by severity (error/warning/debug/exception). A log level has to be specified - more than one can be listed**  

  _A start and end date can be specified using the `-s` and `-u` options. Defaults to the last service start until now._  
  _Different logs can be picked using the `-l` option. All logs will be included if not specified._  
  _Optionally, the directory where the logs are stored (`-p`) and the file where the slices should be dumped (`-f`) can be passed as arguments._  

  _[ex: `ovos-logs list -x`]_  
  <sup>_List the logs with level EXCEPTION (plus tracebacks) from the last service start until now._</sup>
  <img width="992" alt="Screenshot 2023-12-25 184321" src="https://github.com/emphasize/ovos-utils/assets/25036977/da8be23a-4268-4647-8dd3-32c1a889440c">
  
  _[ex: `ovos-logs list -w -e -s 20-12-2023 -l bus -l skills`]_  
  <sup>_List the logs with level WARNING and ERROR from the 20th of December 2023 until now from the logs bus.log and skills.log._</sup>
  <img width="1898" alt="Screenshot 2023-12-25 173739" src="https://github.com/emphasize/ovos-utils/assets/25036977/c5703195-4393-4989-ae40-b37638438c92">
---------------------

- **ovos-logs reduce [options]**
  
  **Downsize logs to a given size (in bytes) or remove entries before a given date.**  
    
  _Different logs can be included using the `-l` option. If not specified, all logs will be included._  
  _Optionally the directory where the logs are stored (`-p`) can be specified._  
  
  _[ex: `ovos-logs reduce`]_  
  <sup>_Downsize all logs to 0 bytes_</sup>  

  _[ex: `ovos-logs reduce -s 1000000`]_  
  <sup>_Downsize all logs to ~1MB (latest logs)_</sup>  

  _[ex: `ovos-logs reduce -d "1-12-2023 17:00"`]_  
  <sup>_Downsize all logs to entries after the specified date/time_</sup>  

  _[ex: `ovos-logs reduce -s 1000000 -l skills -l bus`]_  
  <sup>_Downsize skills.log and bus.log to ~1MB (latest logs)_</sup>  

---------------------

- **ovos-logs show -l [servicelog]**

  **Show logs**

  _[ex: `ovos-logs show -l bus`]_  
  <sup>_Show the logs from bus.log._</sup>  

  _[ex: wrong servicelog]_  
  <sup>_**logs shown depending on the logs present in the folder_</sup>

