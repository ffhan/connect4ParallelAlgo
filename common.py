VERBOSE = False


def log(*values):
    if VERBOSE:
        print(*values)


def calculate_score(score, total) -> float:
    if total == 0:
        return 0
    return score / total
