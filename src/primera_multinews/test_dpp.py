import numpy as np

def greedy_map(L, k):
    M = L.shape[0]
    selected = []
    candidates = list(range(M))
    
    for _ in range(min(k, M)):
        best_idx = -1
        best_det = -float('inf')
        
        for i in candidates:
            subset = selected + [i]
            sub_L = L[np.ix_(subset, subset)]
            sign, log_det = np.linalg.slogdet(sub_L)
            val = log_det if sign > 0 else -float('inf')
            
            if val > best_det:
                best_det = val
                best_idx = i
                
        if best_idx != -1:
            selected.append(best_idx)
            candidates.remove(best_idx)
        else:
            break
            
    return selected

L = np.array([[10, 8], [8, 10]])
print("k=1:", greedy_map(L, 1))
print("k=2:", greedy_map(L, 2))
