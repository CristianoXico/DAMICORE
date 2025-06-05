import numpy as np

def non_dominated_sort_fast(objs):
    """
    Realiza a ordenação não-dominada (NSGA-II) para encontrar a fronteira de Pareto.
    objs: np.ndarray (n_amostras, n_objetivos)
    return: np.ndarray (n_amostras,) com o ranking de Pareto
    """
    n, m = objs.shape
    le_matrix = np.all(objs[:, None, :] <= objs[None, :, :], axis=2)
    lt_matrix = np.any(objs[:, None, :] < objs[None, :, :], axis=2)
    dominates = le_matrix & lt_matrix
    dominated_count = np.sum(dominates, axis=0)
    current_front = np.where(dominated_count == 0)[0].tolist()
    rank = np.zeros(n, dtype=int)
    i = 1
    while current_front:
        for p in current_front:
            rank[p] = i
            for q in np.where(dominates[p])[0]:
                dominated_count[q] -= 1
        next_front = [q for p in current_front for q in np.where(dominates[p])[0] if dominated_count[q] == 0]
        i += 1
        current_front = list(set(next_front))
    return rank
