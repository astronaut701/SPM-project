# SPM-project
Server performance monitor project

This software functions in two components. It will monitor CPU usage and Memory usage as a percentage, the last minute of system load value, and the total Disk I/O and Network I/O in both directions.

The client side simply needs to install the required packakges in the requirements.txt (alternatively, just install the requests and matplotlib packages manually) file, and run `multidashboard.py`.

Once it opens, add a server using the buttons on the top right, pop in the IP address and port number (default 5050), see the thresholds to how much CPU and RAM is desired to be have the limit to, hit the "Start Monitoring" button.

<p align="center">
<img width="300" height="400" alt="image" src="https://github.com/user-attachments/assets/4994d692-8d9f-4f53-a506-1c0768792e2e" />

<img width="300" height="400" alt="image" src="https://github.com/user-attachments/assets/16fff765-073f-4d7e-86da-960ae809e640" />

<img width="300" height="400" alt="image" src="https://github.com/user-attachments/assets/f998f545-59ac-423b-8ca4-89495763518f" />
</p>

Data will begin to populate. Once you are done, you can simply hit the "Stop Monitoring" button to close the connection and finish. Need to keep an eye on more than one server? Simply add another server and select the new tab and flip back and forth between the servers you have added. You can also delete servers as desired, if it's no longer needed to keep an eye on said servers. Finished with monitoring? Just close the window.

The server side functions in a few components.

Firstly, it is expected that again, the required packages in the requirements.txt (again, you may just install flask and psutil packages manually), and to create a `monitor` user (and group, if not made along with the `monitor` user), as well as a directory for the user (`/opt/monitor` is the default) to store the agent.py and collector.py scripts, as well as the checkscript.sh bash script.

To automate the running of agent.py and collector.py, you may add the contents of crontab.txt to root's crontab. (Use sudo if needed)

If you need to change the port number, you may do so by editing agent.py and changing the last line's port variable to any valid port number not already used by anything else.

Provided that the port is accessable to the outside, you should now be able to connect your client.
