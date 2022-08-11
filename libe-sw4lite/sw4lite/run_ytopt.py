# SW4lite-libe run_ytopt.py file
 
"""
Runs libEnsemble to call the ytopt ask/tell interface in a generator function,
and the ytopt findRunTime interface in a simulator function.

Execute locally via one of the following commands (e.g. 3 workers):
   mpiexec -np 4 python run_ytopt_xsbench.py
   python run_ytopt_xsbench.py --nworkers 3 --comms local

The number of concurrent evaluations of the objective function will be 4-1=3.
"""

import os
import glob
import secrets
import numpy as np
import sys

# Import libEnsemble items for this test
from libensemble.libE import libE
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens as alloc_f
from libensemble.tools import parse_args, save_libE_output, add_unique_random_streams

from ytopt_obj import init_obj  # Simulator function, calls Plopper
from ytopt_asktell import persistent_ytopt  # Generator function, communicates with ytopt optimizer

import ConfigSpace as CS
import ConfigSpace.hyperparameters as CSH
from ytopt.search.optimizer import Optimizer

# Parse comms, default options from commandline
nworkers, is_manager, libE_specs, user_args_in = parse_args()
num_sim_workers = nworkers - 1  # Subtracting one because one worker will be the generator
'''
assert len(user_args_in), "learner, etc. not specified, e.g. --learner RF"
user_args = {}
for entry in user_args_in:
    if entry.startswith('--'):
        if '=' not in entry:
            key = entry.strip('--')
            value = user_args_in[user_args_in.index(entry)+1]
        else:
            split = entry.split('=')
            key = split[0].strip('--')
            value = split[1]

    user_args[key] = value

req_settings = ['learner','max-evals']
assert all([opt in user_args for opt in req_settings]), \
    "Required settings missing. Specify each setting in " + str(req_settings)
'''

# written by larson. Commented temporarily to check with Xingfu's part
# Set options so workers operate in unique directories
here = os.getcwd() + '/'
libE_specs['use_worker_dirs'] = True
libE_specs['sim_dirs_make'] = False  # Otherwise directories separated by each sim call
libE_specs['ensemble_dir_path'] = './ensemble_' + secrets.token_hex(nbytes=4)


#written by Xingfu
#THIS PART IS FROM SW4lite problem.py file
#HERE = os.path.dirname(os.path.abspath(__file__))

#here = os.path.dirname(os.path.abspath(__file__)) + '/'
#sys.path.insert(1, os.path.dirname(here)+ '/plopper')

from plopper import Plopper

# Copy or symlink needed files into unique directories
#libE_specs['sim_dir_symlink_files'] = [here + f for f in ['mmp.c', 'Materials.c', 'XSutils.c', 'XSbench_header.h', 'exe.pl', 'plopper.py', 'processexe.pl']]

#libE_specs['sim_dir_symlink_files'] = [here + f for f in ['../src/main.C', '../src/Sarray.C', '../src/Source.C', '../src/SuperGrid.C', '../src/GridPointSource.C', '../src/time_functions.C', '../src/EW_cuda.C', '../src/ew-cfromfort.C', '../src/EWCuda.C', '../src/CheckPoint.C', '../src/Parallel_IO.C', '../src/EW-dg.C', '../src/MaterialData.C', '../src/MaterialBlock.C', '../src/Polynomial.C', '../src/SecondOrderSection.C', '../src/Filter.C', '../src/TimeSeries.C', '../src/sacsubc.C', '../src/curvilinear-c.C', 'mmp.C', 'exe.pl', 'plopper.py', 'processexe.pl']]

libE_specs['sim_dir_symlink_files'] = [here + f for f in ['./src', './loh1', 'mmp.C', 'exe.pl', 'plopper.py', 'processexe.pl']]    #suggested by Dr. Xingfu


#libE_specs['sim_dir_symlink_files'] = [here + f for f in ['./src/main.C', './src/Sarray.C', './src/Source.C', './src/SuperGrid.C', './src/GridPointSource.C', './src/time_functions.C', './src/EW_cuda.C', './src/ew-cfromfort.C', './src/EWCuda.C', './src/CheckPoint.C', './src/Parallel_IO.C', './src/EW-dg.C', './src/MaterialData.C', './src/MaterialBlock.C', './src/Polynomial.C', './src/SecondOrderSection.C', './src/Filter.C', './src/TimeSeries.C', './src/sacsubc.C', './src/curvilinear-c.C', './src', './loh1', 'mmp.C', 'exe.pl', 'plopper.py', 'processexe.pl']]
# Declare the sim_f to be optimized, and the input/outputs
sim_specs = {
    'sim_f': init_obj,
    'in': ['p0', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7'],
    'out': [('RUNTIME', float),('elapsed_sec', float)],

}

cs = CS.ConfigurationSpace(seed=1234)
# number of threads
#p0= CSH.OrdinalHyperparameter(name='p0', sequence=['2','4','8','16','32','48','64','96','128','192','256'], default_value='64')
p0= CSH.OrdinalHyperparameter(name='p0', sequence=[2, 4, 8, 16, 32, 48, 64, 96, 128, 192, 256], default_value=64)
# omp placement
p1= CSH.CategoricalHyperparameter(name='p1', choices=['cores','threads','sockets'], default_value='cores')
# OMP_PROC_BIND
p2= CSH.CategoricalHyperparameter(name='p2', choices=['close','spread','master'], default_value='close')
# OMP_SCHEDULE
p3= CSH.CategoricalHyperparameter(name='p3', choices=['dynamic','static'], default_value='static')
#omp parallel
p4= CSH.CategoricalHyperparameter(name='p4', choices=['#pragma omp parallel for',' '], default_value=' ')
#unroll
p5= CSH.CategoricalHyperparameter(name='p5', choices=['#pragma unroll (6)','#pragma unroll',' '], default_value=' ')
#omp parallel
p6= CSH.CategoricalHyperparameter(name='p6', choices=['#pragma omp for','#pragma omp for nowait'], default_value='#pragma omp for')
#MPI Barrier
p7= CSH.CategoricalHyperparameter(name='p7', choices=['MPI_Barrier(MPI_COMM_WORLD);',' '], default_value='MPI_Barrier(MPI_COMM_WORLD);')

cs.add_hyperparameters([p0, p1, p2, p3, p4, p5, p6, p7])

ytoptimizer = Optimizer(
    num_workers=num_sim_workers,
    space=cs,
    learner='RF',
    liar_strategy='cl_max',
    acq_func='gp_hedge',
    #These values are added by me later
    set_KAPPA=1.96,
    set_SEED=12345,
    set_NI=10,
)

# Declare the gen_f that will generate points for the sim_f, and the various input/outputs
gen_specs = {
    'gen_f': persistent_ytopt,
    #'out': [('p0', "<U9", (1,)), ('p1', "<U9", (1,)), ('p2', "<U9", (1,)),
    #        ('p3', "<U9", (1,)), ('p4', "<U30", (1,)), ('p5', "<U30", (1,)), ('p6', "<U30", (1,)), ('p7', "<U30", (1,)), ],

    'out': [('p0', int, (1,)), ('p1', "<U9", (1,)), ('p2', "<U9", (1,)),
            ('p3', "<U9", (1,)), ('p4', "<U30", (1,)), ('p5', "<U30", (1,)), ('p6', "<U30", (1,)), ('p7', "<U30", (1,)), ],

    'persis_in': sim_specs['in'] + ['RUNTIME'] + ['elapsed_sec'],
    'user': {
        'ytoptimizer': ytoptimizer,  # provide optimizer to generator function
        'num_sim_workers': num_sim_workers,
    },
}

alloc_specs = {
    'alloc_f': alloc_f,
    'user': {'async_return': True},
}

# Specify when to exit. More options: https://libensemble.readthedocs.io/en/main/data_structures/exit_criteria.html
exit_criteria = {'gen_max': 2000}

# Added as a workaround to issue that's been resolved on develop
persis_info = add_unique_random_streams({}, nworkers + 1)

# Perform the libE run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info,
                            alloc_specs=alloc_specs, libE_specs=libE_specs)

# Save History array to file
if is_manager:
    print("\nlibEnsemble has completed evaluations.")
    #save_libE_output(H, persis_info, __file__, nworkers)

    #print("\nSaving just sim_specs[['in','out']] to a CSV")
    #H = np.load(glob.glob('*.npy')[0])
    #H = H[H["sim_ended"]]
    #H = H[H["returned"]]
    #dtypes = H[gen_specs['persis_in']].dtype
    #b = np.vstack(map(list, H[gen_specs['persis_in']]))
    #print(b)
    #np.savetxt('results.csv',b, header=','.join(dtypes.names), delimiter=',',fmt=','.join(['%s']*b.shape[1]))


