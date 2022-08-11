


To run XSBench Baseline:
------------------------------------------------------------------------------------

Go the directory: /XSBench-baseline/openmp-threading
Execute the below command to submit a job at Theta:    
qsub baseline_script.sh

To change the problem size change : "-s small" to use smaller problem size and  "-s large" to use larger problem size in the below command:
aprun -n 4 -N 1 -cc depth -d 64 -j 1 ./XSBench -s small




To run ytopt+libEnsemble+XSBench:
------------------------------------------------------------------------------------

Go the directory: ~/libe-xsbench
Execute the below command to submit a job to run ytopt+libEnsemble+XSBench at Theta:    
./runs.cob

This will create a submission script and submit the job in the Theta.







To run sq4lite Baseline:
------------------------------------------------------------------------------------

Go the directory:   ~/sw4lite-baseline/optimize_mp_c_theta
Execute the below command to submit a job at Theta:    

qsub baseline_submission_script.sh

Input size used is: LOH.1-h100.in 




To run ytopt+libEnsemble+sq4lite:
------------------------------------------------------------------------------------

Go the directory: ~/libe-sw4lite/sw4lite
Execute the below command to submit a job to run ytopt+libEnsemble+XSBench at Theta:    
./runs2_for_default_queue.cob

This will create a submission script and submit the job in the Theta default queue.



