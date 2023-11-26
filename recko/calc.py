from math import sqrt


def incr_mean(mean, n, add_v=0, sub_v=0):

    n_pr = incr_n(n, add_v, sub_v)

    if n_pr == 0:
        return 0

    v = add_v - sub_v

    return (n * mean + v) / n_pr


def incr_sum_sq(sum_sq, add_v=0, sub_v=0):
    return sum_sq + (add_v ** 2) - (sub_v ** 2)


def incr_stdev(mean, sum_sq_pr, n, add_v=0, sub_v=0):

    n_pr = incr_n(n, add_v, sub_v)

    if n_pr == 0:
        return 0

    v = add_v - sub_v

    sum_pr = n * mean + v

    return sqrt(sum_sq_pr / n_pr - (sum_pr ** 2) / n_pr / n_pr)


def incr_n(n, add_v=0, sub_v=0):

    n_pr = n

    if add_v > 0:
        n_pr += 1
    if sub_v > 0:
        n_pr -= 1

    return n_pr
