from math import sqrt


# Increment or Decrement a Mean
def incr_mean(mean, n, add_v=0, sub_v=0):

    n_pr = incr_n(n, add_v, sub_v)

    if n_pr == 0:
        return 0

    v = add_v - sub_v

    return (n * mean + v) / n_pr


# Increment or Decrement a Sum of Squares
def incr_sum_sq(sum_sq, add_v=0, sub_v=0):
    return sum_sq + (add_v ** 2) - (sub_v ** 2)


# Increment or Decrement a Standard Deviation
def incr_stdev(mean, sum_sq_pr, n, add_v=0, sub_v=0):

    n_pr = incr_n(n, add_v, sub_v)

    if n_pr == 0:
        return 0

    v = add_v - sub_v

    sum_pr = n * mean + v

    return sqrt((sum_sq_pr / n_pr) - (sum_pr ** 2) / n_pr / n_pr)


def incr_n(n, add_v=0, sub_v=0):

    n_pr = n

    if add_v > 0:
        n_pr += 1
    if sub_v > 0:
        n_pr -= 1

    return n_pr


# Adjusted Cosine Similarity with Significance Weighting
def adj_cos_sim(uij):

    sum_prods = 0
    sum_sqs_i = 0
    sum_sqs_j = 0

    gamma = 25

    for user_id in uij:

        rui_sub_ru = uij[user_id]['rating'] - uij[user_id]['rating_mean']
        ruj_sub_ru = uij[user_id]['rating_j'] - uij[user_id]['rating_mean']

        sum_prods += rui_sub_ru * ruj_sub_ru
        sum_sqs_i += rui_sub_ru ** 2
        sum_sqs_j += ruj_sub_ru ** 2

    denominator = sqrt(sum_sqs_i * sum_sqs_j)

    if denominator == 0:
        return 0

    similarity = sum_prods / denominator
    significance = min(len(uij), gamma) / gamma

    return significance * similarity


# Rating Prediction
def predict_rating(data_i):

    weighted_sum = 0
    sum_weights = 0

    for sim_id in data_i['sims']:
        sim = data_i['sims'][sim_id]
        weighted_sum += sim['sim_ij'] * (sim['rating_j'] - sim['mean_j']) / sim['stdev_j']
        sum_weights += abs(sim['sim_ij'])

    return data_i['mean_i'] + data_i['stdev_i'] * (weighted_sum / sum_weights)
