# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from deep_rl import *

FOLDER = '/Users/Shangtong/Dropbox/Paper/geoff-pac/img'


def plot(**kwargs):
    kwargs.setdefault('average', False)
    # kwargs.setdefault('color', 0)
    kwargs.setdefault('top_k', 0)
    kwargs.setdefault('max_timesteps', 1e8)
    kwargs.setdefault('window', 100)
    kwargs.setdefault('down_sample', True)
    kwargs.setdefault('root', '../large_logs/two-circle')
    kwargs.setdefault('type', 'mean')
    plt.rc('text', usetex=True)

    plotter = Plotter()
    names = plotter.load_log_dirs(**kwargs)
    data = plotter.load_tf_results(names, 'p0', kwargs['window'], align=True)
    if len(data) == 0:
        print('FIle not found')
        return
    print('')

    if kwargs['average']:
        color = kwargs['color']
        x = np.asarray(data[0][0])
        y = [y for _, y in data]
        y = np.asarray(y)
        print(y.shape)
        if kwargs['down_sample']:
            indices = np.linspace(0, len(x) - 1, 500).astype(np.int)
            x = x[indices]
            y = y[:, indices]
        name = names[0].split('/')[-1]
        kwargs.setdefault('label', name)
        if kwargs['type'] == 'mean':
            plotter.plot_standard_error(y, x, label=kwargs['label'], color=Plotter.COLORS[color])
        elif kwargs['type'] == 'median':
            plotter.plot_median_std(y, x, label=kwargs['label'], color=Plotter.COLORS[color])
        else:
            raise NotImplementedError

        # sns.tsplot(y, x, condition=name, , ci='sd')
        # plt.title(names[0])
    else:
        for i, name in enumerate(names):
            x, y = data[i]
            if 'color' not in kwargs.keys():
                color = Plotter.COLORS[i]
            else:
                color = Plotter.COLORS[kwargs['color']]
            plt.plot(x, y, color=color, label=name if i == 0 else '')
    if 'y_lim' in kwargs.keys():
        plt.ylim(kwargs['y_lim'])
    # plt.ylabel('episode return')


def ddpg_plot(**kwargs):
    kwargs.setdefault('average', True)
    kwargs.setdefault('color', 0)
    kwargs.setdefault('top_k', 0)
    kwargs.setdefault('max_timesteps', 1e8)
    kwargs.setdefault('type', 'mean')
    kwargs.setdefault('window', 0)

    plotter = Plotter()
    names = plotter.load_log_dirs(**kwargs)
    data = plotter.load_tf_results(names, tag=kwargs['tag'], align=True, window=kwargs['window'])
    if len(data) == 0:
        print('File not found')
        return

    # data = [y[: len(y) // kwargs['rep'] * kwargs['rep']] for x, y in data]
    # min_y = np.min([len(y) for y in data])
    # data = [y[:min_y] for y in data]
    # random_agent = np.asarray(data)[:, 0].mean()
    # new_data = []
    # for y in data:
    #     y = np.reshape(np.asarray(y), (-1, kwargs['rep'])).mean(-1)
    #     x = np.arange(y.shape[0]) * kwargs['x_interval']
    #     new_data.append([x, y])
    # data = new_data
    # random_agent = [x, [random_agent] * len(x)]

    if kwargs['top_k']:
        scores = []
        for x, y in data:
            scores.append(np.sum(y))
        best = list(reversed(np.argsort(scores)))
        best = best[:kwargs['top_k']]
        data = [data[i] for i in best]

    print('')

    game = kwargs['game']
    color = kwargs['color']
    if kwargs['average']:
        x = data[0][0]
        y = [entry[1] for entry in data]
        y = np.stack(y)
        if kwargs['type'] == 'mean':
            plotter.plot_standard_error(y, x, label=kwargs['label'], color=Plotter.COLORS[color])
        elif kwargs['type'] == 'median':
            plotter.plot_median_std(y, x, label=kwargs['label'], color=Plotter.COLORS[color])
        else:
            raise NotImplementedError
    else:
        for i, name in enumerate(names):
            x, y = data[i]
            plt.plot(x, y, color=Plotter.COLORS[i], label=name if i == 0 else '')
    # return random_agent


def plot_mujoco_learning_curves(**kwargs):
    kwargs.setdefault('average', True)
    kwargs.setdefault('top_k', 0)
    kwargs.setdefault('type', 'mean')
    kwargs.setdefault('tag', 'averaged_value')
    kwargs.setdefault('ddpg', False)

    games = [
        'HalfCheetah-v2',
        'Walker2d-v2',
        'Hopper-v2',
        'Reacher-v2',
        'Swimmer-v2',
    ]

    if kwargs['ddpg']:
        labels = [
            'Geoff-PAC',
            'DDPG',
        ]
    else:
        labels = [
            'Geoff-PAC',
            'ACE',
            'Off-PAC',
        ]

    def info(game):
        with open('data/random_agent_mujoco.bin', 'rb') as f:
            rnd_perf = pickle.load(f)
        rnd_perf = rnd_perf[game][kwargs['tag']]
        if kwargs['ddpg']:
            patterns = [
                'algo_geoff-pac-gamma_hat_0\.2-lam1_0\.7-lam2_0\.6-run',
                'remark_ddpg',
            ]
        else:
            patterns = [
                'algo_geoff-pac-gamma_hat_0\.2-lam1_0\.7-lam2_0\.6-run',
                'algo_ace-lam1_0-run',
                'algo_off-pac-run',
            ]
        if game == 'Reacher-v2':
            x_ticks = [[0, int(2e4)], ['0', r'$2\times10^4$']]
            rnd_x = np.linspace(0, int(2e4), 100).astype(np.int)
        elif game == 'Swimmer-v2':
            x_ticks = [[0, int(5e6)], ['0', r'$5\times10^6$']]
            rnd_x = np.linspace(0, int(5e6), 100).astype(np.int)
        else:
            x_ticks = [[0, int(1e6)], ['0', r'$10^6$']]
            rnd_x = np.linspace(0, int(1e6), 100).astype(np.int)
        rnd_y = [rnd_perf] * len(rnd_x)
        return patterns, x_ticks, rnd_x, rnd_y

    l = len(games)
    plt.figure(figsize=(l * 5, 5))
    plt.rc('text', usetex=True)
    for j, game in enumerate(games):
        plt.subplot(1, l, j + 1)
        patterns, x_ticks, rnd_x, rnd_y = info(game)
        for i, p in enumerate(patterns):
            ddpg_plot(pattern='.*geoff-pac-mujoco/.*%s.*%s.*' % (game, p), color=i, label=labels[i], game=game,
                      **kwargs)
        if not kwargs['ddpg']:
            plt.plot(rnd_x, rnd_y, color='black', linestyle=':')
        plt.xticks(*x_ticks, fontsize=30)
        plt.tick_params(axis='y', labelsize=30)
        if j == 0:
            plt.legend(fontsize=20, frameon=False)
            if kwargs['tag'] == 'averaged_value':
                plt.ylabel(r'$J_\pi$', fontsize=30, rotation='horizontal')
            elif kwargs['tag'] == 'episodic_return':
                plt.ylabel('Episode Return', fontsize=30)
            else:
                raise NotImplementedError
        if j > -1:
            plt.xlabel('Steps', fontsize=30)
        plt.title(game, fontsize=30, fontweight="bold")
    plt.tight_layout()
    plt.savefig('%s/mujoco-%s-%s-ddpg-%s.png' % (
        FOLDER, kwargs['type'], kwargs['tag'], kwargs['ddpg']), bbox_inches='tight')
    plt.show()


def plot_lam1_ACE(**kwargs):
    coefs = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    pattern_tmp = 'algo_ace-lam1_%s-run'
    label_template = r'$\lambda_1 = %s$'
    patterns = []
    labels = []
    for c in coefs:
        patterns.append(translate(pattern_tmp % (c)))
        labels.append(label_template % (c))

    for i, p in enumerate(patterns):
        ddpg_plot(pattern='.*geoff-pac-params/other/.*%s.*%s.*' % (kwargs['game'], p), color=i, label=labels[i],
                  **kwargs)
    plt.title('ACE', fontsize=25)
    plt.xticks([0, int(1e6)], ['0', r'$10^6$'])
    plt.legend()


def plot_lam1_GeoffPAC(**kwargs):
    patterns = [
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_1-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0\.1-lam2_1-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0\.2-lam2_1-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0\.4-lam2_1-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0\.8-lam2_1-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_1-lam2_1-run',
    ]

    label_template = r'$\lambda_1 = %s$'
    labels = []
    for i in [0, 0.1, 0.2, 0.4, 0.8, 1]:
        labels.append(label_template % (i))

    for i, p in enumerate(patterns):
        ddpg_plot(pattern='.*geoff-pac-5/.*%s.*%s.*' % (kwargs['game'], p), color=i, label=labels[i], **kwargs)
    plt.title(r'Geoff-PAC ($\lambda_2=1, \hat{\gamma}=0.1$)', fontsize=25, fontweight="bold")
    plt.xticks([0, int(1e6)], ['0', r'$10^6$'])
    plt.legend()


def plot_lam2_GeoffPAC(**kwargs):
    patterns = [
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_0-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_0\.1-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_0\.2-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_0\.4-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_0\.8-run',
        'algo_geoff-pac-gamma_hat_0\.1-lam1_0-lam2_1-run',
    ]

    label_template = r'$\lambda_2 = %s$'
    labels = []
    for i in [0, 0.1, 0.2, 0.4, 0.8, 1]:
        labels.append(label_template % (i))

    for i, p in enumerate(patterns):
        ddpg_plot(pattern='.*geoff-pac-5/.*%s.*%s.*' % (kwargs['game'], p), color=i, label=labels[i], **kwargs)
    plt.title(r'Geoff-PAC ($\lambda_1=0, \hat{\gamma}=0.1$)', fontsize=25, fontweight="bold")
    plt.xticks([0, int(1e6)], ['0', r'$10^6$'])
    plt.legend()


def plot_gamma_hat_GeoffPAC(**kwargs):
    coefs = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    # pattern_tmp = 'algo_geoff-pac-gamma_hat_%s-lam1_0.3-lam2_0.1-run'
    pattern_tmp = 'algo_geoff-pac-gamma_hat_%s-lam1_0.7-lam2_0.6-run'
    label_template = r'$\hat{\gamma} = %s$'
    patterns = []
    labels = []
    for c in coefs:
        patterns.append(translate(pattern_tmp % (c)))
        labels.append(label_template % (c))

    for i, p in enumerate(patterns):
        ddpg_plot(pattern='.*geoff-pac-params/other/.*%s.*%s.*' % (kwargs['game'], p), color=i, label=labels[i],
                  **kwargs)
    plt.title(r'Geoff-PAC ($\lambda_1=0.7, \lambda_2=0.6$)', fontsize=25, fontweight="bold")
    plt.xticks([0, int(1e6)], ['0', r'$10^6$'])
    plt.legend()


def plot_parameter_study(type):
    kwargs = {
        'average': True,
        'top_k': 0,
        'game': 'HalfCheetah-v2',
        # 'tag': 'episodic_return',
        'tag': 'averaged_value',
        'type': type,
    }
    # funcs = [plot_lam1_ACE, plot_lam1_GeoffPAC, plot_lam2_GeoffPAC, plot_gamma_hat_GeoffPAC]
    funcs = [plot_lam1_ACE, plot_gamma_hat_GeoffPAC]
    for i in range(len(funcs)):
        plt.figure(figsize=(5, 5))
        plt.rc('text', usetex=True)
        # plt.subplot(1, len(funcs), i + 1)
        plt.ylim([-60, 30])
        funcs[i](**kwargs)
        plt.xlabel('Steps', fontsize=20)
        plt.ylabel(r'$J_\pi$', fontsize=20, rotation='horizontal')
        plt.tick_params(axis='both', labelsize=30)
        plt.tight_layout()
        plt.savefig('%s/params-%d.png' % (FOLDER, i), bbox_inches='tight')
        plt.show()


def extract_heatmap_data():
    coef = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

    results = {}
    plotter = Plotter()
    root = '../large_logs/two-circle'
    for gamma_hat in coef:
        for lam2 in coef:
            print(gamma_hat, lam2)
            pattern = 'alg_GACE-gamma_hat_%s-lam2_%s-run' % (gamma_hat, lam2)
            pattern = translate(pattern)
            pattern = '.*%s.*' % (pattern)
            print(pattern)
            dirs = plotter.load_log_dirs(pattern, root=root)
            data = plotter.load_tf_results(dirs, 'p0', align=True)
            _, y = zip(*data)
            y = np.asarray(y)
            print(y.shape)
            y = y[:, :-100].mean()
            results[(gamma_hat, lam2)] = y

    print(results)
    with open('data/two-circle.bin', 'wb') as f:
        pickle.dump(results, f)


def two_circle_heatmap():
    plt.figure(figsize=(5, 4))
    plt.tight_layout()
    plt.rc('text', usetex=True)
    with open('data/two-circle.bin', 'rb') as f:
        data = pickle.load(f)
    print(data)
    coef = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    p0 = np.zeros((len(coef[:-1]), len(coef)))
    for i in range(len(coef[:-1])):
        for j in range(len(coef)):
            p0[i, j] = data[(coef[i], coef[j])]
    p0 = np.flip(p0, 0)
    sns.set(font_scale=2)
    ax = sns.heatmap(p0, cmap='YlGnBu')
    # ax.set_xticks(np.arange(0, 11) + 0.5)
    ax.set_xticks([0.5, 10.5])
    ax.set_xticklabels(['0', '1'], fontsize=30)
    # ax.set_xticklabels(['%s' % x for x in coef], fontsize=15)
    # ax.set_yticks(np.arange(0, 10) + 0.5)
    ax.set_yticks([0.5, 9.5])
    ax.set_yticklabels(['0.9', '0'], rotation='horizontal', fontsize=30)
    # ax.set_yticklabels(['%s' % x for x in reversed(coef[:-1])], rotation='horizontal', fontsize=15)
    plt.xlabel(r'$\lambda_2$', fontsize=30)
    plt.ylabel(r'$\hat{\gamma}$', rotation='horizontal', fontsize=30)
    plt.title(r'$\pi(\texttt{A} \rightarrow \texttt{B})$', fontsize=30)
    plt.savefig('%s/mdp-heatmap.png' % (FOLDER), bbox_inches='tight')
    plt.show()


def two_circle_learning_curve():
    kwargs = {
        'window': 0,
        'top_k': 0,
        'max_timesteps': int(1e5),
        'average': True,
        'x_interval': 100
    }

    patterns = [
        'alg_GACE-gamma_hat_0.9-lam2_1-run',
        'alg_ACE-run',
        # 'alg_GACE-gamma_hat_0.9-lam2_0-run',
        # 'alg_GACE-gamma_hat_0.9-lam2_0.2-run',
        # 'alg_GACE-gamma_hat_0.9-lam2_0.4-run',
        # 'alg_GACE-gamma_hat_0.9-lam2_0.6-run',
        # 'alg_GACE-gamma_hat_0.9-lam2_0.8-run',
    ]

    labels = [
        'Geoff-PAC',
        'ACE',
    ]

    plt.tight_layout()
    plt.figure(figsize=(5, 5))
    for i, p in enumerate(patterns):
        p = translate(p)
        plot(pattern='.*%s.*' % (p), color=i, label=labels[i], **kwargs)
    plt.xticks([0, int(1e4)], ['0', r'$10^4$'], fontsize=30)
    plt.xlabel('Steps', fontsize=30)
    plt.yticks([0, 1], ['0', '1'], fontsize=30)
    plt.ylabel(r'$\pi(\texttt{A} \rightarrow \texttt{B})$', fontsize=30)
    plt.legend(fontsize=30, frameon=False)
    plt.savefig('%s/mdp-curve.png' % (FOLDER), bbox_inches='tight')
    plt.show()


def extract_geoff_pac_heatmap():
    def measure(data):
        y = [y for x, y in data]
        y = np.asarray(y)
        y = y[:, -100:]
        return np.mean(y)

    plotter = Plotter()
    coefs = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    pattern_tmp = 'algo_geoff-pac-gamma_hat_0.1-lam1_%s-lam2_%s-run'
    data = dict()
    for lam1 in coefs:
        for lam2 in coefs:
            pattern = translate(pattern_tmp % (lam1, lam2))
            names = plotter.load_log_dirs(pattern='.*geoff-pac-params/.*%s.*' % (pattern))
            R = plotter.load_tf_results(names, tag='episodic_return', align=True)
            J = plotter.load_tf_results(names, tag='averaged_value', align=True)
            data[(lam1, lam2)] = [measure(R), measure(J)]
            print('lam1 %s, lam2 %s' % (lam1, lam2))
            print(data[(lam1, lam2)])

    with open('data/geoff_pac_heatmap.bin', 'wb') as f:
        pickle.dump(data, f)


def plot_geoff_pac_heatmap(key='J'):
    plt.figure(figsize=(5, 4.5))
    plt.tight_layout()
    plt.rc('text', usetex=True)
    with open('data/geoff_pac_heatmap.bin', 'rb') as f:
        data = pickle.load(f)
    print(data)
    coef = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    perf = np.zeros((len(coef), len(coef)))
    for i in range(len(coef)):
        for j in range(len(coef)):
            if key == 'J':
                perf[i, j] = data[(coef[i], coef[j])][1]
            elif key == 'R':
                perf[i, j] = data[(coef[i], coef[j])][0]
            else:
                raise NotImplementedError
    ax = sns.heatmap(perf, cmap='YlGnBu')
    ax.set_xticks(np.arange(0, 11) + 0.5)
    ax.set_xticklabels(['%s' % x for x in coef])
    ax.set_yticks(np.arange(0, 11) + 0.5)
    ax.set_yticklabels(['%s' % x for x in coef], rotation='horizontal')
    plt.xlabel(r'$\lambda_2$', fontsize=20)
    plt.ylabel(r'$\lambda_1$', rotation='horizontal', fontsize=20)
    plt.title(r'$J_\pi \, (\hat{\gamma}=0.1)$', fontsize=25)
    plt.savefig('%s/geoff-pac-heatmap.png' % (FOLDER), bbox_inches='tight')
    plt.show()


def get_td3_baseline(game):
    dir = './log/geoff-pac-td3'
    data = []
    for seed in range(10):
        filename = 'TD3_%s_%s.npy' % (game, str(seed))
        file = '%s/%s' % (dir, filename)
        data.append(np.load(file))
    return np.asarray(data)


def rebuttal_with_td3(**kwargs):
    kwargs.setdefault('average', True)
    kwargs.setdefault('top_k', 0)
    kwargs.setdefault('type', 'mean')
    kwargs.setdefault('tag', 'episodic_return')
    kwargs.setdefault('ddpg', True)

    games = [
        'HalfCheetah-v2',
        'Walker2d-v2',
        'Hopper-v2',
        'Reacher-v2',
        'Swimmer-v2',
    ]

    labels = [
        'Geoff-PAC',
        'DDPG',
        'TD3',
    ]

    def info(game):
        with open('data/Geoff-PAC/random_agent_mujoco.bin', 'rb') as f:
            rnd_perf = pickle.load(f)
        rnd_perf = rnd_perf[game][kwargs['tag']]
        if kwargs['ddpg']:
            patterns = [
                'algo_geoff-pac-gamma_hat_0\.2-lam1_0\.7-lam2_0\.6-run',
                'remark_ddpg',
            ]
        else:
            patterns = [
                'algo_geoff-pac-gamma_hat_0\.2-lam1_0\.7-lam2_0\.6-run',
                'algo_ace-lam1_0-run',
                'algo_off-pac-run',
            ]
        if game == 'Reacher-v2':
            x_ticks = [[0, int(2e4)], ['0', r'$2\times10^4$']]
            rnd_x = np.linspace(0, int(2e4), 100).astype(np.int)
        elif game == 'Swimmer-v2':
            x_ticks = [[0, int(5e6)], ['0', r'$5\times10^6$']]
            rnd_x = np.linspace(0, int(5e6), 100).astype(np.int)
        else:
            x_ticks = [[0, int(1e6)], ['0', r'$10^6$']]
            rnd_x = np.linspace(0, int(1e6), 100).astype(np.int)
        rnd_y = [rnd_perf] * len(rnd_x)
        return patterns, x_ticks, rnd_x, rnd_y

    def get_td3_data(game):
        y = get_td3_baseline(game)
        if game == 'Reacher-v2':
            x = np.linspace(0, 2e4, y.shape[1]).astype(np.int)
        else:
            x = np.linspace(0, 1e6, y.shape[1]).astype(np.int)
        return x, y

    l = len(games)
    plt.figure(figsize=(l * 5, 5))
    plt.rc('text', usetex=True)
    for j, game in enumerate(games):
        plt.subplot(1, l, j + 1)
        patterns, x_ticks, rnd_x, rnd_y = info(game)
        for i, p in enumerate(patterns):
            ddpg_plot(pattern='.*geoff-pac-mujoco/.*%s.*%s.*' % (game, p), color=i, label=labels[i], game=game,
                      **kwargs)
        # if not kwargs['ddpg']:
        plt.plot(rnd_x, rnd_y, color='black', linestyle=':')
        td3_x, td3_y = get_td3_data(game)
        plt_ = Plotter()
        plt_.plot_standard_error(td3_y, td3_x, label='TD3', color='r')
        plt.xticks(*x_ticks, fontsize=30)
        plt.tick_params(axis='y', labelsize=30)
        if j == 0:
            plt.legend(fontsize=20, frameon=False)
            if kwargs['tag'] == 'averaged_value':
                plt.ylabel(r'$J_\pi$', fontsize=30, rotation='horizontal')
            elif kwargs['tag'] == 'episodic_return':
                plt.ylabel('Episode Return', fontsize=30)
            else:
                raise NotImplementedError
        if j > -1:
            plt.xlabel('Steps', fontsize=30)
        plt.title(game, fontsize=30, fontweight="bold")
    plt.tight_layout()
    plt.savefig('%s/rebuttal.png' % (FOLDER), bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    # two_circle_heatmap()
    # two_circle_learning_curve()
    # plot_parameter_study('mean')
    # plot_geoff_pac_heatmap('J')
    # plot_mujoco_learning_curves(type='mean', tag='averaged_value', top_k=0, ddpg=False)
    # plot_mujoco_learning_curves(type='mean', tag='averaged_value', top_k=0, ddpg=True)
    # plot_mujoco_learning_curves(type='mean', tag='episodic_return', top_k=0, ddpg=False)
    # plot_mujoco_learning_curves(type='mean', tag='episodic_return', top_k=0, ddpg=True)

    # extract_heatmap_data()
    # extract_geoff_pac_heatmap()

    rebuttal_with_td3()
