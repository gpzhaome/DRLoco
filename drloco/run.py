"""
Loads a specified model (by path or from config) and executes it.
The policy can be used sarcastically and deterministically.
"""
# add current working directory to the system path
import sys
from os import getcwd
sys.path.append(getcwd())

import gym, time, mujoco_py
from drloco.mujoco.monitor_wrapper import Monitor
from stable_baselines3 import PPO
from drloco.common.utils import load_env, get_project_path
from drloco.config import hypers as cfg
from drloco.config import config as cfgl
from drloco.mujoco.mimic_walker3d import MimicWalker3dEnv
from drloco.mujoco.mimic_walker_165cm_65kg import MimicWalker165cm65kgEnv

# paths
# PD baseline
path_pd_baseline = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/' \
                   'cstm_pi/mim3d/8envs/ppo2/16mio/918-evaled-ret71'
path_pd_normed_deltas = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/' \
                        'pi_deltas/norm_acts/cstm_pi/mim3d/8envs/ppo2/16mio/431-evaled-ret81'
path_trq_baseline = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/' \
                    'cstm_pi/mim_trq_ff3d/8envs/ppo2/8mio/296-evaled-ret79'
path_mirr_steps = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/' \
                  'steps_mirr/cstm_pi/mim_trq_ff3d/8envs/ppo2/8mio/280'
path_mirr_exps = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/' \
                 'mirr_exps/cstm_pi/mim_trq_ff3d/8envs/ppo2/16mio/331-evaled-ret86'
path_guoping = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/cstm_pi/' \
               'mirr_exps/MimicWalker3d-v0/8envs/ppo2/8mio/361'
path_140cm_40kg = '/mnt/88E4BD3EE4BD2EF6/Masters/M.Sc. Thesis/Code/models/dmm/cstm_pi/' \
                  'refs_ramp/mirr_exps/MimicWalker3d-v0/8envs/ppo2/16mio/197-evaled-ret78'
path_agent = get_project_path() + 'models/dmm/cstm_pi/mim_trq_ff3d/8envs/ppo2/8mio/296-evaled-ret79'
path_agent = '/mnt/88E4BD3EE4BD2EF6/Users/Sony/Google Drive/WORK/DRL/CodeTorch/models/train/' \
             'cstm_pi/refs_ramp/mirr_py/MimicWalker3d-v0/8envs/ppo2/4mio/885'

DETERMINISTIC_ACTIONS = True
RENDER = True

SPEED_CONTROL = False
speeds = [0.5, 1, 1.25, 1.25]
duration_secs = 8

PLAYBACK_TRAJECS = True

# which model would you like to run
FROM_PATH = False
PATH = path_agent
checkpoint = 'final' # 'ep_ret2100_20M' # '33_min24mean24' # 'ep_ret2000_7M' #'mean_rew60'

if FROM_PATH:
    if not PATH.endswith('/'): PATH += '/'

    # load model
    model_path = PATH + f'models/model_{checkpoint}'
    model = PPO.load(path=model_path)
    print('\nModel:\n', model_path + '\n')

    env = load_env(checkpoint, PATH, cfg.env_id)
else:
    from drloco.mujoco.config import env_map
    env = env_map[cfgl.ENV_ID]()
    env = Monitor(env)
    vec_env = env
    if PLAYBACK_TRAJECS:
        obs = vec_env.reset()
        env.activate_evaluation()
        env.playback_ref_trajectories(2000)

if not isinstance(env, Monitor):
    # VecNormalize wrapped DummyVecEnv
    vec_env = env
    env = env.venv.envs[0]

if SPEED_CONTROL:
    env.activate_speed_control(speeds, duration_secs)
    cfg.ep_dur_max = duration_secs * cfgl.CTRL_FREQ
    des_speeds = []
    com_speeds = []

obs = vec_env.reset()
# env.activate_evaluation()


for i in range(10000):

    if FROM_PATH:
        action, hid_states = model.predict(obs, deterministic=DETERMINISTIC_ACTIONS)
        obs, reward, done, _ = vec_env.step(action)
    else:
        action = env.action_space.sample()
        obs, reward, done, _ = env.step(action)

    # only stop episode when agent has fallen
    com_z_pos = env.get_COM_Z_position()
    done = com_z_pos < 0.5

    if SPEED_CONTROL:
        des_speeds.append(env.desired_walking_speed)
        com_speeds.append(env.get_qvel()[0])

    if RENDER: env.render()
    if done: env.reset()
    if SPEED_CONTROL and i >= cfg.ep_dur_max:
        from matplotlib import pyplot as plt
        plt.plot(des_speeds)
        plt.plot(com_speeds)
        plt.legend(['Desired Walking Speed', 'COM X Velocity'])
        plt.show()
        exit(33)

env.close()