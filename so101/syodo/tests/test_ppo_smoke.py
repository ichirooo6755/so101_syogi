from __future__ import annotations

from stable_baselines3 import PPO

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.train import _plot_rewards


def test_ppo_can_learn_save_and_reload(tmp_path) -> None:
    env = CalligraphyEnv("line")
    model = PPO(
        "MlpPolicy",
        env,
        n_steps=32,
        batch_size=16,
        policy_kwargs={"net_arch": [32, 32]},
        device="cpu",
        seed=1,
        verbose=0,
    )
    try:
        model.learn(total_timesteps=32)
        output = tmp_path / "smoke_model"
        model.save(output)
        loaded = PPO.load(output, env=env, device="cpu")
        observation, _ = env.reset(seed=2)
        action, _ = loaded.predict(observation, deterministic=True)
        assert env.action_space.contains(action)
    finally:
        env.close()


def test_monitor_rewards_are_plotted(tmp_path) -> None:
    monitor_dir = tmp_path / "train_logs"
    monitor_dir.mkdir()
    (monitor_dir / "train.monitor.csv").write_text(
        '#{"t_start": 0.0, "env_id": "none"}\n'
        "r,l,t,is_success,progress\n"
        "1.0,10,0.1,False,0.2\n"
        "3.0,12,0.2,True,1.0\n",
        encoding="utf-8",
    )
    _plot_rewards(tmp_path, monitor_dir)
    assert (tmp_path / "reward_curve.png").is_file()
