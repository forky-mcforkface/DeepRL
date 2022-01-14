#######################################################################
# Copyright (C) 2017 Shangtong Zhang(zhangshangtong.cpp@gmail.com)    #
# Permission given to modify the code as long as you keep this        #
# declaration at the top                                              #
#######################################################################

from ..network import *
from ..component import *
from .BaseAgent import *


class PPOAgent(BaseAgent):
    def __init__(self, config):
        BaseAgent.__init__(self, config)
        self.config = config
        self.task = config.task_fn()
        self.oracle = config.task_fn()
        self.oracle.reset()
        self.network = config.network_fn()
        if config.shared_repr:
            self.opt = config.optimizer_fn(self.network.parameters())
        else:
            self.actor_opt = config.actor_opt_fn(self.network.actor_params)
            self.critic_opt = config.critic_opt_fn(self.network.critic_params)
        self.total_steps = 0
        self.states = self.task.reset()
        self.states = config.state_normalizer(self.states)
        if config.shared_repr:
            self.lr_scheduler = torch.optim.lr_scheduler.LambdaLR(
                self.opt, lambda step: 1 - step / config.max_steps)

    def sample_trajectory_from(self, states, mj_state):
        config = self.config
        env = self.oracle
        env.reset()
        env.set_state(mj_state)
        all_rewards = []
        while True:
            prediction = self.network(states)
            next_states, rewards, terminals, info = env.step(
                to_np(prediction['a']))
            all_rewards.append(rewards[0])
            if terminals[0]:
                break
            states = config.state_normalizer(next_states)
        cum_r = 0
        for r in reversed(all_rewards):
            cum_r = r + config.discount * cum_r
        return cum_r

    def compute_oracle_v(self, states, mj_state):
        self.config.state_normalizer.set_read_only()
        rets = []
        for i in range(self.config.mc_n):
            rets.append(self.sample_trajectory_from(states, mj_state))
        self.config.state_normalizer.unset_read_only()
        return tensor(rets).mean().view(1, 1)

    def step(self):
        config = self.config
        storage = Storage(config.rollout_length, ['oracle_v', 'oracle_adv'])
        states = self.states
        for _ in range(config.rollout_length):
            if config.use_oracle_v:
                oracle_v = self.compute_oracle_v(states, self.task.get_state())
            else:
                oracle_v = tensor([0]).view(1, 1)
            prediction = self.network(states)
            next_states, rewards, terminals, info = self.task.step(
                to_np(prediction['a']))
            self.record_online_return(info)
            rewards = config.reward_normalizer(rewards)
            next_states = config.state_normalizer(next_states)
            storage.add(prediction)
            storage.add({'r': tensor(rewards).unsqueeze(-1),
                         'm': tensor(1 - terminals).unsqueeze(-1),
                         'next_s': tensor(next_states),
                         's': tensor(states),
                         'oracle_v': oracle_v})
            states = next_states
            self.total_steps += config.num_workers

        self.states = states
        prediction = self.network(states)
        if config.use_oracle_v or config.bootstrap_with_oracle:
            oracle_v = self.compute_oracle_v(states, self.task.get_state())
        else:
            oracle_v = tensor([0]).view(1, 1)
        if config.bootstrap_with_oracle:
            prediction['v'] = oracle_v
        storage.add(prediction)
        storage.add({'oracle_v': oracle_v})
        storage.placeholder()

        advantages = tensor(np.zeros((config.num_workers, 1)))
        returns = prediction['v'].detach()
        for i in reversed(range(config.rollout_length)):
            returns = storage.r[i] + config.discount * storage.m[i] * returns
            if not config.use_gae:
                advantages = returns - storage.v[i].detach()
            else:
                td_error = storage.r[i] + config.discount * \
                    storage.m[i] * storage.v[i + 1] - storage.v[i]
                advantages = advantages * config.gae_tau * \
                    config.discount * storage.m[i] + td_error
            oracle_adv = storage.r[i] + config.discount * \
                storage.m[i] * storage.oracle_v[i + 1] - \
                storage.oracle_v[i]
            storage.adv[i] = advantages.detach()
            storage.ret[i] = returns.detach()
            storage.oracle_adv[i] = oracle_adv

        states, actions, log_probs_old, returns, advantages, next_states, rewards, masks, oracle_adv \
            = storage.cat(['s', 'a', 'log_pi_a', 'ret', 'adv', 'next_s', 'r', 'm', 'oracle_adv'])

        actions = actions.detach()
        log_probs_old = log_probs_old.detach()
        if config.normalized_adv:
            advantages = (advantages - advantages.mean()) / advantages.std()

        if config.shared_repr:
            self.lr_scheduler.step(self.total_steps)

        for _ in range(config.optimization_epochs):
            sampler = random_sample(
                np.arange(states.size(0)), config.mini_batch_size)
            for batch_indices in sampler:
                batch_indices = tensor(batch_indices).long()
                sampled_states = states[batch_indices]
                sampled_actions = actions[batch_indices]
                sampled_log_probs_old = log_probs_old[batch_indices]
                sampled_returns = returns[batch_indices]
                sampled_advantages = advantages[batch_indices]

                sampled_next_states = next_states[batch_indices]
                sampled_rewards = rewards[batch_indices]
                sampled_masks = masks[batch_indices]

                if config.use_oracle_v:
                    sampled_advantages = oracle_adv[batch_indices]

                prediction = self.network(sampled_states, sampled_actions)
                ratio = (prediction['log_pi_a'] - sampled_log_probs_old).exp()
                obj = ratio * sampled_advantages
                obj_clipped = ratio.clamp(1.0 - self.config.ppo_ratio_clip,
                                          1.0 + self.config.ppo_ratio_clip) * sampled_advantages
                policy_loss = -torch.min(obj, obj_clipped).mean() - \
                    config.entropy_weight * prediction['ent'].mean()

                if config.critic_update == 'mc':
                    value_loss = 0.5 * (sampled_returns -
                                        prediction['v']).pow(2).mean()
                elif config.critic_update == 'td':
                    with torch.no_grad():
                        prediction_next = self.network(sampled_next_states)
                    target = sampled_rewards + config.discount * \
                        sampled_masks * prediction_next['v']
                    value_loss = 0.5 * (target - prediction['v']).pow(2).mean()

                approx_kl = (sampled_log_probs_old -
                             prediction['log_pi_a']).mean()
                if config.shared_repr:
                    self.opt.zero_grad()
                    (policy_loss + value_loss).backward()
                    nn.utils.clip_grad_norm_(
                        self.network.parameters(), config.gradient_clip)
                    self.opt.step()
                else:
                    if approx_kl <= 1.5 * config.target_kl:
                        self.actor_opt.zero_grad()
                        policy_loss.backward()
                        self.actor_opt.step()
                    self.critic_opt.zero_grad()
                    value_loss.backward()
                    self.critic_opt.step()
