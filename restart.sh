# Config
run_cmd="python main.py"
module_name="kuke"

# Logic
pid_file=$module_name".pid"
if [ -f ./$pid_file ]; then
	pid=`cat $pid_file`
	if [ -d /proc/$pid ]; then
		echo "kill $pid"
		kill -9 $pid
	fi
fi
nohup $run_cmd >>$module_name".log" 2>&1 & 
echo $! >$pid_file
