VERBOSE = False
PPRINT = False


def log(*values):
    """
    Log to console only if VERBOSE is set.

    :param values: log values
    :return:
    """
    if VERBOSE:
        print(*values)


def calculate_score(score, total) -> float:
    """
    Calculates the score from (score, total) pair.

    :param score: summed up individual scores from child nodes (not previously divided by total)
    :param total: total number of leaf nodes involved in the subtree
    :return: calculated score
    """
    if total == 0:
        return 0
    return score / total
